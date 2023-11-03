from dataclasses import dataclass
from enum import StrEnum, Enum

from tuya_ble import AbstaractTuyaBLEDeviceManager, TuyaBLEDeviceCredentials


class SwitchDeviceClass(StrEnum):
    """Device class for switches."""

    OUTLET = "outlet"
    SWITCH = "switch"


class ButtonDeviceClass(StrEnum):
    """Device class for buttons."""

    IDENTIFY = "identify"
    RESTART = "restart"
    UPDATE = "update"


class EntityCategory(StrEnum):
    """Category of an entity.

    An entity with a category will:
    - Not be exposed to cloud, Alexa, or Google Assistant components
    - Not be included in indirect service calls to devices or areas
    """

    # Config: An entity which allows changing the configuration of a device.
    CONFIG = "config"

    # Diagnostic: An entity exposing some configuration parameter,
    # or diagnostics of a device.
    DIAGNOSTIC = "diagnostic"


class UndefinedType(Enum):
    """Singleton type for use with not set sentinel values."""

    _singleton = 0


UNDEFINED = UndefinedType._singleton  # pylint: disable=protected-access


@dataclass(slots=True)
class EntityDescription:
    """A class that describes Home Assistant entities."""

    # This is the key identifier for this entity
    key: str

    device_class: str | None = None
    entity_category: EntityCategory | None = None
    entity_registry_enabled_default: bool = True
    entity_registry_visible_default: bool = True
    force_update: bool = False
    icon: str | None = None
    has_entity_name: bool = False
    name: str | UndefinedType | None = UNDEFINED
    translation_key: str | None = None
    unit_of_measurement: str | None = None


@dataclass(slots=True)
class ToggleEntityDescription(EntityDescription):
    """A class that describes toggle entities."""


@dataclass
class SwitchEntityDescription(ToggleEntityDescription):
    """A class that describes switch entities."""

    device_class: SwitchDeviceClass | None = None


@dataclass
class ButtonEntityDescription(EntityDescription):
    """A class that describes button entities."""

    device_class: ButtonDeviceClass | None = None


from typing import TYPE_CHECKING, Any, Dict, Final, List, Optional, Type, TypeVar

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData

_BluetoothServiceInfoSelfT = TypeVar(
    "_BluetoothServiceInfoSelfT", bound="BluetoothServiceInfo"
)

_BluetoothServiceInfoBleakSelfT = TypeVar(
    "_BluetoothServiceInfoBleakSelfT", bound="BluetoothServiceInfoBleak"
)
SOURCE_LOCAL: Final = "local"

_float = float  # avoid cython conversion since we always want a pyfloat
_str = str  # avoid cython conversion since we always want a pystr
_int = int  # avoid cython conversion since we always want a pyint


class BaseServiceInfo:
    """Base class for discovery ServiceInfo."""


class BluetoothServiceInfo(BaseServiceInfo):
    """Prepared info from bluetooth entries."""

    __slots__ = (
        "name",
        "address",
        "rssi",
        "manufacturer_data",
        "service_data",
        "service_uuids",
        "source",
    )

    def __init__(
            self,
            name: _str,  # may be a pyobjc object
            address: _str,  # may be a pyobjc object
            rssi: _int,  # may be a pyobjc object
            manufacturer_data: Dict[_int, bytes],
            service_data: Dict[_str, bytes],
            service_uuids: List[_str],
            source: _str,
    ) -> None:
        """Initialize a bluetooth service info."""
        self.name = name
        self.address = address
        self.rssi = rssi
        self.manufacturer_data = manufacturer_data
        self.service_data = service_data
        self.service_uuids = service_uuids
        self.source = source

    @classmethod
    def from_advertisement(
            cls: Type[_BluetoothServiceInfoSelfT],
            device: "BLEDevice",
            advertisement_data: "AdvertisementData",
            source: str,
    ) -> _BluetoothServiceInfoSelfT:
        """Create a BluetoothServiceInfo from an advertisement."""
        return cls(
            advertisement_data.local_name or device.name or device.address,
            device.address,
            advertisement_data.rssi,
            advertisement_data.manufacturer_data,
            advertisement_data.service_data,
            advertisement_data.service_uuids,
            source,
        )

    @property
    def manufacturer(self) -> Optional[str]:
        """Convert manufacturer data to a string."""
        from bleak.backends._manufacturers import (
            MANUFACTURERS,  # pylint: disable=import-outside-toplevel
        )

        for manufacturer in self.manufacturer_data:
            if manufacturer in MANUFACTURERS:
                name: str = MANUFACTURERS[manufacturer]
                return name
        return None

    @property
    def manufacturer_id(self) -> Optional[int]:
        """Get the first manufacturer id."""
        for manufacturer in self.manufacturer_data:
            return manufacturer
        return None


class BluetoothServiceInfoBleak(BluetoothServiceInfo):
    """BluetoothServiceInfo with bleak data.

    Integrations may need BLEDevice and AdvertisementData
    to connect to the device without having bleak trigger
    another scan to translate the address to the system's
    internal details.
    """

    __slots__ = ("device", "advertisement", "connectable", "time")

    def __init__(
            self,
            name: _str,  # may be a pyobjc object
            address: _str,  # may be a pyobjc object
            rssi: _int,  # may be a pyobjc object
            manufacturer_data: Dict[_int, bytes],
            service_data: Dict[_str, bytes],
            service_uuids: List[_str],
            source: _str,
            device: "BLEDevice",
            advertisement: "AdvertisementData",
            connectable: "bool",
            time: "_float",
    ) -> None:
        self.name = name
        self.address = address
        self.rssi = rssi
        self.manufacturer_data = manufacturer_data
        self.service_data = service_data
        self.service_uuids = service_uuids
        self.source = source
        self.device = device
        self.advertisement = advertisement
        self.connectable = connectable
        self.time = time

    def as_dict(self) -> Dict[str, Any]:
        """Return as dict.

        The dataclass asdict method is not used because
        it will try to deepcopy pyobjc data which will fail.
        """
        return {
            "name": self.name,
            "address": self.address,
            "rssi": self.rssi,
            "manufacturer_data": self.manufacturer_data,
            "service_data": self.service_data,
            "service_uuids": self.service_uuids,
            "source": self.source,
            "advertisement": self.advertisement,
            "device": self.device,
            "connectable": self.connectable,
            "time": self.time,
        }

    @classmethod
    def from_scan(
            cls: Type[_BluetoothServiceInfoBleakSelfT],
            source: str,
            device: "BLEDevice",
            advertisement_data: "AdvertisementData",
            monotonic_time: "_float",
            connectable: "bool",
    ) -> _BluetoothServiceInfoBleakSelfT:
        """Create a BluetoothServiceInfoBleak from a scanner."""
        return cls(
            advertisement_data.local_name or device.name or device.address,
            device.address,
            advertisement_data.rssi,
            advertisement_data.manufacturer_data,
            advertisement_data.service_data,
            advertisement_data.service_uuids,
            source,
            device,
            advertisement_data,
            connectable,
            monotonic_time,
        )

    @classmethod
    def from_device_and_advertisement_data(
            cls: "Type[_BluetoothServiceInfoBleakSelfT]",
            device: "BLEDevice",
            advertisement_data: "AdvertisementData",
            source: str,
            time: "_float",
            connectable: "bool",
    ) -> _BluetoothServiceInfoBleakSelfT:
        """Create a BluetoothServiceInfoBleak from a device and advertisement."""
        return cls(
            advertisement_data.local_name or device.name or device.address,
            device.address,
            advertisement_data.rssi,
            advertisement_data.manufacturer_data,
            advertisement_data.service_data,
            advertisement_data.service_uuids,
            source,
            device,
            advertisement_data,
            connectable,
            time,
        )


class HASSTuyaBLEDeviceManager(AbstaractTuyaBLEDeviceManager):
    """Cloud connected manager of the Tuya BLE devices credentials."""

    async def get_device_credentials(
            self,
            address: str,
            force_update: bool = False,
            save_data: bool = False,
    ) -> TuyaBLEDeviceCredentials | None:
        if address.upper() == "DC:23:4E:8B:60:8F":
            return TuyaBLEDeviceCredentials(
                uuid="c3567acc6e99870d",
                local_key="F$|yP-$~MZ;qgm'#",
                device_id="bf7360fte8jomrnv",
                category="szjqr",
                product_id="xhf790if",
                device_name="CUBETOUCH II",
                product_model="",
                product_name="CUBETOUCH II"
            )
        elif address.upper() == "DC:23:4D:7B:E1:CE":
            return TuyaBLEDeviceCredentials(
                uuid="xmbmd29e724c403a",
                local_key=")YjXO2XH=09}nd#c",
                device_id="bf2d2eox9j31au8q",
                category="jtmspro",
                product_id="rlyxv7pe",
                device_name="Smart lock 2",
                product_model="",
                product_name="Smart lock",
            )

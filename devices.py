"""The Tuya BLE integration."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import logging
from typing import Callable, Coroutine, Any

from ha_mock import EntityDescription, BluetoothServiceInfoBleak
from tuya_ble import (
    AbstaractTuyaBLEDeviceManager,
    TuyaBLEDataPoint,
    TuyaBLEDevice,
    TuyaBLEDeviceCredentials,
)

from const import (
    DEVICE_DEF_MANUFACTURER,
    DOMAIN,
    FINGERBOT_BUTTON_EVENT,
    SET_DISCONNECTED_DELAY,
)

_LOGGER = logging.getLogger(__name__)
CALLBACK_TYPE = Callable[[], None]


@dataclass
class TuyaBLEFingerbotInfo:
    switch: int
    mode: int
    up_position: int
    down_position: int
    hold_time: int
    reverse_positions: int
    manual_control: int = 0
    program: int = 0


@dataclass
class TuyaBLEProductInfo:
    name: str
    manufacturer: str = DEVICE_DEF_MANUFACTURER
    fingerbot: TuyaBLEFingerbotInfo | None = None


class TuyaBLEEntity:
    """Tuya BLE base entity."""

    def __init__(
            self,
            coordinator: TuyaBLECoordinator,
            device: TuyaBLEDevice,
            product: TuyaBLEProductInfo,
            description: EntityDescription,
    ) -> None:
        # super().__init__(coordinator)
        self._coordinator = coordinator
        self._device = device
        self._product = product
        if description.translation_key is None:
            self._attr_translation_key = description.key
        self.entity_description = description
        self._attr_has_entity_name = True
        # self._attr_device_info = get_device_info(self._device)
        self._attr_unique_id = f"{self._device.device_id}-{description.key}"
        self.loop = asyncio.get_running_loop()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._coordinator.connected

    def create_task(self, target: Coroutine[Any, Any, Any]) -> None:
        """Add task to the executor pool.

        target: target to call.
        """
        self.loop.create_task(target)


class TuyaBLECoordinator():
    """Data coordinator for receiving Tuya BLE updates."""

    def __init__(self, device: TuyaBLEDevice) -> None:
        """Initialise the coordinator."""
        self._device = device
        self._disconnected: bool = True
        self._unsub_disconnect: CALLBACK_TYPE | None = None
        device.register_connected_callback(self._async_handle_connect)
        device.register_callback(self._async_handle_update)
        device.register_disconnected_callback(self._async_handle_disconnect)

    @property
    def connected(self) -> bool:
        return not self._disconnected

    def _async_handle_connect(self) -> None:
        if self._unsub_disconnect is not None:
            self._unsub_disconnect()
        if self._disconnected:
            self._disconnected = False
            # self.async_update_listeners()

    def _async_handle_update(self, updates: list[TuyaBLEDataPoint]) -> None:
        """Just trigger the callbacks."""
        self._async_handle_connect()
        # self.async_set_updated_data(None)
        info = get_device_product_info(self._device)
        if info and info.fingerbot and info.fingerbot.manual_control != 0:
            for update in updates:
                if update.id == info.fingerbot.switch and update.changed_by_device:
                    ...
                    # self.hass.bus.fire(
                    #     FINGERBOT_BUTTON_EVENT,
                    #     {
                    #         CONF_ADDRESS: self._device.address,
                    #         CONF_DEVICE_ID: self._device.device_id,
                    #     },
                    # )

    def _set_disconnected(self, _: None) -> None:
        """Invoke the idle timeout callback, called when the alarm fires."""
        self._disconnected = True
        self._unsub_disconnect = None
        # self.async_update_listeners()

    def _async_handle_disconnect(self) -> None:
        """Trigger the callbacks for disconnected."""
        if self._unsub_disconnect is None:
            delay: float = SET_DISCONNECTED_DELAY
            # self._unsub_disconnect = async_call_later(
            #     self.hass, delay, self._set_disconnected
            # )


@dataclass
class TuyaBLEData:
    """Data for the Tuya BLE integration."""

    title: str
    device: TuyaBLEDevice
    product: TuyaBLEProductInfo
    # manager: HASSTuyaBLEDeviceManager
    coordinator: TuyaBLECoordinator


@dataclass
class TuyaBLECategoryInfo:
    products: dict[str, TuyaBLEProductInfo]
    info: TuyaBLEProductInfo | None = None


devices_database: dict[str, TuyaBLECategoryInfo] = {
    "szjqr": TuyaBLECategoryInfo(
        products={
            "xhf790if": TuyaBLEProductInfo(  # device product_id
                name="CubeTouch II",
                fingerbot=TuyaBLEFingerbotInfo(
                    switch=1,
                    mode=2,
                    up_position=5,
                    down_position=6,
                    hold_time=3,
                    reverse_positions=4,
                ),
            ),
        },
    ),
    "jtmspro": TuyaBLECategoryInfo(
        products={
            "rlyxv7pe": TuyaBLEProductInfo(  # device product_id
                name="A1 PRO MAX",
            ),
        },
    ),
}


def get_product_info_by_ids(
        category: str, product_id: str
) -> TuyaBLEProductInfo | None:
    category_info = devices_database.get(category)
    if category_info is not None:
        product_info = category_info.products.get(product_id)
        if product_info is not None:
            return product_info
        return category_info.info
    else:
        return None


def get_device_product_info(device: TuyaBLEDevice) -> TuyaBLEProductInfo | None:
    return get_product_info_by_ids(device.category, device.product_id)


def get_short_address(address: str) -> str:
    results = address.replace("-", ":").upper().split(":")
    return f"{results[-3]}{results[-2]}{results[-1]}"[-6:]


async def get_device_readable_name(
        discovery_info: BluetoothServiceInfoBleak,
        manager: AbstaractTuyaBLEDeviceManager | None,
) -> str:
    credentials: TuyaBLEDeviceCredentials | None = None
    product_info: TuyaBLEProductInfo | None = None
    if manager:
        credentials = await manager.get_device_credentials(discovery_info.address)
        if credentials:
            product_info = get_product_info_by_ids(
                credentials.category,
                credentials.product_id,
            )
    short_address = get_short_address(discovery_info.address)
    if product_info:
        return "%s %s" % (product_info.name, short_address)
    if credentials:
        return "%s %s" % (credentials.device_name, short_address)
    return "%s %s" % (discovery_info.device.name, short_address)

"""The Tuya BLE integration."""
from __future__ import annotations

from dataclasses import dataclass, field

import logging
from typing import Callable, List

from const import DOMAIN
from devices import TuyaBLEData, TuyaBLEEntity, TuyaBLEProductInfo, TuyaBLECoordinator
from ha_mock import ButtonEntityDescription
from tuya_ble import TuyaBLEDataPointType, TuyaBLEDevice

_LOGGER = logging.getLogger(__name__)

TuyaBLEButtonIsAvailable = Callable[["TuyaBLEButton", TuyaBLEProductInfo], bool] | None


@dataclass
class TuyaBLEButtonMapping:
    dp_id: int
    description: ButtonEntityDescription
    force_add: bool = True
    dp_type: TuyaBLEDataPointType | None = None
    is_available: TuyaBLEButtonIsAvailable = None


@dataclass
class TuyaBLELockMapping(TuyaBLEButtonMapping):
    description: ButtonEntityDescription = field(
        default_factory=lambda: ButtonEntityDescription(
            key="push",
        )
    )
    is_available: TuyaBLEButtonIsAvailable = 0


def is_fingerbot_in_push_mode(self: TuyaBLEButton, product: TuyaBLEProductInfo) -> bool:
    result: bool = True
    if product.fingerbot:
        datapoint = self._device.datapoints[product.fingerbot.mode]
        if datapoint:
            result = datapoint.value == 0
    return result


@dataclass
class TuyaBLEFingerbotModeMapping(TuyaBLEButtonMapping):
    description: ButtonEntityDescription = field(
        default_factory=lambda: ButtonEntityDescription(
            key="push",
        )
    )
    is_available: TuyaBLEButtonIsAvailable = is_fingerbot_in_push_mode


@dataclass
class TuyaBLECategoryButtonMapping:
    products: dict[str, list[TuyaBLEButtonMapping]] | None = None
    mapping: list[TuyaBLEButtonMapping] | None = None


mapping: dict[str, TuyaBLECategoryButtonMapping] = {
    # "szjqr": TuyaBLECategoryButtonMapping(
    #     products={
    #         **dict.fromkeys(
    #             ["3yqdo5yt", "xhf790if"],  # CubeTouch 1s and II
    #             [
    #                 TuyaBLEFingerbotModeMapping(dp_id=1),
    #             ],
    #         ),
    #     },
    # ),
    "jtmspro": TuyaBLECategoryButtonMapping(
        products={
            "rlyxv7pe":  # Gimdow Smart Lock
                [
                    TuyaBLELockMapping(
                        dp_id=46,
                        description=ButtonEntityDescription(
                            key="manual_lock",
                        ),
                    ),
                    TuyaBLELockMapping(
                        dp_id=6,
                        description=ButtonEntityDescription(
                            key="manual_unlock",
                        ),
                    ),
                ]
        }
    ),
}


def get_mapping_by_device(device: TuyaBLEDevice) -> list[TuyaBLECategoryButtonMapping]:
    category = mapping.get(device.category)
    if category is not None and category.products is not None:
        product_mapping = category.products.get(device.product_id)
        if product_mapping is not None:
            return product_mapping
        if category.mapping is not None:
            return category.mapping
        else:
            return []
    else:
        return []


class TuyaBLEButton(TuyaBLEEntity):
    """Representation of a Tuya BLE Button."""

    def __init__(
            self,
            coordinator: TuyaBLECoordinator,
            device: TuyaBLEDevice,
            product: TuyaBLEProductInfo,
            mapping: TuyaBLEButtonMapping,
    ) -> None:
        super().__init__(coordinator, device, product, mapping.description)
        self._mapping = mapping

    def press(self) -> None:
        """Press the button."""
        datapoint = self._device.datapoints.get_or_create(
            self._mapping.dp_id,
            TuyaBLEDataPointType.DT_BOOL,
            False,
        )
        if datapoint:
            self.create_task(datapoint.set_value(not bool(datapoint.value)))

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        result = super().available
        if result and self._mapping.is_available:
            result = self._mapping.is_available(self, self._product)
        return result


async def async_setup_buttons(
        data: TuyaBLEData,
        # hass: HomeAssistant,
        # entry: ConfigEntry,
        # async_add_entities: AddEntitiesCallback,
) -> list[TuyaBLEButton]:
    """Set up the Tuya BLE sensors."""
    # data: TuyaBLEData = hass.data[DOMAIN][entry.entry_id]
    mappings = get_mapping_by_device(data.device)
    entities: list[TuyaBLEButton] = []
    for mapping in mappings:
        if mapping.force_add or data.device.datapoints.has_id(
                mapping.dp_id, mapping.dp_type
        ):
            entities.append(
                TuyaBLEButton(
                    # hass,
                    data.coordinator,
                    data.device,
                    data.product,
                    mapping,
                )
            )
    return entities
    # async_add_entities(entities)

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import NumberEntity

from .const import DOMAIN
from .coordinator import LOGGER, _365GPSEntity

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import _365GPSDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: _365GPSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            UpdateIntervalNumber(
                coordinator,
                imei,
                coordinator.update_interval_description,
            )
            for imei in coordinator.data.keys()
        ],
        update_before_add=True,
    )


class UpdateIntervalNumber(NumberEntity, _365GPSEntity):
    @property
    def native_value(self) -> float:
        return self.coordinator.data[self._imei].update_interval

    async def async_set_native_value(self, value: float) -> None:
        LOGGER.debug(
            f"[{self._imei}] Setting {self.entity_description.key} to {int(value)}",
        )
        await self.coordinator.api.set_utime(
            imei=self._imei,
            value=int(value),
        )
        await self.coordinator.async_request_refresh()

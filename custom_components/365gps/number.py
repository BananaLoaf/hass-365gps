from homeassistant.components.number import (
    NumberEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: _365GPSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            UpdateIntervalNumber(
                coordinator, imei, coordinator.update_interval_description
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
        await self.coordinator.api.set_utime(
            imei=self._imei,
            value=int(value),
        )
        await self.coordinator.async_request_refresh()

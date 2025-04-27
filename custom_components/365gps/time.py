from datetime import time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    coordinator: _365GPSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    devices = []
    for imei in coordinator.data.keys():
        devices.extend(
            [
                _365GPSPowerSavingTime(
                    coordinator, imei, coordinator.on_time_description
                ),
                _365GPSPowerSavingTime(
                    coordinator, imei, coordinator.off_time_description
                ),
            ]
        )

    async_add_entities(devices)


class _365GPSPowerSavingTime(_365GPSEntity, TimeEntity):
    @property
    def native_value(self) -> time | None:
        return getattr(
            self.coordinator.data[self._imei].saving, self.entity_description.key
        )

    async def async_set_value(self, value: time):
        saving = self.coordinator.data[self._imei].saving
        setattr(saving, self.entity_description.key, value)

        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()

import asyncio
from datetime import time, datetime

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity, LOGGER


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
                _365GPSTimeEntity(
                    time_type="on", i=16, coordinator=coordinator, imei=imei
                ),
                _365GPSTimeEntity(
                    time_type="off", i=22, coordinator=coordinator, imei=imei
                ),
            ]
        )

    async_add_entities(devices)


class _365GPSTimeEntity(_365GPSEntity, TimeEntity):
    def __init__(self, time_type: str, i: int, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.time_type = time_type
        self.i = i

        self._attr_unique_id = f"{self._imei}_power_saving_{time_type}"
        self._attr_name = (
            self.coordinator.data[self._imei].name
            + f" Power Saving {time_type.upper()} Time"
        )
        # self.entity_description = desc

    @property
    def native_value(self) -> time | None:
        sav = self.coordinator.data[self._imei].sav
        # sav = (await self.coordinator.api.get_sav(self._imei))[0]["saving"]
        return datetime.strptime(sav[self.i : self.i + 4], "%H%M").time()

    async def async_set_value(self, value: time):
        kwargs = {f"{self.time_type}_time": value}
        await self.coordinator.api.set_sav(
            saving=self.coordinator.data[self._imei].sav,
            imei=self._imei,
            **kwargs,
        )
        await self.coordinator.async_request_refresh()

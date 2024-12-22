from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType

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
                _365GPSSensorEntity(
                    desc=desc,
                    coordinator=coordinator,
                    imei=imei,
                )
                for desc in coordinator.sensor_descriptions
            ]
        )

    async_add_entities(devices)


class _365GPSSensorEntity(_365GPSEntity, SensorEntity):
    def __init__(self, desc: SensorEntityDescription, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attr_unique_id = f"{self._imei}_{desc.key}"
        self._attr_name = self.coordinator.data[self._imei].name + " " + desc.name
        self.entity_description = desc

    @property
    def native_value(self) -> StateType:
        return getattr(self.coordinator.data[self._imei], self.entity_description.key)

    @property
    def available(self) -> bool:
        return True

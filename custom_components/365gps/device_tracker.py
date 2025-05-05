from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LocationSource
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: _365GPSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            GPSDeviceTracker(coordinator, imei, coordinator.device_tracker_description)
            for imei in coordinator.data.keys()
        ]
    )


class GPSDeviceTracker(_365GPSEntity, TrackerEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_name = self.coordinator.data[self._imei].name

    @property
    def latitude(self) -> float:
        return self.coordinator.data[self._imei].latitude

    @property
    def longitude(self) -> float:
        return self.coordinator.data[self._imei].longitude

    @property
    def battery_level(self) -> float:
        return self.coordinator.data[self._imei].battery_level

    @property
    def source_type(self) -> LocationSource:
        return self.coordinator.data[self._imei].location_source

    @property
    def location_accuracy(self) -> int:
        return 10 if self.source_type == LocationSource.GPS else 100

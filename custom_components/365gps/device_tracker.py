from typing import TYPE_CHECKING

from homeassistant.components.device_tracker.config_entry import TrackerEntity

from .const import DOMAIN, LocationSource
from .coordinator import _365GPSEntity

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
            GPSDeviceTracker(coordinator, imei, coordinator.device_tracker_description)
            for imei in coordinator.data.keys()
        ],
    )


class GPSDeviceTracker(TrackerEntity, _365GPSEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_name = self.coordinator.data[self._imei].name

    @property
    def latitude(self) -> float | None:
        if (
            self.coordinator.data[self._imei].location_source == LocationSource.LBS
            and self.coordinator.data[self._imei].ignore_lbs
        ):
            return None
        return self.coordinator.data[self._imei].latitude

    @property
    def longitude(self) -> float | None:
        if (
            self.coordinator.data[self._imei].location_source == LocationSource.LBS
            and self.coordinator.data[self._imei].ignore_lbs
        ):
            return None
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

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data[self._imei]
        return {
            "update_time": data.update_time,
            "speed": data.speed,
            "altitude": data.altitude,
            "direction": data.direction,
            "status": data.status,
            "location_source": data.location_source,
            "battery_level": data.battery_level,
            "cellular_signal": data.cellular_signal,
            "update_interval": data.update_interval,
            "imei": data.imei,
            "device": data.device,
            "sw_version": data.sw_version,
            "hw_version": data.hw_version,
        }

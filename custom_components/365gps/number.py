from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator: _365GPSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [UpdateIntervalNumber(coordinator, imei) for imei in coordinator.data.keys()],
        update_before_add=True,
    )


class UpdateIntervalNumber(NumberEntity, _365GPSEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attr_unique_id = f"{self._imei}_update_interval"
        self._attr_name = self.coordinator.data[self._imei].name + " Update Interval"

        self.entity_description = NumberEntityDescription(
            key="update_interval",
            mode=NumberMode.BOX,
            native_min_value=10,
            native_max_value=65535,
            native_step=1,
            native_unit_of_measurement=UnitOfTime.SECONDS,
            icon="mdi:update",
        )

    @property
    def available(self) -> bool:
        return True

    @property
    def native_value(self) -> float:
        return self.coordinator.data[self._imei].update_interval

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.api.set_utime(
            imei=self._imei,
            value=int(value),
        )
        await self.coordinator.async_request_refresh()

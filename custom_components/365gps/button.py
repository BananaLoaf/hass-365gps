from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback


update_interval_map = {
    "precision_mode": 10,
    "power_saving_mode": 600,
    "sleep_mode": 65535,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: _365GPSDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for imei in coordinator.data.keys():
        entities.extend(
            [
                UpdateIntervalModeButton(
                    coordinator, imei, coordinator.precision_mode_description
                ),
                UpdateIntervalModeButton(
                    coordinator, imei, coordinator.power_saving_mode_description
                ),
                UpdateIntervalModeButton(
                    coordinator, imei, coordinator.sleep_mode_description
                ),
            ]
        )

    async_add_entities(entities, update_before_add=True)


class UpdateIntervalModeButton(ButtonEntity, _365GPSEntity):
    async def async_press(self):
        await self.coordinator.api.set_utime(
            imei=self._imei,
            value=update_interval_map[self.entity_description.key],
        )
        await self.coordinator.async_request_refresh()

from enum import StrEnum

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback


class UpdateIntervalMode(StrEnum):
    precision_mode = "Precision Update Interval"
    power_saving_mode = "Power Saving Update Interval"
    sleep_mode = "Sleep Update Interval"


update_interval_map = {
    UpdateIntervalMode.precision_mode: 10,
    UpdateIntervalMode.power_saving_mode: 600,
    UpdateIntervalMode.sleep_mode: 65535,
}

icon_map = {
    UpdateIntervalMode.precision_mode: "mdi:timer-10",
    UpdateIntervalMode.power_saving_mode: "mdi:clock-time-two",
    UpdateIntervalMode.sleep_mode: "mdi:sleep",
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
                UpdateIntervalModeButton(mode, coordinator, imei)
                for mode in list(UpdateIntervalMode)
            ]
        )

    async_add_entities(entities, update_before_add=True)


class UpdateIntervalModeButton(ButtonEntity, _365GPSEntity):
    def __init__(self, mode: UpdateIntervalMode, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mode = mode

        self._attr_unique_id = f"{self._imei}_{mode.name}"
        self._attr_name = self.coordinator.data[self._imei].name + " " + mode.value

        self.entity_description = ButtonEntityDescription(
            key=mode.name,
            icon=icon_map[self._mode],
        )

    async def async_press(self):
        await self.coordinator.api.set_utime(
            imei=self._imei,
            value=update_interval_map[self._mode],
        )
        await self.coordinator.async_request_refresh()

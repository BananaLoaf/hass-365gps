from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity, LOGGER
from .const import DOMAIN


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
                LedSwitch(coordinator, imei),
                SpeakerSwitch(coordinator, imei),
                FindSwitch(coordinator, imei),
            ]
        )

    async_add_entities(entities, update_before_add=True)


class LedSwitch(SwitchEntity, _365GPSEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attr_unique_id = f"{self._imei}_led"
        self._attr_name = self.coordinator.data[self._imei].name + " LED"

        self.entity_description = SwitchEntityDescription(
            key="led",
        )

    @property
    def is_on(self) -> bool:
        return getattr(self.coordinator.data[self._imei], self.entity_description.key)

    @property
    def icon(self) -> str:
        return "mdi:led-on" if self.is_on else "mdi:led-off"

    async def async_turn_on(self):
        await self.coordinator.api.set_led(self._imei, value=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        await self.coordinator.api.set_led(self._imei, value=False)
        await self.coordinator.async_request_refresh()


class SpeakerSwitch(SwitchEntity, _365GPSEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attr_unique_id = f"{self._imei}_speaker"
        self._attr_name = self.coordinator.data[self._imei].name + " Speaker"

        self.entity_description = SwitchEntityDescription(
            key="speaker",
        )

    @property
    def is_on(self) -> bool:
        return getattr(self.coordinator.data[self._imei], self.entity_description.key)

    @property
    def icon(self) -> str:
        return "mdi:volume-high" if self.is_on else "mdi:volume-low"

    async def async_turn_on(self):
        await self.coordinator.api.set_speaker(self._imei, value=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        await self.coordinator.api.set_speaker(self._imei, value=False)
        await self.coordinator.async_request_refresh()


class FindSwitch(SwitchEntity, _365GPSEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attr_unique_id = f"{self._imei}_find"
        self._attr_name = self.coordinator.data[self._imei].name + " Find"

        self.entity_description = SwitchEntityDescription(
            key="find",
            icon="mdi:bell",
        )

    async def async_turn_on(self):
        await self.coordinator.api.set_find(self._imei, value=True)

    async def async_turn_off(self):
        await self.coordinator.api.set_find(self._imei, value=False)

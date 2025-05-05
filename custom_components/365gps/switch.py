from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .coordinator import _365GPSDataUpdateCoordinator, _365GPSEntity
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
                LedSwitch(coordinator, imei, coordinator.led_descriptions),
                SpeakerSwitch(coordinator, imei, coordinator.speaker_description),
                FindSwitch(coordinator, imei, coordinator.find_description),
                PowerSavingSwitch(
                    coordinator, imei, coordinator.power_saving_description
                ),
                RemoteSwitch(coordinator, imei, coordinator.remote_description),
            ]
        )

    async_add_entities(entities, update_before_add=True)


class LedSwitch(SwitchEntity, _365GPSEntity):
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
    async def async_turn_on(self):
        await self.coordinator.api.set_find(self._imei, value=True)

    async def async_turn_off(self):
        await self.coordinator.api.set_find(self._imei, value=False)


class PowerSavingSwitch(SwitchEntity, _365GPSEntity):
    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self._imei].saving.power_saving

    async def async_turn_on(self):
        saving = self.coordinator.data[self._imei].saving
        saving.power_saving = True
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        saving = self.coordinator.data[self._imei].saving
        saving.power_saving = False
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()


class RemoteSwitch(SwitchEntity, _365GPSEntity):
    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self._imei].saving.remote

    async def async_turn_on(self):
        saving = self.coordinator.data[self._imei].saving
        saving.remote = True
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        saving = self.coordinator.data[self._imei].saving
        saving.remote = False
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from .coordinator import _365GPSEntity, LOGGER
from .const import DOMAIN

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

    entities = []
    for imei in coordinator.data.keys():
        entities.extend(
            [
                LedSwitch(
                    coordinator,
                    imei,
                    coordinator.led_descriptions,
                ),
                SpeakerSwitch(
                    coordinator,
                    imei,
                    coordinator.speaker_description,
                ),
                FindSwitch(
                    coordinator,
                    imei,
                    coordinator.find_description,
                ),
                PowerSavingSwitch(
                    coordinator,
                    imei,
                    coordinator.power_saving_description,
                ),
                RemoteSwitch(
                    coordinator,
                    imei,
                    coordinator.remote_description,
                ),
                IgnoreLBSSwitch(
                    coordinator,
                    imei,
                    coordinator.ignore_lbs_description,
                ),
            ],
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
        LOGGER.debug(f"Setting {self.entity_description.key} ON")
        await self.coordinator.api.set_led(self._imei, value=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        LOGGER.debug(f"Setting {self.entity_description.key} OFF")
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
        LOGGER.debug(f"Setting {self.entity_description.key} ON")
        await self.coordinator.api.set_speaker(self._imei, value=True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        LOGGER.debug(f"Setting {self.entity_description.key} OFF")
        await self.coordinator.api.set_speaker(self._imei, value=False)
        await self.coordinator.async_request_refresh()


class FindSwitch(SwitchEntity, _365GPSEntity):
    async def async_turn_on(self):
        LOGGER.debug(f"Setting {self.entity_description.key} ON")
        await self.coordinator.api.set_find(self._imei, value=True)

    async def async_turn_off(self):
        LOGGER.debug(f"Setting {self.entity_description.key} OFF")
        await self.coordinator.api.set_find(self._imei, value=False)


class PowerSavingSwitch(SwitchEntity, _365GPSEntity):
    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self._imei].saving.power_saving

    async def async_turn_on(self):
        LOGGER.debug(f"Setting {self.entity_description.key} ON")
        saving = self.coordinator.data[self._imei].saving
        saving.power_saving = True
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        LOGGER.debug(f"Setting {self.entity_description.key} OFF")
        saving = self.coordinator.data[self._imei].saving
        saving.power_saving = False
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()


class RemoteSwitch(SwitchEntity, _365GPSEntity):
    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self._imei].saving.remote

    async def async_turn_on(self):
        LOGGER.debug(f"Setting {self.entity_description.key} ON")
        saving = self.coordinator.data[self._imei].saving
        saving.remote = True
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self):
        LOGGER.debug(f"Setting {self.entity_description.key} OFF")
        saving = self.coordinator.data[self._imei].saving
        saving.remote = False
        await self.coordinator.api.set_sav(imei=self._imei, saving=saving)
        await self.coordinator.async_request_refresh()


class IgnoreLBSSwitch(SwitchEntity, _365GPSEntity):
    @property
    def is_on(self) -> bool:
        return self.coordinator.data[self._imei].ignore_lbs

    async def async_turn_on(self):
        LOGGER.debug(f"Setting {self.entity_description.key} ON")
        self.coordinator.data[self._imei].ignore_lbs = True

    async def async_turn_off(self):
        LOGGER.debug(f"Setting {self.entity_description.key} OFF")
        self.coordinator.data[self._imei].ignore_lbs = False

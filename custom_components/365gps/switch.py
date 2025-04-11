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
        remote_switch = RemoteSwitch(coordinator, imei)
        remote_switch.sav = await coordinator.get_sav(imei)

        entities.extend(
            [
                remote_switch,
                FindSwitch(coordinator, imei),
            ]
        )

    async_add_entities(entities, update_before_add=True)


class RemoteSwitch(SwitchEntity, _365GPSEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._attr_unique_id = f"{self._imei}_remote"
        self._attr_name = self.coordinator.data[self._imei].name + " Remote"

        self.entity_description = SwitchEntityDescription(
            key="remote",
            icon="mdi:sleep",
        )

        self.sav = None

    # @property
    # def is_on(self) -> bool | None:
    #     if self.sav is None:
    #         return self.sav
    #
    #     return bool(int(self.sav[3]))

    async def async_turn_on(self):
        self.sav = await self.coordinator.get_sav(self._imei)
        self.sav = self.coordinator.sav_with_remote(sav=self.sav, remote=True)
        await self.coordinator.set_sav(
            sav=self.sav,
            imei=self._imei,
        )

    async def async_turn_off(self):
        self.sav = await self.coordinator.get_sav(self._imei)
        self.sav = self.coordinator.sav_with_remote(sav=self.sav, remote=False)
        await self.coordinator.set_sav(
            sav=self.sav,
            imei=self._imei,
        )


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
        await self.coordinator.set_find_status(self._imei, status=True)

    async def async_turn_off(self):
        await self.coordinator.set_find_status(self._imei, status=False)

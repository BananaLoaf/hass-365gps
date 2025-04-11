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
                SavingValueSwitch(
                    key="gps",
                    name="GPS",
                    icon="mdi:crosshairs-gps",
                    coordinator=coordinator,
                    imei=imei,
                ),
                SavingValueSwitch(
                    key="lbs",
                    name="LBS",
                    icon="mdi:radio-tower",
                    coordinator=coordinator,
                    imei=imei,
                ),
                SavingValueSwitch(
                    key="remote",
                    name="Remote",
                    icon="mdi:sleep",
                    coordinator=coordinator,
                    imei=imei,
                ),
                FindSwitch(coordinator, imei),
            ]
        )

    async_add_entities(entities, update_before_add=True)


class SavingValueSwitch(SwitchEntity, _365GPSEntity):
    def __init__(self, key: str, name: str, icon: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.saving_getter = getattr(
            self.coordinator.data[self._imei], f"saving_with_{key}"
        )

        self._attr_unique_id = f"{self._imei}_{key}"
        self._attr_name = self.coordinator.data[self._imei].name + " " + name

        self.entity_description = SwitchEntityDescription(
            key=key,
            icon=icon,
        )

    @property
    def is_on(self) -> bool:
        return getattr(self.coordinator.data[self._imei], self.entity_description.key)

    async def async_turn_on(self):
        await self.coordinator.api.set_saving(
            saving=self.saving_getter(value=True),
            imei=self._imei,
        )
        self.coordinator.data[
            self._imei
        ].saving = await self.coordinator.api.get_saving(self._imei)

    async def async_turn_off(self):
        await self.coordinator.api.set_saving(
            saving=self.saving_getter(value=False),
            imei=self._imei,
        )
        self.coordinator.data[
            self._imei
        ].saving = await self.coordinator.api.get_saving(self._imei)


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
        await self.coordinator.api.set_find_status(self._imei, status=True)

    async def async_turn_off(self):
        await self.coordinator.api.set_find_status(self._imei, status=False)

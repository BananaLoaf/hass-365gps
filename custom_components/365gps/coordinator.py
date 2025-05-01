import json
import logging
import socket
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional, Type

import aiohttp
from homeassistant.components.button import ButtonEntityDescription
from homeassistant.components.device_tracker import TrackerEntityDescription
from homeassistant.components.number import NumberEntityDescription, NumberMode
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.components.time import TimeEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    IntegrationError,
)
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfSpeed,
    DEGREE,
    UnitOfTime,
)

from .api import _365GPSAPI, Saving
from .const import DATA_UPDATE_INTERVAL, DOMAIN, LocationSource


LOGGER = logging.getLogger(DOMAIN)


@dataclass
class DeviceData:
    name: str
    imei: str
    device: str
    sw_version: str
    hw_version: str

    latitude: float
    longitude: float
    update_time: datetime
    speed: Optional[int]
    altitude: int
    direction: int
    status: str
    location_source: LocationSource

    battery_level: int
    cellular_signal: int

    update_interval: int
    led: bool
    speaker: bool

    saving: Saving

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            name=self.name,
            identifiers={(DOMAIN, self.imei)},
            model=self.device,
            sw_version=self.sw_version,
            hw_version=self.hw_version,
        )


class _365GPSDataUpdateCoordinator(DataUpdateCoordinator):
    sensor_descriptions = (
        SensorEntityDescription(
            key="update_time",
            name="Update Time",
            device_class=SensorDeviceClass.TIMESTAMP,
        ),
        SensorEntityDescription(
            key="speed",
            name="Speed",
            device_class=SensorDeviceClass.SPEED,
            native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        ),
        SensorEntityDescription(
            key="altitude",
            name="Altitude",
            device_class=SensorDeviceClass.DISTANCE,
            native_unit_of_measurement=UnitOfLength.METERS,
        ),
        SensorEntityDescription(
            key="direction",
            name="Direction",
            native_unit_of_measurement=DEGREE,
            icon="mdi:compass-rose",
        ),
        SensorEntityDescription(
            key="status",
            name="Status",
            device_class=SensorDeviceClass.ENUM,
        ),
        SensorEntityDescription(
            key="location_source",
            name="Location Source",
            device_class=SensorDeviceClass.ENUM,
            icon="mdi:crosshairs-gps",
        ),
        SensorEntityDescription(
            key="battery_level",
            name="Battery Level",
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
        ),
        SensorEntityDescription(
            key="cellular_signal",
            name="Cellular Signal",
            icon="mdi:signal",
        ),
    )

    led_descriptions = SwitchEntityDescription(
        key="led",
        name="LED",
    )
    speaker_description = SwitchEntityDescription(
        key="speaker",
        name="Speaker",
    )
    find_description = SwitchEntityDescription(
        key="find",
        name="Find",
        icon="mdi:bell",
    )

    remote_description = SwitchEntityDescription(
        key="remote",
        name="Remote",
        icon="mdi:power-sleep",
    )
    power_saving_description = SwitchEntityDescription(
        key="power_saving",
        name="Power Saving",
        icon="mdi:power-sleep",
    )
    on_time_description = TimeEntityDescription(
        key="power_saving_on_time",
        name="Power Saving ON Time",
    )
    off_time_description = TimeEntityDescription(
        key="power_saving_off_time",
        name="Power Saving OFF Time",
    )

    update_interval_description = NumberEntityDescription(
        key="update_interval",
        name="Update Interval",
        mode=NumberMode.BOX,
        native_min_value=10,
        native_max_value=65535,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        icon="mdi:update",
    )
    precision_mode_description = ButtonEntityDescription(
        key="precision_mode",
        name="Precision Update Interval",
        icon="mdi:timer-10",
    )
    power_saving_mode_description = ButtonEntityDescription(
        key="power_saving_mode",
        name="Power Saving Update Interval",
        icon="mdi:clock-time-two",
    )
    sleep_mode_description = ButtonEntityDescription(
        key="sleep_mode",
        name="Sleep Update Interval",
        icon="mdi:sleep",
    )
    shutdown_description = ButtonEntityDescription(
        key="shutdown",
        name="Shutdown",
        icon="mdi:power",
    )
    reboot_description = ButtonEntityDescription(
        key="reboot",
        name="Reboot",
        icon="mdi:autorenew",
    )

    device_tracker_description = TrackerEntityDescription(
        key="device_tracker",
        name="Device Tracker",
    )

    def __init__(
        self,
        api: _365GPSAPI,
        hass: HomeAssistant,
    ):
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{api.username}",
            update_interval=timedelta(seconds=DATA_UPDATE_INTERVAL),
            update_method=self.get_device_data,
        )
        self.api = api

    async def get_device_data(self) -> dict[str, DeviceData]:
        raw_devices = await self.api.get_ilist()
        devices = {}

        for raw_device in raw_devices:
            imei = raw_device["imei"]
            name = raw_device["name"]
            device = raw_device["device"]
            version = raw_device["ver"].split(";")[0]

            lat_google, lng_google = raw_device["google"].split(",")
            lat_google, lng_google = float(lat_google), float(lng_google)
            update_time, _, _, _, direction, _, _, altitude = raw_device["gps"].split(
                ","
            )
            update_time = datetime.strptime(
                update_time + "+00:00", "%Y-%m-%d %H:%M:%S%z"
            )
            speed = (
                int(raw_device["speed"])
                if raw_device["speed"] is not None
                else raw_device["speed"]
            )
            direction, altitude = int(direction), int(altitude)
            if not direction and not altitude:
                direction, altitude = None, None
            status = "Offline" if raw_device["log"].startswith("OUT") else "Static"
            status = "Moving" if speed else status

            source_type = (
                LocationSource.LBS
                if direction is None and altitude is None
                else LocationSource.GPS
            )

            battery_level = int(raw_device["bat"])
            cellular_signal = int(raw_device["level"])

            update_interval = int(raw_device["sec"])
            _onoff = int(raw_device["onoff"], base=16)
            led = bool((_onoff >> 0) & 1)
            speaker = bool((_onoff >> 1) & 1)

            saving = await self.api.get_sav(imei)

            devices[imei] = DeviceData(
                name=name,
                imei=imei,
                device=device,
                sw_version=self.api.ver,
                hw_version=version,
                latitude=lat_google,
                longitude=lng_google,
                update_time=update_time,
                speed=speed,
                altitude=altitude,
                direction=direction,
                status=status,
                location_source=source_type,
                battery_level=battery_level,
                cellular_signal=cellular_signal,
                update_interval=update_interval,
                led=led,
                speaker=speaker,
                saving=Saving(saving[0]["saving"]),
            )
            LOGGER.debug(devices[imei])

        return devices

    # async def _async_update_data(self):
    #     data = await super()._async_update_data()
    #     return data


class _365GPSEntity:
    def __init__(
        self,
        coordinator: _365GPSDataUpdateCoordinator,
        imei: str,
        entity_description: Type[EntityDescription],
    ):
        self.coordinator = coordinator
        self._imei = imei
        self.entity_description = entity_description

        self._attr_device_info = self.coordinator.data[self._imei].device_info
        self._attr_unique_id = f"{self._imei}_{self.entity_description.key}"
        self._attr_name = (
            self.coordinator.data[self._imei].name + " " + entity_description.name
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

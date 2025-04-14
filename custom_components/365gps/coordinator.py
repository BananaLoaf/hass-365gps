import json
import logging
import socket
from dataclasses import dataclass
from datetime import timedelta, datetime
from typing import Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    IntegrationError,
)
from homeassistant.helpers.entity import DeviceInfo
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
)

from .api import _365GPSAPI
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
    location_source: LocationSource

    battery_level: int
    cellular_signal: int

    update_interval: int
    led: bool
    speaker: bool

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
    app_api_headers = {
        "user-agent": "App",
        "content-type": "application/json",
        "Accept": "application/json",
    }

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
            direction, altitude = (
                None if direction == 0 else direction,
                None if altitude == 0 else altitude,
            )
            source_type = (
                LocationSource.LBS
                if direction is None and altitude is None
                else LocationSource.GPS
            )

            battery_level = int(raw_device["bat"])
            cellular_signal = int(raw_device["level"])

            update_interval = int(raw_device["sec"])
            _onoff = int(raw_device["onoff"])
            led = bool((_onoff >> 0) & 1)
            speaker = bool((_onoff >> 1) & 1)

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
                location_source=source_type,
                battery_level=battery_level,
                cellular_signal=cellular_signal,
                update_interval=update_interval,
                led=led,
                speaker=speaker,
            )
            LOGGER.debug(devices[imei])

        return devices

    async def _async_update_data(self):
        data = await super()._async_update_data()

        # for imei, device_data in data.items():
        #     device_data.saving = await self.api.get_sav(imei)

        return data


class _365GPSEntity:
    def __init__(self, coordinator: _365GPSDataUpdateCoordinator, imei: str):
        self.coordinator = coordinator
        self._imei = imei

        self._attr_device_info = self.coordinator.data[self._imei].device_info

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

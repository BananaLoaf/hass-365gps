import json
import logging
import socket
from dataclasses import dataclass
from datetime import timedelta, datetime
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

    latitude: float
    longitude: float
    altitude: int
    direction: int
    speed: int
    location_source: LocationSource

    battery_level: int
    cellular_signal: int

    status: str
    update_time: datetime
    update_interval: int

    saving: str = "00000000000000000000000000"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            name=self.name,
            identifiers={(DOMAIN, self.imei)},
            model=self.device,
        )

    def saving_with_gps(self, value: bool) -> str:
        saving = list(self.saving)
        saving[1] = str(int(value))
        return "".join(saving)

    def saving_with_lbs(self, value: bool) -> str:
        saving = list(self.saving)
        saving[13] = str(int(value))
        return "".join(saving)

    def saving_with_remote(self, value: bool) -> str:
        saving = list(self.saving)
        saving[3] = str(int(value))
        return "".join(saving)

    @property
    def remote(self):
        return bool(int(self.saving[3]))


class _365GPSDataUpdateCoordinator(DataUpdateCoordinator):
    app_api_headers = {
        "user-agent": "App",
        "content-type": "application/json",
        "Accept": "application/json",
    }

    sensor_descriptions = (
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
            key="speed",
            name="Speed",
            device_class=SensorDeviceClass.SPEED,
            native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
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
        SensorEntityDescription(
            key="status",
            name="Status",
            device_class=SensorDeviceClass.ENUM,
        ),
        SensorEntityDescription(
            key="update_time",
            name="Update Time",
            device_class=SensorDeviceClass.TIMESTAMP,
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
            setup_method=api.login,
        )
        self.api = api

    async def get_device_data(self) -> dict[str, DeviceData]:
        raw_devices = await self.api.get_device_table()
        devices = {}

        for raw_device in raw_devices:
            imei = raw_device["imei"]
            name = raw_device["name"]
            device = raw_device["device"]
            lat_google = float(raw_device["lat_google"])
            lng_google = float(raw_device["lng_google"])
            speed = int(raw_device["speed"])
            battery_level = int(raw_device["bat"])
            cellular_signal = int(raw_device["level"])
            update_interval = int(raw_device["sec"])

            status = raw_device["online_status"]
            if "Static" in status:
                status = "Static"
            elif "Moving" in status:
                status = "Moving"
            elif "Driving" in status:
                status = "Driving"
            elif "Offline" in status:
                status = "Offline"

            update_time = datetime.fromisoformat(raw_device["updatetime"] + "+00:00")

            _, _, _, _, direction, _, _, altitude = raw_device["gps"].split(",")
            direction = int(direction)
            altitude = int(altitude)

            is_lbs = direction == 0 and altitude == 0
            source_type = LocationSource.LBS if is_lbs else LocationSource.GPS

            devices[imei] = DeviceData(
                name=name,
                imei=imei,
                device=device,
                latitude=lat_google,
                longitude=lng_google,
                altitude=altitude,
                direction=direction,
                speed=speed,
                battery_level=battery_level,
                cellular_signal=cellular_signal,
                status=status,
                update_interval=update_interval,
                location_source=source_type,
                update_time=update_time,
            )
            LOGGER.debug(devices[imei])

        return devices

    async def _async_update_data(self):
        data = await super()._async_update_data()

        for imei, device_data in data.items():
            device_data.saving = await self.api.get_saving(imei)

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

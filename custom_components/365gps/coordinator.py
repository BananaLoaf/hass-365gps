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

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            name=self.name,
            identifiers={(DOMAIN, self.imei)},
            model=self.device,
        )


class _365GPSDataUpdateCoordinator(DataUpdateCoordinator):
    app_api_headers = {"user-agent": "App", "content-type": "application/json", "Accept": "application/json"}

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
        hass: HomeAssistant,
        username: str,
        password: str,
    ):
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{username}",
            update_interval=timedelta(seconds=DATA_UPDATE_INTERVAL),
            update_method=self.get_device_data,
            setup_method=self.login,
        )
        self.username = username
        self.password = password
        self.is_demo = False

        self._session: aiohttp.ClientSession = async_create_clientsession(
            hass,
            verify_ssl=False,
        )

        self._host = "www.365gps.com"

    async def login(self) -> None:
        await self._session.get(
            f"https://{self._host}/login.php?lang=en",
            timeout=5,
        )

        login_coro = self._session.post(
            f"https://{self._host}/npost_login.php",
            timeout=5,
            data={
                "demo": "T" if self.is_demo else "F",
                "username": self.username,
                "password": self.password,
                "form_type": 0,
            },
        )
        async with login_coro as response:
            response.raise_for_status()
            content = (await response.content.read()).decode("utf-8-sig")
            if content[0] != "Y":
                raise ConfigEntryAuthFailed(content)

    async def get_device_table(self) -> list[dict]:
        coro = self._session.post(
            f"https://{self._host}/post_device_table_list.php",
            timeout=5,
        )
        async with coro as response:
            response.raise_for_status()
            content = await response.content.read()
            try:
                return json.loads(content.decode("utf-8-sig"))["customer_info_list"]
            except json.decoder.JSONDecodeError as exc:
                raise IntegrationError(content) from exc

    async def get_device_data(self) -> dict[str, DeviceData]:
        raw_devices = await self.get_device_table()
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

    async def set_update_interval(self, imei: str, value: int):
        coro = self._session.post(
            f"https://{self._host}/post_submit_customerupload.php",
            timeout=5,
            data={"imei": imei, "sec": value},
        )
        async with coro as response:
            response.raise_for_status()
            content = await response.content.read()
            content = content.decode("utf-8-sig")
            if content != "Y":
                raise IntegrationError(f"Error setting update interval: {content}")

    def sav_with_remote(self, sav: str, remote: bool) -> str:
        sav = list(sav)
        sav[3] = str(int(remote))
        return ''.join(sav)

    async def get_sav(self, imei: str) -> str:
        coro = self._session.post(
            f"https://{self._host}/n365_sav.php?imei={imei}",
            headers=self.app_api_headers,
            timeout=5,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                content = self.evaluate_raw_app_api_content(await response.content.read())
            except IntegrationError as exc:
                raise IntegrationError("Error getting sav") from exc

            return content[0]["saving"]

    async def set_sav(self, imei: str, sav: str):
        coro = self._session.post(
            f"https://{self._host}/n365_sav.php?imei={imei}&msg={sav}",
            headers=self.app_api_headers,
            timeout=5,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                self.evaluate_raw_app_api_content(
                    content=await response.content.read(),
                    check_result_yes=True,
                )
            except IntegrationError as exc:
                raise IntegrationError("Error setting sav") from exc

    async def set_find_status(self, imei: str, status: bool):
        coro = self._session.post(
            f"https://{self._host}/n365_find.php?imei={imei}&status={int(status)}&hw=apk",
            headers=self.app_api_headers,
            timeout=5,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                self.evaluate_raw_app_api_content(await response.content.read())
            except IntegrationError as exc:
                raise IntegrationError("Error setting find status") from exc

    def evaluate_raw_app_api_content(self, content: bytes, check_result_yes: bool = False) -> dict | list:
        try:
            content = json.loads(content.decode("utf-8-sig"))
        except json.decoder.JSONDecodeError as exc:
            raise IntegrationError(content) from exc

        if check_result_yes:
            if content["result"] != "Y":
                raise IntegrationError(content)

        return content


class _365GPSEntity:
    def __init__(self, coordinator: _365GPSDataUpdateCoordinator, imei: str):
        self.coordinator = coordinator
        self._imei = imei

        self._attr_device_info = self.coordinator.data[self._imei].device_info

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

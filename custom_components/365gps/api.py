import json
from datetime import datetime, UTC, time
from typing import TypedDict, Optional

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, IntegrationError
from homeassistant.helpers.aiohttp_client import async_create_clientsession


def decode_content(content: bytes) -> dict | list:
    try:
        return json.loads(content.decode("utf-8-sig"))
    except json.decoder.JSONDecodeError as exc:
        raise IntegrationError(content) from exc


class ResultType(TypedDict):
    result: str


class DeviceInfoType(TypedDict):
    login: str
    imei: str
    name: str
    carno: str
    gps: str
    log: str
    google: str
    baidu: str
    speed: Optional[float]
    bat: str
    icon: str
    marker: str
    device: str
    ver: str
    sec: str
    level: str
    expdate: Optional[str]
    loc: str
    onoff: str
    gexpdate: Optional[str]
    iccid: str
    logo: str
    ggkey: Optional[str]
    startdate: str
    pic: str


class SavingType(TypedDict):
    saving: str
    log: str


class _365GPSAPI:
    app_api_headers = {
        "User-Agent": "365App",
        "Accept": "gzip",
    }
    ver = "5.76"
    timeout = 5

    def __init__(self, username: str, password: str, hass: HomeAssistant):
        self.username = username
        self.password = password
        self.is_demo = False

        self._host = "www.365gps.com"
        self._session: aiohttp.ClientSession = async_create_clientsession(
            hass,
            verify_ssl=False,
        )

    @property
    def ak(self) -> str:
        return f"{int(datetime.now(UTC).timestamp() - datetime.fromisoformat('2022-07-16T18:33:20').timestamp()): x}70"

    async def get_ilist(self) -> list[DeviceInfoType]:
        coro = self._session.post(
            f"https://{self._host}/api_ilist.php?imei={self.username}&pw={self.password}&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error getting ilist") from exc

    async def shutdown(self, imei: str) -> ResultType:
        coro = self._session.post(
            f"https://{self._host}/api_req.php?imei={imei}&req=49&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error shutting down") from exc

    async def reboot(self, imei: str) -> ResultType:
        coro = self._session.post(
            f"https://{self._host}/api_req.php?imei={imei}&req=48&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error rebooting") from exc

    async def set_led(self, imei: str, value: bool) -> ResultType:
        coro = self._session.post(
            f"https://{self._host}/api_req.php?imei={imei}&req={44 + int(value)}&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error setting LED") from exc

    async def set_speaker(self, imei: str, value: bool) -> ResultType:
        coro = self._session.post(
            f"https://{self._host}/api_req.php?imei={imei}&req={50 + int(value)}&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error setting speaker") from exc

    async def set_find(self, imei: str, value: bool) -> ResultType:
        coro = self._session.post(
            f"https://{self._host}/api_find.php?imei={imei}&status={int(value)}&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error setting find") from exc

    async def get_sav(self, imei: str) -> list[SavingType]:
        coro = self._session.post(
            f"https://{self._host}/api_sav.php?imei={imei}&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error getting sav") from exc

    async def set_sav(
        self,
        saving: str,
        imei: str,
        value: Optional[bool] = None,
        on_time: Optional[time] = None,
        off_time: Optional[time] = None,
    ) -> tuple[str, ResultType]:
        saving = list(saving)

        if value is not None:
            saving[15] = str(int(value))
            saving[21] = str(int(value))

        if on_time is not None:
            saving[16:20] = list(on_time.strftime("%H%M"))

        if off_time is not None:
            saving[22:26] = list(off_time.strftime("%H%M"))

        saving = "".join(saving)

        coro = self._session.post(
            f"https://{self._host}/api_sav.php?imei={imei}&ver={self.ver}&app=365g&ak={self.ak}&msg={saving}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return saving, decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error setting sav") from exc

    async def set_utime(self, imei: str, value: int) -> ResultType:
        coro = self._session.post(
            f"https://{self._host}/api_utime.php?imei={imei}&sec={value}&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error setting utime") from exc

    async def get_notifications(self, since: Optional[datetime] = None) -> list[None]:
        if since is None:
            since = "null"
        else:
            since = since.strftime("%Y-%m-%d%%20%H:%M:%S")

        coro = self._session.post(
            f"https://{self._host}/api_cwt.php?imei={self.username}&ver={self.ver}&app=365g&ak={self.ak}&chat=2&sd={since}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error getting sav") from exc

    async def clear_notifications(self) -> ResultType:
        coro = self._session.post(
            f"https://{self._host}/api_dalert.php?imei={self.username}&req=2&ver={self.ver}&app=365g&ak={self.ak}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error clearing notifications") from exc

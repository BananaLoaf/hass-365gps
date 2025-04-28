import json
from datetime import datetime, UTC, time
from typing import TypedDict, Optional

import aiohttp
from homeassistant.exceptions import IntegrationError


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


class Saving:
    def __init__(self, value: str):
        self._value = value

    def __str__(self):
        return self._value

    @property
    def is_on(self):
        return bool(int(self._value[15])) and bool(int(self._value[21]))

    @is_on.setter
    def is_on(self, value: bool):
        saving = list(self._value)
        saving[15] = str(int(value))
        saving[21] = str(int(value))
        self._value = "".join(saving)

    @property
    def power_saving_on_time(self) -> time:
        return datetime.strptime(self._value[16:20], "%H%M").time()

    @power_saving_on_time.setter
    def power_saving_on_time(self, value: time):
        saving = list(self._value)
        saving[16:20] = list(value.strftime("%H%M"))
        self._value = "".join(saving)

    @property
    def power_saving_off_time(self) -> time:
        return datetime.strptime(self._value[22:26], "%H%M").time()

    @power_saving_off_time.setter
    def power_saving_off_time(self, value: time):
        saving = list(self._value)
        saving[22:26] = list(value.strftime("%H%M"))
        self._value = "".join(saving)


class _365GPSAPI:
    app_api_headers = {
        "User-Agent": "365App",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }
    ver = "5.76"
    timeout = 5

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession):
        self.username = username
        self.password = password
        self.is_demo = False

        self._host = "www.365gps.com"
        self._session = session

    @property
    def ak(self) -> str:
        return f"{int(datetime.now(UTC).timestamp() - datetime.fromisoformat('2022-07-16T19:33:20+00:00').timestamp()):x}70"

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

    async def set_sav(self, imei: str, saving: str | Saving) -> tuple[str, ResultType]:
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

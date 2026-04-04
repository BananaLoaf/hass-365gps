import json
import random
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
    def remote(self):
        return not bool(int(self._value[3]))

    @remote.setter
    def remote(self, value: bool):
        saving = list(self._value)
        saving[3] = str(int(not value))
        self._value = "".join(saving)

    @property
    def power_saving(self):
        return bool(int(self._value[15])) and bool(int(self._value[21]))

    @power_saving.setter
    def power_saving(self, value: bool):
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
    ver = "6.45"
    timeout = 5

    def __init__(self, username: str, password: str, session: aiohttp.ClientSession):
        self.username = username
        self.password = password
        self.is_demo = False

        self._session = session

    @property
    def _host(self):
        return random.choice(("www.365gps.com", "www.365gps.net", "www.topin.hk"))

    @property
    def ak(self) -> str:
        return f"{int(datetime.now(UTC).timestamp() - datetime.fromisoformat('2022-07-16T19:33:20+00:00').timestamp()):x}70"

    @property
    def _common_params(self) -> dict[str, str]:
        return {
            "ver": self.ver,
            "app": "365g",
            "ak": self.ak,
            "hw": "apk",
        }

    async def get_ilist(self) -> list[DeviceInfoType]:
        coro = self._session.post(
            f"https://{self._host}/api_ilist.php",
            params={**self._common_params, "imei": self.username, "pw": self.password},
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
            f"https://{self._host}/api_req.php",
            params={**self._common_params, "imei": imei, "req": "49"},
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
            f"https://{self._host}/api_req.php",
            params={**self._common_params, "imei": imei, "req": "48"},
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
            f"https://{self._host}/api_req.php",
            params={**self._common_params, "imei": imei, "req": str(44 + int(value))},
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
            f"https://{self._host}/api_req.php",
            params={**self._common_params, "imei": imei, "req": str(50 + int(value))},
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
            f"https://{self._host}/api_find.php",
            params={**self._common_params, "imei": imei, "status": str(int(value))},
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
            f"https://{self._host}/api_sav.php",
            params={**self._common_params, "imei": imei},
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
            f"https://{self._host}/api_sav.php",
            params={**self._common_params, "imei": imei, "msg": str(saving)},
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
            f"https://{self._host}/api_utime.php",
            params={**self._common_params, "imei": imei, "sec": str(value)},
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
        sd = "null" if since is None else since.strftime("%Y-%m-%d %H:%M:%S")
        coro = self._session.post(
            f"https://{self._host}/api_cwt.php",
            params={
                **self._common_params,
                "imei": self.username,
                "chat": "2",
                "sd": sd,
            },
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
            f"https://{self._host}/api_dalert.php",
            params={**self._common_params, "imei": self.username, "req": "2"},
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except Exception as exc:
                raise IntegrationError("Error clearing notifications") from exc

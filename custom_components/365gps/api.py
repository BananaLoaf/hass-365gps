import json

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, IntegrationError
from homeassistant.helpers.aiohttp_client import async_create_clientsession


def decode_content(content: bytes) -> dict | list:
    try:
        return json.loads(content.decode("utf-8-sig"))
    except json.decoder.JSONDecodeError as exc:
        raise IntegrationError(content) from exc


class _365GPSAPI:
    app_api_headers = {
        "user-agent": "App",
        "content-type": "application/json",
        "Accept": "application/json",
    }
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

    async def login(self) -> None:
        await self._session.get(
            f"https://{self._host}/login.php?lang=en",
            timeout=self.timeout,
        )

        login_coro = self._session.post(
            f"https://{self._host}/npost_login.php",
            timeout=self.timeout,
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
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            content = decode_content(await response.content.read())
            return content["customer_info_list"]

    async def set_update_interval(self, imei: str, value: int):
        coro = self._session.post(
            f"https://{self._host}/post_submit_customerupload.php",
            timeout=self.timeout,
            data={"imei": imei, "sec": value},
        )
        async with coro as response:
            response.raise_for_status()
            content = (await response.content.read()).decode("utf-8-sig")
            if content != "Y":
                raise IntegrationError(f"Error setting update interval: {content}")

    async def get_saving(self, imei: str) -> str:
        coro = self._session.post(
            f"https://{self._host}/n365_sav.php?imei={imei}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                content = decode_content(await response.content.read())
            except IntegrationError as exc:
                raise IntegrationError("Error getting saving") from exc

            return content[0]["saving"]

    async def set_saving(self, imei: str, saving: str):
        coro = self._session.post(
            f"https://{self._host}/n365_sav.php?imei={imei}&msg={saving}",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                content = decode_content(await response.content.read())
                if content["result"] != "Y":
                    raise IntegrationError
            except IntegrationError as exc:
                raise IntegrationError("Error setting saving") from exc

    async def set_find_status(self, imei: str, status: bool):
        coro = self._session.post(
            f"https://{self._host}/n365_find.php?imei={imei}&status={int(status)}&hw=apk",
            headers=self.app_api_headers,
            timeout=self.timeout,
        )
        async with coro as response:
            response.raise_for_status()
            try:
                return decode_content(await response.content.read())
            except IntegrationError as exc:
                raise IntegrationError("Error setting find status") from exc

from datetime import datetime, time, UTC
from importlib import import_module

import pytest
from homeassistant.exceptions import IntegrationError

api_module = import_module("custom_components.365gps.api")
Saving = api_module.Saving
_365GPSAPI = api_module._365GPSAPI
decode_content = api_module.decode_content


class TestDecodeContent:
    def test_valid_json_dict(self):
        content = b'{"result": "ok"}'
        assert decode_content(content) == {"result": "ok"}

    def test_valid_json_list(self):
        content = b'[{"name": "device1"}]'
        assert decode_content(content) == [{"name": "device1"}]

    def test_utf8_bom(self):
        content = b'\xef\xbb\xbf{"result": "ok"}'
        assert decode_content(content) == {"result": "ok"}

    def test_invalid_json_raises_integration_error(self):
        with pytest.raises(IntegrationError):
            decode_content(b"not json")


class TestSaving:
    def test_str(self):
        saving = Saving("00000000000000000000000000")
        assert str(saving) == "00000000000000000000000000"

    def test_remote_true(self):
        saving = Saving("00000000000000000000000000")
        assert saving.remote is True

    def test_remote_false(self):
        saving = Saving("00010000000000000000000000")
        assert saving.remote is False

    def test_remote_setter(self):
        saving = Saving("00010000000000000000000000")
        saving.remote = False
        assert saving.remote is False
        assert str(saving)[3] == "1"

    def test_power_saving_true(self):
        saving = Saving("00000000000000010000010000")
        assert saving.power_saving is True

    def test_power_saving_false(self):
        saving = Saving("00000000000000000000000000")
        assert saving.power_saving is False

    def test_power_saving_setter(self):
        saving = Saving("00000000000000000000000000")
        saving.power_saving = True
        assert saving.power_saving is True
        assert str(saving)[15] == "1"
        assert str(saving)[21] == "1"

    def test_power_saving_on_time(self):
        # Index 16:20 should be "2200"
        saving = Saving("00000000000000002200000000")
        assert saving.power_saving_on_time == time(22, 0)

    def test_power_saving_on_time_setter(self):
        saving = Saving("00000000000000000000000000")
        saving.power_saving_on_time = time(23, 30)
        assert saving.power_saving_on_time == time(23, 30)
        assert str(saving)[16:20] == "2330"

    def test_power_saving_off_time(self):
        # Index 22:26 should be "0600"
        saving = Saving("00000000000000000000000600")
        assert saving.power_saving_off_time == time(6, 0)

    def test_power_saving_off_time_setter(self):
        saving = Saving("00000000000000000000000745")
        saving.power_saving_off_time = time(7, 45)
        assert saving.power_saving_off_time == time(7, 45)
        assert str(saving)[22:26] == "0745"


@pytest.mark.asyncio
@pytest.mark.flaky(reruns=3, reruns_exceptions=(TimeoutError,))
class TestAPI:
    @pytest.fixture
    def api(self, credentials, session):
        return _365GPSAPI(credentials["username"], credentials["password"], session)

    async def test_get_ilist(self, api):
        result = await api.get_ilist()
        assert isinstance(result, list)
        if result:
            device = result[0]
            assert "imei" in device
            assert "name" in device

    async def test_get_ilist_returns_valid_device_structure(self, api):
        result = await api.get_ilist()
        if not result:
            pytest.skip("No devices found")
        device = result[0]
        expected_keys = [
            "login",
            "imei",
            "name",
            "carno",
            "gps",
            "log",
            "google",
            "baidu",
            "speed",
            "bat",
            "icon",
            "marker",
            "device",
            "ver",
            "sec",
            "level",
            "expdate",
            "loc",
            "onoff",
            "gexpdate",
            "iccid",
            "logo",
            "ggkey",
            "startdate",
            "pic",
        ]
        for key in expected_keys:
            assert key in device, f"Missing key: {key}"

    async def test_get_sav(self, api):
        result = await api.get_ilist()
        if not result:
            pytest.skip("No devices found")
        imei = result[0]["imei"]
        sav_result = await api.get_sav(imei)
        assert isinstance(sav_result, list)

    async def test_set_utime(self, api):
        result = await api.get_ilist()
        if not result:
            pytest.skip("No devices found")
        imei = result[0]["imei"]
        utime_result = await api.set_utime(imei, 60)
        assert isinstance(utime_result, dict)
        assert "result" in utime_result

    @pytest.mark.skip
    async def test_get_notifications(self, api):
        result = await api.get_notifications()
        assert isinstance(result, list)

    @pytest.mark.skip
    async def test_get_notifications_with_since(self, api):
        since = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        result = await api.get_notifications(since=since)
        assert isinstance(result, list)

    @pytest.mark.skip
    async def test_clear_notifications(self, api):
        result = await api.clear_notifications()
        assert isinstance(result, dict)
        assert "result" in result

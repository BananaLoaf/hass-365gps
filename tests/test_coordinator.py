import logging
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

coordinator_module = import_module("custom_components.365gps.coordinator")


class _OfflineCoordinator(coordinator_module._365GPSDataUpdateCoordinator):
    def __init__(self, hass):
        DataUpdateCoordinator.__init__(
            self, hass, logging.getLogger(__name__), name="365gps", config_entry=None
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "platform", ["device_tracker", "sensor", "switch", "number", "button", "time"]
)
async def test_entities_subscribe_to_coordinator(platform, tmp_path):
    hass = HomeAssistant(str(tmp_path))
    coordinator = _OfflineCoordinator(hass)
    entry = SimpleNamespace(entry_id="test-entry")
    hass.data["365gps"] = {entry.entry_id: coordinator}
    imei = "123456789012345"
    device = SimpleNamespace(name="Test tracker", device_info=None)
    coordinator.async_set_updated_data({imei: device})

    add_entities = Mock()
    module = import_module(f"custom_components.365gps.{platform}")
    await module.async_setup_entry(hass, entry, add_entities)
    (entities,) = add_entities.call_args.args
    assert entities

    for entity in entities:
        entity.async_write_ha_state = Mock()
        await entity.async_added_to_hass()

    coordinator.async_set_updated_data({imei: device})
    for entity in entities:
        entity.async_write_ha_state.assert_called_once_with()
        assert not entity.should_poll
        entity.add_to_platform_abort()
        entity.async_write_ha_state.reset_mock()

    coordinator.async_set_updated_data({imei: device})
    for entity in entities:
        entity.async_write_ha_state.assert_not_called()

[![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)](https://hacs.xyz)
[![version](https://img.shields.io/github/manifest-json/v/BananaLoaf/hass-365gps?filename=custom_components%2F365gps%2Fmanifest.json)](https://github.com/BananaLoaf/hass-365gps/releases/latest)
[![HACS](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.365gps.total)

[![stars](https://img.shields.io/github/stars/BananaLoaf/hass-365gps)](https://github.com/BananaLoaf/hass-365gps/stargazers)
[![issues](https://img.shields.io/github/issues/BananaLoaf/hass-365gps)](https://github.com/BananaLoaf/hass-365gps/issues)

# 365GPS for HomeAssistant

[![Python CI](https://github.com/BananaLoaf/hass-365gps/actions/workflows/python-ci.yml/badge.svg)](https://github.com/BananaLoaf/hass-365gps/actions/workflows/python-ci.yml)
[![Python Test API](https://github.com/BananaLoaf/hass-365gps/actions/workflows/python-test-api.yml/badge.svg)](https://github.com/BananaLoaf/hass-365gps/actions/workflows/python-test-api.yml)

> [!WARNING]  
> **Do not share your IMEIs and passwords with anyone you don't trust!**

Integration for Home Assistant via HACS

![images/img.png](images/img.png)

# Installation 

1. Open HACS
2. Custom Repositories
3. Add repository `BananaLoaf/hass-365gps` with type `integration`
4. Search `365gps` on Home Assistant Community Store
5. Install

# Adding devices

1. Open Settings
2. Open Devices & Services
3. Add Integration
4. Search `365gps`
5. Add

# Setting log level

In your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    365gps: debug
```

# Development

## Setup

Setup python venv
```bash
uv sync
```

Run Home Assistant instance
```bash
docker compose up --build --remove-orphans -d
```

Restart to apply changes
```bash
docker compose restart
```

## Linting

```bash
uv run poe lint
```

## Testing

```bash
uv run pytest
```

API integration tests require credentials. Create a `.env` file:

```
TEST_USERNAME=your_username
TEST_PASSWORD=your_password
```

Tests without credentials will be automatically skipped.

from enum import StrEnum

DOMAIN = "365gps"
PLATFORMS = ["device_tracker", "sensor", "number", "button", "switch", "time"]
DATA_UPDATE_INTERVAL = 10

IS_DEMO_KEY = "Is demo?"


class LocationSource(StrEnum):
    GPS = "gps"
    LBS = "lbs"

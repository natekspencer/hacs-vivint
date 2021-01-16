"""Constants for the Vivint integration."""
import logging

_LOGGER = logging.getLogger(__name__)

VIVINT_DOMAIN = "vivint"
VIVINT_PLATFORMS = [
    "alarm_control_panel",
    "binary_sensor",
    "camera",
    "cover",
    "lock",
    "sensor",
]

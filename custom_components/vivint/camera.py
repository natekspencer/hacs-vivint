"""Support for Vivint cameras."""
import asyncio
from typing import Any, Dict

from haffmpeg.tools import IMAGE_JPEG, ImageFrame
from homeassistant.components.camera import SUPPORT_STREAM, Camera
from homeassistant.components.ffmpeg import DATA_FFMPEG
from homeassistant.core import callback
from pyvivintsky import VivintCamera

from . import VivintHub
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint cameras using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for panel_id in hub.api.get_panels():
        panel = hub.api.get_panel(panel_id)
        for device_id in panel.get_devices():
            device = panel.get_device(device_id)
            if type(device) is VivintCamera:
                entities.append(VivintCam(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint cameras: {entities}")
    async_add_entities(entities, True)


class VivintCam(Camera):
    """Vivint camera."""

    def __init__(self, hub: VivintHub, device):
        super().__init__()
        self.hub = hub
        self.device = device

    async def async_added_to_hass(self) -> None:
        """Set up a listener for the entity."""
        self.device._callback = self._update_callback
        self._ffmpeg = self.hass.data[DATA_FFMPEG]

    @callback
    def _update_callback(self) -> None:
        """Call from dispatcher when state changes."""
        self.async_write_ha_state()

    @property
    def supported_features(self):
        """Return supported features for this camera."""
        return SUPPORT_STREAM

    @property
    def name(self):
        """Return the name of this device."""
        return self.device.name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.get_root().id}-{self.device.id}"

    async def stream_source(self):
        """Return the source of the stream."""
        direct = await self.device.get_direct_rtsp_url(True)
        return direct or await self.device.get_external_rtsp_url(True)

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return the device information for a Vivint binary sensor."""
        return {
            "identifiers": {(VIVINT_DOMAIN, self.device.serial_number)},
            "name": self.device.name,
            "manufacturer": self.device.manufacturer,
            "model": self.device.model,
            "sw_version": self.device.software_version,
            "via_device": (VIVINT_DOMAIN, self.device.get_root().id),
        }

    async def async_camera_image(self):
        """Return a frame from the camera stream."""
        ffmpeg = ImageFrame(self.hass.data[DATA_FFMPEG].binary)
        image = await asyncio.shield(
            ffmpeg.get_image(await self.stream_source(), output_format=IMAGE_JPEG)
        )
        return image

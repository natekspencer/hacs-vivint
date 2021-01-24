"""Support for Vivint cameras."""
import asyncio

from haffmpeg.tools import IMAGE_JPEG, ImageFrame
from homeassistant.components.camera import SUPPORT_STREAM, Camera
from homeassistant.components.ffmpeg import DATA_FFMPEG
from pyvivint.devices import VivintDevice
from pyvivint.devices.camera import Camera as VivintCamera

from . import VivintEntity, VivintHub
from .const import _LOGGER, VIVINT_DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint cameras using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    for system in hub.api.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is VivintCamera:
                    entities.append(VivintCam(hub, device))

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint cameras: {entities}")
    async_add_entities(entities, True)


class VivintCam(VivintEntity, Camera):
    """Vivint camera."""

    def __init__(self, hub: VivintHub, device: VivintDevice):
        super().__init__(hub, device)
        Camera.__init__(self)

    @property
    def supported_features(self):
        """Return supported features for this camera."""
        return SUPPORT_STREAM

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self.device.alarm_panel.id}-{self.device.id}"

    async def stream_source(self):
        """Return the source of the stream."""
        direct = await self.device.get_direct_rtsp_url(hd=True)
        return direct or await self.device.get_rtsp_url(internal=True, hd=True)

    async def async_camera_image(self):
        """Return a frame from the camera stream."""
        ffmpeg = ImageFrame(self.hass.data[DATA_FFMPEG].binary)
        image = await asyncio.shield(
            ffmpeg.get_image(await self.stream_source(), output_format=IMAGE_JPEG)
        )
        return image

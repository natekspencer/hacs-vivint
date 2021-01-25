"""Support for Vivint cameras."""
import asyncio

from haffmpeg.tools import IMAGE_JPEG, ImageFrame
from homeassistant.components.camera import SUPPORT_STREAM, Camera
from homeassistant.components.ffmpeg import DATA_FFMPEG
from pyvivint.devices import VivintDevice
from pyvivint.devices.camera import Camera as VivintCamera

from . import VivintEntity, VivintHub
from .const import (
    _LOGGER,
    CONF_HD_STREAM,
    CONF_RTSP_STREAM,
    DEFAULT_HD_STREAM,
    DEFAULT_RTSP_STREAM,
    RTSP_STREAM_DIRECT,
    RTSP_STREAM_EXTERNAL,
    VIVINT_DOMAIN,
)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Vivint cameras using config entry."""
    entities = []
    hub = hass.data[VIVINT_DOMAIN][config_entry.entry_id]

    hd_stream = config_entry.options.get(CONF_HD_STREAM, DEFAULT_HD_STREAM)
    rtsp_stream = config_entry.options.get(CONF_RTSP_STREAM, DEFAULT_RTSP_STREAM)

    for system in hub.api.systems:
        for alarm_panel in system.alarm_panels:
            for device in alarm_panel.devices:
                if type(device) is VivintCamera:
                    entities.append(
                        VivintCam(
                            hub, device, hd_stream=hd_stream, rtsp_stream=rtsp_stream
                        )
                    )

    if not entities:
        return

    _LOGGER.debug(f"Adding Vivint cameras: {entities}")
    async_add_entities(entities, True)


class VivintCam(VivintEntity, Camera):
    """Vivint camera."""

    def __init__(
        self,
        hub: VivintHub,
        device: VivintDevice,
        hd_stream: bool = DEFAULT_HD_STREAM,
        rtsp_stream: int = DEFAULT_RTSP_STREAM,
    ):
        super().__init__(hub, device)
        Camera.__init__(self)
        self.__hd_stream = hd_stream
        self.__rtsp_stream = rtsp_stream

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
        direct = await self.device.get_direct_rtsp_url(hd=self.__hd_stream)
        return (
            direct if self.__rtsp_stream == RTSP_STREAM_DIRECT else None
        ) or await self.device.get_rtsp_url(
            internal=self.__rtsp_stream != RTSP_STREAM_EXTERNAL, hd=self.__hd_stream
        )

    async def async_camera_image(self):
        """Return a frame from the camera stream."""
        ffmpeg = ImageFrame(self.hass.data[DATA_FFMPEG].binary)
        image = await asyncio.shield(
            ffmpeg.get_image(await self.stream_source(), output_format=IMAGE_JPEG)
        )
        return image

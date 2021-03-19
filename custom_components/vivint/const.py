"""Constants for the Vivint integration."""
DOMAIN = "vivint"
EVENT_TYPE = f"{DOMAIN}_event"

RTSP_STREAM_DIRECT = 0
RTSP_STREAM_INTERNAL = 1
RTSP_STREAM_EXTERNAL = 2
RTSP_STREAM_TYPES = {
    RTSP_STREAM_DIRECT: "Direct (falls back to internal if direct access is not available)",
    RTSP_STREAM_INTERNAL: "Internal",
    RTSP_STREAM_EXTERNAL: "External",
}

CONF_HD_STREAM = "hd_stream"
CONF_RTSP_STREAM = "rtsp_stream"
DEFAULT_HD_STREAM = True
DEFAULT_RTSP_STREAM = RTSP_STREAM_DIRECT

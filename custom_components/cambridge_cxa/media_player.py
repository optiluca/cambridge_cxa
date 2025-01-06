import json
import logging
import urllib.request
import paho.mqtt.client as mqtt
import voluptuous as vol

from homeassistant.components.media_player import MediaPlayerEntity, MediaPlayerEntityFeature, PLATFORM_SCHEMA

from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_TYPE,
    STATE_OFF,
    STATE_ON,
)
import homeassistant.helpers.config_validation as cv

__version__ = "0.3"

_LOGGER = logging.getLogger(__name__)

SUPPORT_CXA = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.SELECT_SOUND_MODE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
)

DEFAULT_NAME = "Cambridge Audio CXA"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TYPE): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

NORMAL_INPUTS_CXA61 = {
    "A1" : "#3,04,00",
    "A2" : "#3,04,01",
    "A3" : "#3,04,02",
    "A4" : "#3,04,03",
    "D1" : "#3,04,04",
    "D2" : "#3,04,05",
    "D3" : "#3,04,06",
    "Bluetooth" : "#3,04,14",
    "USB" : "#3,04,16",
    "MP3" : "#3,04,10"
}

NORMAL_INPUTS_CXA81 = {
    "A1" : "#3,04,00",
    "A2" : "#3,04,01",
    "A3" : "#3,04,02",
    "A4" : "#3,04,03",
    "D1" : "#3,04,04",
    "D2" : "#3,04,05",
    "D3" : "#3,04,06",
    "Bluetooth" : "#3,04,14",
    "USB" : "#3,04,16",
    "XLR" : "#3,04,20"
}

NORMAL_INPUTS_AMP_REPLY_CXA61 = {
    "#04,01,00" : "A1",
    "#04,01,01" : "A2",
    "#04,01,02" : "A3",
    "#04,01,03" : "A4",
    "#04,01,04" : "D1",
    "#04,01,05" : "D2",
    "#04,01,06" : "D3",
    "#04,01,14" : "Bluetooth",
    "#04,01,16" : "USB",
    "#04,01,10" : "MP3"
}

NORMAL_INPUTS_AMP_REPLY_CXA81 = {
    "#04,01,00" : "A1",
    "#04,01,01" : "A2",
    "#04,01,02" : "A3",
    "#04,01,03" : "A4",
    "#04,01,04" : "D1",
    "#04,01,05" : "D2",
    "#04,01,06" : "D3",
    "#04,01,14" : "Bluetooth",
    "#04,01,16" : "USB",
    "#04,01,20" : "XLR"
}

SOUND_MODES = {
    "A" : "#1,25,0",
    "AB" : "#1,25,1",
    "B" : "#1,25,2"
}

AMP_CMD_GET_PWSTATE = "#1,01"
AMP_CMD_GET_CURRENT_SOURCE = "#3,01"
AMP_CMD_GET_MUTE_STATE = "#1,03"

AMP_CMD_SET_MUTE_ON = "#1,04,1"
AMP_CMD_SET_MUTE_OFF = "#1,04,0"
AMP_CMD_SET_PWR_ON = "#1,02,1"
AMP_CMD_SET_PWR_OFF = "#1,02,0"

AMP_REPLY_PWR_ON = "#02,01,1"
AMP_REPLY_PWR_STANDBY = "#02,01,0"
AMP_REPLY_MUTE_ON = "#02,03,1"
AMP_REPLY_MUTE_OFF = "#02,03,0"

def setup_platform(hass, config, add_devices, discovery_info=None):
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    cxatype = config.get(CONF_TYPE)

    if host is None:
        _LOGGER.error("No MQTT host found in configuration.yaml for Cambridge CXA")
        return

    if cxatype is None:
        _LOGGER.error("No CXA type found in configuration.yaml file. Possible values are CXA61, CXA81")
        return

    add_devices([CambridgeCXADevice(host, name, cxatype)])

def on_connect(client, *args, **kwargs):
    _LOGGER.info("on connect: subscribing to base topic...")
    client.subscribe('media/cxa81/response')

class CambridgeCXADevice(MediaPlayerEntity):
    def __init__(self, host, name, cxatype):
        _LOGGER.info("Setting up Cambridge CXA")
        self._host = host

        self._mediasource = "#04,01,16"
        self._pwstate = AMP_REPLY_PWR_STANDBY
        self._muted = AMP_REPLY_MUTE_OFF
        self._name = name
        
        self._cxatype = cxatype.upper()
        if self._cxatype == "CXA61":
            self._source_list = NORMAL_INPUTS_CXA61.copy()
            self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_CXA61.copy()
        else:
            self._source_list = NORMAL_INPUTS_CXA81.copy()
            self._source_reply_list = NORMAL_INPUTS_AMP_REPLY_CXA81.copy()
        self._sound_mode_list = SOUND_MODES.copy()
        self._state = STATE_OFF

        self.client = mqtt.Client(client_id="ha_cambridge_cxa")
        self.client.on_connect = on_connect
        self.client.on_message = self.on_response
        self.client.connect(host)

        self.client.loop_start()

        self.update()
    
    def on_response(self, client, userdata, message):
        topic = message.topic
        msg = json.loads(str(message.payload.decode("utf-8")))
        _LOGGER.debug(f"Message received on topic {topic}: {msg}")

        if AMP_CMD_GET_PWSTATE in msg:
            self._pwstate = msg[AMP_CMD_GET_PWSTATE][0:8]
            _LOGGER.debug(f"CXA - update called. State is: {self._pwstate}")
        
        if AMP_REPLY_PWR_ON in self._pwstate:
            if AMP_CMD_GET_CURRENT_SOURCE in msg:
                self._mediasource = msg[AMP_CMD_GET_CURRENT_SOURCE][0:9]
                _LOGGER.debug(f"CXA - get current source called. Source is: {self._mediasource}")
            
            if AMP_CMD_GET_MUTE_STATE in msg:
                self._muted = msg[AMP_CMD_GET_MUTE_STATE][0:8]
                _LOGGER.debug(f"CXA - current mute state is: {self._muted}")
        
        self.schedule_update_ha_state()

    def update(self):
        self._send_mqtt_command_message(AMP_CMD_GET_PWSTATE)
        self._send_mqtt_command_message(AMP_CMD_GET_CURRENT_SOURCE)
        self._send_mqtt_command_message(AMP_CMD_GET_MUTE_STATE)

    @property
    def is_volume_muted(self):
        if AMP_REPLY_MUTE_ON in self._muted:
            return True
        else:
            return False
    
    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._source_reply_list[self._mediasource]

    @property
    def sound_mode_list(self):
        return sorted(list(self._sound_mode_list.keys()))

    @property
    def source_list(self):
        return sorted(list(self._source_list.keys()))

    @property
    def state(self):
        if "02,01,1" in self._pwstate:
            return STATE_ON
        else:
            return STATE_OFF

    @property
    def supported_features(self):
        return SUPPORT_CXA

    def mute_volume(self, mute):
        if mute:
            self._send_mqtt_command_message(AMP_CMD_SET_MUTE_ON)
        else:
            self._send_mqtt_command_message(AMP_CMD_SET_MUTE_OFF)

    def select_sound_mode(self, sound_mode):
        self._send_mqtt_command_message(self._sound_mode_list[sound_mode])

    def select_source(self, source):
        self._send_mqtt_command_message(self._source_list[source])

    def turn_on(self):
        self._send_mqtt_command_message(AMP_CMD_SET_PWR_ON)

    def turn_off(self):
        self._send_mqtt_command_message(AMP_CMD_SET_PWR_OFF)

    def _send_mqtt_volume_message(self, message):
        self.client.publish('media/cxa81/command/volume', message)

    def _send_mqtt_command_message(self, message):
        self.client.publish('media/cxa81/command/command', message)

    def volume_up(self):
        _LOGGER.debug("Sending VOLUME UP")
        self._send_mqtt_volume_message('VOLUME_UP')

    def volume_down(self):
        _LOGGER.debug("Sending VOLUME DOWN")
        self._send_mqtt_volume_message('VOLUME_DOWN')
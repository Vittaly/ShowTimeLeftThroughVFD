# coding=utf-8
#from ast import Not
import octoprint.plugin


from io import FileIO
from struct import *
from enum import IntEnum, auto



class DISPLAY_MODE(IntEnum):
    NONE = 0 
    CLOCK = auto()
    CHANNEL = auto()
    PLAYBACK_TIME = auto()
    TITLE = auto()
    TEMPERATURE = auto()
    DATE = auto()
    MAX = auto()

class c_time_date:
    def __init__(self):
        self.sec: int = 5
        self.min : int = 10
        self.hrs : int = 12
        self.dofw : int = 1
        self.day : int = 1
        self.month : int = 1
        self.year : int = 8
    def to_bytes(self) -> bytes:
        return pack('BBBBBBH', self.sec ,self.min, self.hrs, self.dofw, self.day, self.month, self.year)

class c_time_secondary:
    def __init__(self):
        self.sec = 11
        self.min = 18
        self.hrs =22
        self.reserved = 0
    def to_bytes(self) -> bytes:
        return pack('BBBB', self.sec ,self.min, self.hrs, self.reserved)

class c_channel_data:
    def __init__(self):
        self.channel = 55
        self.channel_count = 56
    def to_bytes(self) -> bytes:
        return pack('2H', self.channel ,self.channel_count)
	        




class VfdDisplayData:
    def __init__(self):
        
        self.mode: DISPLAY_MODE 
        self.mode = DISPLAY_MODE.CLOCK
        self.colon_on : int = 1
        self.temperature = 22
        self.time_date = c_time_date()
        self.time_secondary = c_time_secondary()
        self.channel_data = c_channel_data()
        self.string_main = 'Hellow word'
        self.string_secondary = 'title:'
    def to_bytes(self) -> bytes:
        sm_len = len(self.string_main)
        ss_len = len(self.string_secondary)
        return pack('H 2B 8B 4B 4B {}s{}x {}s{}x'. format(sm_len, 512-sm_len, ss_len, 128 - ss_len ), self.mode,  self.colon_on,  self.temperature , *(self.time_date.to_bytes()), *(self.time_secondary.to_bytes()), *(self.channel_data.to_bytes()), self.string_main.encode('utf-8'), self.string_secondary.encode('utf-8'))
        ''' ,[], [] ,  self.string_main, self.string_secondary       4B 2B 512s 128s'''


__author__ = "Vitaly Burkut"

class ShowTimeLeftThroughVFD (octoprint.plugin.StartupPlugin, octoprint.plugin.EventHandlerPlugin, octoprint.printer.PrinterCallback):
    def on_after_startup(self, *args, **kwargs):
        self.openvfd: FileIO = open('/tmp/openvfd_service', 'bw', 0) # without buffer
        self.data = VfdDisplayData()
        self._printer.register_callback(self)
        self._logger.info("init complete")

    def sendToDisplay(self)-> None:
        self.openvfd.write(self.data.to_bytes())
        self._logger.debug("sendToDisplay end")

    def __del__(self):
        if self.openvfd is not None and not self.openvfd.closed:
            self.openvfd.close()


    def on_printer_send_current_data(self, data):
        self._logger.debug(data['progress'])
        if data['progress']['printTimeLeft'] is not None:
            new_hrs: int = data['progress']['printTimeLeft'] // 3600
            new_min: int = (data['progress']['printTimeLeft']  - new_hrs * 3600) // 60
            self._logger.info("hrs: old={} new={}, min: old={}, new={}".format(self.data.time_date.hrs, new_hrs, self.data.time_date.min, new_min ))
            if self.data.time_date.hrs != new_hrs or self.data.time_date.min != new_min:
                self.data.mode = DISPLAY_MODE.PLAYBACK_TIME
                self.data.time_date.hrs = new_hrs
                self.data.time_date.min = new_min

                self._logger.info("change dusplayed playback value:{}:{} ({} sec)".format(new_hrs, new_min, data['progress']['printTimeLeft']))
                self.sendToDisplay()



    def on_event(self, event, payload):
        self._logger.debug("event:{}".format(event))
        if event in ("PrintFailed","PrintDone", "PrintCancelled"):
            self._logger.info("event:{}".format(event))
            self.data.mode  = DISPLAY_MODE.CLOCK
            self._logger.info("change dusplay mode to CLOCK by event:{}".format(event))
            self.sendToDisplay()

__plugin_name__ = "OpenVFD timeleft plugin"
__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_version__ = "0.0.1"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = ShowTimeLeftThroughVFD()

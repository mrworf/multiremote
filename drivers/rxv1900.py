# This file is part of multiRemote.
#
# multiRemote is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# multiRemote is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with multiRemote.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Implementation of RX-V1900 commands
"""
import requests
from modules.commandtype import CommandType
from .base import driverBase
import logging

class driverRxv1900(driverBase):
  cfg_YamahaController = None

  # Will be filled out by init
  RESPONSE_HANDLER = {}
  COMMAND_HANDLER = {}

  SYSTEM_TABLE = {
    "zone1" :
      {
        "vol-set"   : ["30", "26"],
      },

    "zone2" :
      {
        "vol-set"   : ["31", "27"],
      },

    "zone3" :
      {
        "vol-set"   : ["34", "A2"],
      },
  }

  OPERATION_TABLE = {
    "zone1" :
      {
        "power_on"  : ["E7E", "20"],
        "power_off" : ["E7F", "20"],
        "mute"      : ["EA2", "23"],
        "unmute"    : ["EA3", "23"],
        "vol-up"    : ["A1A", None],
        "vol-down"  : ["A1B", None],

        "input-phono"   : ["A14", "21"],
        "input-cd"      : ["A15", "21"],
        "input-tuner"   : ["A16", "21"],
        "input-mdcdr"   : ["A19", "21"],
        "input-mdtape"  : ["A18", "21"],
        "input-bd"      : ["AC8", "21"],
        "input-dvd"     : ["AC1", "21"],
        "input-tv"      : ["A54", "21"],
        "input-cbl"     : ["AC0", "21"],
        "input-vcr"     : ["A0F", "21"],
        "input-dvr"     : ["A13", "21"],
        "input-vaux"    : ["A55", "21"],
        "input-multich" : ["A87", "21"],
        "input-xm"      : ["AB4", "21"],
        "input-sirius"  : ["A39", "21"],
      },

    "zone2" :
      {
        "power_on"  : ["EBA", "20"],
        "power_off" : ["EBB", "20"],
        "mute"      : ["EA0", "25"],
        "unmute"    : ["EA1", "25"],
        "vol-up"    : ["ADA", None],
        "vol-down"  : ["ADB", None],

        "input-phono"   : ["AD0", "24"],
        "input-cd"      : ["AD1", "24"],
        "input-tuner"   : ["AD2", "24"],
        "input-mdcdr"   : ["AD4", "24"],
        "input-mdtape"  : ["AD3", "24"],
        "input-bd"      : ["ACE", "24"],
        "input-dvd"     : ["ACD", "24"],
        "input-tv"      : ["AD9", "24"],
        "input-cbl"     : ["ACC", "24"],
        "input-vcr"     : ["AD6", "24"],
        "input-dvr"     : ["AD7", "24"],
        "input-vaux"    : ["AD8", "24"],
        "input-xm"      : ["AB8", "24"],
        "input-sirius"  : ["A3A", "24"],
      },

    "zone3" :
      {
        "power_on"  : ["AED", "20"],
        "power_off" : ["AEE", "20"],
        "mute"      : ["E26", "A1"],
        "unmute"    : ["E66", "A1"],
        "vol-up"    : ["AFD", None],
        "vol-down"  : ["AFE", None],

        "input-phono"   : ["AF1", "A0"],
        "input-cd"      : ["AF2", "A0"],
        "input-tuner"   : ["AF3", "A0"],
        "input-mdcdr"   : ["AF5", "A0"],
        "input-mdtape"  : ["AF4", "A0"],
        "input-bd"      : ["AFB", "A0"],
        "input-dvd"     : ["AFC", "A0"],
        "input-tv"      : ["AF6", "A0"],
        "input-cbl"     : ["AF7", "A0"],
        "input-vcr"     : ["AF9", "A0"],
        "input-dvr"     : ["AFA", "A0"],
        "input-vaux"    : ["AF0", "A0"],
        "input-xm"      : ["AB9", "A0"],
        "input-sirius"  : ["A3B", "A0"],
      }
    }

  # Maps the response codes into the inputs, zone first, input later
  # some input cannot be translated, so they resolve to None
  MAP_INPUT = [
    [
      "input-phono",
      "input-cd",
      "input-tuner",
      "input-mdcdr",
      "input-mdtape",
      "input-dvd",
      "input-tv",
      "input-cbl",
      "input-cbl",  # SAT
      "input-vcr",
      "input-dvr",
      "input-vaux",
      None,         # USB
      "input-xm",
      "input-multich",
      "input-bd",
      None,         # DOCK/BT
      "input-sirius",
    ],
    [
      "input-phono",
      "input-cd",
      "input-tuner",
      "input-mdcdr",
      "input-mdtape",
      "input-dvd",
      "input-tv",
      "input-cbl",
      None,         # DOCK/BT
      "input-vcr",
      "input-dvr",
      "input-sirius",
      "input-vaux",
      None,         # USB
      "input-xm",
      "input-bd",
    ],
    [
      "input-phono",
      "input-cd",
      "input-tuner",
      "input-mdcdr",
      "input-mdtape",
      "input-dvd",
      "input-tv",
      "input-cbl",
      None,         # DOCK/BT
      "input-vcr",
      "input-dvr",
      "input-sirius",
      "input-vaux",
      None,         # USB
      "input-xm",
      "input-bd",
    ],
  ]

  def handlePower(self, cmd, data):
    i = int(data)
    if i == 0:
      self.power = [False, False, False]
    elif i == 1:
      self.power = [True, True, True]
    elif i == 2:
      self.power = [True, False, False]
    elif i == 3:
      self.power = [False, True, True]
    elif i == 4:
      self.power = [True, True, False]
    elif i == 5:
      self.power = [True, False, True]
    elif i == 6:
      self.power = [False, True, False]
    elif i == 7:
      self.power = [False, False, True]

    logging.info("Powerstate has changed to " + str(self.power))
    return

  def handleVolume(self, cmd, data):
    if cmd == "26":   # Zone 1
      z = 0
    elif cmd == "27": # Zone 2
      z = 1
    elif cmd == "A2": # Zone 3
      z = 2
    else:
      logging.warning("Unknown command " + cmd)
      return

    self.volume[z] = int(data, 16)
    logging.info("Volume has changed for Zone " + str(z+1) + " to " + data)
    return

  def handleInput(self, cmd, data):
    # Translate zone info
    if cmd == "21":
      z = 0
    elif cmd == "24":
      z = 1
    elif cmd == "A0":
      z = 2
    else:
      logging.warning("Unknown command " + cmd)
      return
    # now, lets translate the actual input that happened
    self.input[z] = self.MAP_INPUT[z][int(data, 16)]
    logging.info("Input for zone " + str(z+1) + " is " + str(self.input[z]))


  def issueOperation(self, zone, cmd):
    function = self.OPERATION_TABLE["zone" + str(zone)][cmd]
    logging.debug("zone" + str(zone) + ": " + cmd + " = " + repr(function))

    url = self.cfg_YamahaController + "/operation/" + function[0]
    if function[1] != None:
      url += "/" + function[1]

    try:
      r = requests.get(url, timeout=5)
      if r.status_code != 200:
        logging.error("Remote was unable to execute command %s" % cmd)
        return False
    except:
      logging.exception("issueOperation: " + url)
      return False

    j = r.json()

    if j["status"] != 200:
      logging.error("Remote received command but failed to execute")
      return False

    if function[1] != None:
      self.interpretResult(j["result"])

    return True

  def getStatus(self, field=None):
    url = self.cfg_YamahaController + "/report"
    if field is not None and len(field) == 2:
      url += "/" + field

    try:
      r = requests.get(url, timeout=5)
      if r.status_code != 200:
        logging.error("Remote was unable to execute command")
        return None
    except:
      logging.exception("getStatus: " + url)
      return None

    j = r.json()
    logging.info("Report said:" + repr(j))
    return j

  def issueSystem(self, zone, command, data):
    function = self.SYSTEM_TABLE["zone" + str(zone)][command]

    # Convert data into what's needed
    param = str(data)
    if len(param) < 2:
      param = "0" + param

    logging.debug("Zone " + str(zone) + ": " + repr(command) + " = " + repr(function) + " (param: '" + repr(param) + "')")
    url = self.cfg_YamahaController + "/system/" + function[0] + param
    if function[1] != None:
      url += "/" + function[1]

    try:
      r = requests.get(url, timeout=5)
      if r.status_code != 200:
        logging.error("Remote was unable to execute command")
        return False
    except:
      logging.exception("issueSystem: " + url)
      return False

    j = r.json()

    if j["status"] != 200:
      logging.error("Remote received command but failed to execute")
      return False

    if function[1] != None:
      self.interpretResult(j["result"])

    return True

  def interpretResult(self, result):
    # Dig deeper in the result
    if not result["valid"]:
      logging.warning("Result isn't valid: " + result)
    elif not result["command"] in self.RESPONSE_HANDLER:
      logging.warning("No handler defined for " + str(result))
    else:
      self.RESPONSE_HANDLER[result["command"]](result["command"], result["data"])
    return

  def init(self, server):
    self.cfg_YamahaController = server

    # Some tracking stuff
    self.power = [False, False, False]
    self.volume = [0, 0, 0]
    self.input = [None, None, None]
    self.mute = [False, False, False]

    """Response code associated with function that handles it"""
    self.RESPONSE_HANDLER = {
      "20" : self.handlePower,  # Power (for all zones)

      "26" : self.handleVolume, # Zone 1 volume
      "27" : self.handleVolume, # Zone 2 volume
      "A2" : self.handleVolume, # Zone 3 volume

      "21" : self.handleInput,  # Zone 1 input
      "24" : self.handleInput,  # Zone 2 input
      "A0" : self.handleInput,  # Zone 3 input
    }

    """Command name associated with number of arguments"""
    self.COMMAND_HANDLER = {
      "volume-up"     : {
        "arguments"   : 0,
        "handler"     : self.setVolumeUp,
        "name"        : "Volume Up",
        "description" : "Increases volume",
        "type"        : CommandType.VOLUME_UP
      },
      "volume-down"   : {
        "arguments"   : 0,
        "handler"     : self.setVolumeDown,
        "name"        : "Volume Down",
        "description" : "Decreases volume",
        "type"        : CommandType.VOLUME_DOWN
      },
      "volume-set"    : {
        "arguments"   : 1,
        "handler"     : self.setVolume,
        "name"        : "Set Volume",
        "description" : "Sets the volume to a specific level",
        "type"        : CommandType.VOLUME_SET
      },
      "volume-get"    : {
        "arguments"   : 0,
        "handler"     : self.getVolume,
        "name"        : "Get Volume",
        "description" : "Gets the volume for a zone",
        "type"        : CommandType.VOLUME_GET
      },
      "volume-mute"   : {
        "arguments"   : 0,
        "handler"     : self.setMute, "extras" : True,
        "name"        : "Mute",
        "description" : "Mutes the audio",
        "type"        : CommandType.VOLUME_MUTE
      },
      "volume-unmute" : {
        "arguments"   : 0,
        "handler"     : self.setMute, "extras" : False,
        "name"        : "Unmute",
        "description" : "Returns audio to previous level",
        "type"        : CommandType.VOLUME_UNMUTE
      },
      "input-mdcdr"   : {
        "arguments"   : 0,
        "handler"     : self.setInput, "extras" : "input-mdcdr",
        "name"        : "Input MD/CDR",
        "type"        : CommandType.PRIVATE_INPUT
      },
      "input-bd"      : {
        "arguments"   : 0,
        "handler"     : self.setInput, "extras" : "input-bd",
        "name"        : "Input BD",
        "type"        : CommandType.PRIVATE_INPUT
      },
      "input-dvd"     : {
        "arguments"   : 0,
        "handler"     : self.setInput, "extras" : "input-dvd",
        "name"        : "Input DVD",
        "type"        : CommandType.PRIVATE_INPUT
      },
      "input-dvr"   : {
        "arguments"   : 0,
        "handler"     : self.setInput, "extras" : "input-dvr",
        "name"        : "Input DVR",
        "type"        : CommandType.PRIVATE_INPUT
      },
      "input-cbl"      : {
        "arguments"   : 0,
        "handler"     : self.setInput, "extras" : "input-cbl",
        "name"        : "Input CBL",
        "type"        : CommandType.PRIVATE_INPUT
      },
      "input-cd"      : {
        "arguments"   : 0,
        "handler"     : self.setInput, "extras" : "input-cd",
        "name"        : "Input CD",
        "type"        : CommandType.PRIVATE_INPUT
      },
    }

  def getCommands(self):
    ret = {}
    for c in self.COMMAND_HANDLER:
      ret[c] = {"name": "", "description": ""}
      if "name" in self.COMMAND_HANDLER[c]:
        ret[c]["name"] = self.COMMAND_HANDLER[c]["name"]
      if "description" in self.COMMAND_HANDLER[c]:
        ret[c]["description"] = self.COMMAND_HANDLER[c]["description"]
      ret[c]["type"] = self.COMMAND_HANDLER[c]["type"]

    return ret

  def handleCommand(self, zone, command, *args):
    result = None
    if not command in self.COMMAND_HANDLER:
      logging.error("%s is not a command" % command)
      return result
    zone = int(zone)
    item = self.COMMAND_HANDLER[command]
    if item["arguments"] == 0:
      if "extras" in item:
        result = item["handler"](zone, item["extras"])
      else:
        result = item["handler"](zone)
    elif item["arguments"] == 1:
      if "extras" in item:
        result = item["handler"](zone, args[0], item["extras"])
      else:
        result = item["handler"](zone, args[0])
    return result

  # Controls the power of the various zones
  #
  def setPower(self, zone, power):
    # Make sure we don't do silly things
    ret = False
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    if self.power[zone-1] == power:
      logging.warn("Zone " + str(zone) + " already set to desired power state (" + str(power) + ")")
      return True

    if power:
      if self.issueOperation(zone, "power_on"):
        # TODO: HACK FOR VOLUME! THIS NEEDS TO BE IMPROVED!
        zns = ['26', '27', 'A2']
        z = zns[zone-1]
        res = self.getStatus(z)
        if 'result' in res and res['status'] == 200:
          self.interpretResult(res["result"])
        ret = {'volume' : self.translateVolumeFrom(self.volume[zone-1])}

        self.sendEvent('state', None, {'zone' : f'zone{zone}', 'volume' : ret['volume']})
    else:
      ret = self.issueOperation(zone, "power_off")
    return ret

  def getPower(self, zone):
    # Make sure we don't do silly things
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    return self.power[zone-1]

  def setMute(self, zone, mute):
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    if mute:
      ret = self.issueOperation(zone, "mute")
    else:
      ret = self.issueOperation(zone, "unmute")

    return ret

  def getMute(self, zone):
    # Make sure we don't do silly things
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    return self.mute[zone-1]

  def translateVolumeFrom(self, value):
    return int(((value - 39) * 10000) / 160)

  def translateVolumeTo(self, value):
    return int((value * 160) / 10000 + 39)

  def setVolume(self, zone, volume):
    """Setting the volume directly works as follows:
       0-1000 is -80 to 0db (27-C7)
       (DISABLED!) 100-150 is 0 to +16.5db (C7-E8)
    """
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    volume = int(volume)
    if volume > 10000:
      volume = 10000
    #  volume = ((volume * 2) * 33) / 100
    #else:
    volume = self.translateVolumeTo(volume)

    logging.debug("setVoume(%s) = 0x%02x", volume, volume)

    if self.issueSystem(zone, "vol-set", "%02x" % volume):
      ret = {'volume' : self.translateVolumeFrom(self.volume[zone-1])}
      self.sendEvent('state', None, {'zone' : f'zone{zone}', 'volume' : ret['volume']})
      return ret
    else:
      return False

  def setVolumeUp(self, zone):
    # Make sure we don't do silly things
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False
    if self.volume[zone-1] < 199:
      self.volume[zone-1] += 1
      if self.issueOperation(zone, "vol-up"):
        ret = {'volume' : self.translateVolumeFrom(self.volume[zone-1])}
        self.sendEvent('state', None, {'zone' : f'zone{zone}', 'volume' : ret['volume']})
        return ret
    return False

  def setVolumeDown(self, zone):
    # Make sure we don't do silly things
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False
    if self.volume[zone-1] > 39:
      self.volume[zone-1] -= 1
      if self.issueOperation(zone, "vol-down"):
        ret = {'volume' : self.translateVolumeFrom(self.volume[zone-1])}
        self.sendEvent('state', None, {'zone' : f'zone{zone}', 'volume' : ret['volume']})
        return ret

    return False

  def getVolume(self, zone):
    # Make sure we don't do silly things
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    return {'volume' : self.translateVolumeFrom(self.volume[zone-1])}

  def setInput(self, zone, input):
    # Make sure we don't do silly things
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    # Figure out if this is a valid input for the zone
    if not input in self.OPERATION_TABLE["zone" + str(zone)]:
      logging.error("" + input + " not supported by zone " + str(zone))
      return False

    # Alright, let's do it!
    return self.issueOperation(zone, input)

  def getInput(self, zone):
    zone = int(zone)
    if zone < 1 or zone > 3:
      logging.error("Zone " + str(zone) + " not supported by driver")
      return False

    return self.input[zone-1]

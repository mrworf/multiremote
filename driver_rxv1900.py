"""
Implementation of RX-V1900 commands

Supports the required API used by receivers:

setVolume(zone, value)
setVolumeUp(zone)
setVolumeDown(zone)
setPower(zone, bool)
setInput(zone, value)
setMute(zone, bool)

value = getVolume(zone)
bool = getPower(zone)
bool = getMute(zone)
value = getInput(zone)



"""
import requests

class DriverRXV1900:
  cfg_YamahaController = "http://av-interface.sfo.sensenet.nu:5000"

  # Will be filled out by init
  RESPONSE_HANDLER = {}

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
        "vol-up"    : ["A1A", "26"],
        "vol-down"  : ["A1B", "26"],
          
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
        "vol-up"    : ["ADA", "27"],
        "vol-down"  : ["ADB", "27"],
          
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
        "vol-up"    : ["AFD", "A2"],
        "vol-down"  : ["AFE", "A2"],
          
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
      
    print "INFO: Powerstate has changed to " + str(self.power)
    return
    
  def handleVolume(self, cmd, data):
    if cmd == "26":   # Zone 1
      z = 0
    elif cmd == "27": # Zone 2
      z = 1
    elif cmd == "A2": # Zone 3
      z = 2
    else:
      print "WARN: Unknown command " + cmd
      return
    
    self.volume[z] = int(data, 16)
    print "INFO: Volume has changed for Zone " + str(z+1) + " to " + data
    return
    
  def handleInput(self, cmd, data):
    if cmd == "21":
      z = 0
    elif cmd == "24":
      z = 1
    elif cmd == "A0":
      z = 2
    else:
      print "WARN: Unknown command " + cmd
      return
    # now, lets translate
    self.input[z] = self.MAP_INPUT[z][int(data)]
    print "INFO: Input for zone " + str(z+1) + " is " + str(self.input[z])
    
  
  def issueOperation(self, zone, cmd):
    function = self.OPERATION_TABLE["zone" + str(zone)][cmd]
    print "zone" + str(zone) + ": " + cmd + " = " + repr(function)
    r = requests.get(self.cfg_YamahaController + "/operation/" + function[0] + "/" + function[1])
    if r.status_code != 200:
      print "ERROR: Remote was unable to execute command"
      return False

    j = r.json()
    print repr(j);
    
    if j["status"] != 200:
      print "ERROR: Remote received command but failed to execute"
      return False
    
    self.interpretResult(j["result"])
    
    return True

  def issueSystem(self, zone, cmd, data):
    function = self.SYSTEM_TABLE["zone" + str(zone)][cmd]
    
    # Convert data into what's needed
    t = str(data)
    if len(t) < 2:
      t = "0" + t
    function += t
    
    print "Zone " + str(zone) + ": " + cmd + " = " + function
    r = requests.get(self.cfg_YamahaController + "/system/" + function)
    if r.status_code != 200:
      print "ERROR: Remote was unable to execute command"
      return False

    j = r.json()
    
    if j["status"] != 200:
      print "ERROR: Remote received command but failed to execute"
      return False
    
    self.interpretResult(j["result"])
    
    return True
  
  def interpretResult(self, result):
    # Dig deeper in the result
    if not result["valid"]:
      print "WARN: Result isn't valid: " + result
    elif not result["command"] in self.RESPONSE_HANDLER:
      print "WARN: No handler defined for " + str(result)
    else:    
      self.RESPONSE_HANDLER[result["command"]](result["command"], result["data"])
    return
  
  def __init__(self):
    # Some tracking stuff
    self.power = [False, False, False]
    self.volume = [0, 0, 0]
    self.input = [None, None, None]
    self.mute = [False, False, False]
    
    self.RESPONSE_HANDLER = {
      "20" : self.handlePower,  # Power (for all zones)
        
      "26" : self.handleVolume, # Zone 1 volume
      "27" : self.handleVolume, # Zone 2 volume
      "A2" : self.handleVolume, # Zone 3 volume
        
      "21" : self.handleInput,  # Zone 1 input
      "24" : self.handleInput,  # Zone 2 input
      "A0" : self.handleInput,  # Zone 3 input
    }
  
  # Controls the power of the various zones
  #
  def setPower(self, zone, power):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return False
      
    if self.power[zone-1] == power:
      print "Zone " + str(zone) + " already set to desired power state (" + str(power) + ")"
      return True
      
    if power:
      ret = self.issueOperation(zone, "power_on")
    else:
      ret = self.issueOperation(zone, "power_off")
    return ret

  def getPower(self, zone):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return False
      
    return self.power[zone-1]
    
  def setMute(self, zone, mute):
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return False

    if mute:
      ret = self.issueOperation(zone, "mute")
    else:
      ret = self.issueOperation(zone, "unmute")
      
    return ret  
  
  def getMute(self, zone):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return False

    return self.mute[zone-1]

  def setVolume(self, zone, volume):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return 0

    return self.issueSystem(zone, "vol-set", volume)

  def setVolumeUp(self, zone):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return 0
    return self.issueOperation(zone, "vol-up")

  def setVolumeDown(self, zone):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return 0
    return self.issueOperation(zone, "vol-down")

  def getVolume(self, zone):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return 0

    return self.volume[zone-1]    

  def setInput(self, zone, input):
    # Make sure we don't do silly things
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return False
    
    # Figure out if this is a valid input for the zone
    if not input in self.OPERATION_TABLE["zone" + str(zone)]:
      print "ERROR: " + input + " not supported by zone " + str(zone)
      return False
    
    # Alright, let's do it!
    return self.issueOperation(zone, input)
  
  def getInput(self, zone):
    if zone < 1 or zone > 3:
      print "ERROR: Zone " + str(zone) + " not supported by driver"
      return False

    return self.input[zone-1]    
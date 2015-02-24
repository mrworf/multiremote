#!/usr/bin/env python
"""
REST based remote control
It's able to handle multiple remotes controlling the same list of equipment.

It does NOT provide a UI, instead it's up to the user of this API to create
a UI which makes the most sense.

The whole concept is based on remotes being attached/detached to zones and
scenes. Attach/Detach will NOT automatically power things on/off but attaching
to a new scene will automatically detach from the previous.
"""
from flask import Flask
from flask import jsonify
import threading
import Queue
import time

# Import the devices
from driver_rxv1900 import DriverRXV1900
from driver_spotify import DriverSpotify

cfg_ServerAddr = "0.0.0.0"

"""
Lists and loads the various devices which will be needed by
the controller.
"""
DRIVER_TABLE = {
  "receiver"  : DriverRXV1900(),
  "spotify"   : DriverSpotify()
    
}

"""
Scenes describe what's needed to utilize for example, Spotify.

DRIVER tells us which ... driver to use. But it also allows us to
detect when there will be a conflict.

NAME is the name to show in the display

DESCRIPTION is a longer description (if we need it)

AUDIO if true indicates that this scene needs audio (limits zones)

VIDEO if true indicates that this scene needs video (limits zones)

INPUT tells which input on the receiver which is used

AUX adds a possibility to supply extra details which is handled
by the driver.
"""

SCENE_TABLE = {
  "spotify" : {
    "driver"      : "spotify",
    "name"        : "Spotify",
    "description" : "Allows you to listen to music (Swedish Spotify)",
    "audio"       : True,
    "video"       : False,
    "input"       : "input-mdcdr",
  },

  "plex" : {
    "driver"      : "plex",
    "name"        : "Plex Media Center",
    "description" : "Watch movies and TV series",
    "audio"       : True,
    "video"       : True,
    "input"       : "input-dvd",
  },
  
  "netflix" : {
    "driver"      : "roku",
    "name"        : "NetFlix",
    "description" : "Watch movies and TV series",
    "audio"       : True,
    "video"       : True,
    "input"       : "input-bd",
    "aux"         : "app:netflix"
  },

  "amazon" : {
    "driver"      : "roku",
    "name"        : "Amazon",
    "description" : "Watch movies and TV series",
    "audio"       : True,
    "video"       : True,
    "input"       : "input-bd",
    "aux"         : "app:amazon"
  },

  "ps4" : {
    "driver"      : "ps4",
    "name"        : "Playstation 4",
    "description" : "Play games",
    "audio"       : True,
    "video"       : True,
    "input"       : "input-cbl",
    # Below not implemented, put there to remind me,
    # possibly not final solution
    "dependency"  : {
      "driver": "splitter", 
      "enable": [
        "power-on", 
        "input-1"
      ],
      "disable": [
        "power-off"
      ]
    }
  },
}

"""
Zones describe what the zones are capable of

AUDIO the device(s) which are used for playing audio

VIDEO the device(s) which are used for playing video

Both AUDIO and VIDEO are arrays, but you cannot (currently) choose to use
more than ONE of the devices listed in said arrays. If a zone completely lacks
some feature, it will be None instead of an array.
"""
ZONE_TABLE = {
  "zone1" : {
    "id"    : 1,
    "name"  : "Livingroom",
    "audio" : ["receiver"],
    "video" : ["tv", "projector"],
  },
  "zone2" : {
    "id"    : 2,
    "name"  : "Kitchen",
    "audio" : ["receiver"],
    "video" : None,
  },
  "zone3" : {
    "id"    : 3,
    "name"  : "Patio",
    "audio" : ["receiver"],
    "video" : None,
  }
}

"""
Remote configuration

Currently it's a static configuration and it uses basic HTTP authentication
to avoid "mistakes" by regular browsers. Username is derived from the base
key and the password is held within.

It also defines the home zone for a remote. The idea is that usually a remote
will charge in relation to the zone it will control.

This list also holds information needed during runtime which you normally
do not supply during configuration.

Note!
Password not yet implemented
"""
REMOTE_TABLE = {
  "kitchen" : {
    "name"        : "Kitchen",
    "description" : '10" kitchen tablet',
    "zone"        : "zone2",
    "password"    : "secret",
  },
  
  "livingroom" : {
    "name"        : "Livingroom",
    "description" : '7" entertainment phablet',
    "zone"        : "zone1",
    "password"    : "secret",
  }
}

class Router (threading.Thread):
  DELAY = 30 # delay in seconds
  workList = Queue.Queue(10)
  
  RouteMap = {}
  
  def __init__(self):
    threading.Thread.__init__(self)
    self.daemon = True
    self.start()
  
  def submitRoute(self, zone, scene):
    """
    If scene is None, it means to remove the input, ergo, close it. 
    """
    self.workList.put({zone : self.resolveScene(scene)})
  
  def run(self):
    while True:
      order = self.workList.get(True)
      self.processWorkOrder(order)

  def getZoneDriver(self, zone):
    if zone in self.RouteMap:
      return self.RouteMap[zone]
    return None

  def processWorkOrder(self, order):
    zone, newDriver = order.popitem()
    zid = self.resolveZoneId(zone)
    oldDriver = self.getZoneDriver(zone)
    self.RouteMap[zone] = newDriver
    
    if newDriver is None:
      self.resolveDriver(self.resolveZoneAudio(zone)).setPower(zid, False)
      if self.zoneUsage(oldDriver) == False:
        self.resolveDriver(oldDriver).setPower(False)
    elif oldDriver is None:
      self.resolveDriver(self.resolveZoneAudio(zone)).setPower(zid, True)
      self.resolveDriver(newDriver).setPower(True)

    if newDriver != None and newDriver != oldDriver:
      self.resolveDriver(self.resolveZoneAudio(zone)).setInput(zid, self.resolveInput(newDriver))    
  
  def zoneUsage(self, driver):
    """Check if a driver is still in use"""
    for r in self.RouteMap:
      if self.RouteMap[r] == driver:
        return True
    return False

  def resolveScene(self, scene):
    """Resolves a scene into the underlying driver"""
    if scene is None:
      return None
    return SCENE_TABLE[scene]["driver"]

  def resolveDriver(self, driver):
    """Translates a driver into its object"""
    return DRIVER_TABLE[driver]
  
  def resolveZoneId(self, zone):
    """Translates the zone name into a numerical id"""
    return ZONE_TABLE[zone]["id"]

  def resolveZoneAudio(self, zone):
    """Translates the zone name into the audio component, right now we just use the first one"""
    return ZONE_TABLE[zone]["audio"][0]
  
  def resolveInput(self, driver):
    """Translates the driver into the correct input on the receiver"""
    for s in SCENE_TABLE:
      if SCENE_TABLE[s]["driver"] == driver:
        return SCENE_TABLE[s]["input"]
    return None

app = Flask(__name__)
router = Router()

@app.route("/")
def api_root():
  msg = {"status": "ok"}
  result = jsonify(msg)
  result.status_code = 200
    
  return result

@app.route("/scene", defaults={"scene" : None})
@app.route("/scene/<scene>")
def api_scene(scene):
  ret = {
    "status" : 200,
  }
   
  if scene is None:
    ret["scenes"] = sceneGetList(None)
  elif not scene in SCENE_TABLE:
    ret["status"] = 404
    ret["message"] = "No such scene"
  else:
    ret["scene"] = {
      "scene"       : scene,
      "name"        : SCENE_TABLE[scene]["name"],
      "description" : SCENE_TABLE[scene]["description"],
      "zones"       : sceneGetAssigned(scene),
      "remotes"     : sceneGetAttached(scene)
    }
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/assign", defaults={"zone" : None, "scene" : None})
@app.route("/assign/<zone>", defaults={"scene" : None})
@app.route("/assign/<zone>/<scene>")
def api_assign(zone, scene):
  ret = {
    "status" : 200,
  }
  
  if zone == None:
    ret["zones"] = zoneGetList()
  else:
    ret["active"] = zoneGetScene(zone)
  
  if scene != None:
    ZONE_TABLE[zone]["active-scene"] = scene;
    router.submitRoute(zone, scene)
    
  elif zone != None:
    ret["scenes"] = sceneGetList(zone)

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/unassign/<zone>")
def api_unassign(zone):
  ret = {
    "status" : 200,
    "active" : None
  }
  
  ZONE_TABLE[zone]["active-scene"] = None;
  router.submitRoute(zone, None)
  
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/attach/<remote>", defaults={"zone" : None, "options" : None})
@app.route("/attach/<remote>/<zone>", defaults={"options" : None})
@app.route("/attach/<remote>/<zone>/<options>")
def api_attach(remote, zone, options):
  ret = {
    "status" : 200,
  }
  
  ret["active"] = REMOTE_TABLE[remote]["active-zone"]
  if zone != None:
    ret["users"] = sceneGetAttached(zone)
    if options == "check":
      pass
    else:
       REMOTE_TABLE[remote]["active-zone"] = zone

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/detach/<remote>")
def api_detach(remote):
  ret = {
    "status" : 200,
    "active" : None
  }
  REMOTE_TABLE[remote]["active-zone"] = None;

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/command/<remote>", defaults={"command" : None, "arguments" : None})
@app.route("/command/<remote>/<command>", defaults={"arguments" : None})
@app.route("/command/<remote>/<command>/<arguments>")
def api_command(remote, command, arguments):
  """
  /command/<remote>
  Lists available commands for remote, if remote is not attached, this will
  return an error.
  
  /command/<remote>/<command>
  Executes said command without any arguments
  
  /command/<remote>/<command>/<arguments>
  Executes said command supplied argument
  """
  ret = {
    "status" : 200,
  }
  # Are we even attached?
  if REMOTE_TABLE[remote]["active-zone"] == None:
    ret["status"] = 500;
    ret["message"] = "Not attached"
  elif command == None:
    ret["scene-commands"] = sceneListCommands(remote)
    ret["zone-commands"] = zoneListCommands(zone)
  else:
    ret["result"] = sceneExecCommand(remote, command, arguments)
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

# For quick testing
@app.route("/direct/<device>/<function>/<int:zone>/<value>")
def api_direct(device, function, zone, value):
  ret = False
  f = DRIVER_TABLE[device];
  if function == "power":
    if int(value) == 0:
      ret = f.setPower(zone, False)
    else:
      ret = f.setPower(zone, True)
  elif function == "input":
    ret = f.setInput(zone, value)
  elif function == "volup":
    ret = f.setVolumeUp(zone)
  elif function == "voldown":
    ret = f.setVolumeDown(zone)
  elif function == "volume":
    ret = f.setVolume(zone, int(value))
  else:
    return "Unsupported"
    
  msg = "Status: " + str(ret)
  msg += "<br>"
  msg += "Volume: " + str(f.getVolume(zone))
  return msg

def sceneGetAttached(zone):
  ret = []
  for r in REMOTE_TABLE:
    if REMOTE_TABLE[r]["active-zone"] == zone:
      ret.append(r)
  return ret

def sceneGetAssigned(scene):
  ret = []
  for z in ZONE_TABLE:
    if ZONE_TABLE[z]["active-scene"] == scene:
      ret.append(z)
  return ret

def zoneGetList():
  ret = {}
  for z in ZONE_TABLE:
    ret[z] = ZONE_TABLE[z]["name"]
  return ret

def zoneGetScene(zone):
  return ZONE_TABLE[zone]["active-scene"]

def sceneGetList(zone):
  # First, find the capabilities of the zone
  if zone is None:
    audio = True
    video = True
  else:
    audio = ZONE_TABLE[zone]["audio"] != None
    video = ZONE_TABLE[zone]["video"] != None
  
  ret = []
  
  # Next, iterate scenes and pick out the ones which would work
  for s in SCENE_TABLE:
    if SCENE_TABLE[s]["audio"] and not audio:
      continue
    if SCENE_TABLE[s]["video"] and not video:
      continue
    ret.append(s)
    
  return ret

def sceneListCommands(remote):
  # Resolve scene and ask
  obj = DRIVER_TABLE[REMOTE_TABLE[remote]["active-zone"]]
  ret = obj.getCommands()
  return ret

def sceneExecCommand(remote, command, *arguments):
  print "Remote " + remote + " wants to do " + command
  
  # Find the zone
  zone = REMOTE_TABLE[remote]["active-zone"]
  zid = ZONE_TABLE[zone]["id"]
  print "Zone is " + zone + "(" + str(zid) + ")"
  driver = ZONE_TABLE[zone]["audio"][0];
  driver = DRIVER_TABLE[driver]
  
  driver.handleCommand(zid, command, arguments)
  
  return "OK"

# This SHOULD function like the scenes
def zoneListCommands(zone):
  return ["volume-up",
          "volume-down",
          "volume-set",
          "volume-mute",
          "volume-unmute"]


if __name__ == "__main__":
  
  # Initialize the extra data we need to track stuff
  for remote in REMOTE_TABLE:
    REMOTE_TABLE[remote]["active-zone"] = None

  for zone in ZONE_TABLE:
    ZONE_TABLE[zone]["active-scene"] = None

  app.debug = True
  app.run(host=cfg_ServerAddr)


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
    "audio" : ["receiver"],
    "video" : ["tv", "projector"],
  },
  "zone2" : {
    "audio" : ["receiver"],
    "video" : None,
  },
  "zone3" : {
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


app = Flask(__name__)

@app.route("/")
def api_root():
  msg = {"status": "ok"}
  result = jsonify(msg)
  result.status_code = 200
    
  return result

@app.route("/scene/<scene>")
def api_scene(scene):
  if not scene in SCENE_TABLE:
    ret = {"status": 404}
  else:
    ret = {
      "status" : 200,
      "scene" : SCENE_TABLE[scene]
    }
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/assign/<zone>", defaults={"scene" : None})
@app.route("/assign/<zone>/<scene>")
def api_assign(zone, scene):
  ret = {
    "status" : 200,
    "active-scene" : getZoneScene(zone)
  }
  
  if scene != None:
    ZONE_TABLE[zone]["active-scene"] = scene;
  
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/unassign/<zone>")
def api_unassign(zone):
  ret = {
    "status" : 200,
    "active-scene" : None
  }
  
  ZONE_TABLE[zone]["active-scene"] = None;
  
  ret = jsonify(ret)
  ret.status_code = 200
  return ret
    


@app.route("/attach/<remote>/<zone>", defaults={"scene" : None, "options" : None})
@app.route("/attach/<remote>/<zone>/<scene>", defaults={"options" : None})
@app.route("/attach/<remote>/<zone>/<scene>/<options>")
def api_attach(remote, zone, scene, options):
  ret = {
    "status" : 200,
  }
  
  if scene == None:
    # List available scenes for this zone
    ret["scenes"] = sceneList(zone)
    ret["active-scene"] = getZoneScene(zone)
  else:
    ret["scene-in-use"] = isSceneActive(scene, remote)
    ret["active-scene"] = getZoneScene(zone)
    if options == "check":
      pass
    else:
      REMOTE_TABLE[remote]["active-scene"] = scene

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/detach/<remote>")
def api_detach(remote):
  ret = {
    "status" : 200,
  }
  REMOTE_TABLE[remote]["active-scene"] = None;
    
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
  if REMOTE_TABLE[remote]["active-scene"] == None:
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

def isSceneActive(scene, skipRemote=None):
  for r in REMOTE_TABLE:
    if skipRemote != None and r == skipRemote:
      continue;
    if REMOTE_TABLE[r]["active-scene"] == scene:
      return True
  return False  

def getZoneScene(zone):
  return ZONE_TABLE[zone]["active-scene"]

def sceneList(zone):
  # First, find the capabilities of the zone
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
  obj = DRIVER_TABLE[REMOTE_TABLE[remote]["active-scene"]]
  ret = obj.getCommands()
  return ret

def sceneExecCommand(remote, command, arguments):
  return "OK"

# This SHOULD function like the scenes
def zoneListCommands(zone):
  return ["power-on", 
          "power-off",
          "volume-up",
          "volume-down",
          "volume-set",
          "volume-mute",
          "volume-unmute",
          "input-set"]


if __name__ == "__main__":
  
  # Initialize the extra data we need to track stuff
  for remote in REMOTE_TABLE:
    REMOTE_TABLE[remote]["active-scene"] = None
    REMOTE_TABLE[remote]["active-zone"] = None

  for zone in ZONE_TABLE:
    ZONE_TABLE[zone]["active-scene"] = None

  app.debug = True
  app.run(host=cfg_ServerAddr)


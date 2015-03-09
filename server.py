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

from router import Router
from config import Config

cfg_ServerAddr = "0.0.0.0"

app = Flask(__name__)
config = Config()
router = Router(config)

@app.route("/")
def api_root():
  msg = {"status": "ok"}
  result = jsonify(msg)
  result.status_code = 200
    
  return result

@app.route("/scene", defaults={"scene" : None})
@app.route("/scene/<scene>")
def api_scene(scene):
  ret = {}
   
  if scene is None:
    ret["scenes"] = config.getSceneList(None)
  elif not config.hasScene(scene):
    ret["error"] = "No such scene"
  else:
    ret["scene"] = {
      "scene"       : scene,
      "name"        : config.getScene(scene)["name"],
      "description" : config.getScene(scene)["description"],
      "zones"       : config.getSceneZoneUsage(scene),
      "remotes"     : config.getSceneRemoteUsage(scene)
    }
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/zone", defaults={"zone" : None})
@app.route("/zone/<zone>")
def api_zone(zone):
  ret = {}
  
  if zone is None:
    ret["zones"] = config.getZoneList()
  elif not config.hasZone(zone):
    ret["error"] = "No such zone"
  else:
    ret = {
      "zone"        : zone,
      "name"        : config.getZone(zone)["name"],
      "scene"       : config.getZoneScene(zone),
      "remotes"     : config.getZoneRemoteList(zone)
    }
    if config.hasSubZones(zone):
      ret["subzones"] = config.getSubZoneList(zone)
      ret["subzone"] = config.getSubZone(zone)
  ret = jsonify(ret)
  ret.status_code = 200
  return ret
  

@app.route("/assign", defaults={"zone" : None, "scene" : None, "options" : None})
@app.route("/assign/<zone>", defaults={"scene" : None, "options" : None})
@app.route("/assign/<zone>/<scene>", defaults={"options" : None})
@app.route("/assign/<zone>/<scene>/<options>")
def api_assign(zone, scene, options):
  """
  Options can be either clone or unassign:
    clone = Other zones will do the same thing
    unassign = Other zones will be unassigned
  """
  ret = {}
  
  if zone == None:
    ret["zones"] = config.getZoneList()
  else:
    if scene == None:
      ret["scenes"] = config.getSceneListForZone(zone)
    else:
      conflict = config.checkConflict(zone, scene)
      if conflict is None:
        config.setZoneScene(zone, scene)
      else:
        if options is None:
          ret["conflict"] = conflict
        elif options == "unassign":
          for z in conflict:
            config.clearZoneScene(z)
          config.setZoneScene(zone, scene)
        elif options == "clone":
          for z in conflict:
            config.setZoneScene(z, scene)
          config.setZoneScene(zone, scene)            
    ret["active"] = config.getZoneScene(zone)

  ret = jsonify(ret)
  ret.status_code = 200

  router.updateRoutes()
  return ret

@app.route("/unassign", defaults={"zone" : None})
@app.route("/unassign/<zone>")
def api_unassign(zone):
  ret = {
  }
  
  if zone == None:
    ret["zones"] = config.getZoneList()
  else:
    config.clearZoneScene(zone)
  
  ret = jsonify(ret)
  ret.status_code = 200
  
  router.updateRoutes()
  return ret

@app.route("/attach", defaults={"remote" : None, "zone" : None, "options" : None})
@app.route("/attach/<remote>", defaults={"zone" : None, "options" : None})
@app.route("/attach/<remote>/<zone>", defaults={"options" : None})
@app.route("/attach/<remote>/<zone>/<options>")
def api_attach(remote, zone, options):
  ret = {}
  
  if remote is None:
    ret["remotes"] = config.getRemoteList()
  else:
    if zone == None:
      ret["zones"] = config.getZoneList()
    else:
      if options == "check":
        pass
      else:
         config.setRemoteZone(remote, zone)
      ret["users"] = config.getZoneRemoteList(zone)
    ret["active"] = config.getRemoteZone(remote)

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/detach/<remote>")
def api_detach(remote):
  ret = {
    "status" : 200,
    "active" : None
  }
  config.clearRemoteZone(remote)

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/command/<remote>", defaults={"command" : None, "arguments" : None, "category" : None})
@app.route("/command/<remote>/<category>/<command>", defaults={"arguments" : None})
@app.route("/command/<remote>/<category>/<command>/<arguments>")
def api_command(remote, category, command, arguments):
  """
  /command/<remote>
  Lists available commands for remote, if remote is not attached, this will
  return an error. 
  
  /command/<remote>/<category>/<command>
  Executes said command without any arguments
  
  /command/<remote>/<category>/<command>/<arguments>
  Executes said command supplied argument
  """
  ret = {}
  if category == None:
    ret["zone"] = config.getRemoteZone(remote)
    ret["commands"] = config.getRemoteCommands(remote)
  else:
    pass
  
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/test")
def api_test():
  ret = config.getCurrentState()
  
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

if __name__ == "__main__":
  app.debug = True
  app.run(host=cfg_ServerAddr)


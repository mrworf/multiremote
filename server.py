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
from flask import Flask, jsonify
import threading
import Queue
import time

from router import Router
from config import Config

try:
  from flask.ext.cors import CORS # The typical way to import flask-cors
except ImportError:
  # Path hack allows examples to be run without installation.
  import os
  parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  os.sys.path.insert(0, parentdir)
  from flask.ext.cors import CORS

cfg_ServerAddr = "0.0.0.0"

app = Flask(__name__)
cors = CORS(app) # Needed to make us CORS compatible


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
    scenes = config.getSceneList(None)
  elif not config.hasScene(scene):
    ret["error"] = "No such scene"
    scenes = None
  else:
    scenes = [scene]

  if scenes is not None:
    for scene in scenes:
      ret[scene] = {
        "scene"       : scene,
        "name"        : config.getScene(scene)["name"],
        "description" : config.getScene(scene)["description"],
        "zones"       : config.getSceneZoneUsage(scene),
        "remotes"     : config.getSceneRemoteUsage(scene)
      }
    if len(scenes) == 1:
      ret = ret[scenes[0]]
      
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/zone", defaults={"zone" : None})
@app.route("/zone/<zone>")
def api_zone(zone):
  ret = {}
  
  if zone is None:
    zones = config.getZoneList();
  elif not config.hasZone(zone):
    ret["error"] = "No such zone"
    zones = None
  else:
    zones = [zone]

  if zones is not None:
    for zone in zones:
      ret[zone] = {
        "zone"        : zone,
        "name"        : config.getZone(zone)["name"],
        "scene"       : config.getZoneScene(zone),
        "remotes"     : config.getZoneRemoteList(zone)
      }
      if config.hasSubZones(zone):
        ret[zone]["subzones"] = config.getSubZoneList(zone)
        ret[zone]["subzone"] = config.getSubZone(zone)
    if len(zones) == 1:
      ret = ret[zones[0]]
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/subzone/<zone>", defaults={"subzone" : None})
@app.route("/subzone/<zone>/<subzone>")
def api_subzone(zone, subzone):
  """ Changes the subzone for a specific zone
  """
  ret = {}
  if not config.hasSubZones(zone):
    ret["error"] = "Zone does not have subzones"
  elif subzone is None:
    ret["subzones"] = config.getSubZoneList(zone)
  elif not config.hasSubZone(zone, subzone):
    ret["error"] = "Zone does not have specified subzone"
  else:
    config.setSubZone(zone, subzone)
    router.updateRoutes()
    ret["subzone"] = config.getSubZone(zone)

  if config.hasSubZones(zone):
    ret["active-subzone"] = config.getSubZone(zone)
  ret["zone"] = zone
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
        router.updateRoutes()
      else:
        if options is None:
          ret["conflict"] = conflict
        elif options == "unassign":
          for z in conflict:
            config.clearZoneScene(z)
          config.setZoneScene(zone, scene)
          router.updateRoutes()
        elif options == "clone":
          for z in conflict:
            config.setZoneScene(z, scene)
          config.setZoneScene(zone, scene)            
          router.updateRoutes()
    ret["active"] = config.getZoneScene(zone)
    ret["zone"] = zone

  ret = jsonify(ret)
  ret.status_code = 200

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
  lst = config.getRemoteCommands(remote)
  
  if category == None:
    ret["zone"] = config.getRemoteZone(remote)
    ret["commands"] = lst
  elif category == "zone":
    if command not in lst["zone"]:
      ret["error"] = "%s is not a zone command" % command
    elif config.execZoneCommand(remote, command, arguments):
      ret["result"] = "ok"
    else:
      ret["error"] = "%s failed" % command
  elif category == "scene":
    if command not in lst["scene"]:
      ret["error"] = "%s is not a scene command" % command
    elif config.execSceneCommand(remote, command, arguments):
      ret["result"] = "ok"
    else:
      ret["error"] = "%s failed" % command
  else:
    ret["error"] = "%s is not a supported category" % category

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


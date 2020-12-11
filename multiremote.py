#!/usr/bin/env python3
#
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
REST based remote control
It's able to handle multiple remotes controlling the same list of equipment.

It does NOT provide a UI, instead it's up to the user of this API to create
a UI which makes the most sense.

The whole concept is based on remotes being attached/detached to zones and
scenes. Attach/Detach will NOT automatically power things on/off but attaching
to a new scene will automatically detach from the previous.
"""

import logging
import argparse
import sys

""" Parse command line """
parser = argparse.ArgumentParser(description="multiRemote - The future of IoT based remote control for your home", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--logfile', metavar="FILE", help="Log to file instead of stdout")
parser.add_argument('--debug', action='store_true', default=False, help='Enable loads more logging')
parser.add_argument('--port', default=5000, type=int, help="Port to listen on")
parser.add_argument('--listen', metavar="ADDRESS", default="0.0.0.0", help="Address to listen on")
parser.add_argument('--host', metavar='HTML', default=None, help='If set, use built-in HTTP server to host UX')
cmdline = parser.parse_args()

""" Setup logging first """
logging.getLogger('').handlers = []
if cmdline.debug or True: # Sorry, always full debug for now
  logging.basicConfig(filename=cmdline.logfile, level=logging.DEBUG, format='%(filename)s@%(lineno)d - %(levelname)s - %(message)s')
else:
  logging.basicConfig(filename=cmdline.logfile, level=logging.INFO, format='%(filename)s@%(lineno)d - %(levelname)s - %(message)s')

""" Continue with the rest """

from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop
from tornado.web import Application, FallbackHandler
from tornado.websocket import WebSocketHandler

from flask import Flask, jsonify, Response, abort, send_from_directory
import threading
import queue
import time

from modules.remotemgr import RemoteManager
from modules.router import Router
from modules.core import Core
from modules.ssdp import SSDPHandler
from modules.parser import SetupParser

try:
  from flask_cors import CORS # The typical way to import flask-cors
except ImportError:
  # Path hack allows examples to be run without installation.
  import os
  parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
  os.sys.path.insert(0, parentdir)
  from flask_cors import CORS

""" Disable some logging by-default """
logging.getLogger("Flask-Cors").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

""" Initialize the REST server """
app = Flask(__name__, static_url_path='/ux/')
cors = CORS(app) # Needed to make us CORS compatible

""" Create the various cogs of the machinery """
parser   = SetupParser()
setup = {}
if not parser.load("conf/setup.conf", setup):
  logging.error('Failed to load "setup.conf"')
  sys.exit(255)

if cmdline.host is not None:
  if (":%d" % cmdline.port) not in setup['OPTIONS']["ux-server"] or not setup['OPTIONS']["ux-server"].endswith('/ux') or not setup['OPTIONS']["ux-server"].endswith('/ux/'):
    logging.warning("You're using hosted UX, make sure \"%s\" points to the right server", setup['OPTIONS']["ux-server"])
    logging.warning('It should use port %d and end with /ux/' % cmdline.port)

remotes = RemoteManager()
core    = Core(setup, remotes)
router  = Router(core)
ssdp    = SSDPHandler(setup['OPTIONS']["ux-server"], cmdline.port)


""" Tracking information """
event_subscribers = []

def notifySubscribers(zone, message):
  for subscriber in event_subscribers:
    if zone is None or core.getRemoteZone(subscriber.remoteId) == zone:
      logging.info("Informing remote %s about \"%s\"", subscriber.remoteId, message)
      subscriber.write_message(message)
    else:
      logging.info("Skipped remote %s", subscriber.remoteId)

""" Start defining REST end-points """
@app.route("/")
def api_root():
  msg = {"status": "ok"}
  result = jsonify(msg)
  result.status_code = 200
  return result

@app.route("/scene", defaults={"scene" : None})
@app.route("/scene/<scene>")
def api_scene(scene):
  """
  Allows probing of the various scenes provided by multiREMOTE
  """
  ret = {}

  if scene is None:
    scenes = core.getSceneList(None)
  elif not core.hasScene(scene):
    ret["error"] = "No such scene"
    scenes = None
  else:
    scenes = [scene]

  if scenes is not None:
    for scene in scenes:
      ret[scene] = {
        "scene"       : scene,
        "name"        : core.getScene(scene)["name"],
        "description" : core.getScene(scene)["description"],
        "ux-hint"     : core.getScene(scene)["ux-hint"],
        "zones"       : core.getSceneZoneUsage(scene),
        "remotes"     : core.getSceneRemoteUsage(scene),
      }
    if len(scenes) == 1:
      ret = ret[scenes[0]]

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/zone", defaults={"zone" : None})
@app.route("/zone/<zone>")
def api_zone(zone):
  """
  Allows probing of the various zones provided by multiREMOTE
  """
  ret = {}

  if zone is None:
    zones = core.getZoneList();
  elif not core.hasZone(zone):
    ret["error"] = "No such zone"
    zones = None
  else:
    zones = [zone]

  if zones is not None:
    for zone in zones:
      ret[zone] = {
        "zone"        : zone,
        "name"        : core.getZone(zone)["name"],
        "scene"       : core.getZoneScene(zone),
        "remotes"     : core.getZoneRemoteList(zone),
        "ux-hint"     : core.getZone(zone)["ux-hint"],
        "compatible"  : core.getSceneListForZone(zone),
      }
      if core.hasSubZones(zone):
        ret[zone]["subzones"] = core.getSubZoneList(zone)
        ret[zone]["subzone"] = core.getSubZone(zone)
        ret[zone]["subzone-default"] = core.getSubZoneDefault(zone)
    if len(zones) == 1:
      ret = ret[zones[0]]
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/subzone/<zone>", defaults={"subzone" : None})
@app.route("/subzone/<zone>/<subzone>")
def api_subzone(zone, subzone):
  """
  Changes the subzone for a specific zone
  """
  ret = {}
  if not core.hasSubZones(zone):
    ret["error"] = "Zone does not have subzones"
  elif subzone is None:
    ret["subzones"] = core.getSubZoneList(zone)
  elif not core.hasSubZone(zone, subzone):
    ret["error"] = "Zone does not have specified subzone"
  else:
    core.setSubZone(zone, subzone)
    router.updateRoutes()
    ret["subzone"] = core.getSubZone(zone)

  if core.hasSubZones(zone):
    ret["active-subzone"] = core.getSubZone(zone)
  ret["zone"] = zone
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/assign", defaults={"zone" : None, "scene" : None, "options" : None})
@app.route("/assign/<zone>", defaults={"scene" : None, "options" : None, "remote" : None})
@app.route("/assign/<zone>/<remote>/<scene>", defaults={"options" : None})
@app.route("/assign/<zone>/<remote>/<scene>/<options>")
def api_assign(zone, remote, scene, options):
  """
  Options can be either clone or unassign:
    clone = Other zones will do the same thing
    unassign = Other zones will be unassigned
  These are used in situations where assigning a zone fails with a conflict.
  """
  ret = {}

  if zone == None:
    ret["zones"] = core.getZoneList()
  else:
    if scene == None:
      ret["scenes"] = core.getSceneListForZone(zone)
    else:
      conflict = core.checkConflict(zone, scene)
      if conflict is None:
        core.setZoneScene(zone, scene)
        router.updateRoutes()
      else:
        if options is None:
          ret["conflict"] = conflict
        elif options == "unassign":
          for z in conflict:
            core.clearZoneScene(z)
          core.setZoneScene(zone, scene)
          router.updateRoutes()
        elif options == "clone":
          for z in conflict:
            core.setZoneScene(z, scene)
          core.setZoneScene(zone, scene)
          router.updateRoutes()
    ret["active"] = core.getZoneScene(zone)
    ret["zone"] = zone

    notifySubscribers(zone, {"type":"scene", "source" : remote, "data": {"scene" : core.getZoneScene(zone) } })
    notifySubscribers(None, {"type":"zone", "source" : remote, "data": {"zone" : zone, "inuse" : True}})

  ret = jsonify(ret)
  ret.status_code = 200

  return ret

@app.route("/unassign", defaults={"zone" : None, "remote" : None})
@app.route("/unassign/<zone>/<remote>")
def api_unassign(zone, remote):
  """
  Removes any scenes assigned to a zone, also resets subzone back to
  the defined default.
  """
  ret = {}

  if zone == None:
    ret["zones"] = core.getZoneList()
  else:
    core.clearZoneScene(zone)
    core.clearSubZone(zone)
    notifySubscribers(zone, {"type":"scene", "source" : remote, "data": {"scene" : None } })
    notifySubscribers(None, {"type":"zone", "source" : remote, "data": {"zone" : zone, "inuse" : False}})

  ret = jsonify(ret)
  ret.status_code = 200

  router.updateRoutes()
  return ret

@app.route("/attach", defaults={"remote" : None, "zone" : None, "options" : None})
@app.route("/attach/<remote>", defaults={"zone" : None, "options" : None})
@app.route("/attach/<remote>/<zone>", defaults={"options" : None})
@app.route("/attach/<remote>/<zone>/<options>")
def api_attach(remote, zone, options):
  """
  Attaches a remote to a zone, so that it can control it
  """
  ret = {}

  if remote is None:
    r = []
    for z in core.getZoneList():
      i = core.getZoneRemoteList(z)
      r.extend(i)
    ret["active"] = r
  else:
    if remotes.has(remote):
      if not zone is None:
        core.setRemoteZone(remote, zone)
        ret["users"] = core.getZoneRemoteList(zone)
      ret["active"] = core.getRemoteZone(remote)
    else:
      ret["error"] = "No such remote " + remote

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/detach/<remote>")
def api_detach(remote):
  """
  Detaches a remote from the selected zone.
  In detached state, no scenes or commands are available
  """

  ret = {
    "active" : None
  }
  core.clearRemoteZone(remote)

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
  lst = core.getRemoteCommands(remote)
  result = None

  if category == None:
    ret["zone"] = core.getRemoteZone(remote)
    ret["commands"] = lst
  elif category == "zone":
    if command not in lst["zone"]:
      ret["error"] = "%s is not a zone command" % command
    else:
      result = core.execZoneCommand(remote, command, arguments)
      if result == False or result == None:
        ret["error"] = "%s failed" % command
      elif result == True:
        ret["result"] = "ok"
      else:
        # Advanced driver :)
        ret = result
        ret["result"] = "ok"
        logging.debug('Result contains: ' + repr(result))
  elif category == "scene":
    if command not in lst["scene"]:
      ret["error"] = "%s is not a scene command" % command
    elif core.execSceneCommand(remote, command, arguments):
      ret["result"] = "ok"
    else:
      ret["error"] = "%s failed" % command
  else:
    ret["error"] = "%s is not a supported category" % category

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/debug")
def api_debug():
  """
  Handy endpoint which prints out current routing/state of the system,
  useful for debugging purposes.
  """
  ret = {
    "routes" : core.getCurrentState(),
    "remotes" : remotes.list(),
    "subscribers" : [],
    "config" : {
      "scenes" : core.getSceneList(),
      "zones" : core.getZoneList(),
    }
  }
  for l in event_subscribers:
    ret["subscribers"].append(l.remoteId)

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/register/<pin>/<name>/<desc>/<zone>")
def api_register(pin, name, desc, zone):
  """
  Allows remotes to register themselves with the system. For registration,
  remote must provide:
  <pin>  = PIN which has been configured in multiremote, or an existing UUID
  <name> = Human-readable name that can be used by the system
  <desc> = Short human-readable description of device
  <zone> = Zone which should be considered the default or home zone for the remote

  Upon success, the server will return a UNIQUE id which has to be used in situations
  where you refer to the remote.

  Should it fail, the server returns error AND a description of why.

  Registering an existing remote will invalidate the old UID, making that invalid.
  Reregistering can be used to change the name, desc or zone if the UUID is provided
  as PIN.

  Registrations are saved as a JSON file locally on the server and should only
  be edited (or deleted) when the server isn't running.
  """
  ret = {}
  if not core.checkPin(pin):
    ret["error"] = "Invalid PIN"
  else:
    if core.getZone(zone) is None:
      ret["error"] = "No such zone " + zone
    elif len(pin) == 32:
      ret["uuid"] = remotes.register(name, desc, zone, pin)
    else:
      ret["uuid"] = remotes.register(name, desc, zone)

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/unregister/<pin>/<uuid>")
def api_unregister(pin, uuid):
  """
  Removes a registered remote from the system, also detaches
  from any zone it might be a member of.
  """
  ret = {}
  if not core.checkPin(pin, False):
    ret["error"] = "Invalid PIN"
  elif not remotes.has(uuid):
    ret["error"] = "No such remote " + uuid
  else:
    core.clearRemoteZone(uuid)
    remotes.unregister(uuid)
    ret["status"] = "Remote has been unregistered"

  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/remotes", defaults={"uuid": None})
@app.route("/remotes/<uuid>")
def api_remotes(uuid):
  """
  Lists all registered remotes and which zones they're currently
  attached to.
  """
  ret = {}
  if uuid is None:
    ret = {"remotes" : remotes.list()}
  elif uuid == "*":
    for r in remotes.list():
      ret[r] = remotes.describe(r)
  else:
    ret = remotes.describe(uuid)
    if ret is None:
      ret = {"error": "No such remote"}
    else:
      ret["uuid"] = uuid
  ret = jsonify(ret)
  ret.status_code = 200
  return ret

@app.route("/description.xml")
def api_ssdp():
  return Response(ssdp.generateXML(), mimetype='text/xml')

@app.route('/ux', defaults={'path' : None})
@app.route('/ux/', defaults={'path' : None})
@app.route("/ux/<path:path>")
def serve_html(path):
  if cmdline.host is None:
    logging.warning('Client tried to access UX hosting when not enabled')
    abort(404)
  else:
    if path is None:
      path = 'index.html'
    return send_from_directory(cmdline.host, path)

class WebSocket(WebSocketHandler):
  def open(self, remoteId):
    logging.info("Remote %s has connected", remoteId);
    if not remotes.has(remoteId):
      logging.warning("No such remote registered, close connection");
      self.finish();
    else:
      event_subscribers.append(self)
      self.remoteId = remoteId
      self.subscriptions = []

  # TODO: We don't care (for now) about origin
  def check_origin(self, origin):
    return True

  def on_message(self, message):
    if message.startswith('LOG '):
      logging.debug('%s DEBUG: %s', self.remoteId, message[4:])
    elif message.startswith('SUBSCRIBE '):
      subscribe = message[10:].lower()
      if subscribe in self.subscriptions:
        logging.debug('%s already subcribed to %s', self.remoteId, subscribe)
      else:
        logging.debug('%s has subscribed to %s', self.remoteId, subscribe)
        self.subscriptions.append(subscribe)
    else:
      logging.debug("%s sent unknown message: %s", self.remoteId, message)

  def on_close(self):
    logging.info("Remote %s has disconnected", self.remoteId)
    event_subscribers.remove(self)

""" Finally, launch! """
if __name__ == "__main__":
  app.debug = False
  logging.info("multiRemote starting")
  container = WSGIContainer(app)
  server = Application([
    (r'/events/(.*)', WebSocket),
    (r'.*', FallbackHandler, dict(fallback=container))
    ])
  server.listen(cmdline.port)
  ssdp.start()
  logging.info("multiRemote running")
  IOLoop.instance().start()

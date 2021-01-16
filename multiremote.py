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
import os

""" Parse command line """
parser = argparse.ArgumentParser(description="multiRemote - The future of IoT based remote control for your home", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--logfile', metavar="FILE", help="Log to file instead of stdout")
parser.add_argument('--debug', action='store_true', default=False, help='Enable loads more logging')
parser.add_argument('--port', default=5000, type=int, help="Port to listen on")
parser.add_argument('--listen', metavar="ADDRESS", default="0.0.0.0", help="Address to listen on")
parser.add_argument('--host', metavar='HTML', default=None, help='If set, use built-in HTTP server to host UX')
parser.add_argument('--ssdp', action='store', default='yes', type=str, choices=['yes', 'no'], help='Controls use of SSDP')
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
from modules.api import multiremoteAPI
from modules.eventmgr import EventHandler

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
app = Flask(__name__, static_url_path='')
cors = CORS(app) # Needed to make us CORS compatible

""" Create the various cogs of the machinery """

class WorkRunner(threading.Thread):
  class Work:
    def __init__(self, task, *args):
      self.task = task
      self.args = args
      self.event = threading.Event()
      self.result = None
    
    def wait(self):
      self.event.wait()

    def execute(self):
      self.result = self.task(*self.args)
      self.event.set()

  def __init__(self):
    threading.Thread.__init__(self)
    self.queue = queue.Queue()
    self.start()
  
  def asynctask(self, task, *args):
    #logging.debug('asynctask called')
    w = WorkRunner.Work(task, *args)
    self.queue.put_nowait(w)
    return w

  def synctask(self, task, *args):
    #logging.debug('synctask called')
    w = self.asynctask(task, *args)
    w.wait()
    return w.result

  def run(self):
    while True:
      w = self.queue.get()
      logging.info('Processing work')
      w.execute()

workRunner = WorkRunner()

api = multiremoteAPI()
api.init(cmdline)

""" Start defining REST end-points """
@app.route("/")
def api_root():
  data = workRunner.synctask(api.getStatus)
  result = jsonify(data)
  result.status_code = 200
  return result

@app.route("/scene", defaults={"scene" : None})
@app.route("/scene/<scene>")
def api_scene(scene):
  """
  Allows probing of the various scenes provided by multiREMOTE
  """
  data = workRunner.synctask(api.getScene, scene)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/zone", defaults={"zone" : None})
@app.route("/zone/<zone>")
def api_zone(zone):
  """
  Allows probing of the various zones provided by multiREMOTE
  """
  data = workRunner.synctask(api.getZone, zone)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/subzone/<zone>", defaults={"subzone" : None})
@app.route("/subzone/<zone>/<subzone>")
def api_subzone(zone, subzone):
  """
  Changes the subzone for a specific zone
  """
  data = workRunner.synctask(api.getSubZone, zone, subzone)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/assign", defaults={"zone" : None, "scene" : None, "options" : None})
@app.route("/assign/<zone>", defaults={"scene" : None, "options" : None, "remote" : None})
@app.route("/assign/<zone>/<remote>/<scene>", defaults={"options" : None})
@app.route("/assign/<zone>/<remote>/<scene>/<options>")
def api_assign(zone, remote, scene, options):
  data = workRunner.synctask(api.assignZone, zone, remote, scene, options)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/unassign", defaults={"zone" : None, "remote" : None})
@app.route("/unassign/<zone>/<remote>")
def api_unassign(zone, remote):
  data = workRunner.synctask(api.unassignZone, zone, remote)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/attach", defaults={"remote" : None, "zone" : None, "options" : None})
@app.route("/attach/<remote>", defaults={"zone" : None, "options" : None})
@app.route("/attach/<remote>/<zone>", defaults={"options" : None})
@app.route("/attach/<remote>/<zone>/<options>")
def api_attach(remote, zone, options):
  data = workRunner.synctask(api.attachRemote, remote, zone, options)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/detach/<remote>")
def api_detach(remote):
  data = workRunner.synctask(api.detachRemote, remote)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/command/<remote>", defaults={"command" : None, "arguments" : None, "category" : None})
@app.route("/command/<remote>/<category>/<command>", defaults={"arguments" : None})
@app.route("/command/<remote>/<category>/<command>/<arguments>")
def api_command(remote, category, command, arguments):
  data = workRunner.synctask(api.executeCommand, remote, category, command, arguments)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/debug")
def api_debug():
  data = workRunner.synctask(api.getDebugInformation)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/register/<pin>/<name>/<desc>/<zone>")
def api_register(pin, name, desc, zone):
  data = workRunner.synctask(api.registerRemote, pin, name, desc, zone)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/unregister/<pin>/<uuid>")
def api_unregister(pin, uuid):
  data = workRunner.synctask(api.unregisterRemote, pin, uuid)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/remotes", defaults={"uuid": None})
@app.route("/remotes/<uuid>")
def api_remotes(uuid):
  data = workRunner.synctask(api.getRemotes, uuid)
  ret = jsonify(data)
  ret.status_code = 200
  return ret

@app.route("/description.xml")
def api_ssdp():
  data = workRunner.synctask(api.getSSDPDescriptor)
  return Response(data, mimetype='text/xml')

@app.route('/ux', defaults={'path' : None})
@app.route('/ux/', defaults={'path' : None})
@app.route("/ux/<path:path>")
def serve_html(path):
  print((repr(path)))
  if cmdline.host is None:
    logging.warning('Client tried to access UX hosting when not enabled')
    abort(404)
  else:
    if path is None:
      path = 'index.html'
    actual = os.path.abspath(os.path.join(cmdline.host, path))
    if not os.path.exists(actual):
      logging.error('Unable to server %s, does not exist', actual)
    #logging.debug('Sending file %s from %s', path, os.path.abspath(cmdline.host))
    return send_from_directory(os.path.abspath(cmdline.host), path)

# Cheap workaround to allow us to schedule work on the main thread
main_thread = IOLoop.instance()

class WebSocket(WebSocketHandler):
  def open(self, remoteId):
    if not api.hasRemote(remoteId):
      logging.warning("No such remote registered, close connection")
      self.finish()
    else:
      api.events.addRemote(EventHandler.Remote(self, remoteId, lambda msg: main_thread.add_callback(callback=lambda: self.write_message(msg))))

  # TODO: We don't care (for now) about origin
  def check_origin(self, origin):
    return True

  def on_message(self, message):
    api.events.handleMessage(self, message)

  def on_close(self):
    api.events.removeRemote(socket=self)

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
  if cmdline.ssdp == 'yes':
    api.ssdp.start()
  else:
    logging.warning('SSDP has been disabled from command line')
  logging.info("multiRemote running")
  IOLoop.instance().start()

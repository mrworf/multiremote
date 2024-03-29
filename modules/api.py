import threading
import queue
import time
import logging
import json
from inspect import signature

import flask

from modules.remotemgr import RemoteManager
from modules.router import Router
from modules.core import Core
from modules.ssdp import SSDPHandler
from modules.parser import SetupParser
from modules.eventmgr import EventHandler
from modules.webhook import WebhookManager

def alwaysObject(x):
  return "***Unknown***"

class multiremoteAPI:
    def __init__(self):
        pass

    def init(self, cmdline):
        parser = SetupParser()
        self.setup = {}
        if not parser.load("conf/setup.conf", self.setup):
            logging.error('Failed to load "setup.conf"')
            return False

        if cmdline.host is not None:
            if (":%d" % cmdline.port) not in self.setup['OPTIONS']["ux-server"] or not self.setup['OPTIONS']["ux-server"].endswith('/ux') or not self.setup['OPTIONS']["ux-server"].endswith('/ux/'):
                logging.warning("You're using hosted UX, make sure \"%s\" points to the right server", self.setup['OPTIONS']["ux-server"])
                logging.warning('It should use port %d and end with /ux/' % cmdline.port)

        self.remotes  = RemoteManager()
        self.core     = Core(self.setup, self.remotes)
        self.router   = Router(self.core)
        self.ssdp     = SSDPHandler(self.setup['OPTIONS']["ux-server"], cmdline.port)
        self.events   = EventHandler(self.core)
        self.webhooks = WebhookManager()

        # Load all webhooks
        self.webhooks.load('conf/webhooks.conf')

        # Register the webhook attributes we'll use
        for zone in self.core.getZoneList():
          self.webhooks.register_attribute(zone)
          self.webhooks.register_attribute('%s.scene' % zone)
          self.webhooks.register_attribute('%s.subzone' % zone)

        self.events.registerCommand('execute', self.handleCommand)

        # Also assign the eventmanager to all drivers
        for _, v in self.setup['DRIVER_TABLE'].items():
          v.setEventManager(self.events)

    def getStatus(self):
        msg = {"status": "ok"}
        return msg

    def getScene(self, scene):
        ret = {}

        if scene is None:
          scenes = self.core.getSceneList(None)
        elif not self.core.hasScene(scene):
          ret["error"] = "No such scene"
          scenes = None
        else:
          scenes = [scene]

        if scenes is not None:
          for scene in scenes:
            ret[scene] = {
              "scene"       : scene,
              "name"        : self.core.getScene(scene)["name"],
              "description" : self.core.getScene(scene)["description"],
              "ux-hint"     : self.core.getScene(scene)["ux-hint"],
              "zones"       : self.core.getSceneZoneUsage(scene),
              "remotes"     : self.core.getSceneRemoteUsage(scene),
            }
          if len(scenes) == 1:
            ret = ret[scenes[0]]

        return ret

    def getZone(self, zone):
      """
      Allows probing of the various zones provided by multiREMOTE
      """
      ret = {}

      if zone is None:
        zones = self.core.getZoneList()
      elif not self.core.hasZone(zone):
        ret["error"] = "No such zone"
        zones = None
      else:
        zones = [zone]

      if zones is not None:
        for zone in zones:
          ret[zone] = {
            "zone"        : zone,
            "name"        : self.core.getZone(zone)["name"],
            "scene"       : self.core.getZoneScene(zone),
            "remotes"     : self.core.getZoneRemoteList(zone),
            "ux-hint"     : self.core.getZone(zone)["ux-hint"],
            "compatible"  : self.core.getSceneListForZone(zone),
          }
          if self.core.hasSubZones(zone):
            ret[zone]["subzones"] = self.core.getSubZoneList(zone)
            ret[zone]["subzone"] = self.core.getSubZone(zone)
            ret[zone]["subzone-default"] = self.core.getSubZoneDefault(zone)
        if len(zones) == 1:
          ret = ret[zones[0]]
      return ret

    def getSubZone(self, zone, subzone):
      """
      Changes the subzone for a specific zone
      """
      ret = {}
      if not self.core.hasSubZones(zone):
        ret["error"] = "Zone does not have subzones"
      elif subzone is None:
        ret["subzones"] = self.core.getSubZoneList(zone)
      elif not self.core.hasSubZone(zone, subzone):
        ret["error"] = "Zone does not have specified subzone"
      else:
        self.core.setSubZone(zone, subzone)
        self.router.updateRoutes()
        ret["subzone"] = self.core.getSubZone(zone)

        self.webhooks.update_attribute('%s.subzone' % zone, self.core.getSubZone(zone))

      if self.core.hasSubZones(zone):
        ret["active-subzone"] = self.core.getSubZone(zone)
      ret["zone"] = zone
      return ret

    def assignZone(self, zone, remote, scene, options):
      """
      Options can be either clone or unassign:
        clone = Other zones will do the same thing
        unassign = Other zones will be unassigned
      These are used in situations where assigning a zone fails with a conflict.
      """
      ret = {}

      if zone == None:
        ret["zones"] = self.core.getZoneList()
      else:
        if scene == None:
          ret["scenes"] = self.core.getSceneListForZone(zone)
        else:
          conflict = self.core.checkConflict(zone, scene)
          if conflict is None:
            self.core.setZoneScene(zone, scene)
            self.router.updateRoutes()
          else:
            if options is None:
              ret["conflict"] = conflict
            elif options == "unassign":
              for z in conflict:
                self.core.clearZoneScene(z)
              self.core.setZoneScene(zone, scene)
              self.router.updateRoutes()
            elif options == "clone":
              for z in conflict:
                self.core.setZoneScene(z, scene)
              self.core.setZoneScene(zone, scene)
              self.router.updateRoutes()
        ret["active"] = self.core.getZoneScene(zone)
        ret["zone"] = zone

        self.events.notify(zone, {"type":"scene", "source" : remote, "data": {"scene" : self.core.getZoneScene(zone) } })
        self.events.notify(None, {"type":"zone", "source" : remote, "data": {"zone" : zone, "inuse" : True}})

        self.webhooks.update_attribute(zone, WebhookManager.ACTIVE)
        self.webhooks.update_attribute('%s.scene' % zone, self.core.getZoneScene(zone))
        self.webhooks.update_attribute('%s.subzone' % zone, self.core.getSubZone(zone))

      return ret

    def unassignZone(self, zone, remote):
      """
      Removes any scenes assigned to a zone, also resets subzone back to
      the defined default.
      """
      ret = {}

      if zone == None:
        ret["zones"] = self.core.getZoneList()
      else:
        self.core.clearZoneScene(zone)
        self.core.clearSubZone(zone)
        self.events.notify(zone, {"type":"scene", "source" : remote, "data": {"scene" : None } })
        self.events.notify(None, {"type":"zone", "source" : remote, "data": {"zone" : zone, "inuse" : False}})

        self.webhooks.update_attribute(zone, WebhookManager.INACTIVE)
        self.webhooks.update_attribute('%s.scene' % zone, WebhookManager.EMPTY)
        self.webhooks.update_attribute('%s.subzone' % zone, WebhookManager.EMPTY)


      self.router.updateRoutes()
      return ret

    def attachRemote(self, remote, zone, options):
      """
      Attaches a remote to a zone, so that it can control it
      """
      ret = {}

      if remote is None:
        # Return remote(s) currently viewing this zone
        r = []
        for z in self.core.getZoneList():
          i = self.core.getZoneRemoteList(z)
          r.extend(i)
        ret["active"] = r
      else:
        if self.remotes.has(remote):
          if not zone is None:
            # Assign the remote to this zone
            self.core.setRemoteZone(remote, zone)
            state = self.core.updateZoneState(zone, remote)
            state['zone'] = zone
            self.events.notify(None, {"type":"state", "source" : None, "data": state})
            ret["users"] = self.core.getZoneRemoteList(zone)
          # Show the zone active for this remote
          ret["active"] = self.core.getRemoteZone(remote)
        else:
          ret["error"] = "No such remote " + remote

      return ret

    def detachRemote(self, remote):
      """
      Detaches a remote from the selected zone.
      In detached state, no scenes or commands are available
      """

      ret = {
        "active" : None
      }
      self.core.clearRemoteZone(remote)
      return ret

    def executeCommand(self, remote, category, command, arguments):
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
      lst = self.core.getRemoteCommands(remote)
      result = None

      if category == None:
        ret["zone"] = self.core.getRemoteZone(remote)
        ret["commands"] = lst
      elif category == "zone":
        if command not in lst["zone"]:
          ret["error"] = "%s is not a zone command" % command
        else:
          result = self.core.execZoneCommand(remote, command, arguments)
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
        elif self.core.execSceneCommand(remote, command, arguments):
          ret["result"] = "ok"
        else:
          ret["error"] = "%s failed" % command
      else:
        ret["error"] = "%s is not a supported category" % category
      return ret

    def getDebugInformation(self):
      """
      Handy endpoint which prints out current routing/state of the system,
      useful for debugging purposes.
      """
      ret = {
        "routes" : self.core.getCurrentState(),
        "remotes" : self.remotes.list(),
        "subscribers" : [],
        "config" : {
          "scenes" : self.core.getSceneList(),
          "zones" : self.core.getZoneList(),
        }
      }
      for l in self.events.remotes:
        ret["subscribers"].append(l.uuid)
      return ret

    def registerRemote(self, pin, name, desc, zone):
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
      if not self.core.checkPin(pin):
        ret["error"] = "Invalid PIN"
      else:
        if self.core.getZone(zone) is None:
          ret["error"] = "No such zone " + zone
        elif len(pin) == 32:
          ret["uuid"] = self.remotes.register(name, desc, zone, pin)
        else:
          ret["uuid"] = self.remotes.register(name, desc, zone)
      return ret

    def unregisterRemote(self, pin, uuid):
      """
      Removes a registered remote from the system, also detaches
      from any zone it might be a member of.
      """
      ret = {}
      if not self.core.checkPin(pin, False):
        ret["error"] = "Invalid PIN"
      elif not self.remotes.has(uuid):
        ret["error"] = "No such remote " + uuid
      else:
        self.core.clearRemoteZone(uuid)
        self.remotes.unregister(uuid)
        ret["status"] = "Remote has been unregistered"
      return ret

    def getRemotes(self, uuid):
      """
      Lists all registered remotes and which zones they're currently
      attached to.
      """
      ret = {}
      if uuid is None:
        ret = {"remotes" : self.remotes.list()}
      elif uuid == "*":
        for r in self.remotes.list():
          ret[r] = self.remotes.describe(r)
      else:
        ret = self.remotes.describe(uuid)
        if ret is None:
          ret = {"error": "No such remote"}
        else:
          ret["uuid"] = uuid
      return ret

    def hasRemote(self, uuid):
      return self.remotes.has(uuid)

    def getSSDPDescriptor(self):
      return self.ssdp.generateXML()

    def handleCommand(self, remote, data):
      logging.debug('Contents: ' + repr(data))
      obj = json.loads(data)
      logging.debug('Data in message says: %s', repr(obj))
      measure = time.time()

      mapping = {
        'attach' : self.attachRemote,
        'subzone' : self.getSubZone,
        'zone' : self.getZone,
        'assign' : self.assignZone,
        'command' : self.executeCommand,
        'unassign' : self.unassignZone,
        'scene' : self.getScene,
        'detach' : self.detachRemote,
        'debug' : self.getDebugInformation,
        'register' : self.registerRemote,
        'unregister' : self.unregisterRemote,
        'remotes' : self.remotes,

      }
      parts = obj['addr'][1:].split('/')

      if parts[0] in mapping:
        # Figure out how many parameters it expects and substitute with None
        sig = signature(mapping[parts[0]])
        delta = len(sig.parameters) - len(parts) + 1
        if delta < 0:
          logging.error('We were provided MORE parameters than expected, abort!')
          return
        #logging.debug('Delta is %d', delta)
        for x in range(0, delta):
          parts.append(None)
        if len(parts) > 1:
          result = mapping[parts[0]](*parts[1:])
        else:
          result = mapping[parts[0]]()

        retstr = json.dumps(
          {
            'type' : 'result', 
            'source' : remote.uuid,
            'data': {
              'id' : obj['id'], 
              'result' : result
            }
          }
        )
        logging.debug('Result: ' + retstr)
        remote.post(retstr)
      else:
        logging.warning('Unregistered mapping: ' + parts[0])

      measure = (time.time() - measure)*1000
      logging.debug('Handle command took %dms', measure)
      return

import threading
import queue
import time
import logging

import flask

from modules.remotemgr import RemoteManager
from modules.router import Router
from modules.core import Core
from modules.ssdp import SSDPHandler
from modules.parser import SetupParser

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

        self.remotes = RemoteManager()
        self.core    = Core(self.setup, self.remotes)
        self.router  = Router(self.core)
        self.ssdp    = SSDPHandler(self.setup['OPTIONS']["ux-server"], cmdline.port)
        self.event_subscribers = []
    
    def notifySubscribers(self, zone, message):
        for subscriber in self.event_subscribers:
            if zone is None or self.core.getRemoteZone(subscriber.remoteId) == zone:
                logging.info("Informing remote %s about \"%s\"", subscriber.remoteId, message)
                subscriber.write_message(message)
            else:
                logging.info("Skipped remote %s", subscriber.remoteId)

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

      if self.core.hasSubZones(zone):
        ret["active-subzone"] = self.core.getSubZone(zone)
      ret["zone"] = zone
      return ret

"""
ROKU driver
Talks to a specified ROKU device using REST api.
Based on http://sdkdocs.roku.com/display/sdkdoc/External+Control+Guide

Does not make use of the SSDP (Simple Service Discovery Protocol) since
a home may contain more than one device, making it important that the
driver can be directed to a specific ROKU.

Does not support power functions, but will automatically navigate home
when getting power off (to avoid stream stuff when noone is watching)

This is the first driver to support the driver-extras directive. This
information is provided by the applyExtras() API call and is called
whenever a device selected. Meaning you may get setPower() once but
applyExtras() multiple times if you have plenty of roku scenes.
"""

from driver_null import DriverNull
import requests
from xml.etree import ElementTree
from commandtype import CommandType

class DriverRoku(DriverNull):
  def __init__(self, server):
    DriverNull.__init__(self)

    self.server = "http://" + server + ":8090/"
    self.home = None

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("select", CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)
    self.addCommand("home",   CommandType.NAVIGATE_HOME,    self.navHome)

    self.addCommand("info",    CommandType.PLAYBACK_OSD,          self.playbackInfo)
    self.addCommand("play",    CommandType.PLAYBACK_PLAY,         self.playbackPlay)
    self.addCommand("rewind",  CommandType.PLAYBACK_REWIND,       self.playbackRW)
    self.addCommand("forward", CommandType.PLAYBACK_FASTFORWARD,  self.playbackFF)

  def eventOff(self):
    if self.home == None:
      self.getApps()
    if self.home == None:
      print "WARN: Roku did not report a home screen id"
      return
    self.startApp(self.home)

  def handleExtras(self, extras):
    """
    Two ways of doing this, either we are told the ID, or we need to
    do a text search. Obviously text search using app=XXX is convenient
    but also runs the risk (if poorly specified) to run the wrong app.

    Use appid=XXX if you know the app id.
    """
    self.apps = self.getApps()

    if "app" in extras:
      k = extras["app"].lower()
      for key in self.apps:
        if k.find(key.lower()) > -1:
          self.startApp(self.apps[key])
          break
    elif "appid" in extras:
      i = int(extras[appid])
      for key in self.apps:
        if self.apps[key] == i:
          self.startApp(i)
          break

  def getApps(self):
    result = {}
    r = request.get(self.server + "query/apps")
    tree = ElementTree.fromstring(r.content)
    if tree.tag != "apps":
      print "ERR: Roku didn't respond with apps list"
      return {}
    for branch in tree:
      if branch.tag == "app" and branch.attrib["type"] == "menu":
        if "home".find(branch.text.lower()) > -1:
          self.home = int(branch.attrib["id"])

      if branch.tag != "app" or branch.attrib["type"] != "appl":
        continue
      result[branch.text] = int(branch.attrib["id"])
    return result

  def startApp(self, appid):
    request.get(self.server + "launch/" + appid)

  def navUp(self, zone):
    request.get(self.server + "keypress/Up")

  def navDown(self, zone):
    request.get(self.server + "keypress/Down")

  def navLeft(self, zone):
    request.get(self.server + "keypress/Left")

  def navRight(self, zone):
    request.get(self.server + "keypress/Right")

  def navEnter(self, zone):
    request.get(self.server + "keypress/Select")

  def navBack(self, zone):
    request.get(self.server + "keypress/Back")

  def navHome(self, zone):
    request.get(self.server + "keypress/Home")

  def playbackInfo(self, zone):
    request.get(self.server + "keypress/Info")

  def playbackPlay(self, zone):
    request.get(self.server + "keypress/Play")

  def playbackFF(self, zone):
    request.get(self.server + "keypress/Fwd")

  def playbackRW(self, zone):
    request.get(self.server + "keypress/Rev")

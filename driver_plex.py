"""
Plex Home Theater driver
Talks to a specified Plex Home Theater client over network and uses 
Wake-On-Lan to wake it from sleep.

Note! Currently no way of placing PHT back to sleep after usage.
"""

from driver_null import DriverNull
import requests
import base64
import json
from commandtype import CommandType
import subprocess

class DriverPlex(DriverNull):
  def __init__(self, server, macaddress = None, iface = "eth0"):
    DriverNull.__init__(self)

    self.urlPlayback = "/player/playback/"
    self.urlNavigate = "/player/navigation/"

    self.server = "http://" + server + ":3005"
    self.mac = macaddress
    self.iface = iface

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("enter",  CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)
    self.addCommand("home",   CommandType.NAVIGATE_HOME,    self.navHome)

    self.addCommand("play",   CommandType.PLAYBACK_PLAY,    self.playbackPlay)
    self.addCommand("pause",  CommandType.PLAYBACK_PAUSE,   self.playbackPause)
    self.addCommand("stop",   CommandType.PLAYBACK_STOP,    self.playbackStop)

    self.addCommand("+30s",   CommandType.PLAYBACK_SKIP_FORWARD,   self.playbackSkip, None, None, "stepForward")
    self.addCommand("-15s",   CommandType.PLAYBACK_SKIP_BACKWARD,  self.playbackSkip, None, None, "stepBack")

  def eventOn(self):
    if self.mac == None:
      print "WARN: DriverPlex is not configured to support power management"
      return
    subprocess.call(['extras/etherwake', '-i', self.iface, self.mac])

  def eventOff(self):
    # Stop and navigate home (avoid leaving it playing)
    self.playbackStop(None)
    self.navHome(None)
    # Sorry, no power control yet
    print "DBG: Power off isn't implemented yet"

  def navUp(self, zone):
    self.execServer(self.urlNavigate + "moveUp")

  def navDown(self, zone):
    print "INFO: Hello"
    self.execServer(self.urlNavigate + "moveDown")

  def navLeft(self, zone):
    self.execServer(self.urlNavigate + "moveLeft")

  def navRight(self, zone):
    self.execServer(self.urlNavigate + "moveRight")

  def navEnter(self, zone):
    self.execServer(self.urlNavigate + "select")

  def navBack(self, zone):
    self.execServer(self.urlNavigate + "back")

  def navHome(self, zone):
    self.execServer(self.urlNavigate + "home")

  def playbackPlay(self, zone):
    self.execServer(self.urlPlayback + "play")

  def playbackPause(self, zone):
    self.execServer(self.urlPlayback + "pause")

  def playbackStop(self, zone):
    self.execServer(self.urlPlayback + "stop")

  def playbackSkip(self, zone, size):
    self.execServer(self.urlPlayback + size)

  def execServer(self, url):
    print "INFO: DriverPlex -> " + url
    r = requests.get(self.server + url)
    if r.status_code != 200:
      print "ERROR: Driver was unable to execute %s due to %s" % (self.server + url, repr(r))
      return False

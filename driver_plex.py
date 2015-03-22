"""
Plex Home Theater driver


"""

from driver_null import DriverNull
import requests
import base64
import json
from commandtype import CommandType
import subprocess

class DriverPlex(DriverNull):
  def __init__(self, server, macaddress = None):
    DriverNull.__init__(self)

    self.urlPlayback = "/player/playback/"
    self.urlNavigate = "/player/navigation/"

    self.server = server
    self.mac = macaddress

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("enter",  CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)

    self.addCommand("play",   CommandType.PLAYBACK_PLAY,    self.playbackPlay)
    self.addCommand("pause",  CommandType.PLAYBACK_PAUSE,   self.playbackPause)
    self.addCommand("stop",   CommandType.PLAYBACK_STOP,    self.playbackStop)

  def setPower(self, enable):
    if self.mac == None:
      print "WARN: DriverPlex is not configured to support power management"
      return

    if self.power == enable:
      return True

    if enable:
      subprocess.call(['extras/etherwake', self.mac])
    else:
      print "DBG: Power off isn't implemented yet"

    self.power = enable
    return True

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

  def playbackPlay(self, zone):
    self.execServer(self.urlPlayback + "play")

  def playbackPause(self, zone):
    self.execServer(self.urlPlayback + "pause")

  def playbackStop(self, zone):
    self.execServer(self.urlPlayback + "stop")

  def execServer(self, url):
    print "INFO: DriverPlex -> " + url
    r = requests.get(self.server + url)
    if r.status_code != 200:
      print "ERROR: Driver was unable to execute %s" % url
      return False

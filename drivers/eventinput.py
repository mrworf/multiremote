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
Plex Home Theater driver
Talks to a specified Plex Home Theater client over network and uses
Wake-On-Lan to wake it from sleep.
"""

from null import driverNull
import requests
import base64
import json
from commandtype import CommandType
import subprocess
import logging
import socket

class driverEventinput(driverNull):
  def __init__(self, server, macaddress = None, iface = "eth0"):
    driverNull.__init__(self)

    self.server = server
    self.port =5050
    self.mac = macaddress
    self.iface = iface

    self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("enter",  CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)

    self.addCommand("play",   CommandType.PLAYBACK_PLAYPAUSE,    self.playbackPlay)
    #self.addCommand("pause",   CommandType.PLAYBACK_PAUSE,    self.playbackPause)
    self.addCommand("stop",   CommandType.PLAYBACK_STOP,    self.playbackStop)

    self.addCommand("+30s",   CommandType.PLAYBACK_SKIP_FORWARD,   self.playbackForward)
    self.addCommand("-10s",   CommandType.PLAYBACK_SKIP_BACKWARD,  self.playbackBackward)

    self.addCommand("next chapter",   CommandType.PLAYBACK_CNEXT,   self.playbackNext)
    self.addCommand("previous chapter",   CommandType.PLAYBACK_CPREVIOUS,  self.playbackPrev)

    self.addCommand("subtitle",   CommandType.PLAYBACK_SUBTITLE,  self.playbackSubtitle)
    self.addCommand("audio",      CommandType.PLAYBACK_AUDIO,     self.playbackAudio)

  def eventOn(self):
    if self.mac == None:
      logging.warning("DriverEventService is not configured to support power management")
      return
    subprocess.call(['extras/etherwake', '-i', self.iface, self.mac])

  def eventOff(self):
    # Stop and navigate home (avoid leaving it playing)
    self.execServer([0,35])

  def navUp(self, zone):
    self.execServer([0,103])

  def navDown(self, zone):
    self.execServer([0,108])

  def navLeft(self, zone):
    self.execServer([0,105])

  def navRight(self, zone):
    self.execServer([0,106])

  def navEnter(self, zone):
    self.execServer([0,28])

  def navBack(self, zone):
    self.execServer([0,1])

  def playbackPlay(self, zone):
    self.execServer([0,25])

  def playbackStop(self, zone):
    self.execServer([0,45])

  def playbackNext(self, zone):
    self.execServer([0,163])

  def playbackPrev(self, zone):
    self.execServer([0,165])

  def playbackForward(self, zone):
    self.execServer([0,106])

  def playbackBackward(self, zone):
    self.execServer([0,105])

  def playbackSubtitle(self, zone):
    self.execServer([0,38])

  def playbackAudio(self, zone):
    self.execServer([0,30])

  def execServer(self, actions, text=None):
    try:
      i = 0
      while i < len(actions):
        data = bytearray.fromhex('deadbeef0000')
        data[4] = actions[i]
        data[5] = actions[i+1]
        i += 2
        self.socket.sendto(data, (self.server, self.port))

    except:
      logging.exception("execServer: " + url)
      return False

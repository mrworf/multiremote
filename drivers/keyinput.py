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
from modules.commandtype import CommandType
import subprocess
import logging

class driverKeyinput(driverNull):
  def __init__(self, server, macaddress = None, iface = "eth0"):
    driverNull.__init__(self)

    self.server = "http://" + server + ":5000"
    self.mac = macaddress
    self.iface = iface

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("enter",  CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)

    self.addCommand("play",   CommandType.PLAYBACK_PLAY,    self.playbackPlay)
    self.addCommand("pause",   CommandType.PLAYBACK_PAUSE,    self.playbackPause)
    self.addCommand("stop",   CommandType.PLAYBACK_STOP,    self.playbackStop)

    self.addCommand("+30s",   CommandType.PLAYBACK_SKIP_FORWARD,   self.playbackForward)
    self.addCommand("-10s",   CommandType.PLAYBACK_SKIP_BACKWARD,  self.playbackBackward)

    self.addCommand("next chapter",   CommandType.PLAYBACK_CNEXT,   self.playbackNext)
    self.addCommand("previous chapter",   CommandType.PLAYBACK_CPREVIOUS,  self.playbackPrev)

    self.addCommand("subtitle",   CommandType.PLAYBACK_SUBTITLE,  self.playbackSubtitle)
    self.addCommand("audio",      CommandType.PLAYBACK_AUDIO,     self.playbackAudio)

  def eventOn(self):
    if self.mac == None:
      logging.warning("DriverRestService is not configured to support power management")
      return
    subprocess.call(['extras/etherwake', '-i', self.iface, self.mac])

  def eventOff(self):
    # Stop and navigate home (avoid leaving it playing)
    self.execServer(["ESCAPE","ESCAPE","ESCAPE","ESCAPE","ESCAPE","ESCAPE","ESCAPE"])
    self.execPower()

  def navUp(self, zone):
    self.execServer(["UP"])

  def navDown(self, zone):
    self.execServer(["DOWN"])

  def navLeft(self, zone):
    self.execServer(["LEFT"])

  def navRight(self, zone):
    self.execServer(["RIGHT"])

  def navEnter(self, zone):
    self.execServer(["RETURN"])

  def navBack(self, zone):
    self.execServer(["ESCAPE"])

  def playbackPlay(self, zone):
    self.execServer(["MEDIA_PLAY_PAUSE"])

  def playbackPause(self, zone):
    self.execServer(["+LCONTROL", "VK_P", "-LCONTROL"])

  def playbackStop(self, zone):
    self.execServer(["MEDIA_STOP"])

  def playbackNext(self, zone):
    self.execServer(['MEDIA_NEXT_TRACK'])

  def playbackPrev(self, zone):
    self.execServer(['MEDIA_PREV_TRACK'])

  def playbackForward(self, zone):
    self.execServer(["RIGHT"])

  def playbackBackward(self, zone):
    self.execServer(["LEFT"])

  def playbackSubtitle(self, zone):
    self.execServer(["VK_S"])

  def playbackAudio(self, zone):
    self.execServer(["VK_A"])

  def execServer(self, actions, text=None):
    try:
      data = {"action" : actions}
      if text is not None:
        data['text'] = text

      r = requests.post(self.server + "/interact", data=json.dumps(data), timeout=5)
      if r.status_code != 200:
        logging.error("Driver was unable to execute %s due to %s" % (repr(data), repr(r)))
        return False
    except:
      logging.exception("execServer: " + url)
      return False

  def execPower(self, hibernate=False):
    try:
      data = {"state" : "suspend"}
      if hibernate:
        data['state'] = "hibernate"

      r = requests.post(self.server + "/power", data=json.dumps(data), timeout=5)
      if r.status_code != 200:
        logging.error("Driver was unable to execute %s due to %s" % (repr(data), repr(r)))
        return False
    except:
      logging.exception("execPower: " + url)
      return False

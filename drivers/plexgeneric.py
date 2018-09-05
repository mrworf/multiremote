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
ROKU driver
Talks to a specified ROKU device using REST api.
Based on http://sdkdocs.roku.com/display/sdkdoc/External+Control+Guide

Does not make use of the SSDP (Simple Service Discovery Protocol) since
a home may contain more than one device, making it important that the
driver can be directed to a specific ROKU.

Does not support power functions, but will automatically navigate home
when getting power off (to avoid streaming stuff when noone is watching)

This is the first driver to support the driver-extras directive. This
information is provided by the applyExtras() API call and is called
whenever a device selected. Meaning you may get setPower() once but
applyExtras() multiple times if you have plenty of roku scenes.

The information in driver-extras should be:
  app=<name of app>

This will cause the driver to automatically start the correct app
when user activates the scene.
"""

from null import driverNull
#import requests
#from xml.etree import ElementTree
from modules.commandtype import CommandType
import logging

class driverPlexgeneric(driverNull):
  def __init__(self, server):
    driverNull.__init__(self)

    # ALWAYS RESOLVE DNS NAMES TO IP or ROku will not respond!
    self.server = "http://" + self.FQDN2IP(server) + ":8060/"
    self.home = None

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("select", CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)
    self.addCommand("home",   CommandType.NAVIGATE_HOME,    self.navHome)

    self.addCommand("info",     CommandType.PLAYBACK_OSD,           self.playbackInfo)
    self.addCommand("play",     CommandType.PLAYBACK_PLAY,          self.playbackPlay)
    self.addCommand("pause",    CommandType.PLAYBACK_PAUSE,         self.playbackPause)
    self.addCommand("stop",     CommandType.PLAYBACK_STOP,          self.playbackStop)
    self.addCommand("rewind",   CommandType.PLAYBACK_REWIND,        self.playbackRW)
    self.addCommand("forward",  CommandType.PLAYBACK_FASTFORWARD,   self.playbackFF)

    self.addCommand("text",     CommandType.NAVIGATE_TEXTINPUT,     self.navTextInput, None, None, None, 1)

    self.addCommand("subtitle",   CommandType.PLAYBACK_SUBTITLE,  self.playbackSubtitle)
    self.addCommand("audio",      CommandType.PLAYBACK_AUDIO,     self.playbackAudio)

  def eventOff(self):
    self.httpPost(self.server + "keypress/multiremote_host:reboot")    

  def eventOn(self):
    self.httpPost(self.server + "keypress/Home")    

  def navUp(self, zone):
    self.httpPost(self.server + "keypress/Up")

  def navDown(self, zone):
    self.httpPost(self.server + "keypress/Down")

  def navLeft(self, zone):
    self.httpPost(self.server + "keypress/Left")

  def navRight(self, zone):
    self.httpPost(self.server + "keypress/Right")

  def navEnter(self, zone):
    self.httpPost(self.server + "keypress/Select")

  def navBack(self, zone):
    self.httpPost(self.server + "keypress/Back")

  def navHome(self, zone):
    self.httpPost(self.server + "keypress/Home")

  def playbackInfo(self, zone):
    self.httpPost(self.server + "keypress/Info")

  def playbackPlay(self, zone):
    self.httpPost(self.server + "keypress/multiremote_play")

  def playbackPause(self, zone):
    self.httpPost(self.server + "keypress/multiremote_pause")

  def playbackStop(self, zone):
    self.httpPost(self.server + "keypress/multiremote_stop")

  def playbackFF(self, zone):
    self.httpPost(self.server + "keypress/Fwd")

  def playbackRW(self, zone):
    self.httpPost(self.server + "keypress/Rev")

  def playbackSubtitle(self, zone):
    self.httpPost(self.server + "keypress/multiremote_cycle_subtitles")

  def playbackAudio(self, zone):
    self.httpPost(self.server + "keypress/multiremote_cycle_audio")

  def navTextInput(self, zone, txt):
    """ This function is somewhat limited since it does not care about
        handling special characters at all (they should be UTF-8 encoded)
        But it allows us to start using text input at least
    """
    for l in txt:
      if l == 0x0D or l == 0x0A:
        l = "Enter"
      elif l == 0x08:
        l = "Backspace"
      else:
        l = "Lit_" + l
      self.httpPost(self.server + "keypress/" + l)

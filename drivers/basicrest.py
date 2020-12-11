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
Base IR driver, most of the time, this is what you need.
"""

from .null import driverNull
import requests
import base64
import json
from modules.commandtype import CommandType
import logging

class driverBasicrest(driverNull):
  def __init__(self, server, mode):
    driverNull.__init__(self)

    self.code_on = "on"
    self.code_off = "off"
    self.server = server

    if mode != 'onoffonly':
      logging.error('Currently cannot support anything but command/on or command/off')

  def eventOn(self):
    logging.debug("eventOn() for %s" % self.server)
    self.restCall('/command/on')

  def eventOff(self):
    logging.debug("eventOff() for %s" % self.server)
    self.restCall('/command/off')

  def sendCommand(self, zone, command):
    pass

  def restCall(self, url):
    url = self.server + url
    try:
      r = requests.get(url, timeout=5)
    except:
      logging.exception("restCall: " + url)
      return False

    if r.status_code != 200:
      logging.error("Driver was unable to execute %s" % url)
      return False

    j = r.json()

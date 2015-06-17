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

from driver_null import DriverNull
import requests
import base64
import json
from commandtype import CommandType
import logging

class DriverBasicIR(DriverNull):
  def __init__(self, server, commandfile):
    DriverNull.__init__(self)

    self.code_on = "on"
    self.code_off = "off"
    self.server = server
    self.file = commandfile

    jdata = open(commandfile)
    self.ircmds = json.load(jdata)
    if not "on" in self.ircmds:
      logging.debug("Using toggle for %s instead of discreet on/off" % commandfile)
      code_on = code_off = "toggle"

    """
    By default, this driver will prefill the commandlist with PRIVATE_UNDEFINED, this way
    a driver based on this can easily fill in the gaps.
    """
    for cmd in self.ircmds:
      if cmd == "on" or cmd == "off" or cmd == "toggle":
        continue
      self.COMMAND_HANDLER[cmd] = {
        "arguments"   : 0,
        "handler"     : self.sendCommand, "extras" : cmd,
        "name"        : "Undefined",
        "description" : "Undefined",
        "type"        : CommandType.PRIVATE_UNDEFINED
      }

  def eventOn(self):
    logging.debug("eventOff() for %s" % self.file)
    self.sendIr(self.code_on)

  def eventOff(self):
    logging.debug("eventOn() for %s" % self.file)
    self.sendIr(self.code_off)

  def sendCommand(self, zone, command):
    self.sendIr(command)

  def sendIr(self, command):
    if not command in self.ircmds:
      logging.warning("%s is not a defined IR command" % command)

    ir = self.ircmds[command]

    url = self.server + "/write"
    try:
      r = requests.post(url, data=json.dumps(ir), timeout=5)
    except:
      logging.exception("sendIr: " + url)
      return False

    if r.status_code != 200:
      logging.error("Driver was unable to execute %s" % url)
      return False

    j = r.json()

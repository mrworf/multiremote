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
Improved IR driver which uses a separate config file to produce
desired results.

JSON config file looks like this:

{
  "commandfile" : "<file with IR commands>",
  "commandlist" : {
    "<command>..." : {
      "type" : <see commandtype.py>,
      "name" : "<readable name>", (optional)
      "description" : "<readable description>" (optional)
      "sequence" : "[<ircmd>|<ms>]..." (optional)
      "cooldown" : <delay in ms> (optional)
    }
  }
}

commandfile = Which IR file to get ir commands from
command = the exposed command
type = Maps to a command type so UX knows what to do with it
name = A humanreadble name
description = A humanreadble description
sequence = A list of ir commands and delays (in ms)
cooldown = When this command is executed, no new commands can be executed until this time has expired (milliseconds)
           This is useful for devices which do not accept new inputs until a certain time has passed (like power on)

If you omit the optional items, they get the command name as name/desc/sequence.
Any sequence item which is all numbers is considered to be a delay of X milliseconds.

For example:

{
  "file" : "projector.json",
  "commands" : {
    "on" : {
      "type" : 901,
    },
    "off" : {
      "type" : 902,
      "sequence" : "off,200,off"
    }
  }
}

NOTE!
For automatic power management to work, you need to define an on and an off
sequence. If you miss either or both, the power manegement will not happen.

"""
from .null import driverNull
import requests
import base64
import json
import time
import os
import logging

from modules.commandtype import CommandType

class driverIrplus(driverNull):
  def __init__(self, server, commandfile):
    driverNull.__init__(self)

    self.server = server
    self.cmd_on = None
    self.cmd_off = None

    self.cooldown = 0
    self.cmdfile = commandfile

    if not os.path.exists(commandfile):
      logging.error('No such file "%s"', commandfile)
      return
      
    jdata = open(commandfile)
    data = json.load(jdata)

    if data['file'].startswith('/'):
      jdata = open(data["file"])
    else:
      path = os.path.dirname(commandfile)
      jdata = open(os.path.join(path, data["file"]))
    self.ircmds = json.load(jdata)

    for cmd in data["commands"]:
      self.COMMAND_HANDLER[cmd] = {
        "arguments"   : 0,
        "handler"     : self.sendCommand,
        "extras"      : cmd,
        "name"        : cmd,
        "description" : cmd,
        "type"        : data["commands"][cmd]["type"]
      }
      if "sequence" in data["commands"][cmd]:
        self.COMMAND_HANDLER[cmd]["extras"] = data["commands"][cmd]["sequence"]
      if "name" in data["commands"][cmd]:
        self.COMMAND_HANDLER[cmd]["name"] = data["commands"][cmd]["name"]
      if "description" in data["commands"][cmd]:
        self.COMMAND_HANDLER[cmd]["description"] =  data["commands"][cmd]["description"]
      if data["commands"][cmd]["type"] == 901:
        self.cmd_on = cmd
      if data["commands"][cmd]["type"] == 902:
        self.cmd_off = cmd

  def getTime(self):
   return int(round(time.time() * 1000))

  def setPower(self, enable):
    """
    We need to override this and use the on/off pair or toggle to handle
    power.
    """
    if self.power == enable:
      return True

    if enable and self.cmd_on is not None:
      self.sendCommand(None, self.COMMAND_HANDLER[self.cmd_on]["extras"])
    elif self.cmd_off is not None:
      self.sendCommand(None, self.COMMAND_HANDLER[self.cmd_off]["extras"])

    self.power = enable
    return True

  def sendCommand(self, zone, command, extras=None):
    logging.debug("Sending command: " + repr(command))
    logging.debug("Extras is: " + repr(extras))

    cool = self.cooldown - self.getTime()
    if cool > 0:
      logging.info("Cooldown needed before executing new commands, delaying %d ms", cool)
      time.sleep(cool / 1000.0)
      logging.info("Cooldown complete, continuing")

    seq = command.split(",")
    for cmd in seq:
      if cmd.isdigit():
        logging.debug("Command sequence: Sleep %s ms" % cmd)
        time.sleep(int(cmd)/1000.0)
      else:
        logging.debug("Command sequence: Sending %s" % cmd)
        self.sendIr(cmd)
    if extras is not None and "cooldown" in extras:
      logging.info("This command requires a cooldown of %d ms", extras["cooldown"])
      self.cooldown = self.getTime() + extras["cooldown"]

  def sendIr(self, command):
    if not command in self.ircmds:
      logging.warning("%s is not a defined IR command" % command)

    ir = self.ircmds[command]

    url = self.server + "/write"
    try:
      r = requests.post(url, data=json.dumps(ir))
    except:
      logging.exception("sendIr: " + url)
      return False

    if r.status_code != 200:
      logging.error("Driver was unable to execute %s" % url)
      return False

    j = r.json()

  def __str__(self):
    return "IRPlus(" + self.cmdfile + ")"

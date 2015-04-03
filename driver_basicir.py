"""
Base IR driver, most of the time, this is what you need.
"""

from driver_null import DriverNull
import requests
import base64
import json
from commandtype import CommandType

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
      print "INFO: Using toggle for %s instead of discreet on/off" % commandfile
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
    print "DBG: eventOff() for %s" % self.file
    self.sendIr(self.code_on)

  def eventOff(self):
    print "DBG: eventOn() for %s" % self.file
    self.sendIr(self.code_off)

  def sendCommand(self, zone, command):
    self.sendIr(command)

  def sendIr(self, command):
    if not command in self.ircmds:
      print "WARN: %s is not a defined IR command" % command

    ir = self.ircmds[command]

    url = self.server + "/write/" + ir
    r = requests.get(url)
    if r.status_code != 200:
      print "ERROR: Driver was unable to execute %s" % url
      return False

    j = r.json()

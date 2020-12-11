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
Simplest driver of all, provides logic for power handling, commands and
simplifications for some of the more nitty-gritty work that all drivers must
do.

It's HIGHLY RECOMMENDED that drivers utilize this class as the base class,
since it provides quite a bit of abstraction and easier power management.
"""
from modules.commandtype import CommandType
import traceback
import logging
import socket
import requests
from xml.etree import ElementTree

class driverNull:
  def __init__(self):
    self.power = False
    self.COMMAND_HANDLER = {}
    self.httpTimeout = 250 # 250ms
    self.handlers = []

  def eventOn(self):
    """ Override to handle power on event
    """
    logging.warning("" + repr(self) + " is not implementing power on")

  def eventOff(self):
    """ Override to handle power off event
    """
    logging.warning("" + repr(self) + " is not implementing power off")

  def eventExtras(self, keyvalue):
    """ Override this to handle extra data
    """
    pass

  ############################################################################
  ## Functions below provide convenience for the new driver. 
  ############################################################################

  def _handleResponse(self, r, contentIsJSON=False, contentIsXML=False):
    result = {
      'success' : False, 
      'code': 501, 
      'content' : None
    }
    try:
      if contentIsJSON:
        content = r.json
      elif contentIsXML:
        content = ElementTree.fromstring(r.content)
      else:
        content = r.content
      result = {
        'success' : r.status_code == requests.codes.ok, 
        'code': r.status_code, 
        'content' : content
      }
    except:
      logging.exception('Failed to parse result')
    return result

  def httpGet(self, url, contentIsJSON=False, contentIsXML=False):
    result = {
      'success' : False, 
      'code': 500, 
      'content' : None
    }
    try:
      r = requests.get(url, timeout=self.httpTimeout/1000.0)
      print((repr(r.content)))
      result = self._handleResponse(r, contentIsXML=contentIsXML, contentIsJSON=contentIsJSON)
    except:
      logging.exception('HTTP GET failed')
    return result

  def httpPost(self, url, data = None, contentIsJSON=False, contentIsXML=False):
    result = {
      'success' : False, 
      'code': 500, 
      'content' : None
    }
    try:
      r = requests.post(url, data=data, timeout=self.httpTimeout/1000.0)
      self._handleResponse(r, contentIsXML=contentIsXML, contentIsJSON=contentIsJSON)
    except:
      logging.exception('HTTP POST failed')
    return result

  def FQDN2IP(self, fqdn, getIPV6 = False):
    """ Takes a regular DNS name and resolves it into an IP address instead.
        If you provide an IP address, it will simply return the IP address.
    """
    try:
      family = socket.AF_INET
      if getIPV6:
        family = socket.AF_INET6
      details = socket.getaddrinfo(fqdn, 80, family, socket.SOCK_STREAM)
      if details is None or len(details) < 1:
        logging.error('Unable to resolve "%s" to a network address', fqdn)
      elif len(details) > 1:
        logging.warning('"%s" returned %d results, only using the first entry', fqdn, len(details))
      return details[0][4][0]
    except:
      logging.exception('Unable to resolve "%s"', fqdn)
      return None

  def registerHandler(self, handler, cmds):
    """ API: Registers a handler to be called for cmds defined in list
        Does not have unregister since this should not change during its lifetime
        """
    self.handlers.append({'handler':handler, 'commands': cmds})

  def addCommand(self, command, cmdtype, handler, name = None, desc = None, extras = None, args = 0):
    """ Convenience function, allows adding commands to the list which
        is exposed by getCommands() and handleCommand()
    """
    name = command
    desc = name

    if extras == None:
      self.COMMAND_HANDLER[command] = {
        "arguments"   : args,
        "handler"     : handler,
        "name"        : name,
        "description" : desc,
        "type"        : cmdtype
      }
    else:
      self.COMMAND_HANDLER[command] = {
        "arguments"   : args,
        "handler"     : handler,
        "name"        : name,
        "description" : desc,
        "type"        : cmdtype,
        "extras"      : extras
      }


  ############################################################################
  ## Functions below are usually not overriden since they provide basic
  ## housekeeping. It's better to override eventXXX() functions above.
  ############################################################################

  def setPower(self, enable):
    """ API: Changes the power state of the device, if the state already
        is at the requested value, then nothing happens.
    """

    if self.power == enable:
      return True
    self.power = enable
    try:
      if enable:
        self.eventOn()
      else:
        self.eventOff()
    except:
      logging.exception("Exception when calling setPower(%s)" % repr(enable))
    return True

  def applyExtras(self, keyvaluepairs):
    """ API: Called when this device is selected as a scene, can be called more
        than once during a powered session, since user may switch between
        different scenes which all use the same driver but different extras.

        By default, this parses a string that looks like this:
          key=value,key=value,...
        And calls eventExtras() with a dict, but drivers can override this
        directly if needed. Otherwise, eventExtras is the recommended override
        method.
    """
    result = {}
    pairs = keyvaluepairs.split(",")
    for pair in pairs:
      parts = pair.split("=", 1)
      if len(parts) == 2:
        result[parts[0].strip()] = parts[1].strip()
    if len(result) > 0:
      self.eventExtras(result)

  def handleCommand(self, zone, command, argument):
    """ API: Called by the server whenever a command needs to be executed,
        the only exception is power commands, they are ALWAYS called
        through the setPower() function.

        -- FUTURE: --
        Eventually it will do low-level handling of state, what that
        means is that certain command types will be grouped and multiple
        calls to the same command will only execute the first one.
        For example, calling input-hdmi1 three times will only execute
        the first time. This is to avoid unnecessary latencies.

        A driver will be able to override this behavior by adding a flag
        to the command definition.
    """
    '''
    result = None
    for handler in self.handlers:
      if command in handler['commands']:
        try:
          result = handler['handler'](zone, command, argument)
        except:
          logging.exception("Exception executing command %s for zone %s" % (repr(command), repr(zone)))
        break
    return result
    '''
    result = None
    if command not in self.COMMAND_HANDLER:
      logging.error("%s is not a supported command" % command)
      return result

    try:
      item = self.COMMAND_HANDLER[command]
      if item["arguments"] == 0:
        if "extras" in item:
          result = item["handler"](zone, item["extras"])
        else:
          result = item["handler"](zone)
      elif item["arguments"] == 1:
        if "extras" in item:
          result = item["handler"](zone, args[0], item["extras"])
        else:
          result = item["handler"](zone, args[0])
      return result
    except:
      logging.exception("Exception executing command %s for zone %s" % (repr(command), repr(zone)))
      return None


  def getCommands(self):
    """ API: Returns the list of supported commands. For now it also limits this
        list depending on the type. This is less than ideal, but for now
        this is how it's done.
    """
    ret = {}
    '''
    for handler in self.handlers:
      for cmd in handler['commands']:
        ret
    '''
    for c in self.COMMAND_HANDLER:
      # Do not expose certain commands
      if self.COMMAND_HANDLER[c]["type"] > CommandType.LIMIT_GETCOMMANDS:
        continue

      ret[c] = {"name": "", "description": ""}
      if "name" in self.COMMAND_HANDLER[c]:
        ret[c]["name"] = self.COMMAND_HANDLER[c]["name"]
      if "description" in self.COMMAND_HANDLER[c]:
        ret[c]["description"] = self.COMMAND_HANDLER[c]["description"]
      ret[c]["type"] = self.COMMAND_HANDLER[c]["type"]
    return ret

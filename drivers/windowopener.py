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
The information in driver-extras should be:
  app=<name of app>

This will cause the driver to automatically start the correct app
when user activates the scene.
"""

from .base import driverBase
import requests
from modules.commandtype import CommandType
import logging

class driverWindowopener(driverBase):
  def init(self, server, token):
    # ALWAYS RESOLVE DNS NAMES TO IP or ROku will not respond!
    self.server = "http://" + self.FQDN2IP(server) + ":8080/program"
    self.token = token

  def eventOff(self):
    requests.post(self.server, json={'stop': None, 'token':self.token})

  def eventExtras(self, extras):
    if 'app' not in extras:
      logging.error(f'"app" was not present in extras ({extras})')
      return

    requests.post(self.server, json={'start':extras['app'], 'token':self.token})

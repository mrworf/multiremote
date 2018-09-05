#!/usr/bin/env python
#
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

import json
import base64
import uuid
import logging

"""
Remote registration and management is handled in this class.
A remote constitues any app which accesses the REST API provided
by multiRemote.

An app can range from web page (using multiRemote-UX), dedicated iOS/Android
native app or indeed another server.

Each remote can have states associated with it, but these are not saved
by the system. They are most definitely volatile :)
"""
class RemoteManager:
  FILENAME="remotes.json"

  def __init__(self):
    """
    Initializes our list of recognized remotes
    """
    self.REMOTES = self.load()
    self.STATE = {}

  def load(self):
    """
    Loads the remote object.
    !DOES NOT VALIDATE THE DATA!
    """
    data = {}
    try:
      jdata = open(self.FILENAME)
      data = json.load(jdata)
      jdata.close()
    except:
      logging.exception("Unable to load " + self.FILENAME)
      return {}

    return data;

  def save(self):
    """
    Saves the remote object, unless it's empty
    """
    if len(self.REMOTES) == 0:
      logging.debug("No remotes in system, will not save")
      return

    try:
      jdata = open(self.FILENAME, "w")
      jdata.write(json.dumps(self.REMOTES))
      jdata.close()
    except:
      logging.exception("Unable to save " + self.FILENAME)
      return

  def register(self, name, desc, zone, existing=None):
    """
    Registers a remote with the system. If there already is
    a remote by a certain name, it will be overwritten.
    """
    if existing == None:
      id = uuid.uuid4().hex
    elif self.has(existing):
      id = existing
    else:
      logging.error("Tried to update " + existing + " but it's not in database")
      return None

    self.REMOTES[id] = {"name" : name, "description" : desc, "zone" : zone}
    self.save()
    return id;

  def unregister(self, uuid):
    """
    Removes a remote based on its UUID.
    """
    if uuid in self.REMOTES:
      self.REMOTES.pop(uuid, None)
    else:
      logging.warning("Trying to remove " + uuid + " which does not exist")
    self.save()

  def list(self):
    """
    Returns an array of UUIDs
    """
    ret = []
    for r in self.REMOTES:
      ret.append(r)
    return ret

  def describe(self, uuid):
    """
    Returns a representation of the selected remote or None if
    it does not exist.
    """
    if uuid in self.REMOTES:
      return self.REMOTES[uuid]
    return None

  def has(self, uuid):
    """
    Tests if UUID is a valid remote
    """
    return uuid in self.REMOTES

  def set(self, uuid, key, value):
    if not uuid in self.REMOTES:
      logging.warning("set() called on non-existant remote: " + uuid)
      return
    if not uuid in self.STATE:
      self.STATE[uuid] = {}
    self.STATE[uuid][key] = value

  def get(self, uuid, key, default=None):
    if not uuid in self.STATE:
      return default
    if not key in self.STATE[uuid]:
      return default
    return self.STATE[uuid][key]
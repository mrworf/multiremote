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
import os
import requests

"""
Webhook Manager allows for registration of outgoing webhooks.

Any user of this class can register that they can make a call
when a certain event happens.

The manager will read a configuration file where the user
can define endpoints to call based on certain events.

For now, only query parameters and JSON payloads are supported.
"""
class WebhookManager:
  ACTIVE = 'active'
  INACTIVE = 'inactive'
  EMPTY = ''

  def __init__(self):
    self.attributes = {}
    self.hooks = []

  def load(self, filename):
    if not os.path.exists(filename):
      logging.error('"%s" does not exist', filename)
      return False
    logging.debug('Loading %s', filename)
    with open(filename, 'r') as f:
      c = 0
      hook = None
      actions = None
      for line in f:
        c += 1
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
          continue
        logging.debug('Line: %s', line)
        try:
          parts = line.split()
          cmd = parts[0].lower()
          if cmd == 'when':
            hook = {
              'checks':[],
              'start':[],
              'end':[],
              'active':False
            }
            actions = 'start'

            p = 1
            while True:
              check = {
                'attribute':parts[p].lower(),
                'operator':parts[p+1].lower(),
                'value':parts[p+2],
              }
              hook['checks'].append(check)
              if len(parts) == (p+3):
                logging.debug('No more parts in line')
                break
              p += 3
              if parts[p].lower() != 'and':
                logging.error('Line %d, only "and" is supported', c)
                self.hooks = []
                return False
              p += 1
            self.hooks.append(hook)
          elif cmd == 'end':
            actions = 'end'
          elif cmd == 'call':
            if actions is not None:
              hook[actions].append({'url':parts[1], 'data':({k: v for k,v in (item.split('=') for item in parts[2:])} if len(parts)>2 else None) })
          else:
            logging.warning('Unknown directive on line %d in "%s": "%s"', c, filename, line)
        except:
          logging.exception('Error on line %d in "%s": "%s"', c, filename, line)
          self.hooks = []
          return False
    logging.debug('Webhooks loaded')
    logging.debug(repr(self.hooks))
    return True

  def register_attribute(self, name):
    # Registers an attribute, otherwise it cannot be set
    if name in self.attributes:
      logging.warning('Attribute "%s" has already been registered', name)
    else:
      self.attributes[name] = None

  def update_attribute(self, name, value):
    if name not in self.attributes:
      logging.error('Attribute "%s" is not registered, cannot update', name)
      return False
    self.attributes[name] = value
    self.evaluate_hooks()
    return True

  def is_when(self, hook):
    final = None
    logging.debug('Attributes are: %s', repr(self.attributes))
    for check in hook['checks']:
      state = self.attributes[check['attribute']]
      result = None
      if state == check['value']:
        result = True
      else:
        result = False
      if check['operator'] == 'neq':
        logging.debug('when %s neq %s is %s', state, check['value'], repr(result))
        result = not result
      else:
        logging.debug('when %s eq %s is %s', state, check['value'], repr(result))
      if final is None:
        final = result
      elif final != result:
        logging.debug('The last check wasn\'t equal to previous check, early exit with false')
        final = False
        break
    return final

  def evaluate_hooks(self):
    for hook in self.hooks:
      if self.is_when(hook) and not hook['active']:
        hook['active'] = True
        self.call_hooks(hook['start'])
      elif not self.is_when(hook) and hook['active']:
        hook['active'] = False
        self.call_hooks(hook['end'])

  def call_hooks(self, endpoints):
    for endpoint in endpoints:
      try:
        logging.debug('Calling "%s"', endpoint['url'])
        if endpoint['data'] != None:
          result = requests.post(endpoint['url'], data=endpoint['data'])
        else:
          result = requests.get(endpoint['url'])
        logging.info('Result: %d %s', result.status_code, result.reason)
      except:
        logging.exception('GET %s failed', endpoint['url'])

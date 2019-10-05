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
This is the SSDP implementation for multiRemote.

Creates a simple UDP server which listens for the following services:
  ssdp:all
  urn:sensenet-nu:service:multiRemote:1

If it sees any M-SEARCH for them, it responds in kind.

"""
import socket
import threading
import time
import struct
import ipaddress
import netifaces
import uuid
import logging
import json
import os.path

class SSDPHandler (threading.Thread):
  CONFIGFILE = "ssdp-info.json"

  """
  location should be an URL where the web interface is hosted.

  notifyInterval is the number of seconds between NOTIFY messages (default 15s)

  listen can be used to override which interface to issue and listen to SSDP messages.
  By default this is set to empty string which means all available interfaces.

  """
  def __init__(self, location, port, notifyInterval=15, listen=''):
    threading.Thread.__init__(self)
    self.daemon = True
    self.listen = listen
    self.location = location
    self.port = port
    self.notifyInterval = notifyInterval
    self.urn = 'urn:sensenet-nu:service:multiRemote:1'
    self.usn = None

    self.load()
    if self.usn is None:
      self.usn = 'uuid:%s' % uuid.uuid4()
      self.save()

  def load(self):
    if not os.path.isfile(self.CONFIGFILE):
      return

    try:
      jdata = open(self.CONFIGFILE)
      data = json.load(jdata)
      jdata.close()
      if "usn" in data:
        self.usn = data["usn"]
    except:
      logging.exception("Unable to load " + self.CONFIGFILE)

  def save(self):
    data = {
      "usn" : self.usn,
    }

    try:
      jdata = open(self.CONFIGFILE, "w")
      jdata.write(json.dumps(data))
      jdata.close()
    except:
      logging.exception("Unable to save " + self.CONFIGFILE)
      return

  def getUSN(self):
    return self.usn

  def getURN(self):
    return self.urn

  def _initSSDP(self):
    logging.info('Init SSDP')
    self.sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sender.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self.sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)

    self.listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self.listener.bind((self.listen, 1900))

    request = struct.pack('4sL', socket.inet_aton('239.255.255.250'), socket.INADDR_ANY)
    self.listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, request)
    self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8192*2)
    # Make sure we don't get stuck longer than 1s so we also can notify
    self.listener.settimeout(1)

  def run(self):
    self._initSSDP()

    nextNotify = 0
    while True:
      try:
        if nextNotify < time.time():
          if not self.sendNotify():
            raise Exception('Send failed, ugly way to trigger re-init')
          nextNotify = time.time() + self.notifyInterval
        data, sender = self.listener.recvfrom(1400)
        data = data.split('\r\n')
        if data[0] == 'M-SEARCH * HTTP/1.1':
          #logging.debug('Search request from: ' + repr(sender))
          self.handleSearch(sender, data)
      except socket.timeout:
        pass # Ignore, it's by design
      except:
        logging.exception('Got an exception in main read loop')
        # Reinit SSDP just-in-case
        self._initSSDP()

  def resolveHost(self, sender):
    for i in netifaces.interfaces():
      if netifaces.AF_INET not in netifaces.ifaddresses(i):
        continue
      ii = netifaces.ifaddresses(i)[netifaces.AF_INET][0]
      if ipaddress.ip_address(unicode(sender)) in ipaddress.ip_network(unicode(ii['addr'] + '/' + ii['netmask']), strict=False):
        return ii['addr']
    return None

  def handleSearch(self, sender, content):
    for line in content:
      if line == "ST: ssdp:all" or line == ("ST: %s" % self.urn):
        self.sendResponse(sender)
        break

  def sendNotify(self):
    msg  = 'NOTIFY * HTTP/1.1\r\n'
    msg += 'Host: 239.255.255.250:1900\r\n'
    msg += 'Location: *\r\n'
    msg += 'Server: multiRemote/1.0\r\n'
    msg += 'NT: %s\r\n' % self.urn
    msg += 'NTS: ssdp:alive\r\n'
    msg += 'USN: %s\r\n' % self.usn
    msg += 'Cache-Control: max-age=120\r\n'
    msg += '\r\n'

    if self.sender.sendto(msg, ('239.255.255.250', 1900)) < len(msg):
      logging.error('Sending notification failed')
      return False
    return True

  def sendResponse(self, sender):
    host = self.resolveHost(sender[0])
    if host is None:
      print "ERROR: SSDP source could not be resolved to interface"
      return

    msg  = 'HTTP/1.1 200 OK\r\n'
    msg += 'Host: 239.255.255.250:1900\r\n'
    msg += 'Location: http://%s:%d/description.xml\r\n' % (host, self.port)
    msg += 'Server: multiRemote/1.0\r\n'
    msg += 'NT: %s\r\n' % self.urn
    msg += 'NTS: ssdp:alive\r\n'
    msg += 'USN: %s\r\n' % self.usn
    msg += 'Cache-Control: max-age=120\r\n'
    msg += '\r\n'

    self.sender.sendto(msg, sender)

  def generateXML(self):
    result = """<?xml version="1.0" encoding="UTF-8"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
   <specVersion>
      <major>1</major>
      <minor>1</minor>
   </specVersion>
   <device>
      <deviceType>{urn}</deviceType>
      <friendlyName>multiRemote</friendlyName>
      <manufacturer>Sense/Net</manufacturer>
      <manufacturerURL>http://multiremote.sensenet.nu</manufacturerURL>
      <modelDescription>Advanced A/V remote control server</modelDescription>
      <modelName>multiRemote</modelName>
      <modelNumber>1</modelNumber>
      <UDN>{usn}</UDN>
      <serviceList>
         <service>
            <!-- Sorry, not 100% compliant -->
            <serviceType>{urn}</serviceType>
            <serviceId>urn:sensenet-nu:serviceId:control</serviceId>
            <SCPDURL></SCPDURL>
            <controlURL>/</controlURL>
            <eventSubURL>/events</eventSubURL>
         </service>
      </serviceList>
      <presentationURL>{interface}</presentationURL>
   </device>
</root>""".format(urn=self.urn, usn=self.usn, interface=self.location)
    return result

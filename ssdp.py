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

It has a nice special feature which allows it to detect the originating
network interface and, if provided with a %s in the location parameter,
automatically substitute the server address with the IP of the network
interface. Solves the case where you bind to 0.0.0.0 (ADDR_ANY).

For testing purposes, this class can be run stand-alone and will then
start the SSDP server by itself, allowing easy debugging.
"""
import socket
import threading
import time
import struct
import ipaddress
import netifaces

class SSDPHandler (threading.Thread):
  def __init__(self, location, unique='changemetounique', listen=''):
    threading.Thread.__init__(self)
    self.daemon = True
    self.listen = listen
    self.location = location
    self.urn = 'urn:sensenet-nu:service:multiRemote:1'
    self.usn = 'uuid:%s' % unique

  def run(self):
    self.sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sender.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sender.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    self.sender.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)

    self.listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self.listener.bind((self.listen, 1900))

    request = struct.pack('4sL', socket.inet_aton('239.255.255.250'), socket.INADDR_ANY)
    self.listener.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, request)

    print "Loop begins..."
    while True:
      data, sender = self.listener.recvfrom(1024)
      data = data.split('\r\n')
      if data[0] == 'M-SEARCH * HTTP/1.1':
        self.handleSearch(sender, data)

  def resolveHost(self, sender):
    for i in netifaces.interfaces():
      ii = netifaces.ifaddresses(i)[netifaces.AF_INET][0]
      if ipaddress.ip_address(unicode(sender)) in ipaddress.ip_network(unicode(ii['addr'] + '/' + ii['netmask']), strict=False):
        return ii['addr']
    return None

  def handleSearch(self, sender, content):
    for line in content:
      if line == "ST: ssdp:all" or line == ("ST: %s" % self.urn):
        print repr(sender) + " is looking for me"
        self.handleNotify(sender)
        break

  def handleNotify(self, sender):
    host = self.resolveHost(sender[0])
    if host is None:
      print "ERROR: SSDP source could not be resolved to interface"
      return

    msg  = 'HTTP/1.1 200 OK\r\n'
    msg += 'Host: 239.255.255.250:1900\r\n'
    msg += 'Location: %s\r\n' % (self.location % host)
    msg += 'Server: multiRemote/1.0\r\n'
    msg += 'NT: %s\r\n' % self.urn
    msg += 'NTS: ssdp:alive\r\n'
    msg += 'USN: %s\r\n' % self.usn
    msg += 'Cache-Control: max-age=120\r\n'
    msg += '\r\n'

    self.sender.sendto(msg, sender)

if __name__ == "__main__":
  ssdp = SSDPHandler('http://%s:5000/desc')
  print "Starting the SSDP thread"
  ssdp.start()
  while True:
    time.sleep(1)

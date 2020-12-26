#!/usr/bin/env python3
"""
Example that shows how the socket client can be used.

All functions (except get_chromecast()) are non-blocking and
return immediately without waiting for the result. You can use
that functionality to include pychromecast into your main loop.
"""
import time
import select
import sys
import logging
import os

import requests
import argparse

import pychromecast

""" This should be a configuration file!

    Format:
        server <http://address:port/>
        token <token>

        name <name of chromecast>
        device <ip/dns of chromecast>
        zone <zone>
        scene <scene>
        ...

"""
class Config:
    def __init__(self):
        self.server = None
        self.token = None
        self.chromemap = {}

    def _addEntry(self, name, entry):
        # Check that all parts of the entry is filled out
        for k in ['address', 'zone', 'scene']:
            if entry[k] is None or entry[k] == '':
                logging.error('Missing parts of "%s" definition: %s', name, repr(entry))
                return False
        self.chromemap[name] = entry

    def load(self, filename='mapping.cfg'):
        if not os.path.exists(filename):
            logging.error('Missing config file "%s"', filename)
            return False
        try:
            self.chromemap = {}
            self.server = None
            self.token = None
            with open(filename) as file:
                l=0
                name = None
                entry = None

                for line in file:
                    line = line.strip()
                    l += 1
                    if line.startswith('#') or line == '':
                        continue
                    if line.startswith('server '):
                        if self.server is not None:
                            logging.error('Multiple definitions of server, 2nd one found at line %d', l)
                            return False
                        self.server = line[7:].strip()
                        if self.server == '':
                            logging.error('Server field cannot be blank on line %d', l)
                            return False
                    elif line.startswith('token '):
                        if self.token is not None:
                            logging.error('Multiple definitions of token, 2nd one found at line %d', l)
                            return False
                        self.token = line[6:].strip()
                        if self.token == '':
                            logging.error('Token field cannot be blank on line %d', l)
                            return False
                    elif line.startswith('name '):
                        if name is not None:
                            self._addEntry(name, entry)
                        name = line[5:].strip()
                        if name == '':
                            logging.error('On line %d, name cannot be blank', l)
                            return False
                        if name in self.chromemap:
                            logging.warning('"%s" is already defined (redefinition found at line %d)', l)
                        entry = {'address':None, 'zone':None, 'scene':None, 'timeout': 0, 'auto': False, 'device': None}
                    elif entry:
                        if line.startswith('address '):
                            entry['address'] = line[8:].strip()
                        elif line.startswith('zone '):
                            entry['zone'] = line[5:].strip()
                        elif line.startswith('scene '):
                            entry['scene'] = line[6:].strip()
                        else:
                            logging.error('Error on line %d: %s', l, line)
                            return False
                    else:
                        logging.error('Error on line %d: %s', l, line)
                        return False
                if name is not None and entry is not None:
                    self._addEntry(name, entry)
        except:
            logging.exception('Cannot read file')
            return False

        # Check that all mandatory parts are available
        if self.server is None:
            logging.error('Missing server definition')
        elif self.token is None:
            logging.error('Missing token definition')
        elif len(self.chromemap) == 0:
            logging.error('No chromecast devices defined')
        else:
            return True
        return False

class CastDevice:
    def __init__(self, name, address, zone, scene):
        self.name = name
        self.address = address
        self.zone = zone
        self.scene = scene
        self.state = 'UNKNOWN'
        self.appid = -1
        self.idle = True
        self.backdropSource = 'http://development.sfo.sensenet.nu/img/test.jpg'
        self.backdropMime = 'image/jpeg'
        self.backdropTimeout = 0

        self.listenState = None
        self.listenIdle = None

        self.device = pychromecast.Chromecast(host=self.address, blocking=False)

    def getName(self):
        return self.name

    def getSocket(self):
        return self.device.socket_client.get_socket()

    def isMySocket(self, socket):
        logging.debug('My socket!! %d', self.device.socket_client.get_socket())
        return self.device.socket_client.get_socket() == socket

    def processData(self):
        self.device.socket_client.run_once()

        # Process any changes we need
        if self.device.status is None:
            return
        self.handleState()
        self.handleAppId()
        self.handleIdle()

    def handleTick(self):
        # Should be called at least every 5 seconds since we need to monitor some stuff
        # which might not actually give a status change
        if self.device.status is None:
            return
        self.handleState()
        self.handleAppId()
        self.handleIdle()

    def handleIdle(self):
        # This is a special, if we detect backdrop, we swap to showing our image
        # Either way, our image or backdrop is considered idle
        isIdle = True
        if self.device.status.app_id == 'E8C28D3C':
            logging.info('Changing to our image to save bandwidth')
            self.device.media_controller.play_media(self.backdropSource, self.backdropMime)
            self.backdropTimeout = time.time() + 600
        elif self.device.media_controller.status.content_id == self.backdropSource or (not self.device.media_controller.status.content_id and self.appid == 'CC1AD845'):
            if self.backdropTimeout < time.time():
                logging.info('Refreshing our image to avoid backdrop module')
                self.device.media_controller.play_media(self.backdropSource, self.backdropMime)
                self.backdropTimeout = time.time() + 600
        else:
            # Now, we need to check the state, UNKNOWN is considered idle
            if self.state != 'UNKNOWN':
                isIdle = False

        if self.idle != isIdle:
            logging.debug('%s Idle: %s', self.zone, repr(isIdle)) #, self.device.media_controller.status)
            self.idle = isIdle
            if self.listenIdle:
                self.listenIdle(self, self.zone, self.scene)
        return isIdle

    def handleAppId(self):
        if self.device.status.app_id == self.appid:
            return False
        self.appid = self.device.status.app_id
        logging.debug('%s app id changed to %s', self.zone, self.appid)
        return True

    def handleState(self):
        if self.device.media_controller.status.player_state == self.state:
            return False
        self.state = self.device.media_controller.status.player_state
        logging.debug('%s state changed to %s', self.zone, self.state)
        if self.listenState:
            self.listenState(self, self.zone, self.scene)
        return True

    def getState(self):
        return self.state

    def isConnected(self):
        return self.device.socket_client.is_connected

    def isIdle(self):
        return self.idle

    def setIdleListener(self, listener):
        self.listenIdle = listener
    
    def setStateListener(self, listener):
        self.listenState = listener

    def setVolume(self, volume):
        if self.idle:
            return
        self.device.set_volume(volume)

class CastMonitor:
    def __init__(self, config):
        self.config = config

        self.discoverStart = 0
        self.discoverStop = None

    def initChromecast(self):
        broken = []
        for entry in self.config.chromemap:
            try:
                logging.info('Initializing "%s"', entry)
                info = self.config.chromemap[entry]
                device = CastDevice(entry, info['address'], info['zone'], info['scene'])
                if not device.isConnected():
                    logging.error('Unable to connect to "%s"', entry)
                    sys.exit(255)
                device.setIdleListener(self.idleListener)
                self.config.chromemap[entry]['device'] = device
            except:
                logging.exception('Unable to initalize %s, skipping' % entry)
                broken.append(entry)

        # Remove all blank entries
        for entry in broken:
            self.config.chromemap.pop(entry, None)

        logging.info('All devices ready')

    def idleListener(self, device, zone, scene):
        info = self.config.chromemap[device.getName()]
        if device.isIdle():
            # Make sure we don't turn off immediately since source might be changing on chromecast
            # and we don't want on/off/on behavior
            # Offline
            info['timeout'] = time.time() + 5
        else:
            # Online!
            info['timeout'] = 0
            r = requests.get('%s/assign/%s' % (self.config.server, zone))
            if r.json()['active'] is None:
                logging.info('Zone %s is not in-use, turn it on', zone)
                info['auto'] = True
                # FORCE max volume since we control it via the amplifier, so no need to run low
                device.setVolume(1)
                requests.get('%s/assign/%s/%s/%s/clone' % (self.config.server, zone, self.config.token, scene))
            else:
                info['auto'] = False

    def start(self):
        self.initChromecast()
        while True:
            # Build array of devices to monitor
            sockets = []
            for entry in self.config.chromemap:
                sockets.append(self.config.chromemap[entry]['device'].getSocket())

            if len(sockets) != 0:
                polltime = 1
                can_read, _, _ = select.select(sockets, [], [], polltime)
                if can_read:
                    for entry in self.config.chromemap:
                        #if self.config.chromemap[entry]['device'].getSocket() in can_read:
                        self.config.chromemap[entry]['device'].processData()
                
                # Make sure all devices get a chance to deal with things
                for item in self.config.chromemap:
                    entry = self.config.chromemap[item]
                    entry['device'].handleTick()
                    if entry['timeout'] != 0 and entry['timeout'] < time.time():
                        entry['timeout'] = 0
                        r = requests.get('%s/assign/%s' % (self.config.server, entry['zone']))
                        if r.json()['active'] == entry['scene'] and entry['auto']:
                            logging.info('Turning off zone %s since no content has been running for over 5s', entry['zone'])
                            requests.get('%s/unassign/%s/%s' % (self.config.server, entry['zone'], self.config.token))
                        else:
                            # If user changed input, don't automatically control the off mode anymore
                            entry['auto'] = False
    
parser = argparse.ArgumentParser(description="ChromeLink - Control multiRemote based on chromecast activity", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--debug', action='store_true', default=False, help="Enable additional information")
parser.add_argument('config', help='Configuration file to use')
cmdline = parser.parse_args()

if cmdline.debug:
    logformat='%(filename)s@%(lineno)d - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logformat)
else:
    logformat='%(levelname)s - %(message)s'
    logging.basicConfig(level=logging.WARNING, format=logformat)
logging.getLogger('pychromecast').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

# e62496050e364aca86f25b1850c5a95b

config = Config()
if not config.load(cmdline.config):
    sys.exit(255)
monitor = CastMonitor(config)
monitor.start()



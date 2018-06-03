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

import requests
import argparse

import pychromecast

""" This should be a configuration file!
"""
class Config:
    def __init__(self):
        self.server = None
        self.token = None
        self.chromemap = {
            'Speakers' : {'zone' : 'zone2', 'scene' : 'chromecast', 'device' : None, 'state' : 'UNKNOWN', 'laststate' : 0, 'reloadtime' : 0},
            'Living Room US' : {'zone' : 'zone1', 'scene' : 'castus', 'device' : None, 'state' : 'UNKNOWN', 'laststate' : 0, 'reloadtime' : 0},
            #'Living Room UK' : {'zone' : 'zone1', 'scene' : 'castuk', 'device' : None, 'state' : None},
            #'Living Room DK' : {'zone' : 'zone1', 'scene' : 'castdk', 'device' : None, 'state' : None},
            #'Living Room SE' : {'zone' : 'zone1', 'scene' : 'castse', 'device' : None, 'state' : None}
        }

class CastMonitor:
    def __init__(self, server, token):
        self.config = Config()
        self.config.server = server
        self.config.token = token

        self.discoverStart = 0
        self.discoverStop = None

    def discovered(self, chromecast):
        # See if it's in the list of devices
        if chromecast.device.friendly_name in self.config.chromemap:
            if self.config.chromemap[chromecast.device.friendly_name]['device'] is None:
                logging.debug('Device %s was discovered', chromecast.device.friendly_name)
                self.config.chromemap[chromecast.device.friendly_name]['device'] = chromecast

    def checkDiscover(self):
        if self.discoverStart > time.time():
            return
        if self.discoverStop:
            self.discoverStop()
            self.discoverStop = None

        # See if we've already discovered all devices...
        skip = True
        for entry in self.config.chromemap:
            if self.config.chromemap[entry]['device'] is None:
                skip = False
                break

        if not skip:
            logging.debug('Reissuing discover since not all devices were found yet')
            self.discoverStop = pychromecast.get_chromecasts(blocking=False, callback=self.discovered)
            self.discoverStart = time.time() + 30 # Every 30s until all devices are detected
        else:
            self.discoverStart = time.time() + 600 # Do it a bit less often 

    def checkStatus(self):
        for entry in self.config.chromemap:
            if self.config.chromemap[entry]['laststate'] > time.time():
                continue
            cast = self.config.chromemap[entry]['device']
            if cast is not None and cast.status is not None:
                # Always check the APP ID, because backdrop will suck up all our bandwidth
                if cast.status.app_id == 'E8C28D3C':
                    logging.info('Seems like backdrop is running, change to OUR image to save bandwidth')
                    cast.media_controller.play_media('http://10.0.3.44/img/test.jpg', 'image/jpeg')
                    self.config.chromemap[entry]['reloadtime'] = time.time() + 600 # We want to reload in 10min to not lose it
                elif self.config.chromemap[entry]['device'].media_controller.status.content_id == 'http://10.0.3.44/img/test.jpg':
                    if self.config.chromemap[entry]['reloadtime'] < time.time():
                        logging.info('Refreshing image so we don\'t time out')
                        cast.media_controller.play_media('http://10.0.3.44/img/test.jpg', 'image/jpeg')
                        self.config.chromemap[entry]['reloadtime'] = time.time() + 600 # We want to reload in 10min to not lose it

            self.config.chromemap[entry]['laststate'] = time.time() + 5 # We want to check in 5s


    def handleDevice(self, entry):
        cast = self.config.chromemap[entry]['device']
        if cast is None:
            logging.warning('handleDevice called for %s but no device available', entry)
            return

        self.config.chromemap[entry]['laststate'] = time.time() + 5 # We want to check in 5s

        if cast.media_controller.status.player_state != self.config.chromemap[entry]['state']:
            self.config.chromemap[entry]['state'] = cast.media_controller.status.player_state
            logging.info('"%s" is now in state "%s"', entry, self.config.chromemap[entry]['state'])
        else:
            # No change, so don't process it
            return

        info = self.config.chromemap[entry]
        if info['state'] == 'UNKNOWN' or info['device'].media_controller.status.content_id == 'http://10.0.3.44/img/test.jpg':
            # Offline
            #logging.info('Chromecast is idle, see if we can turn off the zone')
            r = requests.get('%s/assign/%s' % (self.config.server, info['zone']))
            if r.json()['active'] == info['scene']:
                logging.info('Turning off zone since no content is running')
                requests.get('%s/unassign/%s/%s' % (self.config.server, info['zone'], self.config.token))
        else:
            # Online!
            #logging.info('Chromecast is active, see if we can turn on the zone')
            r = requests.get('%s/assign/%s' % (self.config.server, info['zone']))
            if r.json()['active'] is None:
                logging.info('Zone is not in-use, turn it on')
                requests.get('%s/assign/%s/%s/%s/clone' % (self.config.server, info['zone'], self.config.token, info['scene']))

    def start(self):
        while True:
            # Build array of devices to monitor
            sockets = []
            for entry in self.config.chromemap:
                if self.config.chromemap[entry]['device'] is not None:
                    sockets.append(self.config.chromemap[entry]['device'].socket_client.get_socket())

            if len(sockets) != 0:
                polltime = 1
                can_read, _, _ = select.select(sockets, [], [], polltime)
                if can_read:
                    #received something on the socket, handle it with run_once()
                    for sock in can_read:
                        for entry in self.config.chromemap:
                            if self.config.chromemap[entry]['device'] is not None and self.config.chromemap[entry]['device'].socket_client.get_socket() == sock:
                                self.config.chromemap[entry]['device'].socket_client.run_once()
                                self.handleDevice(entry)

            self.checkDiscover()
            self.checkStatus()
    
parser = argparse.ArgumentParser(description="ChromeLink - Control multiRemote based on chromecast activity", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--debug', action='store_true', default=False, help="Enable additional information")
parser.add_argument('--server', default='http://localhost:5000', help="Which server to communicate with")
parser.add_argument('--token', help="Token to use for controlling multiRemote (ie, remote id)")
cmdline = parser.parse_args()

if cmdline.debug:
    logformat=u'%(asctime)s - %(filename)s@%(lineno)d - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logformat)
else:
    logformat=u'%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.WARNING, format=logformat)
logging.getLogger('pychromecast').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

if cmdline.token is None:
    logging.error('You must provide a token')
    # e62496050e364aca86f25b1850c5a95b
    sys.exit(255)

monitor = CastMonitor(cmdline.server, cmdline.token)
monitor.start()



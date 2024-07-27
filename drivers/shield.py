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
nVidia Shield driver

Uses a persistant ADB shell connection to issue input events as well
as managing what app to run.

Does not support power functions, but will automatically navigate home
when getting power off (to avoid streaming stuff when noone is watching)

This is the first driver to support the driver-extras directive. This
information is provided by the applyExtras() API call and is called
whenever a device selected. Meaning you may get setPower() once but
applyExtras() multiple times if you have plenty of shield scenes.

The information in driver-extras should be:
  app=<name of app>

This will cause the driver to automatically start the correct app
when user activates the scene.

App should be the package name you want to launch, use the pm command
in adb shell to find what packages you have.
"""

from .base import driverBase
from modules.commandtype import CommandType
import logging
import subprocess
import time
import select
import fcntl
import os

class driverShield(driverBase):
  def init(self, server):

    self.server = server
    self.adb = None

    self.addCommand("up",     CommandType.NAVIGATE_UP,      self.navUp)
    self.addCommand("down",   CommandType.NAVIGATE_DOWN,    self.navDown)
    self.addCommand("left",   CommandType.NAVIGATE_LEFT,    self.navLeft)
    self.addCommand("right",  CommandType.NAVIGATE_RIGHT,   self.navRight)
    self.addCommand("select", CommandType.NAVIGATE_ENTER,   self.navEnter)
    self.addCommand("back",   CommandType.NAVIGATE_BACK,    self.navBack)

    #self.addCommand("info",     CommandType.PLAYBACK_OSD,           self.playbackInfo)
    self.addCommand("play",     CommandType.PLAYBACK_PLAYPAUSE,     self.playbackPlay)
    self.addCommand("rewind",   CommandType.PLAYBACK_REWIND,        self.playbackRW)
    self.addCommand("forward",  CommandType.PLAYBACK_FASTFORWARD,   self.playbackFF)

    #self.addCommand("text",     CommandType.NAVIGATE_TEXTINPUT,     self.navTextInput, None, None, None, 1)

    self.setup_adb()

  def setup_adb(self):
    # First, flush any running adb process
    logging.debug("Killing any running ADB server")
    try:
      subprocess.run(['adb', 'kill-server'])
    except subprocess.CalledProcessError as e:
      logging.error(f"Failed to kill ADB server: {e}")
      return False
    
    # Then connect to the device
    logging.debug(f"Connecting to ADB device at {self.server}")
    connect_process = subprocess.run(['adb', 'connect', f'{self.server}'], capture_output=True, text=True)
    
    if 'connected to' not in connect_process.stdout:
      logging.error("Failed to connect to ADB device: %s", connect_process.stdout)
      return False

    logging.debug("Starting ADB shell session...")
    self.adb = subprocess.Popen(['adb', 'shell'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # Ensure we are connected
    if self.adb is not None and self.adb.poll() is not None:
      logging.error("Failed to start ADB shell")
      self.adb = None
      return False
    logging.debug("ADB shell session started")

    # Set stdout to non-blocking
    flags = fcntl.fcntl(self.adb.stdout, fcntl.F_GETFL)
    fcntl.fcntl(self.adb.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    return True

  def exec_command(self, command, ignore_result=False):
    if self.adb is None:
      logging.error("ADB shell not started, trying to start")
      if not self.setup_adb():
        logging.error("Failed to start ADB shell")
        return None
      
    # Let's see if the ADB instance works still
    try:
      self.adb.stdout.flush()
    except BrokenPipeError:
      logging.error("ADB shell connection broken, trying to restart")
      if not self.setup_adb():
        logging.error("Failed to start ADB shell")
        return None

    try:
      logging.debug(f"Executing command: {command}")        
      self.adb.stdin.write(command + '\n')
      self.adb.stdin.flush()
      if ignore_result:
        return None
      logging.debug(f"Waiting for result")
      output = ''
      while select.select([self.adb.stdout], [], [], 0.1)[0]:
        logging.debug(f"Reading output")
        while True:
          try:
            chunk = self.adb.stdout.read(1024)
            if not chunk:
              break
            output += chunk
          except IOError:
            break
        logging.debug(f"Command: {command} -> Output: {output}")
        return output
    except Exception as e:
      logging.exception(f"Failed to execute command: {command}. Error: {e}")
    return None

  def launch_app(self, package_name):
    result = self.exec_command(f'pm resolve-activity -a android.intent.action.MAIN -c android.intent.category.LAUNCHER --brief {package_name}')
    if result is None:
      logging.error(f"Failed to resolve activity for package {package_name}")
      return
    found = False
    intent = None
    for line in result.splitlines():
      if line.startswith('priority=0'):
        found = True
        continue
      if found:
        intent = line
        break
    if intent is None:
      logging.error(f"Failed to find intent for package {package_name}")
      return

    # First, make sure it's not running        
    self.exec_command(f'am force-stop {package_name}')
    # Then launch it
    self.exec_command(f'am start -n {intent}')

  def navigate(self, direction):
    map = {
      'up': 19,
      'down': 20,
      'left': 21,
      'right': 22,
      'center': 23,
      'back': 4,
      'home': 3,
      'menu': 82,
      'search': 84,
      'play_pause': 85,
      'rewind': 89,
      'fast_forward': 90,
      'volume_up': 24,
      'volume_down': 25,
      'volume_mute': 164,
      'power': 26,
      'notifications': 83,
      'quick_settings': 95,
      'recent_apps': 187,
      'enter': 66,
      'delete': 67,
      'escape': 111,
      'tab': 61,
      'space': 62,
      'page_up': 92,
      'page_down': 93,
      'move_home': 122,
      'move_end': 123,
      'media_play': 126,
      'media_pause': 127,
      'media_play_pause': 85,
      'media_stop': 86,
      'media_next': 87,
      'media_previous': 88,
      'media_rewind': 89,
      'media_fast_forward': 90,
      'media_record': 130,
      'media_close': 128,
      'media_eject': 129,
      'media_audio_track': 222,
      'media_audio_next': 87,
      'media_audio_previous': 88,
      'media_audio_forward': 90,
      'media_audio_rewind': 89,
      'media_audio_repeat': 127,
      'media_audio_shuffle': 126,
      'media_audio_play': 85,
      'media_audio_pause': 85,
      'media_audio_play_pause': 85,
      'media_audio_stop': 86,
      'media_audio_rewind': 89,
      'media_audio_fast_forward': 90,
      'media_audio_record': 130,
      'media_audio_close': 128,
      'media_audio_eject': 129,
      'media_audio_track': 222,
      'media_audio_repeat': 127,
      'media_audio_shuffle': 126,
      'media_video_next': 87,
      'media_video_previous': 88
    }

    if direction not in map:
      logging.error(f"Invalid direction: {direction}")
      return
    
    self.exec_command(f'input keyevent {map[direction]}', True)


  def eventOff(self):
    self.navigate('home')

  def eventExtras(self, extras):
    """
    By setting app in extras, we will automatically launch the app
    You must provide the packasge name of the app you want to launch
    """
    if "app" in extras:
        self.launch_app(extras["app"])

  def navUp(self, zone):
    self.navigate('up')

  def navDown(self, zone):
    self.navigate('down')

  def navLeft(self, zone):
    self.navigate('left')

  def navRight(self, zone):
    self.navigate('right')

  def navEnter(self, zone):
    self.navigate('center')

  def navBack(self, zone):
    self.navigate('back')

  def navHome(self, zone):
    self.navigate('home')

  def playbackPlay(self, zone):
    self.navigate('play_pause')

  def playbackFF(self, zone):
    self.navigate('fast_forward')

  def playbackRW(self, zone):
    self.navigate('rewind')

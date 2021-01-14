import threading
import queue
import time
import logging

from tornado.ioloop import IOLoop

class EventHandler:
  class Remote():
    def __init__(self, websocket, uuid, funcPost):
      self.socket = websocket
      self.uuid = uuid
      self.subscriptions = []
      self.funcPost = funcPost

    def subscribe(self, topic):
      topic = topic.strip().lower()
      if not topic or topic in self.subscriptions:
        return
      self.subscriptions.append(topic)

    def post(self, message):
      self.funcPost(message)
      #IOLoop.instance().add_callback(callback=self.socket.write_message, args=message)
     
      #self.socket.write_message(message)

  def __init__(self, core):
    self.remotes = []
    self.core = core
    self.commands = {}

  def addRemote(self, remote):
    logging.info('Remote %s has connected', remote.uuid)
    self.remotes.append(remote)
  
  def removeRemote(self, remote=None, uuid=None, socket=None):
    if not remote:
      remote = self.getRemote(uuid=uuid, socket=socket)

    if not remote:
      logging.error('Unable to resolve remote to remove')
      return

    logging.info('Remote %s has disconnected', remote.uuid)
    self.remotes.remove(remote)

  def hasRemote(self, uuid):
    for remote in self.remotes:
      if remote.uuid == uuid:
        return True
    return False

  def getRemote(self, uuid=None, socket=None):
    for remote in self.remotes:
      if uuid and remote.uuid == uuid:
        return remote
      elif socket and remote.socket == socket:
        return remote
    return None

  def handleMessage(self, socket, message):
    remote = self.getRemote(socket=socket)
    if not remote:
      logging.error('Got message from unregistered endpoint')
      return

    command, data = message.strip().split(' ', 1)

    # These should be registered instead of a major if-statement
    if command == 'LOG':
      logging.debug('%s DEBUG: %s', remote.uuid, data)
    elif command == 'SUBSCRIBE':
      remote.subscribe(data)
    else:
      if command.upper() in self.commands:
        self.commands[command.upper()](remote, data)
      else:
        logging.debug("%s sent unknown message: %s", remote.uuid, message)

  def notify(self, zone, message):
    for remote in self.remotes:
      if zone is None or self.core.getRemoteZone(remote.uuid) == zone:
        logging.info("Informing remote %s about \"%s\"", remote.uuid, message)
        remote.post(message)
      else:
        logging.info("Skipped remote %s", remote.uuid)

  def registerCommand(self, command, funcHandler):
    '''
    Registers a command (case-insensititve) and a function that will handle
    the data sent with that command.
    '''
    command = command.strip().upper()
    if not command or command in self.commands:
      return
    
    self.commands[command] = funcHandler
"""
Handles the actual control of the devices.

It will process the routes in an atomical way to avoid an inconsistent state.
"""
import threading
import Queue
import time

class Router (threading.Thread):
  DELAY = 30 # delay in seconds
  workList = Queue.Queue(10)

  prevState = {}

  CONFIG = None

  def __init__(self, config):
    threading.Thread.__init__(self)

    self.CONFIG = config    

    self.daemon = True
    self.start()
  
  def updateRoutes(self):
    """
    Grabs a snapshot of the current state and queues it for
    realization.
    """
    state = self.CONFIG.getCurrentState()
    self.workList.put(state)
  
  def run(self):
    """Takes care of incoming routing requests"""
    while True:
      order = self.workList.get(True)
      self.processWorkOrder(order)

  def processWorkOrder(self, order):
    """Figures out what parts that should be kept on, off or updated"""
    new_drivers = {}
    keep_drivers = {}
    inactive_drivers = []
    
    drivers = {}
    for z in order:
      drivers.update(order[z])
      
    for d in drivers:
      if d in self.prevState:
        keep_drivers[d] = drivers[d]
      else:
        new_drivers[d] = drivers[d]
    
    if not self.prevState is None:
      for d in self.prevState:
        if d not in drivers:
          inactive_drivers.append(d)
    
    self.enableDrivers(new_drivers)
    self.updateDrivers(keep_drivers)
    self.disableDrivers(inactive_drivers)
    
    self.prevState = keep_drivers
    self.prevState.update(new_drivers)

  def enableDrivers(self, drivers):
    """Powers on drivers and sends list of inital commands"""
    if drivers is None or len(drivers) == 0:
      return
    for d in drivers:
      (name, zone) = self.splitDriverZone(d)
      driver = self.CONFIG.getDriver(name)
      if driver is None:
        continue
      print "DBG: Enabling %s" % driver
      if zone is None:
        driver.setPower(True)
        for cmd in drivers[d]:
          driver.handleCommand(None, cmd, None)
      else:
        driver.setPower(zone, True)
        for cmd in drivers[d]:
          driver.handleCommand(zone, cmd, None)
  
  def disableDrivers(self, drivers):
    """Powers off drivers"""
    if drivers is None or len(drivers) == 0:
      return
    for d in drivers:
      (name, zone) = self.splitDriverZone(d)
      driver = self.CONFIG.getDriver(name)
      if driver is None:
        continue
      print "DBG: Disabling %s" % driver
      if zone is None:
        driver.setPower(False)
      else:
        driver.setPower(zone, False)
    
  def updateDrivers(self, drivers):
    """Sends new list of commands to drivers"""
    if drivers is None or len(drivers) == 0:
      return
    for d in drivers:
      (name, zone) = self.splitDriverZone(d)
      driver = self.CONFIG.getDriver(name)
      if driver is None:
        continue
      print "DBG: Updating %s" % driver
      if zone is None:
        for cmd in drivers[d]:
          driver.handleCommand(None, cmd, None)
      else:
        for cmd in drivers[d]:
          driver.handleCommand(zone, cmd, None)

  def splitDriverZone(self, driver):
    """Splits drivers with zoning support into two parts"""
    ret = driver.split(":", 1)
    if len(ret) == 1:
      return (ret[0], None)
    return (ret[0], ret[1])
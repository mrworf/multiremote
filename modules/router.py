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
Handles the actual control of the devices.

It will process the routes in an atomical way to avoid an inconsistent state.
"""
import threading
import Queue
import time
import logging

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
    logging.debug("Queuing route change " + repr(state))
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

    logging.debug("Processing route change " + repr(order))

    drivers = {}
    for z in order:
      drivers.update(order[z]["route"])

    for d in drivers:
      if d in self.prevState:
        keep_drivers[d] = drivers[d]
      else:
        new_drivers[d] = drivers[d]

    if not self.prevState is None:
      for d in self.prevState:
        if d not in drivers:
          inactive_drivers.append(d)

    """ Apply updates """
    self.enableDrivers(new_drivers)
    self.updateDrivers(keep_drivers)
    self.disableDrivers(inactive_drivers)

    logging.debug("Router->On  = " + repr(new_drivers))
    logging.debug("Router->Upd = " + repr(keep_drivers))
    logging.debug("Router->Off = " + repr(inactive_drivers))

    """ Store what drivers that are in-use """
    self.prevState = keep_drivers
    self.prevState.update(new_drivers)

    """ Finally, execute any scene specific extras """
    for z in order:
      if "extras" in order[z]:
        logging.debug(z + " has extras")
        for e in order[z]["extras"]:
          logging.debug(e + " has params " + order[z]["extras"][e])
          self.CONFIG.getDriver(e).applyExtras(order[z]["extras"][e])

  def enableDrivers(self, drivers):
    """Powers on drivers and sends list of inital commands"""
    if drivers is None or len(drivers) == 0:
      return
    for d in drivers:
      (name, zone) = self.splitDriverZone(d)
      driver = self.CONFIG.getDriver(name)
      if driver is None:
        continue
      logging.debug("Enabling %s" % driver)
      try:
        if zone is None:
          driver.setPower(True)
        else:
          driver.setPower(zone, True)
      except:
        logging.exception("Driver %s failed to power on" % driver)
      try:
        for cmd in drivers[d]:
          driver.handleCommand(zone, cmd, None)
      except:
        logging.exception("Driver %s failed during initial command setup" % driver)

  def disableDrivers(self, drivers):
    """Powers off drivers"""
    if drivers is None or len(drivers) == 0:
      return
    for d in drivers:
      (name, zone) = self.splitDriverZone(d)
      driver = self.CONFIG.getDriver(name)
      if driver is None:
        continue
      logging.debug("Disabling %s" % driver)
      try:
        if zone is None:
          driver.setPower(False)
        else:
          driver.setPower(zone, False)
      except:
        logging.error("Driver %s failed to power off" % driver)

  def updateDrivers(self, drivers):
    """Sends new list of commands to drivers"""
    if drivers is None or len(drivers) == 0:
      return
    for d in drivers:
      (name, zone) = self.splitDriverZone(d)
      driver = self.CONFIG.getDriver(name)
      if driver is None:
        continue
      logging.debug("Updating %s" % driver)
      try:
        for cmd in drivers[d]:
          driver.handleCommand(zone, cmd, None)
      except:
        logging.error("Driver %s failed to update state" % driver)

  def splitDriverZone(self, driver):
    """Splits drivers with zoning support into two parts"""
    ret = driver.split(":", 1)
    if len(ret) == 1:
      return (ret[0], None)
    return (ret[0], ret[1])

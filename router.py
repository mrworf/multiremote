import threading
import Queue
import time

class Router (threading.Thread):
  DELAY = 30 # delay in seconds
  workList = Queue.Queue(10)

  CONFIG = None

  RouteMap = {}
  
  def __init__(self, config):
    threading.Thread.__init__(self)

    self.CONFIG = config    

    self.daemon = True
    self.start()
  
  def update(self, zone, scene):
    """
    If scene is None, it means to remove the input, ergo, close it. 
    """
    self.workList.put({zone : self.getSceneDriver(scene)})
  
  def run(self):
    while True:
      order = self.workList.get(True)
      self.processWorkOrder(order)

  def getZoneDriver(self, zone):
    if zone in self.RouteMap:
      return self.RouteMap[zone]
    return None

  def processWorkOrder(self, order):
    zone, newDriver = order.popitem()
    zid = self.resolveZoneId(zone)
    oldDriver = self.getZoneDriver(zone)
    self.RouteMap[zone] = newDriver
    
    if newDriver is None:
      self.resolveDriver(self.resolveZoneAudio(zone)).setPower(zid, False)
      if self.zoneUsage(oldDriver) == False:
        self.resolveDriver(oldDriver).setPower(False)
    elif oldDriver is None:
      self.resolveDriver(self.resolveZoneAudio(zone)).setPower(zid, True)
      self.resolveDriver(newDriver).setPower(True)

    if newDriver != None and newDriver != oldDriver:
      self.resolveDriver(self.resolveZoneAudio(zone)).setInput(zid, self.resolveInput(newDriver))    
  
  def zoneUsage(self, driver):
    """Check if a driver is still in use"""
    for r in self.RouteMap:
      if self.RouteMap[r] == driver:
        return True
    return False

  def getSceneDriver(self, scene):
    """Resolves a scene into the underlying driver"""
    if scene is None:
      return None
    return SCENE_TABLE[scene]["driver"]

  def resolveDriver(self, driver):
    """Translates a driver into its object"""
    return DRIVER_TABLE[driver]
  
  def resolveZoneId(self, zone):
    """Translates the zone name into a numerical id"""
    return ZONE_TABLE[zone]["id"]

  def resolveZoneAudio(self, zone):
    """Translates the zone name into the audio component, right now we just use the first one"""
    return ZONE_TABLE[zone]["audio"][0]
  
  def resolveInput(self, driver):
    """Translates the driver into the correct input on the receiver"""
    for s in SCENE_TABLE:
      if SCENE_TABLE[s]["driver"] == driver:
        return SCENE_TABLE[s]["input"]
    return None

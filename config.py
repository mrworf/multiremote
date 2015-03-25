"""
The brains of the project.

Config class tracks usage and conflicts and will only perform updates of routing
should it be possible.

Also able to reply back regarding state of various parts of the system
"""
from commandtype import CommandType
from setup import RemoteSetup

class Config:
  DRIVER_TABLE = None
  ROUTING_TABLE = None
  SCENE_TABLE = None
  ZONE_TABLE = None
  REMOTE_TABLE = None
  
  def __init__(self):
    """
    At this point, initialize some extra parameters, such as the combined
    capabilties of zones which have sub-zones.
    """
    # Load data
    setup = RemoteSetup()
    self.DRIVER_TABLE   = setup.DRIVER_TABLE
    self.ROUTING_TABLE  = setup.ROUTING_TABLE
    self.SCENE_TABLE    = setup.SCENE_TABLE
    self.ZONE_TABLE     = setup.ZONE_TABLE
    self.REMOTE_TABLE   = setup.REMOTE_TABLE
    
    # Fix remotes
    for remote in self.REMOTE_TABLE:
      self.REMOTE_TABLE[remote]["active-zone"] = None
    
    # Validate zone structure and provide good defaults
    for z in self.ZONE_TABLE:
      self.ZONE_TABLE[z]["active-scene"] = None
      self.ZONE_TABLE[z]["active-subzone"] = None
      if "subzones" in self.ZONE_TABLE[z]:
        self.ZONE_TABLE[z]["audio"] = None
        self.ZONE_TABLE[z]["video"] = None
        for s in self.ZONE_TABLE[z]["subzones"]:
          if not "subzone-default" in self.ZONE_TABLE[z]: # Set a default
            print "WARN: No default subzone defined for %s, setting it to %s" % (z, s)
            self.ZONE_TABLE[z]["subzone-default"] = s

          if not self.ZONE_TABLE[z]["subzones"][s]["audio"] is None and self.ZONE_TABLE[z]["audio"] is None:
            self.ZONE_TABLE[z]["audio"] = []
          if not self.ZONE_TABLE[z]["subzones"][s]["video"] is None and self.ZONE_TABLE[z]["video"] is None:
            self.ZONE_TABLE[z]["video"] = []
        self.ZONE_TABLE[z]["active-subzone"] = self.ZONE_TABLE[z]["subzone-default"]
        

  def hasScene(self, name):
    """Returns true if scene exists"""
    return name in self.SCENE_TABLE

  def getSceneListForZone(self, zone):
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return []
    return self.getSceneList(self.hasZoneAudio(zone), self.hasZoneVideo(zone))

  def getSceneList(self, includeAudio=True, includeVideo=True):
    """
    Get all svailable scenes, 
    if includeAudio is false, all scenes requiring audio is skipped
    if includeVideo is false, all scenes requiring video is skipped
    (needless to say, if both is false, nothing is returned)
    """
    result = []
    for scene in self.SCENE_TABLE:
      if self.SCENE_TABLE[scene]["video"] and includeVideo == False:
        continue
      if self.SCENE_TABLE[scene]["audio"] and includeAudio == False:
        continue
      result.append(scene)
    return result

  def getScene(self, name):
    """Obtains the details of a specific scene"""
    if not self.hasScene(name):
      print "ERR: %s is not a scene" % name
      return None
    return self.SCENE_TABLE[name]

  def hasZone(self, name):
    """Returns true if zone exists"""
    return name in self.ZONE_TABLE
    
  def getSceneZoneUsage(self, name):
    if not self.hasScene(name):
      print "ERR: %s is not a scene"
      return []
      
    result = []
    for z in self.ZONE_TABLE:
      if self.ZONE_TABLE[z]["active-scene"] == name:
        result.append(z)
    return result
  
  def getSceneRemoteUsage(self, name):
    if not self.hasScene(name):
      print "ERR: %s is not a scene"
      return []
      
    result = []
    for z in self.ZONE_TABLE:
      if self.ZONE_TABLE[z]["active-scene"] == name:
        for r in self.REMOTE_TABLE:
          if self.REMOTE_TABLE[r]["active-zone"] == z:
            result.append(r)
    return result
  
  def getZoneList(self):
    """Get all zones"""
    result = []
    for zone in self.ZONE_TABLE:
      result.append(zone)
    return result

  def getZone(self, name):
    """Return the settings for a zone"""
    if not self.hasZone(name):
      print "ERR: %s is not a zone" % name
      return None
    return self.ZONE_TABLE[name]

  def hasSubZones(self, zone):
    """Tests if the zone has subzones"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return False
    return "subzones" in self.ZONE_TABLE[zone]

  def hasSubZone(self, zone, sub):
    """Tests if a zone has a specific subzone"""
    if not self.hasSubZones(zone):
      print "ERR: %s does not have subzones" % zone
      return False
    return sub in self.ZONE_TABLE[zone]["subzones"]

  def setZoneScene(self, zone, scene):
    """Set the scene for a zone"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return False
    elif not self.hasScene(scene):
      print "ERR: %s is not a scene" % scene
      return False
    
    if self.SCENE_TABLE[scene]["audio"] and self.ZONE_TABLE[zone]["audio"] == None:
      print "WARN: Zone %s does not support audio which is provided by the scene %s" % (zone, scene)
    if self.SCENE_TABLE[scene]["video"] and self.ZONE_TABLE[zone]["video"] == None:
      print "WARN: Zone %s does not support video which is provided by the scene %s" % (zone, scene)
    self.ZONE_TABLE[zone]["active-scene"] = scene
    
    # Handle subzones...
    if self.hasSubZones(zone):
      if self.ZONE_TABLE[zone]["active-subzone"] is None:
        self.ZONE_TABLE[zone]["active-subzone"] = self.ZONE_TABLE[zone]["subzone-default"]

    return True
    
  def getZoneScene(self, zone):
    """Get the current scene for a zone"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return None
    return self.ZONE_TABLE[zone]["active-scene"]
  
  def clearZoneScene(self, zone):
    """Removes the scene for a zone"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return False
    self.ZONE_TABLE[zone]["active-scene"] = None
    return True

  def getSubZone(self, zone):
    """Get active subzone for a zone"""
    if not self.hasSubZones(zone):
      print "ERR: %s does not have subzones" % zone
      return None
    return self.ZONE_TABLE[zone]["active-subzone"]

  def setSubZone(self, zone, sub):
    """Set the subzone for a zone"""
    if not self.hasSubZone(zone, sub):
      print "ERR: %s does not have sub zone %s" % (zone, sub)
      return False
    self.ZONE_TABLE[zone]["active-subzone"] = sub
    return True

  def clearSubZone(self, zone):
    """This one is special, it will switch to default subzone"""
    if not self.hasSubZones(zone):
      print "ERR: %s does not have subzones" % zone
      return False
    self.ZONE_TABLE[zone]["active-subzone"] = self.ZONE_TABLE[zone]["subzone-default"]
    return True

  def getSubZoneList(self, zone):
    """Get all subzones"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return {}
    if not self.hasSubZones(zone):
      print "ERR: %s does not have subzones" % zone
      return {}

    result = {}
    for sz in self.ZONE_TABLE[zone]["subzones"]:
      result[sz] = self.ZONE_TABLE[zone]["subzones"][sz]["name"]
    return result

  def hasZoneAudio(self, zone):
    """Tests if a zone has audio capabilities"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return False
    return self.ZONE_TABLE[zone]["audio"] != None

  def hasZoneVideo(self, zone):
    """Tests if a zone has video capabilities"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return False
    return self.ZONE_TABLE[zone]["video"] != None

  def hasRemote(self, name):
    """Check if remote exists"""
    return name in self.REMOTE_TABLE

  def getRemote(self, name):
    """Get remote"""
    if not self.hasRemote(name):
      print "ERR: %s is not a remote" % name
      return None
    return self.REMOTE_TABLE[name]
  
  def setRemoteZone(self, remote, zone):
    """Set the zone which should be controlled by the remote"""
    if not self.hasRemote(remote):
      print "ERR: %s is not a remote" % remote
      return False
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return False
    self.REMOTE_TABLE[remote]["active-zone"] = zone
    return True

  def getRemoteZone(self, name):
    """Get the zone which the remote is controlling"""
    if not self.hasRemote(name):
      print "ERR: %s is not a remote" % name
      return None
    return self.REMOTE_TABLE[name]["active-zone"]

  def getRemoteList(self):
    """Get list of remotes registered in the system"""
    result = []
    for remote in self.REMOTE_TABLE:
      result.append(remote)
    return result
  
  def getZoneRemoteList(self, zone):
    """Gets a list of remotes currently controlling the zone"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return []
    
    result = []
    for r in self.REMOTE_TABLE:
      if self.REMOTE_TABLE[r]["active-zone"] == zone:
        result.append(r)
    return result
  
  def clearRemoteZone(self, remote):
    if not self.hasRemote(remote):
      print "ERR: %s is not a remote" % remote
      return False
    self.REMOTE_TABLE[remote]["active-zone"] = None
    return True  
  
  def getZoneCommands(self, zone):
    result = {}
    s = self.getZoneScene(zone)
    if s is None:
      return {}
    s = self.getScene(s)
    
    (adrv, vdrv) = self.getZoneDrivers(zone)

    adrv = self.getDriver(adrv)
    vdrv = self.getDriver(vdrv)

    if adrv is not None and s["audio"]:
      result.update(adrv.getCommands())
    if vdrv is not None and s["video"]:
      result.update(vdrv.getCommands())

    return result
    
  def getSceneCommands(self, scene):
    if not self.hasScene(scene):
      print "ERR: %s is not a scene" % scene
      return {}
    drv = self.getDriver(self.SCENE_TABLE[scene]["driver"])
    if drv is None:
      print "ERR: Cannot find driver for scene %s" % scene
      return {}
    result = drv.getCommands()

    return result


  def getRemoteCommands(self, remote):
    """
    This function will compile a list of available commands for a remote
    given what zone it's attached to and what scene is assigned to the zone.
    
    Structure of return is:
    {
      "zone" : {
        "command" : {
          "name" : "Human name",
          "description" : "Longer description",
          "type" : <one of CommandType.*>
        }, ...
      },
      "scene" : {
        "command" : {
          "name" : "Human name",
          "description" : "Longer description",
          "type" : <one of CommandType.*>
        }
      }
    }
    """
    result = {"zone" : {}, "scene" : {}}
    if not self.hasRemote(remote):
      print "ERR: %s is not a remote" % remote
      return result
    
    if self.getRemoteZone(remote) == None:
      print "WARN: Remote %s isn't attached to a zone" % remote
      return result
    
    zname = self.getRemoteZone(remote)
    sname = self.getZoneScene(zname)
    if sname is None:
      print "WARN: Zone %s is not assigned a scene" % zname
      #return []
    
    result["zone"] = self.getZoneCommands(zname)
    result["scene"] = self.getSceneCommands(sname)
    
    return result

  def execZoneCommand(self, remote, command, extras):
    if not self.hasRemote(remote):
      print "ERR: %s is not a remote" % remote
      return False
    zone = self.getRemoteZone(remote)
    scene = self.getZoneScene(zone)
    if scene is None:
      return False
    scene = self.getScene(scene)

    (adrv, vdrv) = self.getZoneDrivers(zone)
    if adrv is not None:
      (adrv, az) = self.splitDriver(adrv)
    if vdrv is not None:
      (vdrv, vz) = self.splitDriver(vdrv)
    adrv = self.getDriver(adrv)
    vdrv = self.getDriver(vdrv)
    
    if adrv is not None and scene["audio"]:
      if command in adrv.getCommands():
        return adrv.handleCommand(az, command, extras)
    if vdrv is not None and scene["video"]:
      if command in vdrv.getCommands():
        return vdrv.handleCommand(vz, command, extras)
        
    return False

  def execSceneCommand(self, remote, command, extras):
    print "DBG: execSceneCommand called"
    if not self.hasRemote(remote):
      print "ERR: %s is not a remote" % remote
      return False
    zone = self.getRemoteZone(remote)
    scene = self.getZoneScene(zone)
    if scene is None:
      return False
    scene = self.getScene(scene)

    drv = self.getDriver(scene["driver"])
    if command in drv.getCommands():
      return drv.handleCommand(None, command, extras)
    else:
      print "WARN: %s is not a command" % command
        
    return False


  def getZoneDrivers(self, zone):
    """
    Returns the current audio and video driver. If any or both are unavailable
    then this function replaces that with None
    """
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return (None, None)
    if self.ZONE_TABLE[zone]["active-scene"] is None:
      print "ERR: No scene for zone %s" % zone
      return (None, None)
    if self.hasSubZones(zone):
      sz = self.ZONE_TABLE[zone]["active-subzone"]
      return (self.ZONE_TABLE[zone]["subzones"][sz]["audio"], self.ZONE_TABLE[zone]["subzones"][sz]["video"])
    else:
      return (self.ZONE_TABLE[zone]["audio"], self.ZONE_TABLE[zone]["video"])

  def getCurrentState(self):
    """
    Shows the current state which indicates what's going on.
    Format:
    {<zone> : [<driver>, ...]}
    
    Some examples...
    PS4 is playing in Zone1 and Spotify in Zone2:
    { 
      "zone2" : [ "receiver:2", "spotify" ],
      "zone1" : [ "receiver:1", "splitter", "tv" ],
    }
    
    Spotify playing in both Zone1 and Zon2:
    {
      "zone1" : [ "receiver:1", "spotify" ],
      "zone1" : [ "receiver:2", "spotify" ]
    }
    
    DVD on Projector in Zone1:
    {
      "zone1" : [ "receiver:1", "splitter", "screen", "projector", "dvd" ]
    }
    
    There is no relationship between the order of things shown within the array
    """
    
    result = {}
    
    for z in self.ZONE_TABLE:
      route = self.getCurrentStateForZone(z)
      if not route is None:
        result[z] = route
    return result

  def getCurrentStateForZone(self, zone, subzone=None, sceneOverride=None):
    """
    Obtains a route for a zone based on active scene and potentially subzone.
    If provided with a sceneOverride, the active scene is ignored and the
    provided scene will be used instead.
    """
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return None
    if not sceneOverride is None and not self.hasScene(sceneOverride):
      print "ERR: %s is not a scene" % sceneOverride
      return None
    if self.ZONE_TABLE[zone]["active-scene"] is None and sceneOverride is None:
      return None

    if sceneOverride is None:      
      s = self.ZONE_TABLE[zone]["active-scene"]
    else:
      s = sceneOverride

    if sceneOverride is None:
      (adrv, vdrv) = self.getZoneDrivers(zone)
    else:
      # We need to perform an acrobatics act here since we
      # must resolve drivers without actually assigning them
      if self.hasSubZones(zone):
        if subzone is None:
          sz = self.ZONE_TABLE[zone]["active-subzone"]
          if sz is None:
            sz = self.ZONE_TABLE[zone]["subzone-default"]
        else:
          sz = subzone
        adrv = self.ZONE_TABLE[zone]["subzones"][sz]["audio"]
        vdrv = self.ZONE_TABLE[zone]["subzones"][sz]["video"]
      else:
        adrv = self.ZONE_TABLE[zone]["audio"]
        vdrv = self.ZONE_TABLE[zone]["video"]
      
    sdrv = self.SCENE_TABLE[s]["driver"]
    
    # Translate into route
    if self.SCENE_TABLE[s]["audio"] and not self.SCENE_TABLE[s]["video"]:
      route = self.resolveRoute(sdrv, adrv, None)
    elif self.SCENE_TABLE[s]["audio"] and self.SCENE_TABLE[s]["video"]:
      route = self.resolveRoute(sdrv, adrv, vdrv)
    elif not self.SCENE_TABLE[s]["audio"] and self.SCENE_TABLE[s]["video"]:
      print "ERR: Video only zones are not supported"
    else:
      print "ERR: Scene has neither audio nor video!"
    return self.translateRoute(zone, route)

  def resolveRoute(self, sdrv, adrv, vdrv):
    """
    Resolves the routing needed for a scene driver with audio and
    optionally video driver.
    """
    if sdrv not in self.ROUTING_TABLE:
      print "ERR: %s does not have any routing information" % sdrv
      return []
    
    if vdrv == None or not "audio+video" in self.ROUTING_TABLE[sdrv]:
      baseRoutes = self.ROUTING_TABLE[sdrv]["audio"]
    else:
      baseRoutes = self.ROUTING_TABLE[sdrv]["audio+video"]
    
    routes = self.filterRoutes(baseRoutes, adrv)
    if not vdrv is None:
      routes = self.filterRoutes(routes, vdrv)

    if len(routes) != 1:
      print "WARN: Routing was inconclusive, got %d routes" % len(routes)
      
    route = routes[0]
    if not sdrv in route:
      route[sdrv] = []
    return route

  def filterRoutes(self, routes, drv):
    """
    Removes routes which doesn't contain the driver, this function
    also deals with drivers which have multiple instances
    """
    (drv, ext) = self.translateDriver(drv)

    result = []
    for route in routes:
      keep = False
      for d in route:
        if d == drv:
          keep = True
          break
      if keep:
        result.append(route)

    return result
  
  def translateDriver(self, driver):
    """Removes the :xxx from driver"""
    ret = driver.split(":", 1)
    if len(ret) == 1:
      return (ret[0], "")
    else:
      return (ret[0], ":" + ret[1])

  def splitDriver(self, driver):
    """Splits the driver in two if zone is part of it"""
    ret = driver.split(":", 1)
    if len(ret) == 1:
      return (ret[0], "")
    else:
      return (ret[0], ret[1])
      
  def translateRoute(self, zone, route):
    """
    Takes a route and adjusts drivers based on zone, this is needed since some
    drivers support segmentation.
    """
    (adrv, vdrv) = self.getZoneDrivers(zone)
    if not adrv is None:
      (adrv, aext) = self.translateDriver(adrv)
    else:
      aext = ""
    if not vdrv is None:
      (vdrv, vext) = self.translateDriver(vdrv)
    else:
      vext = ""

    result = {}
    for r in route:
      data = route[r]
      if r == adrv:
        r += aext
      elif r == vdrv:
        r += vext
      result[r] = data

    return result

  def checkConflict(self, zone, scene):
    """
    Checks if there is a conflict assigning a scene to a zone.
    This function returns None if there is no conflict.

    A conflict can manifest itself in two ways:

      1. A sharing conflict, meaning that the proposed change will
         mean that one or more zone(s) will use the same source driver.
      2. A exclusive conflict, meaning that the proposed change will
         make the other zones unroutable. This is typically the case
         if a switch is involved, since it cannot send two inputs at
         the same time.

    There are three options:
        - Don't do it
        - Set other zone(s) to same routing
        - Unassign other zones
        
    This function returns None if no conflict exists and an array of zones
    which would be impacted if there is a conflict.
    """
    
    # Get current state and remove our zone
    active = self.getCurrentState()
    active.pop(zone, None)
    
    if len(active) == 0:
      return None
    
    # Now, generate a route based on provided information
    route = self.getCurrentStateForZone(zone, None, scene)
    
    # Find any overlap of drivers
    result = []
    for z in active:
      print "Checking zone " + z
      for d in active[z]:
        if d in route:
          print "Overlap detected"
          result.append(z)
          break
    
    if len(result) > 0:
      return result
    return None
    
  def getDriver(self, driver):
    if driver is None:
      return None
      
    (driver, ignore) = self.translateDriver(driver)
    if not driver in self.DRIVER_TABLE:
      print "ERR: %s is not a driver" % driver
      return None
    return self.DRIVER_TABLE[driver]

from driver_rxv1900 import DriverRXV1900
from driver_spotify import DriverSpotify

class CommandType:
  VOLUME_UP       = 1
  VOLUME_DOWN     = 2
  VOLUME_MUTE     = 3
  VOLUME_UNMUTE   = 4
  VOLUME_SET      = 5   # Takes argument, 0-100 = 0-100% volume, 100-150 = 0-50% above 0dB

  PLAYBACK_PLAY         = 10
  PLAYBACK_PAUSE        = 11 # DOES NOT TOGGLE, PLAYBACK_PLAY must be issued to resume
  PLAYBACK_STOP         = 11
  PLAYBACK_NEXT         = 12 
  PLAYBACK_PREVIOUS     = 13 
  PLAYBACK_CNEXT        = 14 
  PLAYBACK_CPREVIOUS    = 15 
  PLAYBACK_FASTFORWARD  = 16 
  PLAYBACK_REWIND       = 17 

  NAVIGATE_UP           = 20 
  NAVIGATE_DOWN         = 21
  NAVIGATE_LEFT         = 22
  NAVIGATE_RIGHT        = 23
  NAVIGATE_ENTER        = 24
  NAVIGATE_BACK         = 25
  NAVIGATE_HOME         = 26
  NAVIGATE_MENU         = 27
  NAVIGATE_TOPMENU      = 28
  NAVIGATE_PAGEUP       = 29
  NAVIGATE_PAGEDOWN     = 30

class Config:
  """
  Lists and loads the various devices which will be needed by
  the controller.
  """
  DRIVER_TABLE = {
    "receiver"  : DriverRXV1900(),
    "spotify"   : DriverSpotify()
      
  }
  
  """
  This table describes how a scene can be routed to various devices.
  
  The router will use this information to figure out how to connect
  a driver to the requested zone.
  
  The format is:
  <scene driver> : {"audio" : [{<output audio driver> : [<one or more commands to execute>],
                     ...any number of drivers needed with commands...},
                    ...any number of routes...],
                    "video" : [{<output video driver> : [<one or more commands to execute>],
                     ...any number of drivers needed with commands...},
                    ...any number of routes...]}
  
  If a driver does not any special command to work (just power) then it should
  be defined with an empty array (see projector examples).
  
  For example, to connect roku to the TV and receiver, you would call:
    submitRoute("roku", ["tv", "receiver"])
    
  This will cause the router to look up the driver "roku" and inspect
  the available routes, in this particular case, there are three, one for the
  audio and two for the video, but only one of the video routes have the needed
  device in the route. Thus it will be the chosen one. Audio is easy, there's
  only one option and luckily the one we need. Otherwise the zone would not
  get any audio.
  
  If we do this again but for ps4, like so:
    submitRoute("ps4", ["tv", "receiver"])
    
  Again it would lookup the ps4 to get the routes and find that there
  three options, but only one where tv participates.
  But unlike the previous scenario, this route also has a splitter,
  which means that using this route will affect the splitter as well.
  
  If there is multiple matching routes for the scene, the one found first will
  be the route used for that particular path. This is generally not considered
  a normal use-case and as such, this scenario should be avoided.
  
  Adding the actual driver of the scene to the routing table is not needed
  but can be done if it needs special initialization commands.
  
  You never need to worry about power management, that is done by the router
  and is normally not exposed as a command. As long as a driver is needed by
  any zone, it will remain powered on.

  If multiple scenes need to access the same driver and there is a conflict,
  the REST command will fail and require an extra argument to override.
  This is necessary since there essentially are two options:
    1. Shutdown the conflicting zone
    2. Switch conflicting zone into same scene
  """
  ROUTING_TABLE = {
    "spotify" : [
      {"receiver"  : ["input-mdcdr"]},
    ],
    
    "roku"    : [
      {"tv"        : ["input-hdmi1"],
       "receiver"  : ["input-bd"]},
      {"projector" : ["input-hdmi1"],
       "receiver"  : ["input-bd"],
       "screen"    : []}
    ],
    
    "ps4"     : [
      {"receiver"  : ["input-bd"],
       "tv"        : ["input-hdmi1"],
       "splitter"  : ["input-hdmi2"]},
      {"receiver"  : ["input-bd"],
       "projector" : ["input-hdmi1"],
       "splitter"  : ["input-hdmi2"],
       "screen"    : []},
    ],
  }

  """
  Scenes describe what's needed to utilize for example, Spotify.
  
  DRIVER tells us which ... driver to use. But it also allows us to
  detect when there will be a conflict.

  DRIVER-EXTRAS adds a possibility to supply extra details which is handled
  by the driver. Usually a comma separated list of key/value pairs
  
  NAME is the name to show in the display
  
  DESCRIPTION is a longer description (if we need it)
  
  AUDIO if true indicates that this scene provides audio (limits zones)
  
  VIDEO if true indicates that this scene provides video (limits zones)
  
  """
  
  SCENE_TABLE = {
    "spotify" : {
      "driver"      : "spotify",
      "name"        : "Spotify",
      "description" : "Allows you to listen to music (Swedish Spotify)",
      "audio"       : True,
      "video"       : False,
    },
  
    "plex" : {
      "driver"      : "plex",
      "name"        : "Plex Media Center",
      "description" : "Watch movies and TV series",
      "audio"       : True,
      "video"       : True,
    },
    
    "netflix" : {
      "driver"        : "roku",
      "driver-extras" : "app=netflix",
      "name"          : "NetFlix",
      "description"   : "Watch movies and TV series",
      "audio"         : True,
      "video"         : True,
    },
  
    "amazon" : {
      "driver"        : "roku",
      "driver-extras" : "app=amazon",
      "name"          : "Amazon",
      "description"   : "Watch movies and TV series",
      "audio"         : True,
      "video"         : True,
    },
  
    "ps4" : {
      "driver"      : "ps4",
      "name"        : "Playstation 4",
      "description" : "Play games",
      "audio"       : True,
      "video"       : True,
    },
  }
  
  """
  Table describing what the zones are capable of

  name provides a human readable name for the zone
  audio points out the driver handling audio playback
  video points out the driver handling video playback

  video-extra/audio-extra provides a means to provide parameters to the driver
  when the zone is assigned a scene.
  
  For drivers which support zoning (driving more than location), the zone can
  be provided using a colon, like so:
    "receiver:1" for zone 1 or "sonus:livingroom" for livingroom sonus player
  HOWEVER, it does not handle setups where the zones aren't symmetrical, meaning
  that if your driver only supports some inputs for some zones, you're better off
  doing multiple drivers, one for each room, for example:
    "receiver-a" for zone 1, "receiver-b" for zone 2
  Otherwise the logic for doing routing will not be able to make the correct 
  decisions
  
  Either one can be set to None which means it lacks that capability. 
  Do not set both to None since it would make the zone pointless   
  
  A zone can actually be "virtual" in the sense that it provides more than one
  setup to choose from. Selecting this zone will default to either the active 
  sub-zone or the defined default sub-zone (if no subzone was active at the time)
  
  Only one sub-zone can be active at any given time. This is how various 
  scenarios such as setups with TV & Projection in the same room is supported.

  When filtering virtual zones, it will use the combined capabilities of all 
  subzones.
  
  When subzones are used, there is no point in defining a audio/video for the
  zone itself since the subzones are used.
  
  A subzone cannot have have subzones.
  """
  ZONE_TABLE = {
    "zone1" : {
      "name"  : "Livingroom",
      "subzone-default" : "tv",
      "subzones" : {
        "tv" : {
          "name" : "TV",
          "audio" : "receiver:1",
          "video" : "tv",
        },
        "projector" :  {
          "name" : "Cinema",
          "audio" : "receiver:1",
          "video" : "projector",
        }
      }
    },
    "zone2" : {
      "name"  : "Kitchen",
      "audio" : "receiver:2",
      "video" : None,
    },
    "zone3" : {
      "name"  : "Patio",
      "audio" : "receiver:3",
      "video" : None,
    }
  }
  
  """
  Remote configuration
  
  Currently it's a static configuration and it uses basic HTTP authentication
  to avoid "mistakes" by regular browsers. Username is derived from the base
  key and the password is held within.
  
  It also defines the home zone for a remote. The idea is that usually a remote
  will charge in relation to the zone it will control.
  
  This list also holds information needed during runtime which you normally
  do not supply during configuration.
  
  Note!
  Password not yet implemented
  """
  REMOTE_TABLE = {
    "kitchen" : {
      "name"        : "Kitchen",
      "description" : '10" kitchen tablet',
      "zone"        : "zone2",
      "password"    : "secret",
    },
    
    "livingroom" : {
      "name"        : "Livingroom",
      "description" : '7" entertainment phablet',
      "zone"        : "zone1",
      "password"    : "secret",
    }
  }

  def __init__(self):
    """
    At this point, initialize some extra parameters, such as the combined
    capabilties of zones which have sub-zones.
    """
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
        

  def hasScene(self, name):
    """Returns true if scene exists"""
    return name in self.SCENE_TABLE

  def getSceneListForZone(self, zone):
    if not self.hasZone(zone):
      print "%s is not a zone" % zone
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
    print "A = " + repr(includeAudio)
    print "V = " + repr(includeVideo)
    for scene in self.SCENE_TABLE:
      if self.SCENE_TABLE[scene]["video"] and includeVideo == False:
        print "Video but not to be included"
        continue
      if self.SCENE_TABLE[scene]["audio"] and includeAudio == False:
        print "Audio but not to be included"
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
    
    print "WARNING: setZoneScene() has no conflict testing yet!"
    
    if self.SCENE_TABLE[scene]["audio"] and self.ZONE_TABLE[zone]["audio"] == None:
      print "WARN: Zone %s does not support audio which is required by the scene %s" % (zone, scene)
    if self.SCENE_TABLE[scene]["video"] and self.ZONE_TABLE[zone]["video"] == None:
      print "WARN: Zone %s does not support video which is required by the scene %s" % (zone, scene)
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
    """Removes the scene for a zone, including subzones"""
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return False
    self.ZONE_TABLE[zone]["active-scene"] = None
    
    # Subzones...
    if self.hasSubZones(zone) and self.ZONE_TABLE[zone]["active-subzone"] != None:
      self.ZONE_TABLE[zone]["active-subzone"] = None
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
    """This one is special, if a scene is assigned, it will switch to default subzone instead"""
    if not self.hasSubZones(zone):
      print "ERR: %s does not have subzones" % zone
      return False
    if self.getZoneScene(zone) == None:
      self.ZONE_TABLE[zone]["active-subzone"] = None
    else:
      self.ZONE_TABLE[zone]["active-subzone"] = self.ZONE_TABLE[zone]["subzone-default"]
    return True

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
    return []
    
  def getSceneCommands(self, scene):
    return []


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
      return []
    
    result["zone"] = self.getZoneCommands(zname)
    result["scene"] = self.getSceneCommands(sname)
    
    return result
    
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

  def getCurrentStateForZone(self, zone, sceneOverride=None):
    """
    Obtains a route for a zone based on active scene and potentially subzone.
    If provided with a sceneOverride, the active scene is ignored and the
    provided scene will be used instead.
    """
    if not self.hasZone(zone):
      print "ERR: %s is not a zone" % zone
      return None
    if self.ZONE_TABLE[zone]["active-scene"] is None and sceneOverride is None:
      return None

    if sceneOverride is None:      
      s = self.ZONE_TABLE[zone]["active-scene"]
    else:
      s = sceneOverride

    (adrv, vdrv) = self.getZoneDrivers(zone)
    sdrv = self.SCENE_TABLE[s]["driver"]
    
    # Translate into route
    if self.SCENE_TABLE[s]["audio"] and not self.SCENE_TABLE[s]["video"]:
      route = self.resolveRoute(sdrv, adrv)
    elif not self.SCENE_TABLE[s]["audio"] and self.SCENE_TABLE[s]["video"]:
      route = self.resolveRoute(sdrv, vdrv)
    elif self.SCENE_TABLE[s]["audio"] and self.SCENE_TABLE[s]["video"]:
      route = self.resolveRoute(sdrv, adrv, vdrv)
    else:
      print "ERR: Scene has neither audio nor video!"
    return self.translateRoute(zone, route)

  def resolveRoute(self, sdrv, drv, *opt):
    """
    Takes the scene driver and any number of drivers (minimum 1) and returns
    the routing needed to run the scene
    """
    if sdrv not in self.ROUTING_TABLE:
      print "ERR: %s does not have any routing information" % sdrv
      return []
    
    routes = self.filterRoutes(self.ROUTING_TABLE[sdrv], drv)
    for s in opt:
      routes = self.filterRoutes(routes, s)
      
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
        
    This function returns None on no conflict and an array of zones
    which would be impacted if there is a conflict.
    """
    
    # Get current state and remove our zone
    active = self.getCurrentState()
    active.pop(zone, None)
    
    if len(active) == 0:
      return None
    
    # Now, generate a route based on provided information
    route = self.getCurrentStateForZone(zone, scene)
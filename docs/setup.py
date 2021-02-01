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
This class describes your specific setup, it's automatically loaded into the
config.py class which uses this data as it sees fit.

Eventually this file can be generated from a web-ui, but for now you need to
know your python. Sorry :-(
"""
from drivers.rxv1900   import driverRxv1900
from drivers.spotify   import driverSpotify
from drivers.irplus    import driverIrplus
from drivers.plex      import driverPlex
from drivers.keyinput  import driverKeyinput
from drivers.roku      import driverRoku

from drivers.basicir   import driverBasicir
from drivers.null      import driverBase

from parser import setupParser

from commandtype import CommandType

import re
import json

class SystemSetup_DEAD:
  """
  PIN_REMOTE defines a PIN (actually, could be any combination of letters and numbers)
  that must be provided to register new remotes.

  UX-SERVER defines where the clients can download the HTML5 content to run the UX.
  If not defined, defaults to hosting from the controller itself.
  """
  OPTIONS = {
    "pin-remote" : "1234",
    "ux-server" : "http://magi.sfo.sensenet.nu/multiremote-ux/",
    "data-persist" : "persist/",
    "data-config" : "config/",
  }

  """
  Lists and loads the various devices which will be needed by
  the controller.

  If you have most of hosted on one server, it's recommended to use
  a variable to make changes easier (see AV example).
  """
  AV="http://chip-ir.sfo.sensenet.nu"


  DRIVER_TABLE = {
    "receiver"  : driverRxv1900("http://chip-yamaha.sfo.sensenet.nu:5000"),
    "spotify"   : driverSpotify(),
    "splitter"  : driverBasicir(AV + ":5001", "../ir-devices/accessories/sony-hdmiswitch.json"),
    "tv"        : driverBasicir(AV + ":5001", "../ir-devices/displays/lg-55la7400.json"),
    "screen"    : driverBasicir(AV + ":5001", "../ir-devices/accessories/elite_screens-electric100h.json"),
    "projector" : driverIrplus(AV + ":5001", "config/projector.json"),
    "plex"      : driverKeyinput("plex.sfo.sensenet.nu", "00:25:22:e0:94:7d", "eth0"),
    "roku"      : driverRoku("roku-livingroom.sfo.sensenet.nu"),
    "null1"     : driverBase(),
  }

  """
  This table describes how a scene can be routed to various devices.

  The router will use this information to figure out how to connect
  a driver to the requested zone.

  The format is:
  <scene driver> : {"audio" : [{<output audio driver> : [<one or more commands to execute>],
                     ...any number of drivers needed with commands...},
                    ...any number of routes...],
                    "audio+video" : [{<output video driver> : [<one or more commands to execute>],
                     ...any number of drivers needed with commands...},
                    ...any number of routes...]}

  If a driver does not any special command to work (just power) then it should
  be defined with an empty array (see projector examples).

  audio array defines an audio path only, while audio+video defines an path
  which is able to do both video and audio. This is to support different kinds
  of zones. Currently video only zones are not supported.

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
    "chromecast" : {
      "audio" : [{"receiver"  : ["input-mdcdr"]}],
    },

    "plex" : {
      "audio" : [{"receiver"  : ["input-dvr"]}],
      "audio+video" : [
        {"tv"         : ["input-hdmi1"],
         "receiver"   : ["input-dvr"]},
        {"projector"  : [],
         "receiver"   : ["input-dvr"],
         "screen"     : [],
         },
      ]
    },

    "roku"    : {
      "audio+video" : [
        {"tv"        : ["input-hdmi1"],
         "receiver"  : ["input-dvd"]},
        {"projector" : [],
         "receiver"  : ["input-dvd"],
         "screen"    : []}
      ],
      "audio" : [
        {"receiver"  : ["input-dvd"]},
      ],
    },

    "ps4"     : {
      "audio+video" : [
        {"receiver"  : ["input-bd"],
         "tv"        : ["input-hdmi1"]},
        {"receiver"  : ["input-bd"],
         "projector" : [],
         "screen"    : []},
      ],
      "audio" : [
        {"receiver"  : ["input-bd"]},
      ]
    },

    "ps3"     : {
      "audio+video" : [
        {"receiver"  : ["input-cd"],
         "tv"        : ["input-hdmi2"]},
      ],
      "audio" : [
        {"receiver"  : ["input-cd"]},
      ]
    },

    "steamlink"     : {
      "audio+video" : [
        {"receiver"  : ["input-cbl"],
         "tv"        : ["input-hdmi1"]},
        {"receiver"  : ["input-cbl"],
         "projector" : [],
         "screen"    : []},
      ],
      "audio" : [
        {"receiver"  : ["input-cbl"]},
      ]
    },

  }

  """
  Scenes describe what's needed to utilize for example, Spotify.

  DRIVER tells us which ... driver to use. But it also allows us to
  detect when there will be a conflict.

  DRIVER-EXTRAS adds a possibility to supply extra details which is handled
  by the driver. Usually a comma separated list of key/value pairs. Each
  driver will describe it's need of this.

  NAME is the name to show in the display

  DESCRIPTION is a longer description (if we need it)

  AUDIO if true indicates that this scene provides audio (limits zones)

  VIDEO if true indicates that this scene provides video (limits zones)

  UX-HINT provides purely cosmetic information that is exposed to the clients.
  It's a comma separated list of key/value pairs.

  Typically UX-HINT holds:
    android-app: Package name for an android app which allows better control
    category: Imply what this is used for (music, video, gaming, etc...)
    icon: name for an icon to be shown

  """

  SCENE_TABLE = {
    "plex" : {
      "driver"      : "plex",
      "name"        : "Plex Media Center",
      "description" : "Watch movies and TV series",
      "audio"       : True,
      "video"       : True,
      "ux-hint"     : "category=video,icon=plex",
    },

    "netflix" : {
      "driver"        : "roku",
      "driver-extras" : "app=netflix",
      "name"          : "NetFlix",
      "description"   : "Watch movies and TV series",
      "audio"         : True,
      "video"         : True,
      "ux-hint"       : "category=video,icon=netflix",
    },

    "amazon" : {
      "driver"        : "roku",
      "driver-extras" : "app=amazon",
      "name"          : "Amazon Prime",
      "description"   : "Watch movies and TV series",
      "audio"         : True,
      "video"         : True,
      "ux-hint"       : "category=video,icon=amazon",
    },

    "ps4" : {
      "driver"      : "ps4",
      "name"        : "Playstation 4",
      "description" : "Play games",
      "audio"       : True,
      "video"       : True,
      "ux-hint"     : "category=gaming,icon=ps4",
    },

    "ps3" : {
      "driver"      : "ps3",
      "name"        : "Playstation 3",
      "description" : "Play games",
      "audio"       : True,
      "video"       : True,
      "ux-hint"     : "category=gaming,icon=ps3",
    },

    "steamlink" : {
      "driver"      : "steamlink",
      "name"        : "SteamLink",
      "description" : "Play games",
      "audio"       : True,
      "video"       : True,
      "ux-hint"     : "category=gaming,icon=steamlink",
    },

    "chromecast" : {
      "driver"      : "chromecast",
      "name"        : "Chromecast",
      "description" : "Listen to music",
      "audio"       : True,
      "video"       : False,
      "ux-hint"     : "category=music,icon=chromecast,apps=com.spotify.music:tunein.player:radiotime.player:com.pandora.android,message=Connect to \"HomeTheater\" to play here",
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
          "ux-hint" : "",
        },
        "projector" :  {
          "name" : "Cinema",
          "audio" : "receiver:1",
          "video" : "projector",
          "ux-hint" : "",
        }
      },
      "ux-hint" : "",
    },
    "zone2" : {
      "name"  : "Kitchen",
      "audio" : "receiver:2",
      "video" : None,
      "ux-hint" : "",
    },
    "zone3" : {
      "name"  : "Patio",
      "audio" : "receiver:3",
      "video" : None,
      "ux-hint" : "",
    }
  }



if __name__ == "__main__":
  # Let's see if we can parse the config
  setup2 = {}
  parser = setupParser()
  parser.load("setup.conf", setup2)
  #print json.dumps(setup2["ROUTING_TABLE"], indent=2)
  print(repr(setup2["DRIVER_TABLE"]))

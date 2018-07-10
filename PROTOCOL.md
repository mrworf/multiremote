CommandTypes.py is misleading, it's essentially events being issued

Do not use numbers, use namespaces

flag.hidden  = Do not expose to remotes
flag.persist = The last event with a flag like this is saved and reissued to remotes joining the zone as long as scene or zone doesn't change

Events:
volume.* all trigger zone.volume.state
volume.up     = Increase volume
volume.down   = Decrease volume
volume.mute   = Mutes zone
volume.unmute = Unmutes zone
volume.set    = Sets the volume, arg: {"level" : 0-150} (0-100 is normal levels, 100-150 is 0dB and up)

playback.* : Several events have results, but they are all optional, since there is no guarantee that a driver can support the state information

playback.play             = Play result: {"playback" : "playing"}
playback.stop             = Stop result: {"playback" : "stopped"}
playback.pause            = Pause result: {"playback" : "paused"}
playback.playpause        = Toggle pause result: {"playback" : "playing/paused"}
playback.next             = Next
playback.previous         = Previous
playback.chapter.next     = Next chapter
playback.chapter.previous = Previous chapter
playback.forward          = Fast Forward
playback.rewind           = Rewind
playback.skip.forward     = Skips forward arg {"step" : <seconds> } result: {"step" : <seconds>} (depending on driver, may round off to nearest supported)
playback.skip.backward    = Skips backward arg {"step" : <seconds> } result: {"step" : <seconds>}  (depending on driver, may round off to nearest supported)
playback.track.audio      = Changes audio track result: {"track" : X, "total" : Y}
playback.track.subtitle   = Changes subtitle track result: {"track" : X, "total" : Y}
playback.track.video      = Changes video track (think multi angle) result: {"track" : X, "total" : Y}
playback.mode.shuffle     = Toggles shuffle mode result: {"shuffle" : "all/off"} 
playback.mode.repeat      = Toggles repeat mode result: {"repeat" : "all/current/off"}
playback.mode.osd         = Toggles OSD result: {"osd" : "visible/hidden"} 
playback.eject            = Usually physical media, ejects the disc

navigate.up
navigate.down
navigate.left
navigate.right
navigate.back
navigate.home
navigate.select
navigate.menu
navigate.topmenu
navigate.page.up
navigate.page.down
navigate.input.text

## Following section of events are typically unsolicited

media.info.* : All use the same result structure to make it easier to process

media.info.source  = This can be many different things, and even change during one scene when using chromecast
media.info.artist  = Artist information result: {"current" : "..."}
media.info.album   = Album information result: {"current" : "..."}
media.info.track.name
media.info.track.artist (since a track on an album can have a different artist)

media.art.* : All use the same result structure and will reference a HTTP/HTTPS resource with an image to show
media.art.album = Album cover result: {"url" : "http..."}
media.art.artist
media.art.track

media.time = Details about length of media as well as current state result: {"total" : time-in-sec, "current" : time-in-sec, "server" : sec since Jan 1st 1970 UTC}

# Issuing commands:

POST /command/<remote id>/<scope>/<command>

remote id= Registered remote's ID
scope = zone or scene command
command = the unique id of the command

If command takes any arguments, it's provided as JSON data with key/value pairs.

Core: Command list (driver provides this to multiRemote):
{
  unique-identifier : {
    "type" : "kind of command based on CommandType.py",
    "flags" : [flag, flag, ...] (can be empty array)
  },
  ...
}

Remote: Commands list
{
  unique-identifier : {
    "type" : "kind of command based on CommandType.py",
  },
  ...
}

All commands return the following:

{
  "status" : "OK|Error",
  "details" : "msg or empty"
  "result" : {} (key value pairs or just empty in most cases) 
}

## unsolicited information:

From clients:

SUBSCRIBE <namespace>

Namespace uses wildcards to allow different parts to be subscribed to, for example:
SUBSCRIBE * (gets all)
SUBSCRIBE zone.* (only zone)
SUBSCRIBE scene.event.unsolicited (very specific)

A remote may issue multiple subscribe calls but they're all merged, so multiple calls with the same namespace will not result in duplicate messages.

From server, all messages are sent as JSON:

standard header for all messages:
{
  "namespace" : <see below>
  "destination" : "which zone this relates to", (provided to avoid race-conditions where remote is in the process of switching away from a zone)
  "source" : "remote id or blank if no remote is the cause",
  "data" : <message>
}

zone.* - All connected remotes get these messages
  zone.state - Zone in use or not
    {
      "inuse" : True/False  # Indicates that zone is busy or not
    }
  zone.state.subzone 
    {
      "id" : <id of subzone>
    }
  zone.volume.state - Volume state change
    {
      "level" : 0-150,
      "muted" : True/False,
    }

scene.* - Only remotes in the related zone will receive these messages, so a remote in zone1 will not get scene messages for zone2
  scene.state - Scene is assigned or unassigned
    {
      "scene": "Scene ID or blank if no scene" 
    }
  scene.event.result - The result of an issued command (this may seem duplicated, but allows remotes to sync changes)
    {
      "id" : command identifier,
      "type" : kind of event,
      "result" : {} (same as when doing POST)
    }
  scene.event.unsolicited - Almost the same as result, but this isn't originating from a remote, this most likely is the cause of a scene driver
    {
      "type" : kind of event,
      "result" : {} (same as when doing POST)
    }

# Remote debugging

As in allowing remotes signed into the system submit logging to the backend so it's easier analyzed

It uses the same side-channel as SUBSCRIBE, the clients simply issue:

LOG <any data>

The any data is truly anything the client wishes to log. It is recommended to stick to printable characters and NO \n or \r
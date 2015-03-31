class CommandType:
  VOLUME_UP       = 1
  VOLUME_DOWN     = 2
  VOLUME_MUTE     = 3
  VOLUME_UNMUTE   = 4
  VOLUME_SET      = 5   # Takes argument, 0-100 = 0-100% volume, 100-150 = 0-50% above 0dB

  PLAYBACK_PLAY           = 100
  PLAYBACK_PAUSE          = 101
  PLAYBACK_STOP           = 102
  PLAYBACK_NEXT           = 103 
  PLAYBACK_PREVIOUS       = 104 
  PLAYBACK_CNEXT          = 105 
  PLAYBACK_CPREVIOUS      = 106 
  PLAYBACK_FASTFORWARD    = 107 
  PLAYBACK_REWIND         = 108

  PLAYBACK_SKIP_FORWARD   = 109 # Usually 15s
  PLAYBACK_SKIP_BACKWARD  = 110 # Usually 15s
  PLAYBACK_LSKIP_FORWARD  = 111 # Usually 30s
  PLAYBACK_LSKIP_BACKWARD = 112 # Usually 30s

  PLAYBACK_STREAM         = 113
  PLAYBACK_AUDIO          = 114
  PLAYBACK_SUBTITLE       = 115

  PLAYBACK_SHUFFLE        = 116
  PLAYBACK_REPEAT         = 117

  PLAYBACK_OSD            = 118
  PLAYBACK_ANGLE          = 119
  PLAYBACK_EJECT          = 120

  NAVIGATE_UP           = 200 
  NAVIGATE_DOWN         = 201
  NAVIGATE_LEFT         = 202
  NAVIGATE_RIGHT        = 203
  NAVIGATE_ENTER        = 204
  NAVIGATE_BACK         = 205
  NAVIGATE_HOME         = 206
  NAVIGATE_MENU         = 207
  NAVIGATE_TOPMENU      = 208
  NAVIGATE_PAGEUP       = 209
  NAVIGATE_PAGEDOWN     = 210

  LIMIT_GETCOMMANDS     = 499 # The maximum allowed exposed command through getCommands()
  """
  The following section details commands which should not be exposed to the
  end-user but provides info to the UX. Some of them may not always return
  any data to the caller, which is VALID.
  """
  GET_VOLUME            = 500 # (int)    Volume level in percentage, range 0-150
  GET_MUTE              = 501 # (bool)   State of mute, True = mute
  GET_TITLE             = 502 # (string) Title of what's going on
  GET_ALBUM             = 503 # (string) Album of what's going on
  GET_ARTIST            = 504 # (string) Artist of what's going on
  GET_TRACKID           = 505 # (int)    Track Id of what's going on
  GET_TIME_ELAPSED      = 506 # (int)    Seconds since start of activity
  GET_TIME_REMAIN       = 507 # (int)    Seconds to end of activity

  # Private commands aren't meant to be exposed to end-user
  PRIVATE_INPUT         = 900
  PRIVATE_ON            = 901
  PRIVATE_OFF           = 902
  PRIVATE_ONOFF_TOGGLE  = 903

  # Undefined should NEVER be used, but are handy for automatic prefill
  PRIVATE_UNDEFINED     = 10000

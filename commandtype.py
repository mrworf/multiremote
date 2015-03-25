class CommandType:
  VOLUME_UP       = 1
  VOLUME_DOWN     = 2
  VOLUME_MUTE     = 3
  VOLUME_UNMUTE   = 4
  VOLUME_SET      = 5   # Takes argument, 0-100 = 0-100% volume, 100-150 = 0-50% above 0dB

  PLAYBACK_PLAY           = 100
  PLAYBACK_PAUSE          = 101
  PLAYBACK_STOP           = 101
  PLAYBACK_NEXT           = 102 
  PLAYBACK_PREVIOUS       = 103 
  PLAYBACK_CNEXT          = 104 
  PLAYBACK_CPREVIOUS      = 105 
  PLAYBACK_FASTFORWARD    = 106 
  PLAYBACK_REWIND         = 107

  PLAYBACK_SKIP_FORWARD   = 108 # Usually 15s
  PLAYBACK_SKIP_BACKWARD  = 109 # Usually 15s
  PLAYBACK_LSKIP_FORWARD  = 110 # Usually 30s
  PLAYBACK_LSKIP_BACKWARD = 111 # Usually 30s

  PLAYBACK_STREAM         = 112
  PLAYBACK_AUDIO          = 113
  PLAYBACK_SUBTITLE       = 114

  PLAYBACK_SHUFFLE        = 115
  PLAYBACK_REPEAT         = 116

  PLAYBACK_OSD            = 117

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

  # Private commands aren't meant to be exposed to end-user
  PRIVATE_INPUT         = 900

  # Undefined should NEVER be used, but are handy for automatic prefill
  PRIVATE_UNDEFINED     = 10000

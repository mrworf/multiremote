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

  # Private commands aren't meant to be exposed to end-user
  PRIVATE_INPUT         = 100

  # Undefined should NEVER be used, but are handy for automatic prefill
  PRIVATE_UNDEFINED     = 10000
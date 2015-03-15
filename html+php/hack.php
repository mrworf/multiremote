<?php

  $remote = "kitchen";
  $name = "Kitchen";
  $homezone = "zone2";
  switch ($_SERVER["REMOTE_ADDR"]) {
    case "10.0.3.104":
      $remote = "livingroom";
      $name = "Livingroom";
      $homezone = "zone1";
      break;
  }

?>
<html>
  <head>
    <link rel="stylesheet" type="text/css" href="jquery-ui.min.css">
    <link rel="stylesheet" type="text/css" href="hack.css">
    <script src="jquery2.min.js" type="text/javascript"></script>
    <script src="jquery-ui.min.js" type="text/javascript"></script>
    <script type="text/javascript">
      <!-- This will move away as soon as settings is implemented -->
      var baseURL = "http://" + window.location.hostname + ":5000";
      var remote = "<?php print($remote); ?>"
      var homezone = "<?php print($homezone); ?>"
    </script>    
    <script src="hack.js" type="text/javascript"></script>
  </style>
  <body>
    <div style="display: none">
        <input id="template-zonebtn" type="button"/>
        <input id="template-scenebtn" type="button"/>
    </div>
    <div id="dialog-conflict" title="Conflict" style="display: none">
      <p>
        Selecting SCENE would interfer with another user in ZONE.
      </p>
      <p>
        How would you like to resolve this?
      </p>
    </div>

    <h1>multiREMOTE - <?php print($name); ?></h1>
    <div class="volume-ctrl">
      <input id="mute" type="button" onclick="toggleMute()" value="Mute"/>
      <input id="voldown" type="button" onclick="remoteVolumeDown()" value="Volume Down"/>
      <input id="volup" type="button" onclick="remoteVolumeUp()" value="Volume Up"/>
      <input style="text-align: center; width: 41pt; margin-right: 0px" type="text" id="volume" value="0"/>
      <input style="width: 41pt; margin-left: 0px" onclick="setVolume()" type="button" value="Set"/>
    </div>
    <div id="zones"></div>
    <hr/>
    <div id="scenes"></div>
    <div id="controls"></div>
  </body>
</html>

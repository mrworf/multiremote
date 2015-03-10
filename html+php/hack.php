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
  <script type="text/javascript">
    var baseURL = "http://magi.sfo.sensenet.nu:5000";
    var remote = "<?php print($remote); ?>"
    var homezone = "<?php print($homezone); ?>"
    
    function remoteAssign(zone, scene) {
      var url = baseURL + "/assign/" + zone + "/" + scene;
      executeURL(url);
    }
    
    function remoteUnassign(zone) {
      var url = baseURL + "/unassign/" + zone;
      executeURL(url);
    }
    
    function remoteAttach(scene) {
      var url = baseURL + "/attach/" + remote + "/" + scene;
      executeURL(url);
    }

    function remoteDetach() {
      var url = baseURL + "/detach/" + remote;
      executeURL(url);
    }
    
    function remoteSetVolume(value) {
      var url = baseURL + "/command/" + remote + "/zone/volume-set/" + value;
      executeURL(url);
    }

    function remoteVolumeUp() {
      var url = baseURL + "/command/" + remote + "/zone/volume-up";
      executeURL(url);
    }

    function remoteVolumeDown() {
      var url = baseURL + "/command/" + remote + "/zone/volume-down";
      executeURL(url);
    }

    function toggleMute() {
      var obj = document.getElementById("mute");
      if (obj.value == "Mute") {
        remoteMute(remote);
        obj.value = "Unmute";
      } else {
        remoteUnmute(remote);
        obj.value = "Mute";
      }
    }

    function remoteMute() {
      var url = baseURL + "/command/" + remote + "/volume-mute";
      executeURL(url);
    }
    
    function remoteUnmute() {
      var url = baseURL + "/command/" + remote + "/volume-unmute";
      executeURL(url);
    }
    
    function executeURL(url) {
      var obj = document.getElementById("result");
      obj.src = url;
    }
    
    var oldActive = null;
    
    function setVolume() {
      volume = document.getElementById("volume").value;
      remoteSetVolume(volume)
    }
    
    function setActive(obj, scene) {
      remoteAttach(scene);
      if (oldActive != null)
        oldActive.style.background = "#ffffff";
      
      obj.style.background = "#8888ff";
      oldActive = obj;
    }
  </script>
  <style type="text/css">
    div.zone {
      border: none; 
      width: 300pt;
      display: inline-block;
      vertical-align: top;
    }
    
    div.volume-ctrl {
      border: inset 2px;
      width: 95pt;
      display: inline-block;
    }

    div.zone-control {
      border-top: 1px solid;
    }
    
    div.zone-hdr {
      text-align: center;
      border-bottom: 1px solid;
      font-size: 18pt;
    }
    
    input {
      width: 85pt;
      height: 30pt;
      margin: 5pt;
    }
    
  </style>
  <body>
    <h1>multiREMOTE - <?php print($name); ?></h1>
    <div class="volume-ctrl">
      <input id="mute" type="button" onclick="toggleMute()" value="Mute"/>
      <input id="voldown" type="button" onclick="remoteVolumeDown()" value="Volume Down"/>
      <input id="volup" type="button" onclick="remoteVolumeUp()" value="Volume Up"/>
      <input style="text-align: center; width: 41pt; margin-right: 0px" type="text" id="volume" value="0"/>
      <input style="width: 41pt; margin-left: 0px" onclick="setVolume()" type="button" value="Set"/>
    </div>
    <div class="zone" id="zone2">
      <div class="zone-hdr">
        <input id="remote-kitchen" type="button" onclick="setActive(this, 'zone2')" value="Kitchen"/>
      </div>
      <input id="zone2-spotify" type="button" onclick="remoteAssign('zone2', 'spotify')" value="Spotify">
      <input id="zone2-off" type="button" onclick="remoteUnassign('zone2')" value="- Power Off -">
    </div>
    <div class="zone" id="zone1">
      <div class="zone-hdr">
        <input id="remote-livingroom" type="button" onclick="setActive(this, 'zone1')" value="Livingroom"/>
      </div>
      <input id="zone1-spotify" type="button" onclick="remoteAssign('zone1', 'spotify')" value="Spotify">
      <input id="zone1-plex" type="button" onclick="remoteAssign('zone1', 'plex')" value="Plex">
      <input id="zone1-netflix" type="button" onclick="remoteAssign('zone1', 'netflix')" value="Netflix">
      <input id="zone1-amazon" type="button" onclick="remoteAssign('zone1', 'amazon')" value="Amazon">
      <input id="zone1-off" type="button" onclick="remoteUnassign('zone1')" value="- Power Off -">
    </div>
    <hr>
    <iframe id="result" style="width: 100%">Data will come here</iframe>
    <script type="text/javascript">
      obj = document.getElementById("remote-" + remote);
      setActive(obj, homezone);
    </script>
  </body>
</html>

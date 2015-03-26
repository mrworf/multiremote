var zoneList = [];
var activeZone = null;

var cfg_baseURL = null;
var cfg_name = null;
var cfg_home = null;
var cfg_id = null;

// Holds the list of zones
var cfg_zones = null;

// Holds the list of scenes
var cfg_scenes = null;

function execServer(addr, successFunc, sync = false) {
  console.log("execServer(" + addr + ")");
  $.ajax({ 
    url: cfg_baseURL + addr,
    type: "GET",
    async: !sync,
    success: successFunc,
    error: function(obj, info, t) {
      alert("Failed to execute request due to:\n" + info );
    }
  });
}

function remoteAssign(scene) {
  execServer("/assign/" + zone + "/" + scene, function(data) {
    if (data["active"] != null) {
      setSceneActive(data["zone"], data["active"]);
    } else {
    }
  });
}

function remoteSetVolume(value) {
  execServer("/command/" + cfg_id + "/zone/volume-set/" + value, null);
}

function remoteVolumeUp() {
  execServer("/command/" + cfg_id + "/zone/volume-up", null);
}

function remoteVolumeDown() {
  execServer("/command/" + cfg_id + "/zone/volume-down", null);
}

function toggleMute() {
  var obj = document.getElementById("mute");
  if (obj.value == "Mute") {
    remoteMute(cfg_id);
    obj.value = "Unmute";
  } else {
    remoteUnmute(cfg_id);
    obj.value = "Mute";
  }
}

function remoteMute() {
  execServer("/command/" + cfg_id + "/zone/volume-mute", null);
}

function remoteUnmute() {
  execServer("/command/" + cfg_id + "/zone/volume-unmute", null);
}

function setVolume() {
  volume = document.getElementById("volume").value;
  remoteSetVolume(volume)
}

function setActiveScene(data, reqScene) {
  if (reqScene == "standby") {
    // Special case, standby does not generate any results...
    scenes = $("#scenes").children();
    for (var i = scenes.length - 1; i >= 0; i--) {
      if (scenes[i].id == "standby") {
        $("#" + scenes[i].id).addClass("active-scene");
      } else {
        $("#" + scenes[i].id).removeClass("active-scene");
      }
    };

    return;
  }

  // Check that it was a success
  which = data["active"]
  if (data["conflict"] == null) {
    scenes = $("#scenes").children();
    for (var i = scenes.length - 1; i >= 0; i--) {
      if (scenes[i].id == which) {
        $("#" + scenes[i].id).addClass("active-scene");
      } else {
        $("#" + scenes[i].id).removeClass("active-scene");
      }
    };

    // We need to load up available commands now
    execServer("/command/" + cfg_id, function(data){
      populateCommands(data);
    });

  } else {
    showConflictInfo(data["conflict"], reqScene);
  }
}

function showConflictDialog(details, reqScene) {
    scene = cfg_scenes[reqScene]["name"];
    zones = "";
    scenes = "";
    differs = false;

    for (detail in details) {
      zones += " and " + detail;
      if (scenes.indexOf(" and " + details[detail]) == -1)
        scenes += " and " + details[detail];
      if (details[detail] != scene)
        differs = true;
    }
    zones = zones.substring(5);
    scenes = scenes.substring(5);

    str_they = "they are";
    str_are = "are";

    if (Object.keys(details).length == 1) {
      str_they = "it's";
      str_are = "is";
    }

    /* We really should detect what the user is doing, setting the same scene should have a different warning */
    var str_clone;
    var str_unassign;

    if (differs) {
      $("#conflict-text").text("Selecting " + scene + " will cause problems for " + zones + " since " + str_they + " using " + scenes);
      str_clone = "Play " + scene + " in " + zones + " as well";
      str_unassign = "Place " + zones + " in standby and play here only";
    } else {
      $("#conflict-text").text(zones + " " + str_are + " already playing " + scene);
      str_clone = "Play " + scene + " here as well";
      str_unassign = "Place " + zones + " in standby and play " + scene + " here only";
    }

    buttons = {};
    buttons[str_clone] = function() { 
          $(this).dialog("close"); 
          execServer("/assign/" + activeZone + "/" + reqScene + "/clone", function(data){
            setActiveScene(data, reqScene);
          });
        };
    buttons[str_unassign] = function() { 
          $(this).dialog("close"); 
          execServer("/assign/" + activeZone + "/" + reqScene + "/unassign", function(data){
            setActiveScene(data, reqScene);
          });
        };
    buttons["Cancel"] = function() { $(this).dialog("close"); };

    $("#dialog-conflict").dialog({
      modal: true,
      resizable: false,
      width: "30%",
      dialogClass: "dlg-no-title",
      buttons: buttons
    });

}

/**
 * Takes an array of zone(s) and the requested scene which is causing a conflict
 * and translates the zones into human-readble information in the terms of
 *   <zone name>:<current scene name>
 * and then calls showConflictDialog() to request the user to take action.
 */
function showConflictInfo(zones, reqScene) {
  result = [];
  execServer("/zone", function(data) {
    cfg_zones = data;
    for (var i = 0; i != zones.length; ++i) {
      zone = zones[i];
      if (data.hasOwnProperty(zone)) {
        result[cfg_zones[zone]["name"]] = cfg_scenes[cfg_zones[zone]["scene"]]["name"];
      }
    }

    showConflictDialog(result, reqScene);
  });
}

function setActiveZone(data) {
  which = data["active"];

  if (which == activeZone)
    return;

  for (var i = zoneList.length - 1; i >= 0; i--) {
    zone = zoneList[i];
    if (zone == which) {
      $("#" + zone).addClass("active-zone");
      activeZone = which;
      populateScenes(which);
    } else {
      $("#" + zone).removeClass("active-zone");
    }
  };
}

function addZone(data) {
  // For prosperity
  zoneList.push(data["zone"]);

  // Clone our nice design
  tmpl = $("#template-zonebtn").clone().prop("id", data["zone"]);
  tmpl.attr("value", data["name"]);
  tmpl.on("click", function() {
    z = $(this).prop("id");
    execServer("/attach/" + cfg_id + "/" + z, function(data){
        setActiveZone(data);
      });
  });

  // Inject
  $("#zones").append(tmpl);
}

function addScene(zone, data, active) {
  // Clone our nice design
  tmpl = $("#template-scenebtn").clone().prop("id", data["scene"]);
  tmpl.attr("value", data["name"]);

  if (data["scene"] == active) {
    tmpl.addClass("active-scene");
  }

  tmpl.on("click", function() {
    s = $(this).prop("id");
    execServer("/assign/" + zone + "/" + s, function(data){
        setActiveScene(data, s);
      });
  });

  // Inject
  $("#scenes").append(tmpl);
}

function addPowerOff(zone, standby) {
  // Clone our nice design
  tmpl = $("#template-scenebtn").clone().prop("id", "standby");
  tmpl.attr("value", "Standby");

  if (standby) {
    tmpl.addClass("active-scene");
  }

  tmpl.on("click", function() {
    s = $(this).prop("id");
    execServer("/unassign/" + zone, function(data){
        setActiveScene(data, s);
      });
  });

  // Inject
  $("#scenes").append(tmpl);
}


function populateScenes(zone) {
  // First, clear out existing
  $("#scenes").empty();

  // Query and react
  execServer("/assign/" + zone, function(data1) {
    // Add the power-off scene
    addPowerOff(zone, data1["active"] == null);
    execServer("/scene", function(data2) {
      cfg_scenes = data2;

      for (var i = 0; i < data1["scenes"].length; i++) {
        addScene(zone, data2[data1["scenes"][i]], data1["active"]);
      }
    });
  });

}

function populateZones() {
  execServer("/zone", function(data) {
  	cfg_zones = data;
    for (var key in data) {
      if (data.hasOwnProperty(key)) {
        addZone(data[key]);
      }
    };
  });
}

function addCommand(id, name, type) {
  // Clone our nice design
  tmpl = $("#template-commandbtn").clone().prop("id", id);
  tmpl.attr("value", name);

  tmpl.on("click", function() {
    c = $(this).prop("id");
    execServer("/command/" + cfg_id + "/scene/" + c, null);
  });

  // Inject
  $("#commands").append(tmpl);
}


function populateCommands(data) {
  $("#commands").empty();
  if (data["commands"] != null && data["commands"]["scene"] != null) {
    data = data["commands"]["scene"]
    for (var key in data) {
      if (data.hasOwnProperty(key)) {
        addCommand(key, data[key]["name"], data[key]["type"]);
      }
    }
  }
}

$( function() {
  cfg_name = $.jStorage.get("cfg-name");
  cfg_id = $.jStorage.get("cfg-id");
  cfg_home = $.jStorage.get("cfg-home");
  cfg_baseURL = "http://" + window.location.hostname + ":5000";

  if (cfg_name == null || cfg_home == null || cfg_id == null) {
    window.location = "settings.html";
    return;
  }

  $("#remote-name").text(cfg_name);

  // prep our dialog
  populateZones();
})

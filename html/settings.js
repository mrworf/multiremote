var zoneList = [];
var activeZone = null;

var baseURL = null;
var remote = null;
var homezone = null;

function execServer(addr, successFunc) {
  console.log("execServer(" + addr + ")");
  $.ajax({ 
    url: baseURL + addr,
    type: "GET",
    success: successFunc,
    error: function(obj, info, t) {
      alert("Failed to execute request due to:\n" + info );
    }
  });
}

$( function() {
  cfg_name = $.jStorage.get("cfg-name");
  cfg_id   = $.jStorage.get("cfg-id");
  cfg_home = $.jStorage.get("cfg-home");
  baseURL = "http://" + window.location.hostname + ":5000";

  $("#cfg-name").val(cfg_name);
  $("#cfg-id").val(cfg_id);
  $("#cfg-home").val(cfg_home);

  $("#save").click(function(){
    $.jStorage.set("cfg-name", $("#cfg-name").val());
    $.jStorage.set("cfg-id", $("#cfg-id").val());
    $.jStorage.set("cfg-home", $("#cfg-home").val());

    if (
      $("#cfg-name").val() != "" &&
      $("#cfg-id").val() != "" &&
      $("#cfg-home").val() != ""
    ) {
      window.location = "hack.php";
      return;
    }
  });
})

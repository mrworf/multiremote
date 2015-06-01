/**
 * This file is part of multiRemote.
 * 
 * multiRemote is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 2 of the License, or
 * (at your option) any later version.
 * 
 * multiRemote is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with multiRemote.  If not, see <http://www.gnu.org/licenses/>.
 *  
 */
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
      window.location = "client.html";
      return;
    }
  });
})

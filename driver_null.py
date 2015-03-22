"""
Dumbest driver of all, provides logic for power handling which is the bare
necessities which a driver MUST have.
"""
class DriverNull:
  def __init__(self):
    # Dumbest driver there is
    self.power = False
    self.COMMAND_HANDLER = {}
  

  def setPower(self, enable):
    if self.power == enable:
      return True
    self.power = enable
    return True

  def handleCommand(self, zone, command, argument):
    if command not in self.COMMAND_HANDLER:
      print "ERR: %s is not a supported command" % command
      return False
      
    item = self.COMMAND_HANDLER[command]
    print repr(item)
    if item["arguments"] == 0:
      if "extras" in item:
        item["handler"](zone, item["extras"])
      else:
        item["handler"](zone)
    elif item["arguments"] == 1:
      if "extras" in item:
        item["handler"](zone, args[0], item["extras"])
      else:
        item["handler"](zone, args[0])
    return True    
  
  def getCommands(self):
    ret = {}
    for c in self.COMMAND_HANDLER:
      ret[c] = {"name": "", "description": ""}
      if "name" in self.COMMAND_HANDLER[c]:
        ret[c]["name"] = self.COMMAND_HANDLER[c]["name"]
      if "description" in self.COMMAND_HANDLER[c]:
        ret[c]["description"] = self.COMMAND_HANDLER[c]["description"]
      ret[c]["type"] = self.COMMAND_HANDLER[c]["type"]
    return ret  

  def addCommand(self, command, cmdtype, handler, name = None, desc = None):
    if name == None:
      name = command
    if desc == None:
      desc = name
    self.COMMAND_HANDLER[command] = {
      "arguments"   : 0, 
      "handler"     : handler,
      "name"        : name,
      "description" : desc,
      "type"        : cmdtype
    }

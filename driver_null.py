"""
Dumbest driver of all, provides logic for power handling which is the bare
necessities which a driver MUST have.
"""
class DriverNull:
  power = False
  commands = []
  
  def __init__(self):
    # Dumbest driver there is
    self.commands.append(["power-on", "power-off"])

  def setPower(self, enable):
    if self.power == enable:
      return True
    self.power = enable
    return True

  def handleCommand(self, command, argument):
    if command == "power-on":
      self.setPower(True)
    elif command == "power-off":
      self.setPower(False)
    else:
      return False
    return True
  
  def getCommands(self):
    return self.commands
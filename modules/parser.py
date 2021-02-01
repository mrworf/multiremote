import re
import importlib
import logging

class SetupParser:
  def __init__(self):
    pass

  def handleOptions(self, config, line, temp):
    valid = {
      'options' : 'options',
      'remote pin ([0-9]+)' : 'pin',
      'ux server (https?://[a-zA-Z\.:0-9\-/]+)' : 'ux',
    }
    result = self.findEntry(line, valid)
    if result is None:
      return False
    (key, m) = result
    value = valid[key]
    if value == 'options':
      pass
    elif value == 'pin':
      config['OPTIONS']['pin-remote'] = m[0]
    elif value == 'ux':
      config['OPTIONS']['ux-server'] = m[0]
    else:
      return False

    return True

  def handleDevice(self, config, line, temp):
    valid = {
      'device ([a-zA-Z0-9]+)' : 'device',
      'has ([1-9][0-9]*) zones' : 'zones',
      'uses driver ([a-zA-Z0-9]+)' : 'uses-noargs',
      'uses driver ([a-zA-Z0-9]+) with options (.*)' : 'uses-args',
      'path (audio|video|audio\+video|video\+audio) requires (.+)' : 'path'
    }
    result = self.findEntry(line, valid)
    if result is None:
      return False
    (key, m) = result
    value = valid[key]
    if value == 'device':
      temp['device'] = {'name' : m[0]}
      #config['DRIVER_TABLE'][temp['device']['name']] = None
    elif 'device' not in temp:
      return False
    elif value == 'uses-noargs':
      config['DRIVER_TABLE'][temp['device']['name']] = {m[0].lower() : []}
    elif value == 'uses-args':
      config['DRIVER_TABLE'][temp['device']['name']] = {m[0].lower() : self.parseStringArguments(m[1])}
    elif value == 'zones': # Not used for now
      pass
    elif value == 'path':
      dev = temp['device']['name']
      if dev not in config['ROUTING_TABLE']:
        config['ROUTING_TABLE'][dev] = {}
      if m[0] not in config['ROUTING_TABLE'][dev]:
        config['ROUTING_TABLE'][dev][m[0]] = [self.parsePathArguments(m[1])]
      else:
        config['ROUTING_TABLE'][dev][m[0]].append(self.parsePathArguments(m[1]))
    else:
      return False
    return True

  def handleScene(self, config, line, temp):
    valid = {
      'scene ([a-zA-Z0-9]+) ?: ?(.+)' : 'name',
      'uses device ([a-zA-Z0-9]+)' : 'uses-noargs',
      'uses device ([a-zA-Z0-9]+) with options (.*)' : 'uses-args',
      'described as (.+)' : 'desc',
      'requires (audio|video|video\+audio|audio\+video)' : 'requires',
      'hint ux (.+)' : 'hint'
    }
    result = self.findEntry(line, valid)
    if result is None:
      return False
    (key, m) = result
    value = valid[key]
    if value == "name":
      temp['scene'] = {'name' : m[0]}
      config['SCENE_TABLE'][temp['scene']['name']] = {'name' : m[1]}
    elif 'name' not in temp['scene']:
      return False
    elif value == 'uses-noargs':
      config['SCENE_TABLE'][temp['scene']['name']]['driver'] = m[0]
    elif value == 'uses-args':
      config['SCENE_TABLE'][temp['scene']['name']]['driver'] = m[0]
      config['SCENE_TABLE'][temp['scene']['name']]['driver-extras'] = m[1]
    elif value == 'desc':
      config['SCENE_TABLE'][temp['scene']['name']]['description'] = m[0]
    elif value == 'requires':
      if m[0] == "video":
        config['SCENE_TABLE'][temp['scene']['name']]['audio'] = False
        config['SCENE_TABLE'][temp['scene']['name']]['video'] = True
      elif m[0] == "audio":
        config['SCENE_TABLE'][temp['scene']['name']]['audio'] = True
        config['SCENE_TABLE'][temp['scene']['name']]['video'] = False
      elif m[0] == "video+audio" or m[0] == 'audio+video':
        config['SCENE_TABLE'][temp['scene']['name']]['audio'] = True
        config['SCENE_TABLE'][temp['scene']['name']]['video'] = True
    elif value == "hint":
      config['SCENE_TABLE'][temp['scene']['name']]['ux-hint'] = m[0]
    else:
      return False
    return True

  def handleZone(self, config, line, temp):
    valid = {
      'zone ([a-zA-Z0-9]+) ?: ?(.+)' : 'zone',
      'subzone ([a-zA-Z0-9]+) ?: ?(.+)' : 'subzone',
      'default subzone ([a-zA-Z0-9]+)' : 'subzone-def',
      'audio uses ([a-zA-Z0-9]+)' : 'audio-noargs',
      'audio uses ([a-zA-Z0-9]+) zone ([1-9][0-9]*)' : 'audio-args',
      'video uses ([a-zA-Z0-9]+)' : 'video-noargs',
      'video uses ([a-zA-Z0-9]+) zone ([1-9][0-9]*)' : 'video-args',
      'hint ux (.+)' : 'hint'
    }
    result = self.findEntry(line, valid)
    if result is None:
      return False
    (key, m) = result
    value = valid[key]
    if value == "zone":
      temp['zone'] = {'name':m[0]}
      config['ZONE_TABLE'][temp['zone']['name']] = {'name' : m[1]}
    elif 'name' not in temp['zone']:
      return False
    elif value == "subzone":
      temp['zone']['subzone'] = {'name' : m[0]}
      if not 'subzones' in config['ZONE_TABLE'][temp['zone']['name']]:
        config['ZONE_TABLE'][temp['zone']['name']]['subzones'] = {m[0] : { 'name' : m[1]}}
      else:
        config['ZONE_TABLE'][temp['zone']['name']]['subzones'][m[0]] = { 'name' : m[1]}
    elif value == 'subzone-def':
      config['ZONE_TABLE'][temp['zone']['name']]['subzone-default'] = m[0]
    elif 'subzone' in temp['zone']:
      if value == 'audio-noargs':
        config['ZONE_TABLE'][temp['zone']['name']]['subzones'][temp['zone']['subzone']['name']]['audio'] = m[0]
      elif value == 'audio-args':
        config['ZONE_TABLE'][temp['zone']['name']]['subzones'][temp['zone']['subzone']['name']]['audio'] = '%s:%s' % (m[0], m[1])
      elif value == 'video-noargs':
        config['ZONE_TABLE'][temp['zone']['name']]['subzones'][temp['zone']['subzone']['name']]['video'] = m[0]
      elif value == 'video-args':
        config['ZONE_TABLE'][temp['zone']['name']]['subzones'][temp['zone']['subzone']['name']]['video'] = '%s:%s' % (m[0], m[1])
      elif value == 'hint':
        config['ZONE_TABLE'][temp['zone']['name']]['subzones'][temp['zone']['subzone']['name']]['ux-hint'] = m[0]
      else:
        return False
    else:
      if value == 'audio-noargs':
        config['ZONE_TABLE'][temp['zone']['name']]['audio'] = m[0]
      elif value == 'audio-args':
        config['ZONE_TABLE'][temp['zone']['name']]['audio'] = '%s:%s' % (m[0], m[1])
      elif value == 'video-noargs':
        config['ZONE_TABLE'][temp['zone']['name']]['video'] = m[0]
      elif value == 'video-args':
        config['ZONE_TABLE'][temp['zone']['name']]['video'] = '%s:%s' % (m[0], m[1])
      elif value == 'hint':
        config['ZONE_TABLE'][temp['zone']['name']]['ux-hint'] = m[0]
      else:
        return False

    return True

  def parsePathArguments(self, args):
    result = {}
    p = re.compile('''([a-zA-Z0-9]+) *(?:\(([a-zA-Z0-9,\- ]+)\)|()),?''')
    m = p.findall(args)
    for n in m:
      tmp = re.split(' *, *', n[1].strip())
      if tmp[0] == "":
        tmp = []
      result[n[0]] = tmp
    return result

  def parseStringArguments(self, args):
    result = []
    p = re.compile('''(?:"([^"]+)"|'([^']+)'|([^,]+)),? ?''')
    m = p.findall(args)
    for n in m:
      if n[0] != '':
        result.append(n[0])
      elif n[1] != '':
        result.append(n[1])
      elif n[2] != '':
        result.append(n[2])
    return result

  def findHandler(self, line, handlers):
    for handler in handlers:
      p = re.compile('^' + handler + '$', re.DOTALL|re.IGNORECASE)
      if p.match(line):
        return handlers[handler]
    return None

  def findEntry(self, line, handlers):
    for handler in handlers:
      p = re.compile('^' + handler + '$', re.DOTALL|re.IGNORECASE)
      m = p.match(line)
      if m:
        return (handler, m.groups())
    return None

  def validateKeys(self, config, keys, optional = None , othersOk = False):
    opts = 0
    for key in keys:
      if key not in config:
        return (False, key + ' is missing')
    if optional is not None:
      for key in optional:
        if key in config:
          opts += 1
    if not othersOk and len(config) != (len(keys) + opts):
      return (False, "There are additional entries which isn't allowed")
    return (True, None)

  def findIssues(self, config):
    usedDrivers = {}
    usedRoutes = {}
    virtualDrivers = {}

    # First, the basics...
    valid, err = self.validateKeys(config, ['OPTIONS', 'DRIVER_TABLE', 'ROUTING_TABLE', 'SCENE_TABLE', 'ZONE_TABLE'])
    if not valid: return err

    if 'ux-server' not in config['OPTIONS']: config['OPTIONS']['ux-server'] = ""
    valid, err = self.validateKeys(config['OPTIONS'], ['pin-remote', 'ux-server'])
    if not valid: return 'Section "options", ' + err

    if len(config['DRIVER_TABLE']) == 0: return 'No devices defined'
    if len(config['ROUTING_TABLE']) == 0: return 'No paths defined'
    if len(config['SCENE_TABLE']) == 0: return 'No scenes defined'
    if len(config['ZONE_TABLE']) == 0: return 'No zones defined'

    for dev in config['DRIVER_TABLE']:
      if config['DRIVER_TABLE'][dev] is None:
        return 'Device %s, missing driver' % dev
      usedDrivers[dev] = 0

    for route in config['ROUTING_TABLE']:
      usedRoutes[route] = 0
      if route in usedDrivers:
        usedDrivers[route] += 1
      elif route in virtualDrivers:
        virtualDrivers[route] += 1
      else:
        virtualDrivers[route] = 1
      if config['ROUTING_TABLE'][route] is None:
        return 'Device %s, missing path(s)' % route
      for path in config['ROUTING_TABLE'][route]:
        if config['ROUTING_TABLE'][route][path] is None:
          return 'Device %s, path %s is undefined' % (route, path)
        for item in config['ROUTING_TABLE'][route][path]:
          for dev in item:
            if dev in usedDrivers:
              usedDrivers[dev] += 1
            else:
              return "Device %s, path %s references unknown device %s" % (route, path, dev)

    for scene in config['SCENE_TABLE']:
      if 'ux-hint' not in config['SCENE_TABLE'][scene]: config['SCENE_TABLE'][scene]['ux-hint'] = ''
      valid, err = self.validateKeys(config['SCENE_TABLE'][scene], ['driver', 'description', 'audio', 'video', 'name', 'ux-hint'], ['driver-extras'])
      if not valid:
        return 'Scene %s, %s' % (scene, err)
      dev = config['SCENE_TABLE'][scene]['driver']
      if dev in usedRoutes:
        usedRoutes[dev] += 1
      else:
        return "Scene %s references unknown device %s" % (scene, dev)

    for zone in config['ZONE_TABLE']:
      if 'ux-hint' not in config['ZONE_TABLE'][zone]: config['ZONE_TABLE'][zone]['ux-hint'] = ''
      if 'subzones' in config['ZONE_TABLE'][zone]:
        for subzone in config['ZONE_TABLE'][zone]['subzones']:
          if 'audio' not in config['ZONE_TABLE'][zone]['subzones'][subzone]: config['ZONE_TABLE'][zone]['subzones'][subzone]['audio'] = None
          if 'video' not in config['ZONE_TABLE'][zone]['subzones'][subzone]: config['ZONE_TABLE'][zone]['subzones'][subzone]['video'] = None
          if 'ux-hint' not in config['ZONE_TABLE'][zone]['subzones'][subzone]: config['ZONE_TABLE'][zone]['subzones'][subzone]['ux-hint'] = ''
          valid, err = self.validateKeys(config['ZONE_TABLE'][zone]['subzones'][subzone], ['name', 'audio', 'video', 'ux-hint'])
          if not valid:
            return 'Zone %s, %s' % (zone, err)
          if config['ZONE_TABLE'][zone]['subzones'][subzone]['audio'] is not None:
            dev = config['ZONE_TABLE'][zone]['subzones'][subzone]['audio'].split(':')[0]
            if dev in usedDrivers:
              usedDrivers[dev] += 1
            else:
              return "Zone %s, subzone %s references unknown audio device %s" % (zone, subzone, dev)

          if config['ZONE_TABLE'][zone]['subzones'][subzone]['video'] is not None:
            dev = config['ZONE_TABLE'][zone]['subzones'][subzone]['video'].split(':')[0]
            if dev in usedDrivers:
              usedDrivers[dev] += 1
            else:
              return "Zone %s, subzone %s references unknown video device %s" % (zone, subzone, dev)

      else:
        if 'audio' not in config['ZONE_TABLE'][zone]: config['ZONE_TABLE'][zone]['audio'] = None
        if 'video' not in config['ZONE_TABLE'][zone]: config['ZONE_TABLE'][zone]['video'] = None
        valid, err = self.validateKeys(config['ZONE_TABLE'][zone], ['name', 'audio', 'video', 'ux-hint'])
        if not valid:
          return 'Zone %s, %s' % (zone, err)
        if config['ZONE_TABLE'][zone]['audio'] is not None:
          dev = config['ZONE_TABLE'][zone]['audio'].split(':')[0]
          if dev in usedDrivers:
            usedDrivers[dev] += 1
          else:
            return "Zone %s references unknown audio device %s" % (zone, dev)
        if config['ZONE_TABLE'][zone]['video'] is not None:
          dev = config['ZONE_TABLE'][zone]['video'].split(':')[0]
          if dev in usedDrivers:
            usedDrivers[dev] += 1
          else:
            return "Zone %s references unknown video device %s" % (zone, dev)

    # Since we got here, check for warnings and return that instead
    warn = []
    info = []
    #print "DRV: " + repr(usedDrivers)
    for driver in usedDrivers:
      if usedDrivers[driver] == 0:
        warn.append("No path uses %s" % driver)
    #print "RTE: " + repr(usedRoutes)
    for route in usedRoutes:
      if usedRoutes[route] == 0:
        warn.append("No scene uses %s" % route)
    #print "VRT: " + repr(virtualDrivers)
    for driver in virtualDrivers:
      if driver not in usedRoutes or usedRoutes[driver] > 0:
        info.append("%s has path only, does not allow control" % driver)

    return {'warn' : warn, 'info' : info}

  def instanciate(self, klass, arglist):
    module = importlib.import_module('drivers.' + klass)
    my_class = getattr(module, 'driver' + klass.capitalize())

    args = ''
    for a in arglist:
      args += '"""%s""", ' % a
    args = args[:-2]

    return eval('my_class(%s)' % args)

  def load(self, filename, config):
    handler = None
    temp = {}
    config['OPTIONS'] = {}
    config['DRIVER_TABLE'] = {}
    config['ROUTING_TABLE'] = {}
    config['SCENE_TABLE'] = {}
    config['ZONE_TABLE'] = {}

    tree = {
      'options' : self.handleOptions,
      'device [a-zA-Z0-9]+' : self.handleDevice,
      'scene [a-zA-Z0-9]+ ?: ?.+' : self.handleScene,
      'zone [a-zA-Z0-9]+ ?: ?.+' : self.handleZone,
    }

    with open(filename) as file:
      l=0
      for line in file:
        line = line.strip()
        l += 1
        if line == "" or line[0] == '#':
          continue

        #Use existing handler if we have one
        if handler and handler(config, line, temp) == False:
          handler = None

        # No handler? No problem, find one!
        if not handler:
          handler = self.findHandler(line, tree)
          temp = {}
          if not handler or handler(config, line, temp) == False:
            print(('ERROR: Unable to parse "%s" at line %d' % (line, l)))
            return False

    warn = []
    info = []
    err = self.findIssues(config)
    if not isinstance(err, str):
      warn = err['warn']
      info = err['info']
      err = None

    if err is not None:
      print("ERROR: Validation of configuration failed")
      print(("       " + err))
      return False

    for w in warn:
      logging.warn(w)
    for i in info:
      logging.info(i)

    # Lets instanciate the drivers now that we know we're good to go!
    for item in config['DRIVER_TABLE']:
      for k in config['DRIVER_TABLE'][item]:
        driver = k
        arguments = config['DRIVER_TABLE'][item][k]

        logging.debug("Loading " + driver)
        config['DRIVER_TABLE'][item] = self.instanciate(driver, arguments)
        break

    return True

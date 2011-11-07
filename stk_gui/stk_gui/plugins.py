import os
import os.path
import sys
import traceback

import gtk.gdk

import debug

import time
from stk_gui.interface import plugin_xml


plugins = []

# This is our signal class: we can use this within a plugin to 
# emit a signal that we've changed the XML - the GUI should then get
# it and act on that (i.e. read it in)
import gobject
class PluginSender(gobject.GObject):
    def __init__(self):
        self.__gobject_init__()
        

gobject.type_register(PluginSender)
gobject.signal_new("plugin_changed_xml", PluginSender, gobject.SIGNAL_RUN_FIRST,
                   gobject.TYPE_NONE, ())


class PluginReceiver(gobject.GObject):
    def __init__(self, sender):
        self.__gobject_init__()
        sender.connect('plugin_changed_xml', self.report_signal)
        
    def report_signal(self, sender):
        debug.deprint("A plugin has altered the XML: reloading.")


class PluginDetails(object):
  def __init__(self, applies, name, cb):
    self.applies = applies
    self.name = name
    self.cb = cb

  def matches(self, xpath):
    try:
      return self.applies(xpath)
    except Exception:
      debug.deprint("Warning: plugin %s raised an exception in matching function." % self.name, 0)
      return False

  def execute(self, xml, xpath):
     self.cb(xml, xpath)
     return


def register_plugin(applies, name, cb):
  global plugins
  p = PluginDetails(applies, name, cb)
  plugins.append(p)

def configure_plugins(suffix):
  homedir = os.path.expanduser('~')
  dirs = [os.path.join(homedir, ".stk", "plugins", suffix),
      "/usr/local/share/stk_gui/plugins/" + suffix]
  if sys.platform != "win32" and sys.platform != "win64":
    dirs.append("/etc/stk/plugins/" + suffix)

  for dir in dirs:
    sys.path.insert(0, dir)
    try:
      for file in os.listdir(dir):
        module_name, ext = os.path.splitext(file)
        if ext == ".py":
          try:
            debug.deprint("Attempting to import " + module_name, 1)
            module = __import__(module_name)
          except:
            debug.deprint("Plugin raised an exception:", 0)
            tb = traceback.format_exception(sys.exc_info()[0] ,sys.exc_info()[1], sys.exc_info()[2])
            tb_msg = ""
            for tbline in tb:
              tb_msg += tbline
            debug.deprint(tb_msg, 0)
    except OSError:
      pass

def cb_decorator(f):
  def wrapper(*args, **kwargs):

    try:
      f(*args, **kwargs)
    except:
      debug.deprint("Plugin raised an exception:", 0)
      tb = traceback.format_exception(sys.exc_info()[0] ,sys.exc_info()[1], sys.exc_info()[2])
      tb_msg = ""
      for tbline in tb:
        tb_msg += tbline
      debug.deprint(tb_msg, 0)

  return wrapper

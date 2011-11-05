from distutils.core import setup
from distutils.extension import Extension
import os
import os.path
import glob

try:
  destdir = os.environ["DESTDIR"]
except KeyError:
  destdir = ""

# Get all the plugin directories we have
plugin_dirs = [dir for dir in os.listdir('plugins') if os.path.isdir(os.path.join('plugins', dir)) and dir[0] != '.']
plugin_data_files = []
for plugin in plugin_dirs:
  plugin_data_files.append((destdir + "/usr/local/share/diamond/plugins/" + plugin,
    glob.glob('plugins/' + plugin + '/*.py')))

setup(
      name='supertree-toolkit',
      version='0.1',
      description="Supertree data source management",
      author = "The STK Team",
      author_email = "jon.hill@imperial.ac.uk",
      url = "https://launchpad.net/supertree-tookit",
      packages = ['stk-gui'],['stk'],['supertree-toolkit']
      scripts=["bin/stk-gui"],
      data_files = [(destdir + "/usr/local/share/stk/gui", ["gui/gui.glade", "gui/stk.svg"])] +
                   plugin_data_files
     )


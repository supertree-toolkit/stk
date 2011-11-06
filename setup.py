from distutils.core import setup
from distutils.extension import Extension
import os
import os.path
import glob
from setuptools import find_packages

try:
  destdir = os.environ["DESTDIR"]
except KeyError:
  destdir = ""

# Get all the plugin directories we have
plugin_dirs = ['supertree-toolkit/plugins']
plugin_data_files = []
for plugin in plugin_dirs:
  plugin_data_files.append((destdir + "/usr/local/share/stk/plugins/" + plugin,
    glob.glob('plugins/' + plugin + '/*.py')))

setup(
      name='supertree-toolkit',
      version='0.1',
      description="Supertree data source management",
      author = "The STK Team",
      author_email = "jon.hill@imperial.ac.uk",
      url = "https://launchpad.net/supertree-tookit",
      packages = find_packages(),
      scripts=["stk_gui/bin/stk-gui", "stk/stk"],
      data_files = [(destdir + "/usr/local/share/stk/", ["stk_gui/gui/gui.glade", "stk_gui/gui/stk.svg"])] +
                   plugin_data_files
     )


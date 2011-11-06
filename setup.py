from distutils.core import setup
import os
import os.path
import glob

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
      packages = ['stk', 'stk_gui'],
      package_dir = {'stk': 'stk', 'stk_gui':'stk_gui/stk_gui'},
      scripts=["stk_gui/bin/stk-gui", "stk/stk"],
      data_files = [(destdir + "/usr/local/share/stk/", ["stk_gui/gui/gui.glade", "stk_gui/gui/stk.svg"])] +
                   plugin_data_files
     )


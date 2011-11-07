from distutils.core import setup
import os
import os.path
import glob

try:
  destdir = os.environ["DESTDIR"]
except KeyError:
  destdir = ""

# Get all the plugin directories we have
plugin_dirs = ['stk_gui/plugins/']
plugin_data_files = []
for plugin in plugin_dirs:
  plugin_data_files.append((destdir + "/usr/local/share/plugin",
    glob.glob(plugin + '/*.py')))

schema_dirs = ['schema']
schema_data_files = []
for s in schema_dirs:
  schema_data_files.append((destdir + "/usr/local/share/stk/schemata/schema",
    glob.glob(s + '/*.rng')))



setup(
      name='supertree-toolkit',
      version='0.1',
      description="Supertree data source management",
      author = "The STK Team",
      author_email = "jon.hill@imperial.ac.uk",
      url = "https://launchpad.net/supertree-tookit",
      packages = ['stk', 'stk_gui', 'stk.yapbib', 'dxdiff'],
      package_dir = {'stk': 'stk', 'stk_gui':'stk_gui/stk_gui', 'stk.yapbib':'stk/yapbib', 'dxdiff':'stk_gui/dxdiff/dxdiff'},
      scripts=["stk_gui/bin/stk-gui", "stk/stk"],
      data_files = [(destdir + "/usr/local/share/stk/", ["stk_gui/gui/gui.glade", "stk_gui/gui/stk.svg"])] +
                   plugin_data_files + schema_data_files +
                   [(destdir + "/usr/local/share/stk/schemata", ["schema/phyml"])]
    )


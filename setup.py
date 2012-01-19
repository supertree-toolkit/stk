from setuptools import setup
import os
import os.path
import glob
import sys

try:
  destdir = os.environ["DESTDIR"]
except KeyError:
  destdir = ""

# Get all the plugin directories we have
plugin_dirs = ['stk_gui/plugins/']
plugin_data_files = []
for plugin in plugin_dirs:
  plugin_data_files.append((destdir + "/usr/local/share/plugin/phyml/",
    glob.glob(plugin + '/*.py')))

schema_dirs = ['schema']
schema_data_files = []
for s in schema_dirs:
  schema_data_files.append((destdir + "/usr/local/share/stk/schemata/schema/",
    glob.glob(s + '/*.rng')))

if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        app=['stk_gui/bin/stk-gui.py'],
        # Cross-platform applications generally expect sys.argv to
        # be used for opening files.
        options=dict(py2app=dict(argv_emulation=True)),
    )
elif sys.platform == 'win32':
    extra_options = dict(
        setup_requires=['py2exe'],
        app=['stk_gui'],
    )
else:
    extra_options = dict(
        app=['stk']
    )

setup(
      name='supertree-toolkit',
      version='0.1',
      description="Supertree data source management",
      author = "The STK Team",
      author_email = "jon.hill@imperial.ac.uk",
      url = "https://launchpad.net/supertree-tookit",
      packages = ['stk', 'stk_gui', 'stk.yapbib', 'dxdiff', 'stk.p4'],
      package_dir = {
          'stk': 'stk', 
          'stk_gui':'stk_gui/stk_gui', 
          'stk.yapbib':'stk/yapbib', 
          'dxdiff':'stk_gui/dxdiff/dxdiff',
          'stk.p4':'stk/p4'},
      scripts=["stk_gui/bin/stk-gui", "stk/stk"],
      data_files = [(destdir + "/usr/local/share/stk/", ["stk_gui/gui/gui.glade", "stk_gui/gui/stk.svg"])] +
                   plugin_data_files + schema_data_files +
                   [(destdir + "/usr/local/share/stk/schemata", ["schema/phyml"])],
      **extra_options
    )


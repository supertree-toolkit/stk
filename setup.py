from setuptools import setup
import os
import os.path
import glob
import sys

try:
  destdir = os.environ["DESTDIR"]
except KeyError:
  destdir = "/usr/local/share/"
try:
    set
except NameError:
    from sets import Set
  

# Get all the plugin directories we have
plugin_dirs = ['stk_gui/plugins/']
plugin_data_files = []
schema_dirs = ['schema']
schema_data_files = []   

if sys.platform == 'win32':
    extra_options = dict(
        setup_requires=['py2exe'],
        app=['stk_gui'],
    )
elif sys.platform == 'darwin':
    for plugin in plugin_dirs:
      plugin_data_files.append((destdir + "plugins/phyml/",
        glob.glob(plugin + '/*.py')))
        
    extra_options = dict(
   		data_files = [("./",
    	["stk_gui/gui/gui.glade", "stk_gui/gui/stk.svg", "stk_gui/gui/stk.png"])] +
    	plugin_data_files
    )
else:
    for plugin in plugin_dirs:
      plugin_data_files.append((destdir + "plugins/phyml/",
        glob.glob(plugin + '/*.py')))
    
    for s in schema_dirs:
      schema_data_files.append((destdir + "stk/schemata/schema/",
        glob.glob(s + '/*.rng')))
    
    extra_options = dict(
            app=['stk'],
            data_files = [(destdir + "stk/", ["stk_gui/gui/gui.glade", "stk_gui/gui/stk.svg"])] +
                   plugin_data_files + schema_data_files +
                   [(destdir + "stk/schemata", ["schema/phyml"])]
    )

setup(
      name='supertree-toolkit',
      version='0.1.1',
      description="Supertree data source management",
      author = "The STK Team",
      author_email = "jon.hill@imperial.ac.uk",
      url = "https://launchpad.net/supertree-tookit",
      packages = ['stk', 'stk_gui', 'yapbib', 'dxdiff', 'stk.p4','stk.nameparser'],
      package_dir = {
          'stk': 'stk/', 
          'stk_gui':'stk_gui/stk_gui', 
          'yapbib':'stk/yapbib', 
          'dxdiff':'stk_gui/dxdiff/dxdiff',
          # Note, we use out own P4 - better tested within STK this way and removes the requirement
          # of pre-installing it. It also means we don't overwrite any previous p4 install.
          'stk.p4':'stk/p4',
          'stk.nameparser':'stk/nameparser'},
      scripts=["stk_gui/bin/stk-gui", "stk/stk"],
      **extra_options
    )


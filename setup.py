from setuptools import setup
import os
import os.path
import glob
import sys
from setuptools.command.install import install as _install
from subprocess import call

# Produces blank file when using debian instl
#call(["bzr version-info --python > stk/bzr_version.py"], shell=True)

class install(_install):
    def run(self):
        _install.run(self)
        try:
            call(["update-desktop-database"])
        except:
            pass
        

try:
  destdir = os.environ["DESTDIR"]
except KeyError:
  destdir = "/usr/share/"
try:
    set
except NameError:
    from sets import Set
  

# Get all the plugin directories we have
plugin_dirs = ['stk_gui/plugins/phyml']
plugin_data_files = []
schema_dirs = ['schema']
schema_data_files = []   

if sys.platform == 'win32':
    extra_options = dict(
        setup_requires=['py2exe'],
        app=['stk_gui'],
    )
else:
    for plugin in plugin_dirs:
      plugin_data_files.append((destdir + "plugins/phyml/",
        glob.glob(plugin + '/*.py')))
    
    for s in schema_dirs:
      schema_data_files.append((destdir + "stk/schemata/schema/",
        glob.glob(s + '/*.rng')))
    
    extra_options = dict(
            cmdclass={'install': install},
            app=['stk'],
            data_files = [(destdir + "stk/", ["stk_gui/gui/gui.glade", "stk_gui/gui/stk.png", "stk_gui/gui/stk.svg"])] +
                   plugin_data_files + schema_data_files +
                   [(destdir + "stk/schemata", ["schema/phyml"])] +
                   [(destdir+"icons/hicolor/48x48/apps/", ["stk_gui/gui/stk.png"])] +
                   [(destdir+"applications/",["debian/stk.desktop"])]
    )

setup(
      name='supertree-toolkit',
      version='2.0',
      description="Supertree data source management",
      author = "The STK Team",
      author_email = "jon.hill@imperial.ac.uk",
      url = "https://launchpad.net/supertree-tookit",
      packages = ['stk', 'dxdiff', 'stk_gui', 'stk.yapbib', 'stk.p4','stk.nameparser'],
      package_dir = {
          'stk': 'stk',
          'dxdiff': 'dxdiff/dxdiff',
          'stk_gui':'stk_gui/stk_gui', 
          'stk.yapbib':'stk/yapbib', 
          #'stk.dxdiff':'stk_gui/dxdiff/dxdiff',
          # Note, we use out own P4 - better tested within STK this way and removes the requirement
          # of pre-installing it. It also means we don't overwrite any previous p4 install.
          'stk.p4':'stk/p4',
          'stk.nameparser':'stk/nameparser'},
      scripts=["stk_gui/bin/stk-gui", "stk/stk"],
      **extra_options
    )


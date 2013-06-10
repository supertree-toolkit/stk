#!/bin/bash
#
# Package script for the STK GUI.
#
# Thanks: http://stackoverflow.com/questions/1596945/building-osx-app-bundle

# Also fix $INSTALLDIR/MacOS/stk in case this number changes
PYVER=2.7
APP=STK.app
INSTALLDIR=$APP/Contents
LIBDIR=$INSTALLDIR/lib
APPDIR=/Applications/$INSTALLDIR
LOCALDIR=/opt/gtk
export DESTDIR="./"

# set up our virtual python environment
virtualenv --python=python$PYVER --no-site-packages $INSTALLDIR 

# install stk in it
sed -i .bak 's/packaging=False/packaging=True/' setup.py
macosx/$INSTALLDIR/bin/python setup.py install

mkdir $INSTALLDIR/MacOS
mkdir $INSTALLDIR/Resources
cd macosx;

# Sort out the MacResources
cp PkgInfo $INSTALLDIR/
cp Info.plist $INSTALLDIR/
cp pango_rc $INSTALLDIR/
mkdir $INSTALLDIR/Resources
cp stk.icns $INSTALLDIR/Resources/
cp stk $INSTALLDIR/MacOS

# Now we have to feed the app some schemas or it's all for nothing
# Set up the schema folders
mkdir -p $INSTALLDIR/share/schemata
# Make the schemata description
rm -rf $INSTALLDIR/Resources/schemata/stk
mkdir -p $INSTALLDIR/Resources/schemata/stk
cat > $INSTALLDIR/Resources/schemata/phyml << EOF
Phylogenetics Markup Language
/Applications/STK.app/Contents/Resources/schemata/stk/phylo_storage.rng
EOF
cp schema/*.rng $INSTALLDIR/share/schemata/stk/

# Let's get lxml installed
$INSTALLDIR/bin/easy_install --allow-hosts=lxml.de,*.python.org lxml
# Numpy
$INSTALLDIR/bin/easy_install numpy


# Temp. solution - Just manually copy stuff we know we need
SITEPACKAGES=$LIBDIR/python$PYVER/site-packages

mkdir -p $SITEPACKAGES

# This locates pygtk.pyc. We want the source file
pygtk=`python -c "import pygtk; print pygtk.__file__[:-1]"`
oldsite=`dirname $pygtk`
gobject=`python -c "import gobject; print gobject.__file__[:-1]"`
glib=`python -c "import glib; print glib.__file__[:-1]"`

# Copy PyGtk and related libraries
cp $pygtk $SITEPACKAGES
cp -r `dirname $gobject` $SITEPACKAGES
cp -r `dirname $glib` $SITEPACKAGES
cp -r $oldsite/cairo $SITEPACKAGES
cp -r $oldsite/gtk-2.0 $SITEPACKAGES
cp $oldsite/pygtk.pth $SITEPACKAGES


# Modules, config, etc.
for dir in lib etc/pango etc/gtk-2.0 share/themes; do
  mkdir -p $INSTALLDIR/$dir
  cp -r $LOCALDIR/$dir/* $INSTALLDIR/$dir
done

# Resources, are processed on startup
for dir in etc/gtk-2.0 etc/pango lib/gdk-pixbuf-2.0/2.10.0; do
  mkdir -p $INSTALLDIR/Resources/$dir
  cp $LOCALDIR/$dir/* $INSTALLDIR/Resources/$dir
done

# Somehow files are writen with mode 444
find $INSTALLDIR -type f -exec chmod u+w {} \;

function log() {
  echo $* >&2
}

function resolve_deps() {
  local lib=$1
  local dep
  otool -L $lib | grep -e "^.$LOCALDIR/" |\
      while read dep _; do
    echo $dep
  done
}

function fix_paths() {
  local lib=$1
  log Fixing $lib
  for dep in `resolve_deps $lib`; do
    log Fixing `basename $lib`
    log "|  $dep"
    install_name_tool -change $dep @executable_path/../lib/`basename $dep` $lib
  done
}

binlibs=`find $INSTALLDIR -type f -name '*.so'`

for lib in $binlibs; do
  log Resolving $lib
  resolve_deps $lib
  fix_paths $lib
done | sort -u | while read lib; do
  log Copying $lib
  cp $lib $LIBDIR
  chmod u+w $LIBDIR/`basename $lib`
  fix_paths $LIBDIR/`basename $lib`
done

for lib in $dylibs; do
  log Resolving $lib
  resolve_deps $lib
  fix_paths $lib
done | sort -u | while read lib; do
  log Copying $lib
  cp $lib $LIBDIR
  chmod u+w $LIBDIR/`basename $lib`
  fix_paths $LIBDIR/`basename $lib`
done


# Fix config files
sed -i .bak 's#/opt/gtk/#'$APPDIR'/#' $INSTALLDIR/etc/pango/pango.modules 
sed -i .bak 's#/opt/gtk/#'$APPDIR'/#' $INSTALLDIR/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache
sed -i .bak 's#/opt/gtk/#'$APPDIR'/#' $INSTALLDIR/Resources/etc/pango/pango.modules 
sed -i .bak 's#/opt/gtk/#'$APPDIR'/#' $INSTALLDIR/Resources/lib/gdk-pixbuf-2.0/2.10.0/loaders.cache



# Package!
VERSION=0.01
# we now need to fiddle with the Python run path on the diamond script
# COMMENT THESE OUT IF YOU WANT TO TEST YOUR APP WITHOUT INSTALLING
# EDIT AS REQUIRED
sed -i .bak 's|/Users/amcg/Software/stk/mac_port/|/Applications/|' $INSTALLDIR/lib/python2.7/site-packages/supertree_toolkit-0.1.1-py2.7.egg/EGG-INFO/scripts/stk-gui	
sed -i .bak 's|/Users/amcg/Software/stk/mac_port/|/Applications/|' $INSTALLDIR/MacOS/stk

zip -rq STK-$VERSION-osx.zip $APP
hdiutil create -srcfolder $APP STK-$VERSION.dmg		

# To test, temporarily move your /opt/gtk folder
# Move the Diamond.app folder to /Applications and go
# open -a Console 
# helps to debug
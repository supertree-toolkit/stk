Getting started
===============

Introduction
------------

This first chapter a brief guide to setting-up the STK on Linux, Windows and
MacOS X. STK comes as either pre-compiled binaries for some platform or as a
source package. Both downloading an archived source package or downloading via
bzr are covered. We assume little knowledge of Linux or DOS commands, but some
knowledge on how to install software. Contact your local sys admin if you need
further help. 

We store all source code and downloads on Canonical's Launchpad system: 
http://launchpad.net/supertree-toolkit

Linux
-----

The STK is distributed via Launchpad PPA. You need to add the Supertree Toolkit
PPA (https://launchpad.net/~stk-developers/+archive/release) to your system,
along with an additional one which contains some dependencies. You can then
install the package. Run the commands below to do all this.
 
.. code-block:: bash   

    sudo apt-add-repository ppa:fluidity-core/ppa
    sudo apt-add-repository ppa:stk-developers/release
    sudo apt-get update
    sudo apt-get -y install supertree-toolkit

This will install the GUI and CLI to standard locations and add the GUI to your
Applications menu.

Windows
-------

A pre-built binary package is available. Simply download and run to install. 
Follow the on-screen instructions.

The STK CLI is also available from a Command Prompt.

MacOS X
-------

A DMG is available on Launchpad. Drag the STK icon into the Applications folder. This will install
the STK GUI on your Mac.

To install the CLI you must alter your PATH and PYTHONPATH variables. To do this
permanently, edit your .bash_profile file and add the following lines:

.. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/Applications/STK.app/Contents/Resources/lib/python2.7/site-packages/
    export PATH=/Applications/STK.app/Contents/Resources/bin/:$PATH

You can access the STK CLI from a standard terminal

Source
------

The source is available as either a compressed tarball or via bzr. To obtain the tarball, simply
download from `Launchpad <http://launchpad.net/supertree-toolkit>`_, then:
    
.. code-block:: bash
    
    tar zxvf supertree-toolkit.tgz

Using bzr, you can either obtain the bleeding-edge development version or the current release (recommended) using:

.. code-block:: bash
    
    bzr branch lp:supertree-toolkit/trunk

or

.. code-block:: bash
    
    bzr branch lp:supertree-toolkit/release

respectively.

Regardless of how the source was obtained, you can now either use the STK in-place or install it using:

.. code-block:: bash
    
    sudo python setup.py install

(for Windows users, the sudo is not required).

Prerequisites and dependencies
""""""""""""""""""""""""""""""

When running from source you must install the following prerequisites and dependencies:

* Python 2.5 to 2.7
* Matplotlib
* networkx
* libspud
* numpy
* lxml
* pyGTK
* dxdiff (available from http://launchpad.net/spud)


Running the STK
---------------

There are two ways to run the STK: via the GUI (Graphical User Interface) or the
CLI (Command Line Interface). Most data collecting and curation is done via the
GUI. However, processing can be done using either. The CLI also contains a few
more utility functions that are not available in the GUI.

The GUI is run from the command line using:

.. code-block:: bash
    
    stk-gui

The CLI version is run using:

.. code-block:: bash
    
    stk

which will produce the following help.

.. code-block:: bash

    usage: stk [-h] [-v] [-i]
           
            {create_matrix,sub_taxa,import_data,export_data,export_trees,export_bib,
             data_summary,safe_taxonomic_reduction,data_ind,data_overlap,permute_trees,
             clean_data,replace_genera,convert_files,create_subset}
            ...
    stk: error: too few arguments

The STK GUI can also be accessed via the Start Menu (Windows), the Applications
folder (Mac OS X) or in the Applications menu (most Linux varients).


The STK Graphical User Interface
=================================

The Graphical User Interface (GUI) is used to perform all of the STKs primary
functionality. It allows you to enter data, visualise data and process data all
within a single interface.

Starting out
------------

To open the GUI either click on the icon or run the following on the command
line:

.. code:: bash
    stk-gui [filename]

The GUI looks like this.

.. figure:: images/STK_gui.png
    :align: center
    :alt: The STK GUI
    :figclass: align-center

    The STK GUI with no data loaded. The GUI consists of two vertical panels
    where data is edited (left) and entered (right).

The GUI consists of two main halfs. The left-hand side is a tree-structure that
allows you to navigate the data (tree panel). The data is structured into a
project, which in turn contains sources, which in turn contain trees and meta
data. The right-hand side (data panel) contains three sub-panels. Each of
these divisions is called an element. The top gives user context-sensitive
documentation on the current selection in the left-hand side. The middle is
where you add data. Depending on what par tof the data you are editing, the
middle panel will change to suit the data to be edited/input.  The lowermost
sub-panel is where you can add any comments for that part of the dataset. This
is not enabled for all sections of the data but should be used wherever it is
useful. 

To navigate the left hand side, click the small arrows on the left. These will
open and close sub-data within the heirachy. On the right-hand side of the tree,
there are small "+" and "-" signs to allow you add or remove data. Where the
data is a choice, a dropdown list is activated on the right hand side.

The colour in the left-hand side tree informs you if there is missing data. Blue
lines show you are missing required data. The blue then progresses upwards from
the missing data, all the way to the uppermost level. This allows you to drill
downwards to find the missing data. Black text indicates you have fulfilled the
minimum requirements.

There are two types of menus - the main menu on the toolbar and a right-click
menu. This toolbar menu contains:
 * File
 * Edit
 * View
 * STK Functions
 * Validate
 * Tools
 * Help

Of these, the File and STK Functions are most often used. More on these will be
covered later, but briefly the File menu contains command to open and save data,
plus import and export.  The STK Functions menu contains all the STK-only
functionality.

The right click menu allows you to copy and paste elements (e.g. you can copy
and past a source from the same or another file) and change how the data is
visualised. These are covered later.

Entering data
-------------

The best way of starting a new dataset is to import bibliographic file. The STK
uses `bibtex format <http://www.bibtex.org/>`_, which is a common format and all
decent reference managers can output, as can most journal websites. We recommend
using `JabRef <http://jabref.sourceforge.net/>`_, which is free, open source and
available on most OS. We have tested the STK extensively with output from
JabRef, but your milage with other reference managers may vary.

.. index:: bibtex

Once you have a Bibtex file you can import it using the File->Import from
bibliography and import your file. This should import all the papers in that
bibtex file and create a source for each one. These are then named in a sensible
way and sorted alphabetically. You can then start editing your data.

.. figure:: images/stk_gui_source.png
    :align: center
    :alt: A source
    :figclass: align-center

    A source element that consists of a bibliographic entry, with the data
    contained in that paper nested below.

The next thing you will want to do is import some trees. You can use any
software you wish to digitise your trees. The STK will read the output of most
sofware. To import a tree, drill down the tree panel to the correct source, then
open the Tree element and click on the Tree string element. The import tree
button will then appear in the status bar, in the lower left of the GUI.

.. figure:: images/stk_gui_import_tree.png    
    :align: center
    :alt: The STK GUI
    :figclass: align-center

    The import tree button. Click to import a tree into a source.

Once done, your tree string will appear in the data panel.

Using the interface
-------------------

Checking data
-------------

Processing data
---------------


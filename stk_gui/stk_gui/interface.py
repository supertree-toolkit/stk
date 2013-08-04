#!/usr/bin/env python

#    This file is part of the Supertree Toolkit.
#
#    Supertree Toolkit is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Supertree Toolkit is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Supertree Toolkit.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import generators

import os
import os.path
import re
import time
import sys
import tempfile
import cStringIO as StringIO
import Queue
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
import stk.supertree_toolkit as stk
import stk.stk_import_export as stk_import_export
from stk.supertree_toolkit import _removeNonAscii
import pango
import gobject
import gtk
import gtk.glade
from stk.stk_exceptions import *
plugin_xml = None


import choice
import config
import datatype
import debug
import dialogs
import mixedtree
import plist
import plugins
import schema
import scherror
import tree

import StringIO
import TextBufferMarkup

import attributewidget
import commentwidget
import descriptionwidget
import databuttonswidget
import datawidget
import diffview
import sliceview
import useview

from lxml import etree

pluginSender = plugins.PluginSender()
pluginReceiver = plugins.PluginReceiver(pluginSender)
plugin_xml = None

try:
  gtk.Tooltip()
except:
  debug.deprint("Interface warning: Unable to use GTK tooltips")

"""
Here are some notes about the code:

Important fields:
  file_path: the directory containing the current file (the working directory or directory of last opened / saved file if no file is open)
  filename: output filename of the current file
  data_paths: paths (from the root node) to important Diamond data (e.g. geometry dimension)
  geometry_dim_tree: MixedTree, with parent equal to the geometry dimension tree and child equal to the geometry dimension data subtree
  gladefile: input Glade file
  gui: GUI GladeXML object
  logofile: the GUI logo file
  main_window: GUI toplevel window
  node_attrs: RHS attributes entry widget
  description: RHS description widget
  data = RHS data widget
  comment: RHS comment entry widget
  node_data: RHS data entry widget
  node_data_buttons_hbox: container for "Revert Data" and "Store Data" buttons
  node_data_interacted: used to determine if a node data widget has been interacted with without data being stored
  node_data_frame: frame containing data entry widgets
  options_tree_select_func_enabled: boolean, true if the options tree select function is enabled (used to overcome a nasty clash with the treeview clicked signal) - re-enabled on next options_tree_select_func call
  selected_node: a tree.Tree or MixedTree containing data to be displayed on the RHS
  selected_iter: last iter set by on_select_row
  s: current schema
  saved: boolean, false if the current file has been edited
  schemafile: the current RNG schema file
  schemafile_path: the directory containing the current schema file (the working directory if no schema is open)
  signals: dictionary containing signal handlers for signals set up in the Glade file
  statusbar: GUI status bar
  tree: LHS tree root
  treestore: the LHS tree model
  treeview: the LHS tree widget

Important routines:
  cellcombo_changed: called when a choice is selected on the left-hand pane
  init_treemodel: set up the treemodel and treeview
  on_treeview_clicked: when a row is clicked, process the consequences (e.g. activate inactive instance)
  set_treestore: stuff the treestore with a given tree.Tree
  on_find_find_button & search_treestore: the find functionality
  on_select_row: when a row is selected, update the options frame
  update_options_frame: paint the right-hand side

If there are bugs in reading in, see schema.read.
If there are bugs in writing out, see tree.write.
"""

class Diamond:
    
  def __init__(self, gladefile, schemafile = None, schematron_file = None, logofile = None, input_filename = None, 
      dim_path = "/geometry/dimension", suffix=None):
    self.gladefile = gladefile
    self.gui = gtk.glade.XML(self.gladefile)

    self.statusbar = DiamondStatusBar(self.gui.get_widget("statusBar"))
    self.find      = DiamondFindDialog(self, gladefile)
    self.popup = self.gui.get_widget("popupmenu")

    self.add_custom_widgets()
    
    self.plugin_buttonbox = self.gui.get_widget("plugin_buttonbox")
    self.plugin_buttonbox.set_layout(gtk.BUTTONBOX_START)
    self.plugin_buttonbox.show()
    self.plugin_buttons = []
    self.treepath = None

    self.scherror  = scherror.DiamondSchemaError(self, gladefile, schemafile, schematron_file)

    signals     =  {"on_new": self.on_new,
                    "on_quit": self.on_quit,
                    "on_open": self.on_open,
                    "on_open_schema": self.on_open_schema,
                    "on_save": self.on_save,
                    "on_save_as": self.on_save_as,
                    "on_validate": self.scherror.on_validate,
                    "on_validate_schematron": self.scherror.on_validate_schematron,
                    "on_expand_all": self.on_expand_all,
                    "on_collapse_all": self.on_collapse_all,
                    "on_find": self.find.on_find,
                    "on_go_to_node": self.on_go_to_node,
                    "on_display_properties_toggled": self.on_display_properties_toggled,
                    "on_about": self.on_about,
                    "on_copy_spud_path": self.on_copy_spud_path,
                    "on_copy": self.on_copy,
                    "on_paste": self.on_paste,
                    "on_slice": self.on_slice,
                    "on_diff": self.on_diff,
                    "on_diffsave": self.on_diffsave,
                    "on_finduseage": self.on_finduseage,
                    "on_group": self.on_group,
                    "on_ungroup": self.on_ungroup,
                    "on_standardise_names": self.on_standardise_names,
                    "on_import_bib": self.on_import_bib,
                    "on_create_matrix": self.on_create_matrix,
                    "on_export": self.on_export,
                    "on_import": self.on_import,
                    "on_export_trees": self.on_export_trees,
                    "on_export_bib" : self.on_export_bib,
                    "on_sub_taxa": self.on_sub_taxa,
                    "on_data_summary": self.on_data_summary,
                    "on_data_overlap": self.on_data_overlap,
                    "on_data_ind" : self.on_data_ind,
                    "on_permute_all_trees": self.on_permute_all_trees,
                    "on_str": self.on_str,
                    "on_replace_genera": self.on_replace_genera,
                    "on_clean_data": self.on_clean_data
                    }

    self.gui.signal_autoconnect(signals)

    # Set up the plugin XML change signal
    pluginSender.connect("plugin_changed_xml", self.plugin_callback)

    self.main_window = self.gui.get_widget("mainWindow")
    self.main_window.connect("delete_event", self.on_delete)

    self.logofile = logofile
    if self.logofile is not None:
        for logo in  self.logofile:
            try:
                gtk.window_set_default_icon_from_file(logo)
            except:
                print "Error setting logo from file", logo

    self.init_treemodel()

    self.data_paths = {}
    self.data_paths["dim"] = dim_path

    self.suffix = suffix

    self.selected_node = None
    self.selected_iter = None
    self.update_options_frame()

    self.file_path = os.getcwd()
    self.schemafile_path = os.getcwd()
    self.filename = None
    self.schemafile = None
    self.init_datatree()    
    self.set_saved(True)
    self.open_file(schemafile = None, filename = None)

    self.main_window.show()

    if schemafile is not None:
      self.open_file(schemafile = schemafile, filename = input_filename)

    # Hide specific menu items
    menu = self.gui.get_widget("menu")
    
    if schematron_file is None:
      # Disable Validate Schematron
      menu.get_children()[4].get_submenu().get_children()[1].set_property("sensitive", False)

    return

  def plugin_callback(self,object):
    # check if plugin_xml is not None
    global plugin_xml

    f = StringIO.StringIO()
    self.tree.write(f)
    xml = f.getvalue()

    if plugin_xml:
      # Need to remove nonunicode characters
      plugin_xml = _removeNonAscii(plugin_xml)
      ios = StringIO.StringIO(plugin_xml)

      try:
        tree_read = self.s.read(ios)

        if tree_read is None:
          self.statusbar.set_statusbar("Unable to read plugin result")
          return

        self.display_validation_errors(self.s.read_errors())
        self.tree = tree_read
      except:
        dialogs.error_tb(self.main_window, "Unable to read plugin result")
        return

      path = self.treestore.get_path(self.selected_iter)

      self.set_saved(False)
      self.treeview.freeze_child_notify()
      self.treeview.set_model(None)
      self.signals = {}
      self.set_treestore(None, [self.tree], True)
      self.treeview.set_model(self.treestore)
      self.treeview.thaw_child_notify()
      self.set_geometry_dim_tree()
      self.treeview.expand_to_path(path)   
      # We *must* select the path again otherwise we get a segfault if the user alters the XML
      # without clicking on a path first.
      self.treeview.get_selection().select_path(path)    
      self.scherror.destroy_error_list()
      plugin_xml = None

  def program_exists(self, name):
    ret = os.system("which %s > /dev/null" % name)
    return ret == 0

  ### MENU ###

  def update_title(self):
    """
    Update the Diamond title based on the save status of the currently open file.
    """

    title = "Supertree Toolkit: "
    if not self.saved:
      title += "*"
    if self.filename is None:
      title += "(Unsaved)"
    else:
      title += os.path.basename(self.filename)
      if len(os.path.dirname(self.filename)) > 0:
        title += " (%s)" % os.path.dirname(self.filename)

    self.main_window.set_title(title)

    return

  def set_saved(self, saved, filename = ""):
    """
    Change the save status of the current file.
    """

    self.saved = saved
    if filename != "":
      self.filename = filename
      if filename is not None:
        self.file_path = os.path.dirname(filename) + os.path.sep
    self.update_title()

    return

  def close_schema(self):
    if self.schemafile is None:
      return

    # clear the schema.
    self.s = None
    self.schemafile = None
    self.schemafile_path = None
    self.scherror.schema_file = None
       
    return

  def load_schema(self, schemafile):
    # so, if the schemafile has already been opened, then ..
    if schemafile == self.schemafile:
      self.statusbar.set_statusbar('Schema ' + schemafile + ' already loaded')
      return

    # if we aren't using a http schema, and we're passed a relative filename, we
    # need to absolut-ify it.
    if 'http' not in schemafile:
      schemafile = os.path.abspath(schemafile)

    self.statusbar.set_statusbar('Loading schema from ' + schemafile)

    # now, let's try and read the schema.
    try:
      s_read = schema.Schema(schemafile)
      self.s = s_read
      self.statusbar.set_statusbar('Loaded schema from ' + schemafile)
    except:
      dialogs.error_tb(self.main_window, "Unable to open schema file \"" + schemafile + "\"")
      self.statusbar.clear_statusbar()
      return

    self.schemafile = schemafile
    self.schemafile_path = os.path.dirname(schemafile) + os.path.sep
    self.scherror.schema_file = schemafile
    
    self.remove_children(None)
    self.init_datatree()
    
    return

  def close_file(self):
    self.remove_children(None)
    self.init_datatree()

    self.filename = None
    
    return

  def display_validation_errors(self, errors):
    # Extract and display validation errors
    saved = True
    lost_eles, added_eles, lost_attrs, added_attrs = errors
    if len(lost_eles) > 0 or len(added_eles) > 0 or len(lost_attrs) > 0 or len(added_attrs) > 0:
      saved = False
      msg = ""
      if len(lost_eles) > 0:
        msg += "Warning: lost xml elements:\n"
        for ele in lost_eles:
          msg += ele + "\n"
      if len(added_eles) > 0:
        msg += "Warning: added xml elements:\n"
        for ele in added_eles:
          msg += ele + "\n"
      if len(lost_attrs) > 0:
        msg += "Warning: lost xml attributes:\n"
        for ele in lost_attrs:
          msg += ele + "\n"
      if len(added_attrs) > 0:
        msg += "Warning: added xml attributes:\n"
        for ele in added_attrs:
          msg += ele + "\n"

      dialogs.long_message(self.main_window, msg)
    return saved

  def load_file(self, filename):
    # if we have a relative path, make it absolute
    filename = os.path.abspath(filename)

    try:
      os.stat(filename)
    except OSError:
      self.filename = filename
      self.set_saved(False)

      self.remove_children(None)
      self.init_datatree()

      return

    try:
      tree_read = self.s.read(filename)

      if tree_read is None:
        dialogs.error_tb(self.main_window, "Unable to open file \"" + filename + "\"")
        return

      saved = self.display_validation_errors(self.s.read_errors())

      self.tree = tree_read
      self.filename = filename
    except:
      dialogs.error_tb(self.main_window, "Unable to open file \"" + filename + "\"")
      return

    self.set_saved(saved, filename)

    return

  def open_file(self, schemafile = "", filename = ""):
    """
    Handle opening or clearing of the current file and / or schema.
    """

    self.find.on_find_close_button()
    if schemafile is None:
      self.close_schema()
    elif schemafile != "":
      self.load_schema(schemafile)
    if filename is None:
      self.close_file()
    elif filename != "":
      self.load_file(filename)
      
    self.treeview.freeze_child_notify()
    self.treeview.set_model(None)
    self.signals = {}
    self.set_treestore(None, [self.tree], True)
    self.treeview.set_model(self.treestore)
    self.treeview.thaw_child_notify()

    self.set_geometry_dim_tree()

    self.treeview.grab_focus()
    self.treeview.get_selection().select_path(0)

    self.selected_node = None
    self.update_options_frame()

    self.scherror.destroy_error_list()

    return

  def save_continue(self):

    if not self.saved:
      prompt_response = dialogs.prompt(self.main_window, 
        "Unsaved data. Do you want to save the current document before continuing?", gtk.MESSAGE_WARNING, True)
 
      if prompt_response == gtk.RESPONSE_YES:
        if self.filename is None:
          return self.on_save_as()
        else:
          return self.on_save()
      elif prompt_response == gtk.RESPONSE_CANCEL:
        return False

    return True

  def on_new(self, widget=None):
    """
    Called when new is clicked. Clear the treestore and reset the datatree.
    """

    if not self.save_continue():
      return

    self.open_file(filename = None)
    self.filename = None

    return

  def on_open(self, widget=None):
    """
    Called when open is clicked. Open a user supplied file.
    """

    if not self.save_continue():
      return

    filter_names_and_patterns = {}
    if self.suffix is None:
      for xmlname in config.schemata:
        filter_names_and_patterns[config.schemata[xmlname][0]] = ["*." + xmlname]
    elif self.suffix in config.schemata.keys():
      filter_names_and_patterns[config.schemata[self.suffix][0]] = ["*." + self.suffix]
    else:
      filter_names_and_patterns[self.suffix] = ["*." + self.suffix]

    filename = dialogs.get_filename(title = "Open XML file", action = gtk.FILE_CHOOSER_ACTION_OPEN, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)

    if filename is not None:
      self.open_file(filename = filename)

    return

  def on_open_schema(self, widget=None):
    """
    Called when open schema is clicked. Clear the treestore and reset the schema.
    """

    if not self.save_continue():
      return

    filename = dialogs.get_filename(title = "Open RELAX NG schema", action = gtk.FILE_CHOOSER_ACTION_OPEN, filter_names_and_patterns = {"RNG files":["*.rng"]}, folder_uri = self.schemafile_path)
    if filename is not None:
      self.open_file(schemafile = filename)

    return

  def on_save(self, widget=None):
    """
    Write out to XML. If we don't already have a filename, open a dialog to get
    one.
    """

    self.data.store()

    if self.filename is None:
      return self.on_save_as(widget)
    else:
      self.statusbar.set_statusbar("Saving ...")
      self.main_window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
      try:
        self.tree.write(self.filename)
      except:
        dialogs.error_tb(self.main_window, "Saving to \"" + self.filename + "\" failed")
        self.statusbar.clear_statusbar()
        self.main_window.window.set_cursor(None)
        return False

      self.set_saved(True)

      self.statusbar.clear_statusbar()
      self.main_window.window.set_cursor(None)
      return True

    return False

  def on_save_as(self, widget=None):
    """
    Write out the XML to a file.
    """

    if self.schemafile is None:
      dialogs.error(self.main_window, "No schema file open")
      return False

    filter_names_and_patterns = {}
    if self.suffix is None:
      for xmlname in config.schemata:
        filter_names_and_patterns[config.schemata[xmlname][0]] = ["*." + xmlname]
    elif self.suffix in config.schemata.keys():
      filter_names_and_patterns[config.schemata[self.suffix][0]] = ["*." + self.suffix]
    else:
      filter_names_and_patterns[self.suffix] = ["*." + self.suffix]

    filename = dialogs.get_filename(title = "Save PHYML file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)

    if filename is not None:
      # Check that the selected file has a file extension. If not, add a .xml extension.
      if len(filename.split(".")) <= 1:
        filename += ".phyml"

      # Save the file
      self.statusbar.set_statusbar("Saving ...")
      self.main_window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
      self.tree.write(filename)
      self.set_saved(True, filename)
      self.statusbar.clear_statusbar()
      self.main_window.window.set_cursor(None)
      return True

    return False

  def on_delete(self, widget, event):
    """
    Called when the main window is deleted. Return "True" to prevent the deletion
    of the main window (deletion is handled by "on_quit").
    """

    self.on_quit(widget, event)

    return True

  def on_quit(self, widget, event = None):
    """
    Quit the program. Prompt the user to save data if the current file has been
    changed.
    """

    if not self.save_continue():
      return

    self.destroy()

    return

  def destroy(self):
    """
    End the program.
    """

    try:
      gtk.main_quit()
    except:
      debug.dprint("Failed to quit - already quit?")

    return

  def on_display_properties_toggled(self, widget=None):
    optionsFrame = self.gui.get_widget("optionsFrame")
    optionsFrame.set_property("visible", not optionsFrame.get_property("visible"))
    return

  def on_go_to_node(self, widget=None):
   """
   Go to a node, identified by an XPath
   """

   dialog = dialogs.GoToDialog(self)
   spudpath = dialog.run()

   return

  def on_expand_all(self, widget=None):
    """
    Show the whole tree.
    """

    self.treeview.expand_all()

    return

  def on_collapse_all(self, widget=None):
    """
    Collapse the whole tree.
    """

    self.treeview.collapse_all()

    return
    
  def on_console(self, widget = None):
    """
    Launch a python console
    """    
    
    # Construct the dictionary of locals that will be used by the interpreter
    locals = {}
    locals["interface"] = globals()
    locals["stk_gui"] = self
  
    dialogs.console(self.main_window, locals)
    
    return

  def on_about(self, widget=None):
    """
    Tell the user how great we are.
    """

    about = gtk.AboutDialog()
    about.set_name("Supertree Toolkit")
    about.set_copyright("GPLv3")
    about.set_comments("Software to manage supertree source files. Based on Diamond from AMCG.")
    about.set_authors(["Jon Hill", "Katie Davis"])
    about.set_license("Supertree Tookit is free software: you can redistribute it and/or modify\n"+
                      "it under the terms of the GNU General Public License as published by\n"+
                      "the Free Software Foundation, either version 3 of the License, or\n"+
                      "(at your option) any later version.\n"+
                      "\n"+
                      "Supertree Toolkit is distributed in the hope that it will be useful,\n"+
                      "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"+
                      "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"+
                      "GNU General Public License for more details.\n"+
                      "You should have received a copy of the GNU General Public License\n"+
                      "along with the Supertree Toolkit.  If not, see http://www.gnu.org/licenses/.")

    if self.logofile is not None:
      logo = gtk.gdk.pixbuf_new_from_file(self.logofile[0])
      about.set_logo(logo)
      
    try:
      image = about.get_children()[0].get_children()[0].get_children()[0]
      image.set_tooltip_text("Supertree Toolkit: it's supertree-tastic")
    except:
      pass
    
    about.run()
    about.destroy()

    return


  def on_copy_spud_path(self, widget=None):
    path = self.get_selected_row(self.treeview.get_selection())
    if path is None:
      debug.deprint("No selection.")
      return
    iter = self.treestore.get_iter(path)
    active_tree = self.treestore.get_value(iter, 1)
    name = self.get_spudpath(active_tree)
    clipboard = gtk.clipboard_get()
    clipboard.set_text(name)
    clipboard.store()

  def _get_focus_widget(self, parent):
    """
    Gets the widget that is a child of parent with the focus.
    """
    focus = parent.get_focus_child()
    if focus is None or (focus.flags() & gtk.HAS_FOCUS):
      return focus
    else:
      return self._get_focus_widget(focus)

  def _handle_clipboard(self, widget, signal):
    """
    This finds the currently focused widget.
    If no widget is focused or the focused widget doesn't support 
    the given clipboard operation use the treeview (False), otherwise
    signal the widget to handel the clipboard operation (True).
    """
    widget = self._get_focus_widget(self.main_window)

    if widget is None or widget is self.treeview:
      return False

    if gobject.signal_lookup(signal + "-clipboard", widget):
      widget.emit(signal + "-clipboard")
      return True
    else:
      return False

  def on_copy(self, widget=None):
    if self._handle_clipboard(widget, "copy"):
      return

    if isinstance(self.selected_node, mixedtree.MixedTree):
      node = self.selected_node.parent
    else:
      node = self.selected_node    

    if node != None and node.active:
      ios = StringIO.StringIO()
      node.write(ios)
    
      clipboard = gtk.clipboard_get()
      clipboard.set_text(ios.getvalue())
      clipboard.store()

      ios.close()
    return

  def on_paste(self, widget=None):
    if self._handle_clipboard(widget, "paste"):
      return

    clipboard = gtk.clipboard_get()
    ios = StringIO.StringIO(clipboard.wait_for_text())
    
    if self.selected_iter is not None:    
      node = self.treestore.get_value(self.selected_iter, 0)

    if node != None:
  
      expand = not node.active
      if expand:
        self.expand_tree(self.selected_iter)

      newnode = self.s.read(ios, node)

      if newnode is None:
        if expand:
          self.collapse_tree(self.selected_iter, False)
        self.statusbar.set_statusbar("Trying to paste invalid XML.")
        return

      if node.parent is not None:
        newnode.set_parent(node.parent)
        children = node.parent.get_children()
        children.insert(children.index(node), newnode)
        children.remove(node)
 
      self.treeview.freeze_child_notify()
      iter = self.set_treestore(self.selected_iter, [newnode], True, True)
      newnode.recompute_validity()
      self.treeview.thaw_child_notify()

      self.treeview.get_selection().select_iter(iter)

      self.display_validation_errors(self.s.read_errors())

      self.set_saved(False)

    return

  def __diff(self, path):
    def run_diff(self, path):
      start = time.clock()
      diffview.DiffView(path, self.tree)
      seconds = time.clock() - start
      self.statusbar.set_statusbar("Diff calculated (took " + str(seconds) + " seconds)")
      return False

    if path and os.path.isfile(path):
      filename = path
    else:
      dialog = gtk.FileChooserDialog(
                                     title = "Diff against",
                                     action = gtk.FILE_CHOOSER_ACTION_OPEN,
                                     buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK))

      if path:
        dialog.set_current_folder(path)

      response = dialog.run()
      if response != gtk.RESPONSE_OK:
        dialog.destroy()
        return

      filename = dialog.get_filename()
      dialog.destroy()

    self.statusbar.set_statusbar("Calculating diff... (this may take a while)")
    gobject.idle_add(run_diff, self, filename)

  def on_diff(self, widget = None, path = None):
    if path is None:
      path = os.path.dirname(self.filename) if self.filename else None
    self.__diff(path)

  def on_diffsave(self, widget = None):
    if self.filename:
      self.__diff(self.filename)
    else:
      dialogs.error(self.main_window, "No save to diff against.")

  def on_finduseage(self, widget = None):
    useview.UseView(self.s, self.suffix)

  def on_slice(self, widget = None):
    if not self.selected_node.is_sliceable():
      self.statusbar.set_statusbar("Cannot slice on this element.")
      return

    window = sliceview.SliceView(self.main_window)
    window.geometry_dim_tree = self.geometry_dim_tree
    window.update(self.selected_node, self.tree)
    window.connect("destroy", self._slice_destroy)
    return

  def _slice_destroy(self, widget):
    self.on_select_row()


  groupmode = False

  def on_group(self, widget = None):
    """
    Clears the treeview and then fills it with nodes 
    with the same type as the selected node.
    """

    if self.selected_node == self.tree or not self.selected_iter:
      self.statusbar.set_statusbar("Cannot group on this element.")
      return #Group on the entire tree... ie don't group or nothing selected

    self.gui.get_widget("menuitemUngroup").show()
    self.gui.get_widget("popupmenuitemUngroup").show()

    self.groupmode = True
    node, tree = self.treestore.get(self.selected_iter, 0, 1)
    
    self.treeview.freeze_child_notify()
    self.treeview.set_model(None)

    def get_nodes(node, tree):
      nodes = []

      if isinstance(tree, choice.Choice):
        child = tree.get_current_tree()
        if child.name == node.name:
          nodes.append(tree)
        nodes += get_nodes(node, child)
      else:
        for child in tree.get_children():
          if child.name == node.name:
            nodes.append(child)
          nodes += get_nodes(node, child)

      return nodes
    
    self.set_treestore(None, get_nodes(tree, self.tree), True)

    self.treeview.set_model(self.treestore)
    self.treeview.thaw_child_notify()

    path = self.get_treestore_path_from_node(node)
    self.treeview.get_selection().select_path(path)

    return

  def on_ungroup(self, widget = None):
    """
    Restores the treeview to normal.
    """

    self.gui.get_widget("menuitemUngroup").hide()
    self.gui.get_widget("popupmenuitemUngroup").hide()

    self.groupmode = False
    node = self.treestore.get_value(self.selected_iter, 0)

    self.treeview.freeze_child_notify()
    self.treeview.set_model(None)

    self.set_treestore(None, [self.tree], True)

    self.treeview.set_model(self.treestore)
    self.treeview.thaw_child_notify()

    path = self.get_treestore_path_from_node(node)
    self.treeview.expand_to_path(path)
    self.treeview.scroll_to_cell(path)
    self.treeview.get_selection().select_path(path)
 
    return


  def on_data_summary(self, widget=None):
    """ Summarises the data to a few key facts
    """

    signals = {"data_summary_save_clicked": self.on_data_summary_save_clicked,
               "data_summary_output_close": self.on_data_summary_output_close}
    
    self.data_summary_gui = gtk.glade.XML(self.gladefile, root="data_summary_output")
    self.data_summary_dialog = self.data_summary_gui.get_widget("data_summary_output")
    textbox = self.data_summary_gui.get_widget("textview1")
    self.data_summary_gui.signal_autoconnect(signals)
    summary_button = self.data_summary_gui.get_widget("data_summary_save_button")
    summary_button.connect("activate", self.on_data_summary_save_clicked) 
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    try:
        data_summary = stk.data_summary(XML,detailed=True,ignoreWarnings=False)
    except NotUniqueError as detail:
        msg = "Failed to summarise data.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        data_summary = stk.data_summary(XML,detailed=True,ignoreWarnings=True)
    except InvalidSTKData as detail:
        msg = "Failed to summarise data.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        data_summary = stk.data_summary(XML,detailed=True,ignoreWarnings=True)        
    except UninformativeTreeError as detail:
        msg = "Failed to summarise data.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        data_summary = stk.data_summary(XML,detailed=True,ignoreWarnings=True)        


    textbox.get_buffer().set_text(data_summary)
    textbox.set_editable(False)
    self.data_summary_dialog.show()

    return


  def on_data_summary_output_close(self, widget=None):

    self.data_summary_dialog.hide() 

  
  def on_data_summary_save_clicked(self, widget=None):
    """ Save the data_summary
    """

    textbox = self.data_summary_gui.get_widget("textview1")
    buf = textbox.get_buffer()
    summary = buf.get_text(buf.get_start_iter(), buf.get_end_iter())
    filter_names_and_patterns = {}
    # open file dialog
    filename = dialogs.get_filename(title = "Choose output file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
    f = open(filename,'w')
    f.write(summary)
    f.close()


  def on_data_overlap(self, widget=None):
   
    
    signals = {"on_data_overlap_dialog_close": self.on_data_overlap_dialog_cancel_button,
               "on_data_overlap_dialog_cancel_clicked": self.on_data_overlap_dialog_cancel_button,
               "on_data_overlap_dialog_clicked": self.run_data_overlap,
               "on_data_overlap_dialog_browse_clicked": self.on_data_overlap_dialog_browse_button}

    self.data_overlap_gui = gtk.glade.XML(self.gladefile, root="data_overlap_dialog")
    self.dialog = self.data_overlap_gui.get_widget("data_overlap_dialog")
    self.data_overlap_gui.signal_autoconnect(signals)
    overlap = self.data_overlap_gui.get_widget("check_overlap_button")
    overlap.connect("activate", self.run_data_overlap)
    self.dialog.show()

    return
      
  def run_data_overlap(self, button):

    filename_textbox = self.data_overlap_gui.get_widget("entry1")
    filename = filename_textbox.get_text()
    graphic = self.data_overlap_gui.get_widget("checkbutton1").get_active()
    detailed = self.data_overlap_gui.get_widget("checkbutton2").get_active()
    ignoreWarnings = self.data_overlap_gui.get_widget("ignoreWarnings_checkbutton").get_active()
    overlap = max(int(self.data_overlap_gui.get_widget("spinbutton1").get_value()),2)

    show = False
    if (filename == "" and graphic):
        show = True
        filename = None
    elif (filename == ""):
        show = False
        filename = None

    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    if (show):
        try:
            sufficient_overlap, key_list, canvas = stk.data_overlap(XML,filename=filename,overlap_amount=overlap,show=show,detailed=detailed,ignoreWarnings=ignoreWarnings)
        except IOError as detail:
            msg = "Failed to calculate overlap.\n"+detail.message
            dialogs.error(self.main_window,msg)
            return
        except NotUniqueError as detail:
            msg = "Failed to calculate overlap.\n"+detail.msg
            dialogs.error(self.main_window,msg)
            return
        except InvalidSTKData as detail:
            msg = "Failed to calculate overlap.\n"+detail.msg
            dialogs.error(self.main_window,msg)
            return
        except UninformativeTreeError as detail:
            msg = "Failed to calculate overlap.\n"+detail.msg
            dialogs.error(self.main_window,msg)
            return 

    else:
        try:
            sufficient_overlap, key_list = stk.data_overlap(XML,filename=filename,overlap_amount=overlap,show=show,detailed=detailed,ignoreWarnings=ignoreWarnings)
            # we need to save the csv file too
            file_stub = os.path.splitext(filename)[0]
            csv_file = file_stub+"_"+str(overlap)+".csv"
            f = open(csv_file,"w")
            i = 0
            for key in key_list:
                if type(key).__name__=='list':
                    f.write(str(i)+","+",".join(key)+"\n")
                else:
                    f.write(str(i)+","+key+"\n")
                i = i+1
            f.close()

        except IOError as detail:
            msg = "Failed to calculate overlap.\n"+detail.message
            dialogs.error(self.main_window,msg)
            return
        except NotUniqueError as detail:
            msg = "Failed to calculate overlap.\n"+detail.msg
            dialogs.error(self.main_window,msg)
            return
        except InvalidSTKData as detail:
            msg = "Failed to calculate overlap.\n"+detail.msg
            dialogs.error(self.main_window,msg)
            return
        except UninformativeTreeError as detail:
            msg = "Failed to calculate overlap.\n"+detail.msg
            dialogs.error(self.main_window,msg)
            return 
    if (show):
        # create our show result interface
        signals = {"on_data_overlap_show_dialog_close": self.on_data_overlap_show_dialog_cancel_button}

        data_overlap_show_gui = gtk.glade.XML(self.gladefile, root="data_overlap_show_dialog")
        self.show_dialog = data_overlap_show_gui.get_widget("data_overlap_show_dialog")
        data_overlap_show_gui.signal_autoconnect(signals)
        draw = data_overlap_show_gui.get_widget("alignment1")
        treeview_holder = data_overlap_show_gui.get_widget("scrolledwindow1")
        draw.add(canvas)

        # set label appropriately
        infoLabel = data_overlap_show_gui.get_widget("informationLabel")
        infoLabel.set_use_markup=True
        if (sufficient_overlap):
            infoLabel.set_text('Your data are sufficiently well connected at this overlap level')
            infoLabel.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#00AA00'))
        else:
            infoLabel.set_text('Your data are not connected sufficiently at this overlap level')
            infoLabel.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#AA0000'))
        # now create the key table on the rhs
        liststore = gtk.ListStore(int,str)
        treeview = gtk.TreeView(liststore)
        treeview_holder.add(treeview)
        rendererText = gtk.CellRendererText()
        column = gtk.TreeViewColumn("ID", rendererText, text=0)
        column.set_sort_column_id(0)
        treeview.append_column(column)
        column2 = gtk.TreeViewColumn("Tree(s)", rendererText, text=1)
        column2.set_sort_column_id(1)
        treeview.append_column(column2)
        count = 0
        for id in key_list:
            if (detailed):
                liststore.append([count,id])
                count += 1
            else:
                for tree in id:
                    liststore.append([count,tree])
                count += 1

        self.show_dialog.show_all()
    else:
        # Need to make these clearer - big green tick and big red cross respectively
        show_msg = ""
        if not show:
            show_msg = ". File save to "+filename
        if sufficient_overlap:
            dialogs.error(self.main_window, "Your data are sufficiently well connected at this overlap level"+show_msg)
        else:
            dialogs.error(self.main_window, "Your data are not connected sufficiently at this overlap level"+show_msg)
    
    XML = stk.add_historical_event(XML, "Data overlap carried out on data. Result is: " + str(sufficient_overlap) + " with overlap of "+str(overlap))
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (data overlap) to XML", skip_warning=True)

    
  def on_data_overlap_dialog_cancel_button(self, button):
      """ Close the data overlap dialogue
      """
      self.dialog.hide()

  def on_data_overlap_show_dialog_cancel_button(self, button):
      """ Close the data overlap dialogue
      """
      self.show_dialog.hide()


  def on_data_overlap_dialog_browse_button(self, button):
      filter_names_and_patterns = {}
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output graphic fle", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
      filename_textbox = self.data_overlap_gui.get_widget("entry1")
      filename_textbox.set_text(filename)

  # Data independence GUI
  def on_data_ind(self, widget=None):
    """ Check the data independence of the data - display the GUI
        and call the function
    """

    signals = {"on_data_ind_dialog_close": self.on_data_ind_close_button,
               "on_data_ind_close": self.on_data_ind_close_button,
               "on_save_ind_data_phyml": self.on_data_ind_save_phyml_button,
               "on_save_ind_data": self.on_data_ind_save_data_button,
              } 
    self.data_ind_gui = gtk.glade.XML(self.gladefile, root="data_ind_dialog")
    self.data_ind_dialog = self.data_ind_gui.get_widget("data_ind_dialog")
    self.data_ind_gui.signal_autoconnect(signals)

    self.phyml_filename = None
    self.filename = None    
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    try:
        self.data_independence, self.new_phyml_data = stk.data_independence(XML,make_new_xml=True,ignoreWarnings=False)
    except NotUniqueError as detail:
        msg = "Failed to check data independence.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        self.data_independence, self.new_phyml_data = stk.data_independence(XML,make_new_xml=True,ignoreWarnings=True)
    except InvalidSTKData as detail:
        msg = "Failed to check data independence.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        self.data_independence, self.new_phyml_data = stk.data_independence(XML,make_new_xml=True,ignoreWarnings=True)
    except UninformativeTreeError as detail:
        msg = "Failed to check data independence.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        self.data_independence, self.new_phyml_data = stk.data_independence(XML,make_new_xml=True,ignoreWarnings=True)
    liststore = gtk.ListStore(str,str)
    treeview = gtk.TreeView(liststore)
    rendererText = gtk.CellRendererText()
    column = gtk.TreeViewColumn("Flagged tree", rendererText, text=0)
    treeview.append_column(column)
    column1 = gtk.TreeViewColumn("is subset of", rendererText, text=1)
    treeview.append_column(column1)
    for name in self.data_independence:
        count = 0
        if self.data_independence[name][1] == stk.SUBSET:
            clashes = self.data_independence[name][0].split(',')
            for c in clashes:
                if (count == 0):
                    liststore.append([name, c])
                else:
                    liststore.append([None, c])
                count +=1
            
    window = self.data_ind_gui.get_widget("scrolledwindow1")
    window.add(treeview)

    liststore = gtk.ListStore(str,str)
    treeview = gtk.TreeView(liststore)
    rendererText = gtk.CellRendererText()
    column = gtk.TreeViewColumn("Flagged tree", rendererText, text=0)
    treeview.append_column(column)
    column1 = gtk.TreeViewColumn("is identical to", rendererText, text=1)
    treeview.append_column(column1)
    for name in self.data_independence:
        count = 0
        if self.data_independence[name][1] == stk.IDENTICAL:
            clashes = self.data_independence[name][0].split(',')
            for c in clashes:
                if (count == 0):
                    liststore.append([name, c])
                else:
                    liststore.append([None, c])
                count +=1
            
    window = self.data_ind_gui.get_widget("scrolledwindow2")
    window.add(treeview)

    self.data_ind_dialog.show_all()

    return


  def on_data_ind_close_button(self,widget=None):
    # Add a history event
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    msg = "Data independence checked."
    if (not self.phyml_filename == None):
        msg = msg + " Phyml saved to: "+self.phyml_filename+"."
    if (not self.filename == None):
        msg = msg + " Independence data saved to: "+self.filename+"."
    XML = stk.add_historical_event(XML, msg)
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (create matrix) to XML", skip_warning=True)
    self.data_ind_dialog.hide()

  def on_data_ind_save_phyml_button(self,widget=None):

    # open browse window, grab filename
    filter_names_and_patterns = {}
    filter_names_and_patterns['Phyml file'] = ["*.phyml"]
    filter_names_and_patterns['All files'] = ["*"]
    # open file dialog
    self.phyml_filename = dialogs.get_filename(title = "Choose output file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)

    # check if files exist already
    if (os.path.exists(self.phyml_filename)):
        overwrite = dialogs.prompt(None,"Output phyml file exists. Overwrite?")
        if (overwrite == gtk.RESPONSE_NO):
            self.phyml_filename=None
            return

    f = open(self.phyml_filename,"w")
    f.write(self.new_phyml_data)
    f.close()
    return

  def on_data_ind_save_data_button(self,widget=None):

    # open browse window, grab filename
    filter_names_and_patterns = {}
    filter_names_and_patterns['CSV file'] = ["*.csv"]
    filter_names_and_patterns['All files'] = ["*"]
    # open file dialog
    self.filename = dialogs.get_filename(title = "Choose output file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)

    # check if files exist already
    if (os.path.exists(self.filename)):
        overwrite = dialogs.prompt(None,"Output file exists. Overwrite?")
        if (overwrite == gtk.RESPONSE_NO):
            self.filename = None
            return

    # process data
    data_ind = ""
    #column headers
    data_ind = "Source trees that are subsets of others\n"
    data_ind = data_ind + "Flagged tree, is a subset of:\n"
    for name in self.data_independence:
        if ( self.data_independence[name][1] == stk.SUBSET):
            data_ind += name + "," + self.data_independence[name][0] + "\n"
    data_ind = data_ind + "\n\nFlagged tree, is identical to:\n"
    for name in data_independence:
        if ( self.data_independence[name][1] == stk.IDENTICAL):
            data_ind += name + "," + self.data_independence[name][0] + "\n"
    f = open(self.filename,"w")
    f.write(data_ind)
    f.close()
    return

  #permute all tree GUI
  def on_permute_all_trees(self, widget=None):
    """ Permute all permutable trees in the data set and save them all
    """

    signals = {"on_permute_trees_dialog_close": self.on_permute_trees_cancel_button,
               "on_permute_trees_cancel_clicked": self.on_permute_trees_cancel_button,
               "on_permute_trees_clicked": self.on_permute_trees_button,
               "on_permute_trees_browse_clicked": self.on_permute_trees_browse_button}
      
    self.permute_trees_gui = gtk.glade.XML(self.gladefile, root="permute_trees_dialog")
    self.permute_trees_dialog = self.permute_trees_gui.get_widget("permute_trees_dialog")
    self.permute_trees_gui.signal_autoconnect(signals)
    matrix_file = self.permute_trees_gui.get_widget("permute_trees_button")
    matrix_file.connect("activate", self.on_permute_trees_button)
    self.permute_trees_dialog.show()

      
  def on_permute_trees_button(self, button):
    """
    create the trees
    """

    filename_textbox = self.permute_trees_gui.get_widget("entry1")
    filename = filename_textbox.get_text()
    format_radio_1 = self.permute_trees_gui.get_widget("matrix_format_tnt_chooser")
    format_radio_2 = self.permute_trees_gui.get_widget("matrix_format_nexus_chooser")
    format_radio_3 = self.permute_trees_gui.get_widget("tree_format_nexus_chooser")
    format_radio_4 = self.permute_trees_gui.get_widget("tree_format_newick_chooser")
    format_radio_5 = self.permute_trees_gui.get_widget("tree_format_tnt_chooser")

    if (format_radio_1.get_active()):
        format = 'hennig'
        treefile=None
    elif (format_radio_2.get_active()):
        format = 'nexus'
        treefile=None
    elif (format_radio_3.get_active()):
        treefile = 'Newick'
    elif (format_radio_4.get_active()):
        treefile = 'Nexus'
    elif (format_radio_5.get_active()):
        treefile = 'tnt'
    else:
        format = None
        dialogs.error(self.main_window,"Error creating matrix. Incorrect format.")
        return

    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    all_trees = stk.obtain_trees(XML)
    # get all trees
    tree_list = stk._find_trees_for_permuting(XML)

    for t in tree_list:
        # permute
        if (not treefile == None):
            output_string = stk.permute_tree(tree_list[t],treefile=treefile)
        else:
            output_string = stk.permute_tree(tree_list[t],matrix=format,treefile=None)

        #save
        new_output,ext = os.path.splitext(filename)
        new_output += "_"+t+ext
        f = open(new_output,'w')
        f.write(output_string)
        f.close
  

    # Add a history event
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    XML = stk.add_historical_event(XML, "Permuted trees written to: "+filename)
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (permute_trees) to XML", skip_warning=True)

    
    self.permute_trees_dialog.hide()

    return

  def on_permute_trees_cancel_button(self, button):
      """ Close the permute_trees dialogue
      """

      self.permute_trees_dialog.hide()

  def on_permute_trees_browse_button(self, button):
      filter_names_and_patterns = {}
      filter_names_and_patterns['Phylo files'] = ["*.tre","*nex","*.nwk","*.new","*.tnt"]
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
      filename_textbox = self.permute_trees_gui.get_widget("entry1")
      filename_textbox.set_text(filename)


  #STR GUI
  def on_str(self, widget=None):
    """ Perform STR in the dataset
    """

    signals = {"on_str_dialog_close": self.on_str_cancel_button,
               "on_str_cancel_clicked": self.on_str_cancel_button,
               "on_str_clicked": self.on_str_button,
               "on_str_browse_clicked": self.on_str_browse_button}
      
    self.str_gui = gtk.glade.XML(self.gladefile, root="str_dialog")
    self.str_dialog = self.str_gui.get_widget("str_dialog")
    str_progressbar = self.str_gui.get_widget("progressbar1")
    str_progressbar.set_fraction(0.)
    self.str_gui.signal_autoconnect(signals)
    self.str_dialog.show()


  def on_str_button(self, button):
    """
    Actually do the STR
    """
    from multiprocessing import Queue, Process
    import time

    filename_textbox = self.str_gui.get_widget("entry1")
    filename = filename_textbox.get_text()
    delete_subs_checkbox = self.str_gui.get_widget("checkbutton1")
    replace_subs_checkbox = self.str_gui.get_widget("checkbutton2")
    ignoreWarnings = self.str_gui.get_widget("ignoreWarnings_checkbutton").get_active()

    delete_subs = False
    replace_subs = False
    if (delete_subs_checkbox.get_active()):
        delete_subs = True
    if (replace_subs_checkbox.get_active()):
        replace_subs = True
   
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    # Set up progress bar
    str_progressbar = self.str_gui.get_widget("progressbar1")
    str_progressbar.set_pulse_step(0.1)
    self.str_q = Queue()
    # make the fourth argument true for verbose output
    try:
        self.str_p = Process(target=stk.safe_taxonomic_reduction,args=(XML,None,None,False,self.str_q,ignoreWarnings))
    except NotUniqueError as detail:
        msg = "Failed to calculate STR.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except InvalidSTKData as detail:
        msg = "Failed to calculate STR.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except UninformativeTreeError as detail:
        msg = "Failed to calculate STR.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return 
    self.str_p.start()
    waiting=True
    while waiting:
        try:
            output, can_replace= self.str_q.get(True,0.1)
            waiting=False
        except Queue.empty:
            str_progressbar.pulse()
            time.sleep(0.5)
            while gtk.events_pending():
                gtk.main_iteration()
    self.str_p.join()
    if (replace_subs):
        substitutions = stk.subs_file_from_str(output)

    if (filename == ""):
        dialogs.long_message(self.main_window, output,monospace=True)
    else:
        f = open(filename,"w")
        f.write(output)
        f.close()

    if (replace_subs):
        if (filename == ''):
            from os.path import expanduser
            home = expanduser("~")
            filename = os.path.join(home,"str.dat")
        filename_stub =  os.path.splitext(filename)[0]
        subs_replace = filename_stub+"_subs_replace"
        subs_delete = filename_stub+"_subs_delete"

        f = open(subs_replace, "w")
        for r in substitutions:
            f.write(r+"\n")
        f.close()
    if (delete_subs):
        f = open(subs_delete, "w")
        for d in can_replace:
            f.write(d+" = \n")
        f.close()


    # Add a history event
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    XML = stk.add_historical_event(XML, "STR matrix written to: "+filename)
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (STR) to XML", skip_warning=True)

    
    self.str_dialog.hide()

    return

  def on_str_cancel_button(self, button):
      """ Close the STR dialogue
      """
         
      try:
        self.str_p.terminate()
      except:
          pass
      self.str_dialog.hide()
      while gtk.events_pending():
        gtk.main_iteration()

  def on_str_browse_button(self, button):
      filter_names_and_patterns = {}
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output file", action = gtk.FILE_CHOOSER_ACTION_SAVE, folder_uri = self.file_path)
      filename_textbox = self.str_gui.get_widget("entry1")
      filename_textbox.set_text(filename)



  # create a matrix
  def on_create_matrix(self, widget=None):
    """ Creates a MRP matrix from the data in the phyml. Actually, this function
        merely opens the dialog form the glade file...
    """

    signals = {"on_create_matrix_dialog_close": self.on_create_matrix_cancel_button,
               "on_create_matrix_cancel_clicked": self.on_create_matrix_cancel_button,
               "on_create_matrix_clicked": self.on_create_matrix_create_matrix_button,
               "on_create_matrix_browse_clicked": self.on_create_matrix_browse_button}

    self.create_matrix_gui = gtk.glade.XML(self.gladefile, root="create_matrix_dialog")
    self.create_matrix_dialog = self.create_matrix_gui.get_widget("create_matrix_dialog")
    self.create_matrix_gui.signal_autoconnect(signals)
    matrix_file = self.create_matrix_gui.get_widget("create_matrix_button")
    matrix_file.connect("activate", self.on_create_matrix_create_matrix_button)
    self.create_matrix_dialog.show()

    return
      
  def on_create_matrix_create_matrix_button(self, button):
    """
    create the matrix requested 
    """

    filename_textbox = self.create_matrix_gui.get_widget("entry1")
    filename = filename_textbox.get_text()
    format_radio_1 = self.create_matrix_gui.get_widget("matrix_format_tnt_chooser")
    format_radio_2 = self.create_matrix_gui.get_widget("matrix_format_nexus_chooser")
    ignoreWarnings = self.create_matrix_gui.get_widget("ignoreWarnings_checkbutton").get_active()


    if (format_radio_1.get_active()):
        format = 'hennig'
    elif (format_radio_2.get_active()):
        format = 'nexus'
    else:
        format = None
        dialogs.error(self.main_window,"Error creating matrix. Incorrect format.")
        return

    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    try:
        matrix = stk.create_matrix(XML,format=format,ignoreWarnings=ignoreWarnings)
    except NotUniqueError as detail:
        msg = "Failed to create matrix.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except InvalidSTKData as detail:
        msg = "Failed to create matrix.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except UninformativeTreeError as detail:
        msg = "Failed to create matrix.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return 
    
    try:
        f = open(filename, "w")
        f.write(matrix)
        f.close()    
    except:
        msg = "Failed to create matrix file.\n"
        dialogs.error(self.main_window,msg)
        return 

    # Add a history event
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    XML = stk.add_historical_event(XML, "Matrix written to: "+filename)
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (create matrix) to XML", skip_warning=True)

    
    self.create_matrix_dialog.hide()

    return

  def on_create_matrix_cancel_button(self, button):
      """ Close the create_matrix dialogue
      """

      self.create_matrix_dialog.hide()

  def on_create_matrix_browse_button(self, button):
      filter_names_and_patterns = {}
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output matrix file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
      filename_textbox = self.create_matrix_gui.get_widget("entry1")
      filename_textbox.set_text(filename)


  def on_export(self, widget=None):
    """ Export data to old-style STK data
    """

    signals = {"on_export_dialog_close": self.on_export_cancel_button,
               "on_export_cancel_clicked": self.on_export_cancel_button,
               "on_export_button_clicked": self.on_export_button,
               "on_export_browse_clicked": self.on_export_browse_button}

    self.export_gui = gtk.glade.XML(self.gladefile, root="export_data_dialog")
    self.export_dialog = self.export_gui.get_widget("export_data_dialog")
    self.export_gui.signal_autoconnect(signals)
    export_button = self.export_gui.get_widget("export_button")
    export_button.connect("activate", self.on_export_button)
    self.export_dialog.show()

    return
      
  def on_export_button(self, button):

    filename_textbox = self.export_gui.get_widget("entry1")
    filename = filename_textbox.get_text()
    ignoreWarnings = self.export_gui.get_widget("ignoreWarnings_checkbutton").get_active()


    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
    try:
        stk_import_export.export_to_old(XML,filename,verbose=False,ignoreWarnings=ignoreWarnings) 
    except STKImportExportError as e:
        dialogs.error(self.main_window, e.msg)
        return
    except NotUniqueError as detail:
        msg = "Failed to export data.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except InvalidSTKData as detail:
        msg = "Failed to export data.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except UninformativeTreeError as detail:
        msg = "Failed to export data.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return     
    except:
        dialogs.error(self.main_window, "Error exporting.")
        return
    
    self.export_dialog.hide()
    # Add a history event
    XML = stk.add_historical_event(XML, "Data exported to: "+filename)
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (data export) to XML",skip_warning=True)

    return

  def on_export_cancel_button(self, button):
      """ Close the export dialogue
      """

      self.export_dialog.hide()

  def on_export_browse_button(self, button):
      filter_names_and_patterns = {}
      # open file dialog
      filename = dialogs.get_filename(title = "Choose export directory", action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
      filename_textbox = self.export_gui.get_widget("entry1")
      filename_textbox.set_text(filename)

      return

  def on_import(self, widget=None):
    """ Export data to old-style STK data
    """

    signals = {"on_import_dialog_close": self.on_import_cancel_button,
               "on_import_cancel_clicked": self.on_import_cancel_button,
               "on_import_button_clicked": self.on_import_button,
               "on_import_browse_clicked": self.on_import_browse_button}

    self.import_gui = gtk.glade.XML(self.gladefile, root="import_data_dialog")
    self.import_dialog = self.import_gui.get_widget("import_data_dialog")
    self.import_gui.signal_autoconnect(signals)
    import_button = self.import_gui.get_widget("import_button")
    import_button.connect("activate", self.on_import_button)
    self.import_dialog.show()

    return
      
  def on_import_button(self, button):

    filename_textbox = self.import_gui.get_widget("entry1")
    filename = filename_textbox.get_text()

    try:
        XML = stk_import_export.import_old_data(filename,verbose=False)
    except:
           dialogs.error_tb(self.main_window, "Error parsing the old-style XML files. Please see the manual for the correct XML syntax.")
           return
    XML = _removeNonAscii(XML)
    # Add a history event
    XML = stk.add_historical_event(XML, "Data imported from: "+filename)
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error importing data whilst checking XML")

    #except STKImportExportError as e:
    #    dialogs.error(self.main_window, e.msg)
    #except:
    #    dialogs.error(self.main_window, "Error importing.")


    
    self.import_dialog.hide()

    return

  def on_import_cancel_button(self, button):
      """ Close the import dialogue
      """

      self.import_dialog.hide()

  def on_import_browse_button(self, button):
      filter_names_and_patterns = {}
      # open file dialog
      filename = dialogs.get_filename(title = "Choose import directory", action = gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
      filename_textbox = self.import_gui.get_widget("entry1")
      filename_textbox.set_text(filename)


  def on_export_trees(self,widget=None):
    """ Export all tree strings in the XML to a single file
          Can be made anonymous or labelled by a unique identifier
    """
    signals = {"on_export_trees_close": self.on_export_trees_close,
               "on_export_trees_cancelled_clicked": self.on_export_trees_close,
               "on_export_trees_clicked": self.on_export_trees_save}

    self.export_trees_gui = gtk.glade.XML(self.gladefile, root="export_trees")
    self.export_trees_dialog = self.export_trees_gui.get_widget("export_trees")
    self.export_trees_gui.signal_autoconnect(signals)
    self.export_trees_dialog.show()


  def on_export_trees_close(self, widget=None):
      
    self.export_trees_dialog.hide()


  def on_export_trees_save(self, widget=None):
     
      format_radio_1 = self.export_trees_gui.get_widget("tree_format_nexus_chooser")
      format_radio_2 = self.export_trees_gui.get_widget("tree_format_newick_chooser")
      format_radio_3 = self.export_trees_gui.get_widget("tree_format_tnt_chooser")
      anon_check = self.export_trees_gui.get_widget("checkbutton1")
      ignoreWarnings = self.export_trees_gui.get_widget("ignoreWarnings_checkbutton").get_active()

      if (format_radio_1.get_active()):
          format = 'Nexus'
      elif (format_radio_2.get_active()):
          format = 'Newick'
      elif (format_radio_3.get_active()):
          format = 'tnt'
      else:
        format = None
        dialogs.error(self.main_window,"Error exporting trees. Incorrect format.")
        return
      anonymous = False
      if anon_check.get_active():
          anonymous = True

      
      f = StringIO.StringIO()
      self.tree.write(f)
      XML = f.getvalue()
      try:
        self.output_string = stk.amalgamate_trees(XML,format=format,anonymous=anonymous,ignoreWarnings=ignoreWarnings)
      except NotUniqueError as detail:
        msg = "Failed to export trees.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
      except InvalidSTKData as detail:
        msg = "Failed to export trees.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
      except UninformativeTreeError as detail:
        msg = "Failed to export trees.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return 

      filter_names_and_patterns = {}
      filter_names_and_patterns['Trees'] = ["*.tre","*nex","*.nwk","*.tnt"]
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output trees fle", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)

      f = open(filename,"w")
      f.write(self.output_string)
      f.close()

      XML = stk.add_historical_event(XML, "Tree exported to: "+filename)
      ios = StringIO.StringIO(XML)
      self.update_data(ios, "Error adding history event (export trees) to XML", skip_warning=True)
      self.export_trees_dialog.hide()

      return

## Export Bibliography
  def on_export_bib(self,widget=None):
    """ Export all tree strings in the XML to a single file
          Can be made anonymous or labelled by a unique identifier
    """
    signals = {"on_export_bib_close": self.on_export_bib_close,
               "on_export_bib_cancelled_clicked": self.on_export_bib_close,
               "on_export_bib_clicked": self.on_export_bib_save}

    self.export_bib_gui = gtk.glade.XML(self.gladefile, root="export_bib")
    self.export_bib_dialog = self.export_bib_gui.get_widget("export_bib")
    self.export_bib_gui.signal_autoconnect(signals)
    self.export_bib_dialog.show()


  def on_export_bib_close(self, widget=None):
      
    self.export_bib_dialog.hide()


  def on_export_bib_save(self, widget=None):
     
      format_radio_1 = self.export_bib_gui.get_widget("file_format_bibtex_chooser")
      format_radio_2 = self.export_bib_gui.get_widget("file_format_latex_chooser")
      format_radio_3 = self.export_bib_gui.get_widget("file_format_html_chooser")
      format_radio_4 = self.export_bib_gui.get_widget("file_format_long_chooser")
      format_radio_5 = self.export_bib_gui.get_widget("file_format_short_chooser")
      if (format_radio_1.get_active()):
          format = 'bibtex'
      elif (format_radio_2.get_active()):
          format = 'latex'
      elif (format_radio_3.get_active()):
          format = 'html'      
      elif (format_radio_4.get_active()):
          format = 'long'
      elif (format_radio_5.get_active()):
          format = 'short'
      else:
        format = None
        dialogs.error(self.main_window,"Error exporting bibliographic information. Incorrect format.")
        return
      

      filter_names_and_patterns = {}
      filter_names_and_patterns['Trees'] = ["*.bib","*.html","*.txt","*.tex"]
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output fle", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)

      f = StringIO.StringIO()
      self.tree.write(f)
      XML = f.getvalue()
      self.output_string = stk.export_bibliography(XML,filename,format=format)

      XML = stk.add_historical_event(XML, "Bibliographic information exported to: "+filename)
      ios = StringIO.StringIO(XML)
      self.update_data(ios, "Error adding history event (export bibliography) to XML", skip_warning=True)
      self.export_bib_dialog.hide()

      return


  def on_sub_taxa(self, widget=None):
    """ Substitute taxa in the tree. Actually, this function
        merely opens the dialog form the glade file...
    """

    signals = {"on_sub_taxa_dialog_close": self.on_sub_taxa_cancel_button,
               "on_sub_taxa_cancel_clicked": self.on_sub_taxa_cancel_button,
               "on_sub_taxa_clicked": self.on_sub_taxa_sub_taxa_button,
               "on_move_to_subs_clicked": self.on_move_to_subs_clicked,
               "on_remove_from_subs_clicked": self.on_remove_from_subs_clicked,
               "on_reset_clicked": self.on_reset_clicked,
               "on_import_subs_clicked": self.on_import_subs_clicked,
               "on_export_subs_clicked": self.on_export_subs_clicked}

    self.sub_taxa_gui = gtk.glade.XML(self.gladefile, root="sub_taxa_dialog")
    self.sub_taxa_dialog = self.sub_taxa_gui.get_widget("sub_taxa_dialog")
    self.sub_taxa_gui.signal_autoconnect(signals)
    sub_taxa_button = self.sub_taxa_gui.get_widget("sub_taxa_button")
    sub_taxa_button.connect("activate", self.on_sub_taxa_sub_taxa_button)
    self.taxa_list_treeview = self.sub_taxa_gui.get_widget("treeview_taxa_list")
    self.sub_list_treeview = self.sub_taxa_gui.get_widget("treeview_sub_taxa")

    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()

    # construct list and treeview
    taxa = stk.get_all_taxa(XML)
    self.liststore_taxa = gtk.ListStore(str)
    rendererText = gtk.CellRendererText()
    column = gtk.TreeViewColumn("Taxa in data", rendererText, text=0)
    self.taxa_list_treeview.append_column(column)
    for t in taxa:
        self.liststore_taxa.append([t])
    self.taxa_list_treeview.set_model(self.liststore_taxa)

    # now set up the other list
    self.liststore_sub = gtk.ListStore(str,str)
    rendererText = gtk.CellRendererText()
    column = gtk.TreeViewColumn("Taxa to be subbed", rendererText, text=0)
    self.sub_list_treeview.append_column(column)
    column1 = gtk.TreeViewColumn("Subs", rendererText, text=1)
    self.sub_list_treeview.append_column(column1)
    # No data yet
 
    self.sub_taxa_dialog.show_all()

    return

  def on_export_subs_clicked(self, button):
    
      # get data from RH tree view and create a subs file
      pass

  def on_import_subs_clicked(self,button):

      # read in a subs file an populate the RHS

      # Need to check for existing taxa, etc?
      pass

  def on_reset_clicked(self,button):

      # clear the RHS liststore
      self.liststore_sub.clear()
      # restore LHS to taxa list
      self.liststore_taxa.clear()
      f = StringIO.StringIO()
      self.tree.write(f)
      XML = f.getvalue()
      taxa = stk.get_all_taxa(XML)
      for t in taxa:
        self.liststore_taxa.append([t])
      
      return

  def on_remove_from_subs_clicked(self,button):

      # Move a sub from the RHS and put the old taxon back to LHS

      return

  def on_move_to_subs_clicked(self,button):

      # move the selected taxa to RHS with empty sub

      return

      
  def on_sub_taxa_sub_taxa_button(self, button):
    """
    substitute taxa 
    """

    # open browse button and get a filename
    filter_names_and_patterns = {}
    filter_names_and_patterns['Phyml file'] = ["*.phyml"]
    filter_names_and_patterns['All files'] = ["*"]
    # open file dialog
    filename = dialogs.get_filename(title = "Choose output PHYML fle", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)

    old_taxon = self.sub_taxa_gui.get_widget("old_taxon").get_text()
    new_taxon = self.sub_taxa_gui.get_widget("new_taxon").get_text()
    ignoreWarnings = self.sub_taxa_gui.get_widget("ignoreWarnings_checkbutton").get_active()
    
    f = StringIO.StringIO()
    self.tree.write(f)
    XML = f.getvalue()
   
    try:
        XML2 = stk.sub_taxa(XML,old_taxon,new_taxon,ignoreWarnings=ignoreWarnings)
    except NotUniqueError as detail:
        msg = "Failed to substitute taxa.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except InvalidSTKData as detail:
        msg = "Failed to substitute taxa.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
    except UninformativeTreeError as detail:
        msg = "Failed to substitute taxa.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return 
    event_desc = "Taxa substitution from "+old_taxa+" to "+new_taxa+" via GUI to "+filename
    XML2 = stk.add_historical_event(XML2,event_desc) 
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (taxa sub) to new XML",skip_warning=True)


    f = open(filename, "w")
    f.write(XML2)
    f.close()    

    # Add an event to the history of the file
    event_desc = "Taxa substitution from "+old_taxa+" to "+new_taxa+" via GUI to "+filename
    XML = stk.add_historical_event(XML,event_desc) 
    ios = StringIO.StringIO(XML)
    self.update_data(ios, "Error adding history event (taxa sub) to XML",skip_warning=True)
    
    self.sub_taxa_dialog.hide()

    return

  def on_sub_taxa_cancel_button(self, button):
      """ Close the sub_taxa dialogue
      """

      self.sub_taxa_dialog.hide()

  
  def on_import_bib(self, widget = None):
     """
     Imports a bibtex file and sets up a number of sources
     """
     filter_names_and_patterns = {}
     filter_names_and_patterns['Bibtex file'] = ["*.bib"]
     filter_names_and_patterns['All files'] = ["*"]
     filename = dialogs.get_filename(title = "Choose .bib fle", action = gtk.FILE_CHOOSER_ACTION_OPEN, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
     
     f = StringIO.StringIO()
     self.tree.write(f)
     XML = f.getvalue() 
     if (filename == None):
         return

     try:
        XML = stk.import_bibliography(XML, filename)
        XML = _removeNonAscii(XML)
        XML = stk.add_historical_event(XML, "Bibliographic information imported from: "+filename)
        ios = StringIO.StringIO(XML)
     except BibImportError as detail:
        dialogs.error(self.main_window,detail.msg)
        return 
     except:
         dialogs.error(self.main_window,"Error importing bib file")
         return
     
     try:
        stk._check_uniqueness(XML)
     except:
        dialogs.error(self.main_window,"Duplicated or unamed source. Suggest you run standardise source names")

     self.update_data(ios, "Error converting bib file to XML", skip_warning=True)
     
     return  


  def on_standardise_names(self, widget = None):
     """
     Standardises source names to Author1_Author2_Year
     """
     f = StringIO.StringIO()
     self.tree.write(f)
     XML = f.getvalue() 
     try:
        XML = stk.all_sourcenames(XML)
     except NoAuthors as detail:
        dialogs.error(self.main_window,detail.msg)
        return 
         
     XML = _removeNonAscii(XML)
     # Add a history event
     XML = stk.add_historical_event(XML, "Source names standardised")
     ios = StringIO.StringIO(XML)

     self.update_data(ios, "Error standardising names")

     return 



  def on_clean_data(self, widget = None):
     """
     cleans up the data
     """
     f = StringIO.StringIO()
     self.tree.write(f)
     XML = f.getvalue() 
     XML = stk.clean_data(XML)
     try:
        XML = stk.all_sourcenames(XML)
     except NoAuthors as detail:
        dialogs.error(self.main_window,detail.msg)
        return 
         
     XML = _removeNonAscii(XML)
     # Add a history event
     XML = stk.add_historical_event(XML, "Cleaned data")
     ios = StringIO.StringIO(XML)

     self.update_data(ios, "Error cleaning data")

     return 

  def on_replace_genera(self, widget = None):
    signals = {"on_replace_genera_dialog_close": self.on_replace_genera_cancel_button,
               "on_replace_genera_cancel_clicked": self.on_replace_genera_cancel_button,
               "on_replace_genera_button_clicked": self.on_replace_genera_click,
               "on_replace_genera_subs_browse_clicked": self.on_replace_genera_subs_browse_button,
               "on_replace_genera_phyml_browse_clicked": self.on_replace_genera_phyml_browse_button
               }

    self.replace_genera_gui = gtk.glade.XML(self.gladefile, root="replace_genera_dialog")
    self.replace_genera_dialog = self.replace_genera_gui.get_widget("replace_genera_dialog")
    self.replace_genera_gui.signal_autoconnect(signals)
    self.replace_genera_dialog.show()

    return

  def on_replace_genera_click(self, widget = None):
     """
     replace generic level taxa with a polytomy of specific taxa in the dataset belonging to that genera
     """

     gen_subs = self.replace_genera_gui.get_widget("replace_genera_subs_checkbox").get_active()
     gen_phyml = self.replace_genera_gui.get_widget("replace_genera_phyml_checkbox").get_active()
     ignoreWarnings = self.replace_genera_gui.get_widget("ignoreWarnings_checkbutton").get_active()
     filename_subs = self.replace_genera_gui.get_widget("entry1").get_text()
     filename_phyml = self.replace_genera_gui.get_widget("entry2").get_text()


     f = StringIO.StringIO()
     self.tree.write(f)
     XML = f.getvalue() 
     try:
        new_XML,genera,subs = stk.replace_genera(XML,ignoreWarnings=ignoreWarnings)
     except NotUniqueError as detail:
        msg = "Failed to replace generic taxa.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
     except InvalidSTKData as detail:
        msg = "Failed to replace generic taxa.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return
     except UninformativeTreeError as detail:
        msg = "Failed to replace generic taxa.\n"+detail.msg
        dialogs.error(self.main_window,msg)
        return 

     if (gen_subs):
         try:
            subs_file = open(filename_subs, "w")
            i = 0
            for g in genera:
                subs_file.write(g+" = "+subs[i]+"\n")
                i+=1
            subs_file.close()
         except IOError as detail:
            msg = "Failed to save subs file.\n"+detail.message
            dialogs.error(self.main_window,msg)
         except:
            msg = "Failed to save subs file.\n"
            dialogs.error(self.main_window,msg)
            return

     if (gen_phyml):
         try:
            phyml = open(filename_phyml, "w")
            phyml.write(new_XML)
            phyml.close()    
         except IOError as detail:
            msg = "Failed to save phyml file.\n"+detail.message
            dialogs.error(self.main_window,msg)
         except:
            msg = "Failed to save phyml file.\n"
            dialogs.error(self.main_window,msg)
            return
         
     XML = _removeNonAscii(XML)
     # Add a history event
     msg = "Replace generic taxa. "
     if (gen_subs):
         msg += "Subs file saved to "+filename_subs+" "
     if (gen_phyml):
         msg += "New Phyml saved to "+filename_phyml
     XML = stk.add_historical_event(XML, msg)
     ios = StringIO.StringIO(XML)

     self.update_data(ios, "Error replacing genera")

     return 

  def on_replace_genera_cancel_button(self, button):

      self.replace_genera_dialog.hide()

  def on_replace_genera_subs_browse_button(self, button):
      filter_names_and_patterns = {}
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output subs file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
      filename_textbox = self.replace_genera_gui.get_widget("entry1")
      filename_textbox.set_text(filename)
  def on_replace_genera_phyml_browse_button(self, button):
      filter_names_and_patterns = {}
      # open file dialog
      filename = dialogs.get_filename(title = "Choose output phyml file", action = gtk.FILE_CHOOSER_ACTION_SAVE, filter_names_and_patterns = filter_names_and_patterns, folder_uri = self.file_path)
      filename_textbox = self.replace_genera_gui.get_widget("entry2")
      filename_textbox.set_text(filename)


  def update_data(self,ios, error, skip_warning=False):

     try:
        tree_read = self.s.read(ios)

        if tree_read is None:
           dialogs.error_tb(self.main_window, error)
           return

        if (not skip_warning):
           errors = self.s.read_errors()
           lost_eles, added_eles, lost_attrs, added_attrs = errors
           if (len(lost_eles) > 0 or len(lost_attrs) > 0):
              self.display_validation_errors(self.s.read_errors())
        self.tree = tree_read
     except:
        dialogs.error_tb(self.main_window, error)
        return

     path = None
     if (self.selected_iter):
        path = self.treestore.get_path(self.selected_iter)

     self.set_saved(False)
     self.treeview.freeze_child_notify()
     self.treeview.set_model(None)
     self.signals = {}
     self.set_treestore(None, [self.tree], True)
     self.treeview.set_model(self.treestore)
     self.treeview.thaw_child_notify()
     self.set_geometry_dim_tree()
     self.treeview.expand_to_path(path)    
     # We *must* select the path again otherwise we get a segfault if the user alters the XML
     # without clicking on a path first.
     self.treeview.get_selection().select_path(path)    
     self.scherror.destroy_error_list()

     return

  ## LHS ###

  def init_datatree(self):
    """
    Add the root node of the XML tree to the treestore, and its children.
    """

    if self.schemafile is None:
      self.set_treestore(None, [])
      self.tree = None
    else:
      l = self.s.valid_children(":start")

      self.tree = l[0]
      self.signals = {}
      self.set_treestore(None, l)

    root_iter = self.treestore.get_iter_first()
    self.treeview.freeze_child_notify()
    self.treeview.set_model(None)
    self.expand_treestore(root_iter)
    self.treeview.set_model(self.treestore)
    self.treeview.thaw_child_notify()

    return

  def init_treemodel(self):
    """
    Set up the treestore and treeview.
    """

    self.treeview = optionsTree = self.gui.get_widget("optionsTree")
    self.treeview.connect("key_press_event", self.on_treeview_key_press)
    self.treeview.connect("button_press_event", self.on_treeview_button_press)
    self.treeview.connect("row-activated", self.on_activate_row)
    self.treeview.connect("popup_menu", self.on_treeview_popup)

    self.treeview.set_property("rules-hint", True)

    self.treeview.get_selection().set_mode(gtk.SELECTION_SINGLE)
    self.treeview.get_selection().connect("changed", self.on_select_row)
    self.treeview.get_selection().set_select_function(self.options_tree_select_func)
    self.options_tree_select_func_enabled = True

    # Node column
    column = gtk.TreeViewColumn("Node")
    column.set_property("expand", True)
    column.set_resizable(True)

    self.cellcombo = cellCombo = gtk.CellRendererCombo()
    cellCombo.set_property("text-column", 0)
    cellCombo.set_property("editable", True)
    cellCombo.set_property("has-entry", False)
    cellCombo.connect("changed", self.cellcombo_changed)
    column.pack_start(cellCombo)
    column.set_cell_data_func(cellCombo, self.set_combobox_liststore)

    self.choicecell = choiceCell = gtk.CellRendererPixbuf()
    column.pack_end(choiceCell, expand=False)
    column.set_cell_data_func(choiceCell, self.set_cellpicture_choice)

    optionsTree.append_column(column)

    self.imgcell = cellPicture = gtk.CellRendererPixbuf()
    self.imgcolumn = imgcolumn = gtk.TreeViewColumn("", cellPicture)
    imgcolumn.set_property("expand", False)
    imgcolumn.set_property("fixed-width", 20)
    imgcolumn.set_property("sizing", gtk.TREE_VIEW_COLUMN_FIXED)
    imgcolumn.set_cell_data_func(cellPicture, self.set_cellpicture_cardinality)
    optionsTree.append_column(imgcolumn)

    # 0: pointer to node in self.tree -- a choice or a tree
    # 1: pointer to currently active tree
    # 2: gtk.ListStore containing the display names of possible choices

    self.treestore = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
    self.treeview.set_model(self.treestore)
    self.treeview.set_enable_search(False)

    return

  def create_liststore(self, choice_or_tree):
    """
    Given a list of possible choices, create the liststore for the
    gtk.CellRendererCombo that contains the names of possible choices.
    """

    liststore = gtk.ListStore(str, gobject.TYPE_PYOBJECT)

    for t in choice_or_tree.get_choices():
      liststore.append([str(t), t])

    return liststore
  
  def set_treestore(self, iter=None, new_tree=[], recurse=False, replace=False):
    """
    Given a list of children of a node in a treestore, stuff them in the treestore.
    """

    if replace:
      replacediter = iter
      iter = self.treestore.iter_parent(replacediter)
    else: 
      self.remove_children(iter)
  
    for t in new_tree:
      if t is not None and t in self.signals:
        t.disconnect(self.signals[t][0])
        t.disconnect(self.signals[t][1])

      if isinstance(t, tree.Tree):
        if t.is_hidden():
          attrid = t.connect("on-set-attr", self.on_set_attr, self.treestore.get_path(iter))
          dataid = t.connect("on-set-data", self.on_set_data, self.treestore.get_path(iter))
          self.signals[t] = (attrid, dataid)
          continue

        liststore = self.create_liststore(t)

        if replace:
          child_iter = self.treestore.insert_before(iter, replacediter, [t, t, liststore])
        else:
          child_iter = self.treestore.append(iter, [t, t, liststore])

        attrid = t.connect("on-set-attr", self.on_set_attr, self.treestore.get_path(child_iter))
        dataid = t.connect("on-set-data", self.on_set_data, self.treestore.get_path(child_iter))
        self.signals[t] = (attrid, dataid)
 
        if recurse and t.active: self.set_treestore(child_iter, t.children, recurse)

      elif isinstance(t, choice.Choice):
        liststore = self.create_liststore(t)
        ts_choice = t.get_current_tree()
        if ts_choice.is_hidden():
          attrid = t.connect("on-set-attr", self.on_set_attr, self.treestore.get_path(iter))
          dataid = t.connect("on-set-data", self.on_set_data, self.treestore.get_path(iter))
          self.signals[t] = (attrid, dataid)
          continue

        if replace:
          child_iter = self.treestore.insert_before(iter, replacediter, [t, ts_choice, liststore])
        else:
          child_iter = self.treestore.append(iter, [t, ts_choice, liststore])

        attrid = t.connect("on-set-attr", self.on_set_attr, self.treestore.get_path(child_iter))
        dataid = t.connect("on-set-data", self.on_set_data, self.treestore.get_path(child_iter))
        self.signals[t] = (attrid, dataid)

        if recurse and t.active: self.set_treestore(child_iter, ts_choice.children, recurse)

    if replace:
      self.treestore.remove(replacediter)
      return child_iter
   
    return iter

  def expand_choice_or_tree(self, choice_or_tree):
    """
    Query the schema for what valid children can live under this node, and add
    them to the choice or tree. This recurses.
    """

    if isinstance(choice_or_tree, choice.Choice):
      for opt in choice_or_tree.choices():
        self.expand_choice_or_tree(opt)
    else:
      l = self.s.valid_children(choice_or_tree.schemaname)
      l = choice_or_tree.find_or_add(l)
      for opt in l:
        self.expand_choice_or_tree(opt)

    return

  def expand_treestore(self, iter = None):
    """
    Query the schema for what valid children can live under this node, then set the
    treestore appropriately. This recurses.
    """

    if iter is None:
      iter = self.treestore.get_iter_first()
      if iter is None:
        self.set_treestore(iter, [])
        return

    choice_or_tree, active_tree = self.treestore.get(iter, 0, 1)
    if active_tree.active is False or choice_or_tree.active is False:
      return

    l = self.s.valid_children(active_tree.schemaname)
    l = active_tree.find_or_add(l)
    self.set_treestore(iter, l)

    child_iter = self.treestore.iter_children(iter)
    while child_iter is not None:
      # fix for recursive schemata!
      child_active_tree = self.treestore.get_value(child_iter, 1)
      if child_active_tree.schemaname == active_tree.schemaname:
        debug.deprint("Warning: recursive schema elements not supported: %s" % active_tree.name)
        child_iter = self.treestore.iter_next(child_iter)
        if child_iter is None: break

      self.expand_treestore(child_iter)
      child_iter = self.treestore.iter_next(child_iter)

    return

  def remove_children(self, iter):
    """
    Delete the children of iter in the treestore.
    """

    childiter = self.treestore.iter_children(iter)
    if childiter is None: return

    result = True

    while result is True:
      result = self.treestore.remove(childiter)

    return


  def set_combobox_liststore(self, column, cellCombo, treemodel, iter, user_data=None):
    """
    This hook function sets the properties of the gtk.CellRendererCombo for each
    row. It sets up the cellcombo to use the correct liststore for its choices,
    decides whether the cellcombo should be editable or not, and sets the
    foreground colour.
    """

    choice_or_tree, active_tree, liststore = treemodel.get(iter, 0, 1, 2)

    if self.groupmode and treemodel.iter_parent(iter) is None:
      text =  self.mangle_cell_text(choice_or_tree.get_name_path())
      cellCombo.set_property("text", text)
    else:
      text = str(choice_or_tree)
      text = self.mangle_cell_text(text)
      cellCombo.set_property("text", text)


    cellCombo.set_property("model", liststore)

    # set the properties: colour, etc.
    if isinstance(choice_or_tree, tree.Tree):
      cellCombo.set_property("editable", False)
    elif isinstance(choice_or_tree, choice.Choice):
      cellCombo.set_property("editable", True)

    # Set the font for certain headings
    if (cellCombo.get_property("text").lower() == "contributor" or
        cellCombo.get_property("text").lower() == "bibliographic information" or
        cellCombo.get_property("text").lower() == "source tree" or
        cellCombo.get_property("text").lower() == "tree" or 
        cellCombo.get_property("text").lower() == "taxa data" or
        cellCombo.get_property("text").lower() == "character data" or 
        cellCombo.get_property("text").lower() == "analysis used"):

            cellCombo.set_property("font", "Sans Bold")
    else:
            cellCombo.set_property("font", "Sans")


    if self.iter_is_active(treemodel, iter):
      if active_tree.valid is True:
        cellCombo.set_property("foreground", "black")
      else:
        cellCombo.set_property("foreground", "blue")
    else:
        cellCombo.set_property("foreground", "gray")

    return

  def mangle_cell_text(self, text):
      # title case
      text = text.title()
      # replace _ with spaces
      text = text.replace("_"," ")
      # replace DOI and URL correctly
      text = text.replace("Doi","DOI")
      text = text.replace("Url","URL")
      text = text.replace("Iucn","IUCN")
      text = text.replace("Uk Bap","UK BAP")

      return text

  def set_cellpicture_choice(self, column, cell, treemodel, iter):
    """
    This hook function sets up the other gtk.CellRendererPixbuf, the one that gives
    the clue to the user whether this is a choice or not.
    """
    
    choice_or_tree = treemodel.get_value(iter, 0)
    if isinstance(choice_or_tree, tree.Tree):
      cell.set_property("stock-id", None)
    elif isinstance(choice_or_tree, choice.Choice):
      cell.set_property("stock-id", gtk.STOCK_GO_DOWN)

    return

  def set_cellpicture_cardinality(self, column, cell, treemodel, iter):
    """
    This hook function sets up the gtk.CellRendererPixbuf on the extreme right-hand
    side for each row; this paints a plus or minus or nothing depending on whether
    something can be added or removed or has to be there.
    """

    choice_or_tree = treemodel.get_value(iter, 0)
    if choice_or_tree.cardinality == "":
      cell.set_property("stock-id", None)
    elif choice_or_tree.cardinality == "?" or choice_or_tree.cardinality == "*":
      if choice_or_tree.active:
        cell.set_property("stock-id", gtk.STOCK_REMOVE)
      else:
        cell.set_property("stock-id", gtk.STOCK_ADD)
    elif choice_or_tree.cardinality == "+":
      parent_tree = choice_or_tree.parent
      count = parent_tree.count_children_by_schemaname(choice_or_tree.schemaname)
      
      if choice_or_tree.active and count == 2: # one active, one inactive
        cell.set_property("stock-id", None)
      elif choice_or_tree.active:
        cell.set_property("stock-id", gtk.STOCK_REMOVE)
      else:
        cell.set_property("stock-id", gtk.STOCK_ADD)

    return

  def toggle_tree(self, iter):
    """
    Toggles the state of part of the tree.
    """

    choice_or_tree = self.treestore.get_value(iter, 0)

    if choice_or_tree.active:
      self.collapse_tree(iter)
    else:
      self.expand_tree(iter)

    self.on_select_row()

    return
  
  def collapse_tree(self, iter, confirm = True):
    """
    Collapses part of the tree.
    """

    choice_or_tree, = self.treestore.get(iter, 0)
    parent_tree = choice_or_tree.parent

    if not choice_or_tree.active:
      return

    if choice_or_tree.cardinality == "":
      return

    if choice_or_tree.cardinality == "?":
      choice_or_tree.active = False
      self.set_saved(False)
      self.remove_children(iter)

    elif choice_or_tree.cardinality == "*":
      # If this is the only one, just make it inactive.
      # Otherwise, just delete it.
      count = parent_tree.count_children_by_schemaname(choice_or_tree.schemaname)
      if count == 1:
        choice_or_tree.active = False
        self.set_saved(False)
        self.remove_children(iter)
      else:
        self.delete_tree(iter, confirm)

    elif choice_or_tree.cardinality == "+":
      count = parent_tree.count_children_by_schemaname(choice_or_tree.schemaname)
      if count == 2: # one active, one inactive
        # do nothing
        return
      else: # count > 2
        self.delete_tree(iter, confirm)
  
    parent_tree.recompute_validity()
    self.treeview.queue_draw()
    return

  def delete_tree(self, iter, confirm):
    choice_or_tree, = self.treestore.get(iter, 0)
    parent_tree = choice_or_tree.parent
    isSelected = self.treeview.get_selection().iter_is_selected(iter)
    sibling = self.treestore.iter_next(iter)

    if confirm:
      response = dialogs.prompt(self.main_window, "Are you sure you want to delete this node?")

    # not A or B == A implies B
    if not confirm or response == gtk.RESPONSE_YES:
      parent_tree.delete_child_by_ref(choice_or_tree)
      self.remove_children(iter)
      self.treestore.remove(iter)
      self.set_saved(False)
      
      if isSelected and sibling:
        self.treeview.get_selection().select_iter(sibling)
    return

  def expand_tree(self, iter):
    """
    Expands part of the tree.
    """

    choice_or_tree, active_tree = self.treestore.get(iter, 0, 1)
    parent_tree = choice_or_tree.parent

    if choice_or_tree.active:
      return

    if choice_or_tree.cardinality == "":
      return

    elif choice_or_tree.cardinality == "?":
      choice_or_tree.active = True
      self.set_saved(False)
      self.expand_treestore(iter)

    elif choice_or_tree.cardinality == "*" or choice_or_tree.cardinality == "+":
      # Make this active, and add a new inactive instance
      choice_or_tree.active = True
      new_tree = parent_tree.add_inactive_instance(choice_or_tree)
      liststore = self.create_liststore(new_tree)
      self.expand_treestore(iter)
      iter = self.treestore.insert_after(
        None, iter, [new_tree, new_tree.get_current_tree(), liststore])
      attrid = new_tree.connect("on-set-attr", self.on_set_attr, self.treestore.get_path(iter))
      dataid = new_tree.connect("on-set-data", self.on_set_data, self.treestore.get_path(iter))
      self.signals[new_tree] = (attrid, dataid)
      self.set_saved(False)

    parent_tree.recompute_validity()
    return

  def options_tree_select_func(self, info = None):
    """
    Called when the user selected a new item in the treeview. Prevents changing of
    node and attempts to save data if appropriate.
    """

    if not self.options_tree_select_func_enabled:
      self.options_tree_select_func_enabled = True
      return False

    if not self.data.store():
      return False

    if (isinstance(self.selected_node, mixedtree.MixedTree)
       and self.geometry_dim_tree is not None
       and self.selected_node.parent is self.geometry_dim_tree.parent
       and self.selected_node.data is not None):
      self.geometry_dim_tree.set_data(self.selected_node.data)

    return True

  def on_treeview_key_press(self, treeview, event):
    """
    Called when treeview intercepts a key press. Collapse and expand rows.
    """

    if event.keyval == gtk.keysyms.Right:
      self.treeview.expand_row(self.get_selected_row(), open_all = False)

    if event.keyval == gtk.keysyms.Left:
      self.treeview.collapse_row(self.get_selected_row())

    if event.keyval == gtk.keysyms.Delete:
       self.collapse_tree(self.treestore.get_iter(self.get_selected_row()))
       self.on_select_row()
 
    return

  def on_treeview_button_press(self, treeview, event):
    """
    This routine is called every time the mouse is clicked on the treeview on the
    left-hand side. It processes the "buttons" gtk.STOCK_ADD and gtk.STOCK_REMOVE
    in the right-hand column, activating, adding and removing tree nodes as
    necessary.
    """
    pathinfo = treeview.get_path_at_pos(int(event.x), int(event.y))

    if event.button == 1:

      if pathinfo is not None:
        path = pathinfo[0]
        col = pathinfo[1]

        if col is self.imgcolumn:
          iter = self.treestore.get_iter(path)
          self.toggle_tree(iter)

    elif event.button == 3:
      if pathinfo is not None:
        treeview.get_selection().select_path(pathinfo[0])
        self.show_popup(None, event.button, event.time)
        return True

  def popup_location(self, widget):
    column = self.treeview.get_column(0)
    treemodel, treeiter = self.treeview.get_selection().get_selected()
    treepath = treemodel.get_path(treeiter)
    area = self.treeview.get_cell_area(treepath, column)
    sx, sy = self.popup.size_request()
    tx, ty = area.x, area.y + int(sy * 1.25)
    x, y = self.treeview.tree_to_widget_coords(tx, ty)
    return (x, y, True)

  def on_treeview_popup(self, treeview):
    self.show_popup(self.popup_location, 0, gtk.get_current_event_time())
    return

  def show_popup(self, func, button, time):
    self.popup.popup(None, None, func, button, time)
    return

  def on_select_row(self, selection=None):
    """
    Called when a row is selected. Update the options frame.
    """

    if isinstance(selection, str) or isinstance(selection, tuple):
      path = selection
    else:
      path = self.get_selected_row(selection)

    if path is None:
      return  

    self.selected_iter = iter = self.treestore.get_iter(path)
    choice_or_tree, active_tree = self.treestore.get(iter, 0, 1)

    self.selected_node = self.get_painted_tree(iter)
    self.update_options_frame()

    name = self.get_spudpath(active_tree)
    self.statusbar.set_statusbar(name)
    self.current_spudpath = name
    self.current_xpath = self.get_xpath(active_tree)

    self.clear_plugin_buttons()

    for plugin in plugins.plugins:
      if plugin.matches(name):
        self.add_plugin_button(plugin)

    return

  def get_spudpath(self, active_tree):
    # get the name to paint on the statusbar
    name_tree = active_tree
    name = ""
    while name_tree is not None:
      if "name" in name_tree.attrs and name_tree.attrs["name"][1] is not None:
        used_name = name_tree.name + '::%s' % name_tree.attrs["name"][1]
      elif name_tree.parent is not None and name_tree.parent.count_children_by_schemaname(name_tree.schemaname) > 1:
        siblings = [x for x in name_tree.parent.children if x.schemaname == name_tree.schemaname]
        i = 0
        for sibling in siblings:
          if sibling is name_tree:
            break
          else:
            i = i + 1
        used_name = name_tree.name + "[%s]" % i
      else:
        used_name = name_tree.name

      name = "/" + used_name + name
      name_tree = name_tree.parent

    # and split off the root name:
    name = '/' + '/'.join(name.split('/')[2:])
    return name

  def get_xpath(self, active_tree):
    # get the name to paint on the statusbar
    name_tree = active_tree
    name = ""
    while name_tree is not None:
      if "name" in name_tree.attrs and name_tree.attrs["name"][1] is not None:
        used_name = name_tree.name + '[@name="%s"]' % name_tree.attrs["name"][1]
      elif name_tree.parent is not None and name_tree.parent.count_children_by_schemaname(name_tree.schemaname) > 1:
        siblings = [x for x in name_tree.parent.children if x.schemaname == name_tree.schemaname]
        i = 1
        for sibling in siblings:
          if sibling is name_tree:
            break
          else:
            i = i + 1
        used_name = name_tree.name + "[%s]" % i
      else:
        used_name = name_tree.name

      name = "/" + used_name + name
      name_tree = name_tree.parent

    return name

  def clear_plugin_buttons(self):
    for button in self.plugin_buttons:
      self.plugin_buttonbox.remove(button)
    
    self.plugin_buttons = []

  def add_plugin_button(self, plugin):
    button = gtk.Button(label=plugin.name)
    button.connect('clicked', self.plugin_handler, plugin)
    button.show()

    self.plugin_buttons.append(button)
    self.plugin_buttonbox.add(button)

  def plugin_handler(self, widget, plugin):
    
    f = StringIO.StringIO()
    self.tree.write(f)
    xml = f.getvalue()
    plugin.execute(xml, self.current_xpath, path=self.file_path)


  def get_selected_row(self, selection=None):
    """
    Get the iter to the selected row.
    """

    if (selection == None):
        selection = self.treeview.get_selection()

    (model, paths) = selection.get_selected_rows()
    if paths:
      return paths[0]
    else:
      return None

  def on_activate_row(self, treeview, path, view_column):
    """
    Called when you double click or press Enter on a row.
    """

    iter = self.treestore.get_iter(path)
    
    self.expand_tree(iter)
    self.on_select_row()

    if path is None: 
      return
    
    if treeview.row_expanded(path):
      treeview.collapse_row(path)
    else:
      treeview.expand_row(path, False)

    return

  def cellcombo_changed(self, combo, tree_path, combo_iter):
    """
    This is called when a cellcombo on the left-hand treeview is edited,
    i.e. the user chooses between more than one possible choice.
    """

    tree_iter = self.treestore.get_iter(tree_path)
    choice = self.treestore.get_value(tree_iter, 0)

    # get the ref to the new active choice
    liststore = self.treestore.get_value(tree_iter, 2)
    ref = liststore.get_value(combo_iter, 1)

    # record the choice in the datatree
    choice.set_active_choice_by_ref(ref)
    new_active_tree = choice.get_current_tree()

    name = self.get_spudpath(new_active_tree)
    self.statusbar.set_statusbar(name)
    self.treestore.set(tree_iter, 1, new_active_tree)
    self.current_spudpath = name
    xpath = self.get_xpath(new_active_tree)
    self.current_xpath = xpath

    self.clear_plugin_buttons()

    for plugin in plugins.plugins:
      if plugin.matches(xpath):
        self.add_plugin_button(plugin)

    self.remove_children(tree_iter)
    self.expand_treestore(tree_iter)
    self.treeview.expand_row(tree_path, False)

    self.set_saved(False)
    self.selected_node = self.get_painted_tree(tree_iter)
    self.update_options_frame()

    return

  def get_treeview_iter(self, selection):
    """
    Get a treeview iterator object, given a selection.
    """

    path = self.get_selected_row(selection)
    if path is None:
      return self.get_treestore_iter_from_xmlpath(self.current_xpath)

    return self.treestore.get_iter(path)

  def on_set_data(self, node, data, path):
    self.set_saved(False)
    self.treeview.queue_draw()

  def on_set_attr(self, node, attr, value, path):
    self.set_saved(False)
    self.treeview.queue_draw()

  def get_painted_tree(self, iter_or_tree, lock_geometry_dim = True):
    """
    Check if the given tree, or the active tree at the given iter in the treestore,
    have any children of the form *_value. If so, we need to make the node painted
    by the options tree a mix of the two: the documentation and attributes come from
    the parent, and the data from the child.

    Also check if it is the geometry node, validity of any tuple data, and, if an
    iter is supplied, check that the node is active.
    """

    if isinstance(iter_or_tree, tree.Tree):
      active_tree = iter_or_tree
    else:
      active_tree = self.treestore.get_value(iter_or_tree, 1)

    painted_tree = active_tree.get_mixed_data()

    if not isinstance(iter_or_tree, tree.Tree) and not self.iter_is_active(self.treestore, iter_or_tree):
      painted_tree = tree.Tree(painted_tree.name, painted_tree.schemaname, painted_tree.attrs, doc = painted_tree.doc)
      painted_tree.active = False
    elif lock_geometry_dim and self.geometry_dim_tree is not None and self.geometry_dim_tree.data is not None:
      if active_tree is self.geometry_dim_tree:
        data_tree = tree.Tree(painted_tree.name, painted_tree.schemaname, datatype = "fixed")
        data_tree.data = painted_tree.data
        painted_tree = MixedTree(painted_tree, data_tree)
      elif isinstance(self.geometry_dim_tree, mixedtree.MixedTree) and active_tree is self.geometry_dim_tree.parent:
        data_tree = tree.Tree(painted_tree.child.name, painted_tree.child.schemaname, datatype = "fixed")
        data_tree.data = painted_tree.data
        painted_tree = mixedtree.MixedTree(painted_tree, data_tree)

    return painted_tree

  def get_treestore_iter_from_xmlpath(self, xmlpath):
    """
    Convert the given XML path to an iter into the treestore. For children of a
    single parent with the same names, only the first child is considered.
    """

    names = xmlpath.split("/")

    iter = self.treestore.get_iter_first()
    if iter is None:
      return None
    for name in names[1:-1]:
      while str(self.treestore.get_value(iter, 0)) != name:
        iter = self.treestore.iter_next(iter)
        if iter is None:
          return None
      iter = self.treestore.iter_children(iter)
      if iter is None:
        return None

    return iter

  def get_treestore_path_from_node(self, node):
    """
    Look for the path for the given node.
    """
    
    def search(iter, node, indent=""):
      while iter:
        if self.treestore.get_value(iter, 0) is node:
          return iter
        else:
          child = search(self.treestore.iter_children(iter), node, indent + "  ")
          if child: return child

          iter = self.treestore.iter_next(iter)      
      return iter

    iter = search(self.treestore.get_iter_first(), node)
    return self.treestore.get_path(iter) if iter else None
 
  def set_geometry_dim_tree(self):
    """
    Find the iter into the treestore corresponding to the geometry dimension, and
    perform checks to test that the geometry dimension node is valid.
    """
    
    self.geometry_dim_tree = self.data.geometry_dim_tree = None
    # The tree must exist
    if self.tree is None:
      return

    # A geometry dimension element must exist
    iter = self.get_treestore_iter_from_xmlpath("/" + self.tree.name + self.data_paths["dim"])
    if iter is None:
      return

    painted_tree = self.get_painted_tree(iter, False)
    if isinstance(painted_tree, mixedtree.MixedTree):
       # If the geometry dimension element has a hidden data element, it must
       # have datatype tuple or fixed
       if not isinstance(painted_tree.datatype, tuple) and painted_tree.datatype != "fixed":
         self.geometry_dim_tree = None
         return
    elif painted_tree.datatype != "fixed":
      # Otherwise, only fixed datatype is permitted
      return

    # All parents of the geometry dimension element must have cardinality ""
    # (i.e. not ?, * or +).
    parent = painted_tree.parent
    while parent is not None:
      if parent.cardinality != "":
        self.geometry_dim_tree = None
        return
      parent = parent.parent

    # All possible geometry dimensions must be positive integers
    if isinstance(painted_tree.datatype, tuple):
      possible_dims = painted_tree.datatype
    elif painted_tree.datatype == "fixed":
      possible_dims = [painted_tree.data]
    else:
      return
    for opt in possible_dims:
      try:
        test = int(opt)
        assert test > 0
      except:
        return
      
    # A valid geometry dimension element has been located
    self.geometry_dim_tree = self.data.geometry_dim_tree = painted_tree
    
    return

  def iter_is_active(self, treemodel, iter):
    """
    Test whether the node at the given iter in the LHS treestore is active.
    """

    while iter is not None:
      choice_or_tree = treemodel.get_value(iter, 0)
      active_tree = treemodel.get_value(iter, 1)
      if not choice_or_tree.active or not active_tree.active:
        return False
      iter = treemodel.iter_parent(iter)

    return True

  def choice_or_tree_matches(self, text, choice_or_tree, recurse, search_active_subtrees = False):
    """
    See if the supplied node matches a given piece of text. If recurse is True,
    the node is deemed to match if any of its children match or, if the node is a
    choice and search_active_subtrees is True, any of the available trees in the
    choice match.
    """

    if choice_or_tree.is_hidden():
      return False
    elif isinstance(choice_or_tree, choice.Choice):
      if self.choice_or_tree_matches(text, choice_or_tree.get_current_tree(), False):
        return True
      elif recurse and self.find.search_gui.get_widget("searchInactiveChoiceSubtreesCheckButton").get_active():
        for opt in choice_or_tree.choices():
          if not search_active_subtrees and opt is choice_or_tree.get_current_tree():
            continue
          if opt.children == []:
            self.expand_choice_or_tree(opt)
          if self.choice_or_tree_matches(text, opt, recurse, True):
            return True
    else:
      if self.get_painted_tree(choice_or_tree).matches(text, self.find.search_gui.get_widget("caseSensitiveCheckButton").get_active()):
        return True
      else:
        if self.find.search_gui.get_widget("caseSensitiveCheckButton").get_active():
          text_re = re.compile(text)
        else:
          text_re = re.compile(text, re.IGNORECASE)
        comment = choice_or_tree.get_comment()
        if comment is not None and comment.data is not None and text_re.search(comment.data) is not None:
          return True
        elif recurse:
          for opt in choice_or_tree.children:
            if self.choice_or_tree_matches(text, opt, recurse, True):
              return True

      return False

  def search_treestore(self, text, iter = None):
    """
    Recursively search the tree for a node that matches a given piece of text.
    MixedTree.matches and choice_or_tree_matches decide what is a match (using
    tree.Matches).

    This uses lazy evaluation to only search as far as necessary; I love
    Python generators. If you don't know what a Python generator is and need to
    understand this, see PEP 255.
    """

    if iter is None:
      iter = self.treestore.get_iter_first()
    if iter is None:
      yield None
    choice_or_tree = self.treestore.get_value(iter, 0)

    if self.choice_or_tree_matches(text, choice_or_tree, isinstance(choice_or_tree, choice.Choice)):
      yield iter

    child_iter = self.treestore.iter_children(iter)
    while child_iter is not None:
      for iter in self.search_treestore(text, child_iter):
        yield iter
      child_iter = self.treestore.iter_next(child_iter)

    return

  ### RHS ###

  def add_custom_widgets(self):
    """
    Adds custom python widgets that aren't easily handeled by glade.
    """
    
    optionsFrame = self.gui.get_widget("optionsFrame")

    vpane1 = gtk.VPaned()
    vpane2 = gtk.VPaned()
    vbox = gtk.VBox()
    
    vpane1.pack2(vpane2, True, False)
    vpane2.pack1(vbox, True, False)
    optionsFrame.add(vpane1)

    self.description = descriptionwidget.DescriptionWidget()
    vpane1.pack1(self.description, True, False)

    self.attributes = attributewidget.AttributeWidget()
    vbox.pack_start(self.attributes, True, True)

    databuttons = databuttonswidget.DataButtonsWidget()
    vbox.pack_end(databuttons, False)
    
    self.data = datawidget.DataWidget()
    self.data.set_buttons(databuttons)
    vbox.pack_end(self.data, True, True)

    self.comment = commentwidget.CommentWidget()
    vpane2.pack2(self.comment, True, False)

    optionsFrame.show_all()
    return 
 
  def update_options_frame(self):
    """
    Update the RHS.
    """
    
    self.description.update(self.selected_node)

    self.attributes.update(self.selected_node)

    self.data.update(self.selected_node)

    self.comment.update(self.selected_node)

    self.gui.get_widget("optionsFrame").queue_resize()
    
    return

class DiamondFindDialog:
  def __init__(self, parent, gladefile):
    self.parent = parent
    self.gladefile = gladefile
    self.search_dialog = None

    return

  def on_find(self, widget=None):
    """
    Open up the find dialog. It has to be created each time from the glade file.
    """

    if not self.search_dialog is None:
      return

    signals =      {"on_find_dialog_close": self.on_find_close_button,
                    "on_close_clicked": self.on_find_close_button,
                    "on_find_clicked": self.on_find_find_button}

    self.search_gui = gtk.glade.XML(self.gladefile, root="find_dialog")
    self.search_dialog = self.search_gui.get_widget("find_dialog")
    self.search_gui.signal_autoconnect(signals)
    search_entry = self.search_gui.get_widget("search_entry")
    search_entry.connect("activate", self.on_find_find_button)

    # reset the search parameters
    self.search_generator = None
    self.search_text = ""
    self.search_count = 0
    self.search_dialog.show()
    self.parent.statusbar.set_statusbar("")

    return

  def on_find_find_button(self, button):
    """
    Search. Each time "Find" is clicked, we compare the stored search text to the
    text in the entry box. If it's the same, we find next; if it's different, we
    start a new search. self.search_treestore does the heavy lifting.
    """

    search_entry = self.search_gui.get_widget("search_entry")

    self.parent.statusbar.clear_statusbar()

    text = search_entry.get_text()
    if text == "":
      self.parent.statusbar.set_statusbar("No text")
      return

    # check if we've started a new search
    if text != self.search_text:
      # started a new search
      self.search_generator = None
      self.search_generator = self.parent.search_treestore(text)
      self.search_text = text
      self.search_count = 0

    try:
      # get the iter of the next tree that matches
      iter = self.search_generator.next()
      path = self.parent.treestore.get_path(iter)
      # scroll down to it, expand it, and select it
      self.parent.treeview.expand_to_path(path)
      self.parent.treeview.get_selection().select_iter(iter)
      self.parent.treeview.scroll_to_cell(path, use_align=True, col_align=0.5)
      # count how many hits we've had
      self.search_count = self.search_count + 1
    except StopIteration:
      # reset the search and cycle
      self.search_text = ""
      # if something was found, go through again
      if self.search_count > 0:
        self.on_find_find_button(button)
      else:
        self.parent.statusbar.set_statusbar("No results")

    return

  def on_find_close_button(self, button = None):
    """
    Close the search widget.
    """

    if not self.search_dialog is None:
      self.search_dialog.hide()
      self.search_dialog = None
    self.parent.statusbar.clear_statusbar()

    return

class DiamondStatusBar:
  def __init__(self, statusbar):
    self.statusbar = statusbar
    self.context_id = statusbar.get_context_id("Messages")

    return

  def set_statusbar(self, msg):
    """
    Set the status bar message.
    """

    self.statusbar.push(self.context_id, msg)

    return

  def clear_statusbar(self):
    """
    Clear the status bar.
    """

    self.statusbar.push(self.context_id, "")

    return



from stk_gui.plugins import register_plugin, cb_decorator
import stk_gui.interface
from stk_gui import dialogs
import gtk
import os.path
import sys
import gobject
import stk

def plugin_applies(xpath):
    # Allow plugin to be used at any element which is under a source dataset
    return (xpath.endswith('/tree_string'))

@cb_decorator

def handle_click(xml, xpath, path=None):
    from lxml import etree

    xml_root = etree.fromstring(xml)

    if (path == None):
        path = os.getcwd()

    filter_names_and_patterns = {}
    filter_names_and_patterns['Trees'] = ["*.tre","*nex","*.nwk","*.tnt"]
   
    filename = dialogs.get_filename(title = "Choose tree file", action = gtk.FILE_CHOOSER_ACTION_OPEN, 
            filter_names_and_patterns = filter_names_and_patterns,
            folder_uri = path)

    if filename == None:
        return

    # Track back along xpath to find the source element where we're going to set the name
    element = xml_root.xpath(xpath+"/string_value")
    try:
        tree = stk.import_tree(filename,gui=True)
    except stk.TreeParseError as detail:
        msg = "Failed to import tree - can't parse tree.\n"+detail.msg
        dialogs.error(self.main_window,msg)
    source_tree_ele = element[0].getparent().getparent().getparent()
    tree_name = stk.create_tree_name(xml,source_tree_ele)
    element[0].text = tree
    source_tree_ele.attrib['name'] = tree_name

    
    stk_gui.interface.plugin_xml = etree.tostring(xml_root)
    stk_gui.interface.pluginSender.emit('plugin_changed_xml')
    return

register_plugin(plugin_applies, "Import Tree", handle_click)

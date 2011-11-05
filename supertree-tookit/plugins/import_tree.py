from diamond.plugins import register_plugin, cb_decorator
import diamond.interface
from diamond import dialogs
import gtk
import os.path
import sys
import gobject
sys.path.append("/home/jhill1/software/supertree_toolkit_2/supertree-toolkit/stk/")
from supertree_toolkit import *

def plugin_applies(xpath):
    # Allow plugin to be used at any element which is under a source dataset
    return (xpath.endswith('/tree_data'))

@cb_decorator

def handle_click(xml, xpath, **kwargs):
    from lxml import etree

    xml_root = etree.fromstring(xml)

    filter_names_and_patterns = {}
    filter_names_and_patterns['Nexus file'] = "*.nex"
    filter_names_and_patterns['Nexus tree file'] = "*.tre"
    filter_names_and_patterns['Newick file'] = "*.nwk"
    filter_names_and_patterns['PhyloXML file'] = "*.phyloxml"    

    filename = dialogs.get_filename(title = "Choose tree file", action = gtk.FILE_CHOOSER_ACTION_OPEN, filter_names_and_patterns = filter_names_and_patterns)
    #filename = '/home/jhill1/test.nex'
    if filename == None:
        return

    # Track back along xpath to find the source element where we're going to set the name
    element = xml_root.xpath(xpath)[0]
    while (element.tag != 'tree_data'):
        element = element.getparent()

    tree = import_tree(filename)
    tree_string_tag = element[0]
    tree_string_tag.text = tree
    
    diamond.interface.plugin_xml = etree.tostring(xml_root)
    diamond.interface.pluginSender.emit('plugin_changed_xml')
    return

register_plugin(plugin_applies, "Import Tree", handle_click)

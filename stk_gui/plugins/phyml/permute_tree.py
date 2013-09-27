from stk_gui.plugins import register_plugin, cb_decorator
import stk_gui.interface
from stk_gui import dialogs
import gtk
import os.path
import sys
import gobject
import stk.supertree_toolkit as stk

def plugin_applies(xpath):
    # Allow plugin to be used at any element which is under a source dataset
    return (xpath.endswith('/tree_string'))

@cb_decorator

def handle_click(xml, xpath, path=None):
    from lxml import etree

    xml_root = etree.fromstring(xml)

    # Track back along xpath to find the source element where we're going to set the name
    element = xml_root.xpath(xpath+"/string_value")
    tree = element[0].text

    if (path == None):
        path = os.getcwd()

    filter_names_and_patterns = {}
    filter_names_and_patterns['Phylo files'] = ["*.tre","*nex","*.nwk","*.new","*.tnt"]
   
    filename = dialogs.get_filename(title = "Choose tree file", action = gtk.FILE_CHOOSER_ACTION_SAVE, 
            filter_names_and_patterns = filter_names_and_patterns,
            folder_uri = path)
    if filename == None:
        return

    # guess format based on ending, assuming matrix
    new_output,ext = os.path.splitext(filename)
    if ext == ".tre":
        # Nexus tree file
        output_string = stk.permute_tree(tree,treefile="nexus")
    elif ext == ".nex":
        # Nexus matrix
        output_string = stk.permute_tree(tree,format="nexus")        
    elif ext==".tnt":
        # tnt matrix
        output_string = stk.permute_tree(tree,format="tnt")
    elif ext==".new" or ext==".nwk":
        # newick tree
        output_string = stk.permute_tree(tree,treefile="newick")
    else:
        dialogs.error(None,"Error creating permuting trees. Incorrect format.")
    
    f = open(filename,'w')
    f.write(output_string)
    f.close
    
    return

register_plugin(plugin_applies, "Permute Tree", handle_click)

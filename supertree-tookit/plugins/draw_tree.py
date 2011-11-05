from diamond.plugins import register_plugin, cb_decorator
import os.path
import sys
sys.path.append("/home/jhill1/software/supertree_toolkit_2/supertree-toolkit/stk/")
from supertree_toolkit import *

def plugin_applies(xpath):
    # Allow plugin to be used at any element which is under a source dataset
    return (xpath.endswith('/tree_data'))

@cb_decorator

def handle_click(xml, xpath, **kwargs):
    from lxml import etree

    xml_root = etree.fromstring(xml)

    # This check is needed in case xpath in Diamond is not updated upon changing an attribute
    # (can be removed once the bug in Diamond has been fixed)
    if (len(xml_root.xpath(xpath)) == 0):
        return

    while (element.tag != 'tree_data'):
        element = element.getparent()

    tree_string = element.text
    print tree_string
    draw_tree(tree_string)
    
    return


register_plugin(plugin_applies, "View Tree", handle_click)

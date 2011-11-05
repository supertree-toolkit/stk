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
    return (xpath.startswith('/sources/source'))

@cb_decorator

def handle_click(xml, xpath, **kwargs):
    from lxml import etree

    xml_root = etree.fromstring(xml)

    # This check is needed in case xpath in Diamond is not updated upon changing an attribute
    # (can be removed once the bug in Diamond has been fixed)
    if (len(xml_root.xpath(xpath)) == 0):
        return

    # Track back along xpath to find the source element where we're going to set the name
    element = xml_root.xpath(xpath)[0]
    while (element.tag != 'source'):
        element = element.getparent()

    new_xml = single_sourcename(etree.tostring(element))  
    ele_T = etree.fromstring(new_xml)
    element.getparent().replace(element,ele_T)

    diamond.interface.plugin_xml = etree.tostring(xml_root)
    diamond.interface.pluginSender.emit('plugin_changed_xml')

    return


register_plugin(plugin_applies, "Auto-name source", handle_click)

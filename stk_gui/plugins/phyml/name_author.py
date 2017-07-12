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
    return (xpath.startswith('/sources/source'))

@cb_decorator

def handle_click(xml, xpath, path=None):
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

    new_xml = stk.single_sourcename(etree.tostring(element))  
    ele_T = etree.fromstring(new_xml)
    element.getparent().replace(element,ele_T)

    # now make all unique
    xml_root = stk.set_unique_names(etree.tostring(xml_root))

    stk_gui.interface.plugin_xml = xml_root
    stk_gui.interface.pluginSender.emit('plugin_changed_xml')

    return


register_plugin(plugin_applies, "Auto-name source", handle_click)

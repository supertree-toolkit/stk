import unittest
import math
import sys
# so we import local stk before any other
sys.path.insert(0,"../../")
from stk.supertree_toolkit import create_name, single_sourcename, all_sourcenames, get_all_source_names
import os
from lxml import etree
from util import *

# our test dataset
xml_single = etree.parse("data/input/single_name.xml")
xml_single_c = etree.parse("data/output/single_name.xml")
xml_two = etree.parse("data/input/two_names.xml")
xml_two_c = etree.parse("data/output/two_names.xml")
xml_lots = etree.parse("data/input/lots.xml")
xml_lots_c = etree.parse("data/output/lots.xml")
xml_full = etree.parse("data/input/full_tree.phyml")
xml_full_c = etree.parse("data/output/full_tree.phyml")
non_unique_names = etree.parse("data/input/non_unique_names.phyml")

class TestSetSourceNames(unittest.TestCase):

    def test_get_single_name(self):
        authors = ['Smith']
        year = '2001'
        source_name = create_name(authors, year)
        self.assert_(source_name=="Smith_2001", "Name obtained: "+source_name)
    
    def test_get_single_name_append(self):
        authors = ['Smith']
        year = '2001'
        source_name = create_name(authors, year,"a")
        self.assert_(source_name=="Smith_2001a", "Name obtained: "+source_name)
    
    def test_get_two_names(self):
        authors = ['Smith', 'Jones']
        year = '2001'
        source_name = create_name(authors, year)
        self.assert_(source_name=="Smith_Jones_2001", "Name obtained: "+source_name)

    def test_get_etal_names(self):
        authors = ['Smith', 'Jones', 'Davis', 'Hill']
        year = '2001'
        source_name = create_name(authors, year)
        self.assert_(source_name=="Smith_etal_2001", "Name obtained: "+source_name)

    def test_singlename(self):
        # the XML has a <sources> element as root, and the function takes
        # a <source> element, so compare the first child.
        new_xml = single_sourcename(etree.tostring(xml_single.getroot()[0]))
        self.assert_(isEqualXML(new_xml,etree.tostring(xml_single_c.getroot()[0])))

    def test_twonames(self):
        # the XML has a <sources> element as root, and the function takes
        # a <source> element, so compare the first child.
        new_xml = single_sourcename(etree.tostring(xml_two.getroot()[0]))   
        self.assert_(isEqualXML(new_xml,etree.tostring(xml_two_c.getroot()[0]))) 

    def test_lotsofnames(self):
        # the XML has a <sources> element as root, and the function takes
        # a <source> element, so compare the first child.
        new_xml = single_sourcename(etree.tostring(xml_lots.getroot()[0]))
        self.assert_(isEqualXML(new_xml,etree.tostring(xml_lots_c.getroot()[0])))

    def test_full_sourcenames(self):
        new_xml = all_sourcenames(etree.tostring(xml_full))
        names = get_all_source_names(new_xml)
        expected_names = get_all_source_names(etree.tostring(xml_full_c))
        self.assertListEqual(names,expected_names)

    def test_get_all_source_names(self):
        input_data = etree.tostring(xml_full_c)
        names = get_all_source_names(input_data)
        expected_names = ['Hill_1996', 'Hill_etal_1996', 'Hill_Davis_1996']
        self.assert_(expected_names.sort() == names.sort())

    def test_all_unique_names_not_altered(self):
        new_xml = all_sourcenames(etree.tostring(xml_full))
        names = get_all_source_names(new_xml)
        expected_names = ['Hill_1996', 'Hill_etal_1996', 'Hill_Davis_1996']
        self.assert_(expected_names.sort() == names.sort())
       
    def test_all_unique_names_altered(self):
        new_xml = all_sourcenames(etree.tostring(non_unique_names))
        names = get_all_source_names(new_xml)
        expected_names = ['Hill_1996b', 'Hill_1996a', 'Hill_etal_1996', 'Hill_Davis_1996']
        self.assert_(expected_names.sort() == names.sort())

if __name__ == '__main__':
    unittest.main()
 

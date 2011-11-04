import unittest
import math
import sys
sys.path.append("../")
from supertree_toolkit import create_name, single_sourcename, all_sourcenames
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
xml_full = etree.parse("data/input/full_tree.xml")
xml_full_c = etree.parse("data/output/full_tree.xml")

class TestSetSourceNames(unittest.TestCase):

    def test_get_single_name(self):
        authors = ['Smith']
        year = '2001'
        source_name = create_name(authors, year)
        self.assert_(source_name=="Smith_2001", "Name obtained: "+source_name)

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
        new_xml = single_sourcename(etree.tostring(xml_single))      
        self.assert_(isEqualXML(new_xml,etree.tostring(xml_single_c)))

    def test_twonames(self):
        new_xml = single_sourcename(etree.tostring(xml_two))   
        self.assert_(isEqualXML(new_xml,etree.tostring(xml_two_c))) 

    def test_lotsofnames(self):
        new_xml = single_sourcename(etree.tostring(xml_lots))
        self.assert_(isEqualXML(new_xml,etree.tostring(xml_lots_c)))

    def test_full_sourcenames(self):
        new_xml = all_sourcenames(etree.tostring(xml_full))
        self.assert_(isEqualXML(new_xml,etree.tostring(xml_full_c)))

if __name__ == '__main__':
    unittest.main()
 

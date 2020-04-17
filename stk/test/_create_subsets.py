#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2011, Jon Hill, Katie Davis
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Jon Hill. jon.hill@imperial.ac.uk. 

import unittest
import math
import sys
# so we import local stk before any other
sys.path.insert(0,"../../")
from stk.supertree_toolkit import create_subset, _parse_xml
import os
from lxml import etree
from util import *
import io
import numpy
import stk.p4 as p4
parser = etree.XMLParser(remove_blank_text=True)

import sys
sys.path.append("../../stk_gui/stk_gui/")

# The unit tests proper
class TestSubset(unittest.TestCase):

    def testEmptyMatchInput(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        searchTerms = {}
        new_XML = create_subset(XML,searchTerms) #empty search terms - warning and return original XML
        self.assertTrue(new_XML == XML)

    def testSingleYear(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        searchTerms = {'years':[2011]}
        new_XML = create_subset(XML,searchTerms) #these data are all 2011
        root = _parse_xml(new_XML)
        find = etree.XPath("//year")
        yrs = find(root)
        for y in yrs:
            self.assertTrue(int(y.xpath('integer_value')[0].text) == 2011)
        # could do more extensive tests here...

    def testRealDataYears(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'years':[1999]}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        find = etree.XPath("//year")
        yrs = find(root)
        i = 0
        for y in yrs:
            self.assertTrue(int(y.xpath('integer_value')[0].text) == 1999)
            i+=1
        self.assertTrue(i==4)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Andersson_1999a","Andersson_1999b","Aragon_etal_1999","Baptista_Visser_1999"]
        self.assertListEqual(expected_names,names)

    def testCharType(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        searchTerms = {'character_types':["molecular"]}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        find = etree.XPath("//character")
        chrs = find(root)
        i = 0
        for c in chrs:
            self.assertTrue(c.attrib['type'] == "molecular")
            i+=1
        self.assertTrue(i==2)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Davis_2011","Hill_2011"]
        self.assertListEqual(expected_names,names)
        # and two source trees too
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 2)
    
    def testRealDataCharType(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'character_types':["morphological"]}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        find = etree.XPath("//character")
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Aliabadian_etal_2007","Andersson_1999a","Baptista_Visser_1999","Bertelli_etal_2006"]
        self.assertListEqual(expected_names,names)
        # and two source trees too
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 7)

    def testRealDataCharTypeMorphOnly(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'character_types':["morphological"]}
        new_XML = create_subset(XML,searchTerms,includeMultiple=False)
        root = _parse_xml(new_XML)
        find = etree.XPath("//character")
        chrs = find(root)
        for c in chrs:
            self.assertTrue(c.attrib['type'] == "morphological")
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Aliabadian_etal_2007","Andersson_1999a","Bertelli_etal_2006"]
        self.assertListEqual(expected_names,names)
        # and two source trees too
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 4)

    def testRealDataCharCytb(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'characters':["cytb"]}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Aleixo_2002","Allende_etal_2001","Aragon_etal_1999","Baker_etal_2005","Baker_etal_2006","Baker_etal_2007a",
                "Baker_etal_2007b","Barhoum_Burns_2002"]
        self.assertListEqual(expected_names,names)
        # and two source trees too
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 9)

    
    def testRealDataCharMorphYear(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'character_types':["morphological"], 'years':["2005-2008"]}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Aliabadian_etal_2007","Bertelli_etal_2006"]
        self.assertListEqual(expected_names,names)
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 4)


    def testRealDataCharMorphMol(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'character_types':["morphological","molecular"]}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Bertelli_etal_2006"]
        self.assertListEqual(expected_names,names)
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 1)

    def testRealDataCharMorphOrMol(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'character_types':["morphological","molecular"]}
        new_XML = create_subset(XML,searchTerms,andSearch=False)
        root = _parse_xml(new_XML)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Aleixo_2002","Aliabadian_etal_2007","Allende_etal_2001","Andersson_1999a","Aragon_etal_1999","Baker_Strauch_1988","Baker_etal_2005","Baker_etal_2006","Baker_etal_2007a","Baker_etal_2007b","Baptista_Visser_1999","Barber_Peterson_2004","Barhoum_Burns_2002","Bertelli_etal_2006"]
        self.assertListEqual(expected_names,names)

    def testRealDataCharTaxon(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'taxa':["Gallus gallus"]} # note - no _
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Aragon_etal_1999","Baker_etal_2006"]
        self.assertListEqual(expected_names,names)
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 2)

    def testRealDataCharTaxonYearEmpty(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'taxa':["Gallus gallus"], 'years':['2009']}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = []
        self.assertListEqual(expected_names,names)
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 0)

    def testRealDataAllFossil(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        searchTerms = {'fossil':"all_fossil"}
        new_XML = create_subset(XML,searchTerms)
        root = _parse_xml(new_XML)
        srcs = root.findall(".//source")
        names = []
        for s in srcs:
            names.append(s.attrib['name'])
        names.sort()
        expected_names = ["Baker_etal_2005"]
        self.assertListEqual(expected_names,names)
        src_trs = root.findall(".//source_tree")
        self.assertTrue(len(src_trs) == 1)

if __name__ == '__main__':
    unittest.main()




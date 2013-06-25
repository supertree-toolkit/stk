import unittest
import math
import sys
import os
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
from stk.supertree_toolkit import _check_uniqueness, _parse_subs_file, _check_taxa, _check_data, get_all_characters
from stk.supertree_toolkit import get_fossil_taxa, get_publication_years, data_summary, get_character_numbers, get_analyses_used
from stk.supertree_toolkit import add_historical_event, _sort_data, _parse_xml
from lxml import etree
from util import *
from stk.stk_exceptions import *
from collections import defaultdict
parser = etree.XMLParser(remove_blank_text=True)
import re

# Class to test all those loverly internal methods
# or stuff that doesn't fit within the other tests

class TestSetSourceNames(unittest.TestCase):

    def test_check_uniqueness(self):
        non_unique_names = etree.parse("data/input/non_unique_names.phyml")
        try:
            _check_uniqueness(etree.tostring(non_unique_names))
        except NotUniqueError:
            self.assert_(True)
            return
            
        self.assert_(False)

    def test_check_nonuniquess_pass(self):
        new_xml = etree.parse("data/input/full_tree.phyml")
        try:
            _check_uniqueness(etree.tostring(new_xml))
        except:
            self.assert_(False)
            return
            
        self.assert_(True)

    def test_parse_subs_file(self):
        """ tests a very standard subs file with some 
            deletes and subs
        """
        second_sub = "Anomalopteryx didiformis,Megalapteryx benhami,Megalapteryx didinus,Pachyornis australis,Pachyornis elephantopus,Pachyornis mappini,Euryapteryx curtus,Euryapteryx geranoides,Emeus crassus,Dinornis giganteus,Dinornis novaezealandiae"
        third_subs = "Avisaurus archibaldi,Avisaurus gloriae,Cathayornis,Concornis lacustris,Enantiornis leali,Eoalulavis,Gobipteryx minuta,Iberomesornis,Lectavis bretincola,Neuquenornis volans,Noguerornis,Sinornis santensis,Soroavisaurus australis,Two medicine form,Yungavolucris brevipedalis"
        
        old_taxa, new_taxa = _parse_subs_file('data/input/sub_files/subs1.txt')
        self.assert_(old_taxa[0] == "MRPoutgroup")
        self.assert_(new_taxa[0] == None)
        self.assert_(new_taxa[1] == second_sub);
        self.assert_(old_taxa[1] == "Dinornithidae")
        self.assert_(old_taxa[2] == "Enantiornithes")
        self.assert_(new_taxa[2] == third_subs)

    def test_parse_subs_correct_but_badly_formatted(self):
        """ This file is correct, but difficult to parse
        """

        edge1 = "taxa2,taxa3,taxa2,taxa4"
        edge2 = "taxa11,'taxa12=taxa13','taxa14+taxa15'"
        edge3 = "some_thing"
        edge2In = "taxa9+taxa10"
        edge4In = "'already=quoted'"
        bad2 = "taxa5,taxa6"
        edge4 =  "taxa3,taxa6,taxa4,taxa5"

        old_taxa, new_taxa = _parse_subs_file('data/input/sub_files/subs_edge.txt')

        self.assert_(len(old_taxa) == len(new_taxa))
        self.assert_(len(old_taxa) == 7)
        self.assert_(old_taxa[1] == edge2In)
        self.assert_(old_taxa[3] == edge4In)
        self.assert_(new_taxa[0] == edge1)
        self.assert_(new_taxa[1] == edge2)
        self.assert_(new_taxa[2] == edge3)
        self.assert_(new_taxa[4] == edge4)
        self.assert_(new_taxa[5] == edge4)
        self.assert_(new_taxa[6] == edge4)

    def test_bad_subs_file(self):
        """ Tests what happens when an incorrectly formatted subs file is passed in
        """

        #this test should die, so wrap it up...
        try:
            old_taxa, new_taxa = _parse_subs_file('data/input/nonsense.dat'); 
        except UnableToParseSubsFile:
            self.assert_(True)
            return
        self.assert_(False)

    def test_taxa_tree(self):
        """Tests the _check_taxa function
        """

        #this test should pass, but wrap it up anyway
        try:
            _check_taxa(etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)); 
        except e as InvalidSTKData:
            print e.msg
            self.assert_(False)
            return
        self.assert_(True)

    def test_incorrect_taxa_tree(self):
        """Tests the _check_taxa function
        """

        #this test should pass, but wrap it up anyway
        try:
            _check_taxa(etree.tostring(etree.parse('data/input/check_taxa.phyml',parser),pretty_print=True)); 
        except InvalidSTKData:
            self.assert_(True)
            return
        self.assert_(False)

    def test_check_data(self):
        """Tests the _check_data function
        """

        #this test should pass, but wrap it up anyway
        try:
            _check_data(etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)); 
        except e as InvalidSTKData:
            self.assert_(False)
            print e.msg
            return
        except e as NotUniqueError:
            self.assert_(False)
            print e.msg
            return
        self.assert_(True)

    def test_get_all_characters(self):
        """ Check the characters dictionary
        """
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        characters = get_all_characters(XML)
        expected_keys = ['molecular', 'morphological']
        key = characters.keys()
        key.sort()
        self.assertListEqual(key,expected_keys)
        
        self.assertListEqual(characters['molecular'],['12S'])
        self.assertListEqual(characters['morphological'],['feathers'])


    def test_get_fossil_taxa(self):
        """ Check the fossil taxa function
        """
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        fossils = get_fossil_taxa(XML)
        expected_fossils = ['A','B']
        self.assertListEqual(fossils,expected_fossils)
        
    def test_get_publication_years(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        years = get_publication_years(XML)
        self.assert_(years[2011] == 2)
        self.assert_(years[2010] == 1)
        self.assert_(years[2009] == 0) 

    def test_data_summary(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        simple_summary = data_summary(XML)
        full_summary = data_summary(XML,detailed = True)

        self.assertRegexpMatches(simple_summary,'Number of taxa: 8')
        self.assertRegexpMatches(simple_summary,'Number of characters: 2')
        self.assertRegexpMatches(simple_summary,'Number of character types: 2')
        self.assertRegexpMatches(simple_summary,'Number of trees: 3')
        self.assertRegexpMatches(simple_summary,'Number of fossil taxa: 2')
        self.assertRegexpMatches(simple_summary,'Number of analyses: 2')
        self.assertRegexpMatches(simple_summary,'Data spans: 2010 - 2011')

        self.assertRegexpMatches(full_summary,'Number of taxa: 8')
        self.assertRegexpMatches(full_summary,'Number of characters: 2')
        self.assertRegexpMatches(full_summary,'Number of character types: 2')
        self.assertRegexpMatches(full_summary,'Number of trees: 3')
        self.assertRegexpMatches(full_summary,'Number of fossil taxa: 2')
        self.assertRegexpMatches(full_summary,'Number of analyses: 2')
        self.assertRegexpMatches(full_summary,'Data spans: 2010 - 2011')
        self.assertRegexpMatches(full_summary,'     morphological')
        self.assertRegexpMatches(full_summary,'     molecular')
        self.assertRegexpMatches(full_summary,'Taxa List')

    def test_character_numbers(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        characters = get_character_numbers(XML)
        self.assert_(characters['feathers'] == 1)
        self.assert_(characters['12S'] == 2)
        self.assert_(characters['nonsense'] == 0)

    def test_analyses(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        analyses = get_analyses_used(XML)
        expected_analyses = ['Bayesian','MRP']
        self.assertListEqual(analyses,expected_analyses)

    def test_sort_data(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        xml_root = _parse_xml(XML)
        xml_root = _sort_data(xml_root)
        # By getting source, we can then loop over each source_tree
        # within that source and construct a unique name
        find = etree.XPath("//source")
        sources = find(xml_root)
        names = []
        for s in sources:
            # for each source, get source name
            names.append(s.attrib['name'])

        expected_names = ['Davis_2011','Hill_2011','Hill_Davis_2011']
        self.assertListEqual(names,expected_names)


    def test_add_event(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        import datetime
        now1 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        XML2 = add_historical_event(XML, "An event 1")
        import time
        time.sleep(1) # so we have a differet timestamp
        XML2 = add_historical_event(XML2, "An event 2")
        self.assertRegexpMatches(XML2, r'<history>')
        self.assertRegexpMatches(XML2, r'<event>')
        self.assertRegexpMatches(XML2, r'<datetime>')
        self.assertRegexpMatches(XML2, r'An event 2')
        self.assertRegexpMatches(XML2, r'An event 1')
        # That's some tags found, now let's get the datetimes (they have the same unless by some completely random
        # coincedence the two calls straddle a minute - can't really test for that without lots of parsing, etc, so
        # let's just settle with the correct datetime being found
        self.assertRegexpMatches(XML2, now1)

if __name__ == '__main__':
    unittest.main()
 

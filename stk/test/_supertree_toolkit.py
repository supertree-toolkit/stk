import unittest
import math
import sys
sys.path.append("../")
from supertree_toolkit import _check_uniqueness, _parse_subs_file, _check_taxa, _check_data
from supertree_toolkit import safe_taxonomic_reduction
import os
from lxml import etree
from util import *
import stk_exceptions
parser = etree.XMLParser(remove_blank_text=True)


# Class to test all those loverly internal methods
# or stuff that doesn't fit within the other tests

class TestSetSourceNames(unittest.TestCase):

    def test_check_uniqueness(self):
        non_unique_names = etree.parse("data/input/non_unique_names.phyml")
        try:
            _check_uniqueness(etree.tostring(non_unique_names))
        except stk_exceptions.NotUniqueError:
            self.assert_(True)
            return
            
        self.assert_(False)

    def test_check_nonuniquess_pass(self):
        new_xml = etree.parse("data/input/full_tree.xml")
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
        except stk_exceptions.UnableToParseSubsFile:
            self.assert_(True)
            return
        self.assert_(False)

    def test_taxa_tree(self):
        """Tests the _check_taxa function
        """

        #this test should pass, but wrap it up anyway
        try:
            _check_taxa(etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)); 
        except e as stk_exceptions.InvalidSTKData:
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
        except stk_exceptions.InvalidSTKData:
            self.assert_(True)
            return
        self.assert_(False)

    def test_check_data(self):
        """Tests the _check_data function
        """

        #this test should pass, but wrap it up anyway
        try:
            _check_data(etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)); 
        except e as stk_exceptions.InvalidSTKData:
            self.assert_(False)
            print e.msg
            return
        except e as stk_exceptions.NotUniqueError:
            self.assert_(False)
            print e.msg
            return
        self.assert_(True)

    def test_str(self):
        """Test STR function. Just prints out the equiv matrix
        """

        safe_taxonomic_reduction(etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)); 
        self.assert_(True)
  
if __name__ == '__main__':
    unittest.main()
 

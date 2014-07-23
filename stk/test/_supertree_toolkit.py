import unittest
import math
import sys
sys.path.insert(0,"../../")
sys.path.insert(0,"../")
from stk.supertree_toolkit import _check_uniqueness, parse_subs_file, _check_taxa, _check_data, get_all_characters, safe_taxonomic_reduction
import os
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
from stk.supertree_toolkit import _check_uniqueness, _check_taxa, _check_data, get_all_characters
from stk.supertree_toolkit import data_independence, get_character_numbers, get_analyses_used
from stk.supertree_toolkit import get_fossil_taxa, get_publication_years, data_summary
from stk.supertree_toolkit import data_overlap, read_matrix, subs_file_from_str, clean_data
from stk.supertree_toolkit import obtain_trees, get_all_source_names, _swap_tree_in_XML, replace_genera
from stk.supertree_toolkit import add_historical_event, _sort_data, _parse_xml, _check_sources
from stk.supertree_toolkit import get_all_taxa, _get_all_siblings, _parse_tree, get_characters_used
from stk.supertree_toolkit import _trees_equal, get_weights, create_taxonomy
from stk.supertree_toolkit import get_outgroup
from lxml import etree
from util import *
from stk.stk_exceptions import *
from collections import defaultdict
import tempfile
parser = etree.XMLParser(remove_blank_text=True)
import re

# Class to test all those loverly internal methods
# or stuff that doesn't fit within the other tests

class TestSTK(unittest.TestCase):

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
        second_sub = "Anomalopteryx_didiformis,Megalapteryx_benhami,Megalapteryx_didinus,Pachyornis_australis,Pachyornis_elephantopus,Pachyornis_mappini,Euryapteryx_curtus,Euryapteryx_geranoides,Emeus_crassus,Dinornis_giganteus,Dinornis_novaezealandiae"
        third_subs = "Avisaurus_archibaldi,Avisaurus_gloriae,Cathayornis,Concornis_lacustris,Enantiornis_leali,Eoalulavis,Gobipteryx_minuta,Iberomesornis,Lectavis_bretincola,Neuquenornis_volans,Noguerornis,Sinornis_santensis,Soroavisaurus_australis,Two_medicine_form,Yungavolucris_brevipedalis"
        
        old_taxa, new_taxa = parse_subs_file('data/input/sub_files/subs1.txt')
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

        old_taxa, new_taxa = parse_subs_file('data/input/sub_files/subs_edge.txt')

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
            old_taxa, new_taxa = parse_subs_file('data/input/nonsense.dat'); 
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
        except InvalidSTKData as e:
            print e.msg
            self.assert_(False)
            return
        self.assert_(True)

    def test_incorrect_taxa_tree(self):
        """Tests the _check_taxa function
        """

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
        except InvalidSTKData as e:
            print e.msg
            self.assert_(False)
            return
        except NotUniqueError as e:
            print e.msg
            self.assert_(False)
            return
        self.assert_(True)


    def test_check_sources(self):
        """Tests the _check_source function
        """
        #this test should pass, but wrap it up anyway
        try:
            # remove some sources first - this should pass
            XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
            name = "Hill_Davis_2011_1"
            new_xml = _swap_tree_in_XML(XML, None, name)
            _check_sources(new_xml); 
        except InvalidSTKData as e:
            print e.msg
            self.assert_(False)
            return
        except NotUniqueError as e:
            self.assert_(False)
            print e.msg
            return
        self.assert_(True)


    def test_str(self):
        """Test STR function.
        """
        # PerEQ.pl gives the following:
        # Taxon       No. Missing  Equivs
        # MRPOutgroup  	    0 
        # A 		        0 	    B(C*) B_b(C*)
        # B 		        2	    A(E) B_b(D)
        # B_b    		    4	    A(E) B(D) E(D) F (D)
        # C 		        2	    D(B*) E(D) F(D)
        # D 		        2	    C(B*) E(D) F(D)
        # E 		        4	    B_b(D) C(D) D(D) F (B*)
        # F 		        4	    B_b(D) C(D) D(D) E (B*)
        output, can_replace = safe_taxonomic_reduction(etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)); 
        substitutions = subs_file_from_str(output)
        expected_can_replace = ["B","B_b","D","F"]
        expected_substitutions = ['A = B,B_b,A']
        self.assertListEqual(expected_can_replace,can_replace)
        self.assertListEqual(expected_substitutions,substitutions)
        
    def test_str_from_matrix(self):
        """Test STR function from matrix
        """
        matrix,taxa = read_matrix("data/input/matrix.nex")
        output, can_replace = safe_taxonomic_reduction(XML=None,matrix=matrix,taxa=taxa); 
        substitutions = subs_file_from_str(output)
        expected_can_replace = ["B","B_b","D","F"]
        expected_substitutions = ['A = B,B_b,A']
        self.assertListEqual(expected_can_replace,can_replace)
        self.assertListEqual(expected_substitutions,substitutions)
  
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

    def test_data_summary_incomplete(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        simple_summary = data_summary(XML)
        XML = etree.tostring(etree.parse('data/input/old_stk_input_data_summary_test.phyml',parser),pretty_print=True)
        simple_summary2 = data_summary(XML,ignoreWarnings=True)
        self.assert_(simple_summary == simple_summary2)

    def test_character_numbers(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        characters = get_character_numbers(XML)
        self.assert_(characters['feathers'] == 1)
        self.assert_(characters['12S'] == 2)
        self.assert_(characters['nonsense'] == 0)

    def test_analyses(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        analyses = get_analyses_used(XML)
        expected_analyses = ['Bayesian','Maximum Parsimony']
        self.assertListEqual(analyses,expected_analyses)
    
    def test_data_independence(self):
        XML = etree.tostring(etree.parse('data/input/check_data_ind.phyml',parser),pretty_print=True)
        expected_dict = {'Hill_2011_2': ['Hill_2011_1', 1], 'Hill_Davis_2011_1': ['Hill_Davis_2011_2', 0]}
        non_ind = data_independence(XML)
        self.assertDictEqual(expected_dict, non_ind)

    def test_data_independence(self):
        XML = etree.tostring(etree.parse('data/input/check_data_ind.phyml',parser),pretty_print=True)
        expected_dict = {'Hill_2011_2': ['Hill_2011_1', 1], 'Hill_Davis_2011_1': ['Hill_Davis_2011_2', 0]}
        non_ind, new_xml = data_independence(XML,make_new_xml=True)
        self.assertDictEqual(expected_dict, non_ind)
        # check the second tree has not been removed
        self.assertRegexpMatches(new_xml,re.escape('((A:1.00000,B:1.00000)0.00000:0.00000,F:1.00000,E:1.00000,(G:1.00000,H:1.00000)0.00000:0.00000)0.00000:0.00000;'))
        # check that the first tree is removed
        self.assertNotRegexpMatches(new_xml,re.escape('((A:1.00000,B:1.00000)0.00000:0.00000,(F:1.00000,E:1.00000)0.00000:0.00000)0.00000:0.00000;'))
    
    def test_overlap(self):
        XML = etree.tostring(etree.parse('data/input/check_overlap_ok.phyml',parser),pretty_print=True)
        overlap_ok,keys = data_overlap(XML)
        self.assert_(overlap_ok)
        # Increase number required for sufficient overlap - this should fail
        overlap_ok,keys = data_overlap(XML,overlap_amount=3)
        self.assert_(not overlap_ok)
        # Now plot some graphics - kinda hard to test this, but not failing will suffice for now
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".png")
        overlap_ok,keys = data_overlap(XML,filename=temp_file,detailed=True)
        self.assert_(overlap_ok)
        os.remove(temp_file)
        overlap_ok,keys = data_overlap(XML,filename=temp_file)
        self.assert_(overlap_ok)
        os.remove(temp_file)

    def test_data_overlap_against_old_stk(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        # Note - we also test PDF output is OK
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".pdf")
        overlap_ok,keys = data_overlap(XML,filename=temp_file,detailed=False)
        # this is not ok!
        self.assert_(not overlap_ok)
        # now compare against the old code. This was created using
        #stk_check_overlap.pl --dir data/input/old_stk_test --compressed --graphic
        #Node number, tree file
        #0,data/input/old_stk_test/Allende_etal_2001/Allende_etal_2001com.tre
        #1,data/input/old_stk_test/Aleixo_2002/Aleixo2002com.tre
        #2,data/input/old_stk_test/Baptista_Visser_1999/Tree 1/Baptista_etal_1999_corr.tre
        #3,data/input/old_stk_test/Baker_etal_2005/Baker_etal_2005com.tre
        #4,data/input/old_stk_test/Aliabadian_etal_2007/Tree 2/Aliabadian_etal_2007_2_corr.tre
        #4,data/input/old_stk_test/Aliabadian_etal_2007/Tree 1/Aliabadian_etal_2007_1_corr.tre
        #5,data/input/old_stk_test/Barber_Peterson_2004/Tree 1/Barber_etal_2004_corr.tre
        #6,data/input/old_stk_test/Aragon_etal_1999/Aragon_etal_1999com1_2.tre
        #6,data/input/old_stk_test/Aragon_etal_1999/Tree 3/Aragon_etal_1999_3_corr.tre
        #7,data/input/old_stk_test/Baker_etal_2007b/Tree 1/Baker_etal_2007b_corr.tre
        #7,data/input/old_stk_test/Andersson_1999a/Tree 1/Andersson_1999a_corr.tre
        #7,data/input/old_stk_test/Andersson_1999b/Tree 2/Andersson_1999b_2_corr.tre
        #7,data/input/old_stk_test/Andersson_1999b/Tree 1/Andersson_1999b_1_corr.tre
        #7,data/input/old_stk_test/Baker_Strauch_1988/Tree 1/Baker_Strauch_1988_corr.tre
        #7,data/input/old_stk_test/Baker_etal_2007a/Tree 1/Baker_etal_2007a_corr.tre
        #8,data/input/old_stk_test/Baker_etal_2006/Tree 1/Baker_etal_2006_corr.tre
        #8,data/input/old_stk_test/Bertelli_etal_2006/Tree 2/Bertelli_etal_2006_2_corr.tre
        #8,data/input/old_stk_test/Bertelli_etal_2006/Tree 3/Bertelli_etal_2006_3_corr.tre
        #8,data/input/old_stk_test/Bertelli_etal_2006/Tree 1/Bertelli_etal_2006_1_corr.tre
        #9,data/input/old_stk_test/Barhoum_Burns_2002/Tree 1/Barhoum_Burns_2002_corr.tre
        # So that's 10 clusters
        self.assert_(len(keys) == 10)
        # the keys should be ordered from large to small, so
        self.assert_(len(keys[0]) == 6) # same as node 7 above
        self.assert_(len(keys[1]) == 4) # same as node 8 above
        self.assert_(len(keys[2]) == 2) # same as node 6 or 4 above
        self.assert_(len(keys[3]) == 2) # same as node 6 or 4 above
        self.assert_(len(keys[4]) == 1) # same as node 0,1,2,3,5 or 9 above
        self.assert_(len(keys[5]) == 1) # same as node 0,1,2,3,5 or 9 above
        self.assert_(len(keys[6]) == 1) # same as node 0,1,2,3,5 or 9 above
        self.assert_(len(keys[7]) == 1) # same as node 0,1,2,3,5 or 9 above
        self.assert_(len(keys[8]) == 1) # same as node 0,1,2,3,5 or 9 above
        self.assert_(len(keys[9]) == 1) # same as node 0,1,2,3,5 or 9 above
        # Now let's check the largest node contains the right things
        # We can only do that as both Andersson_1999a, Andersson_1999b are in same cluster and
        # both the Baker_etal_2007 papers are there too. Otherwise we wouldn't know which 
        # was a and b...
        self.assert_("Andersson_1999b_1" in keys[0])
        self.assert_("Andersson_1999a_1" in keys[0])
        self.assert_("Baker_etal_2007a_1" in keys[0])

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
        # coincidence the two calls straddle a minute - can't really test for that without lots of parsing, etc, so
        # let's just settle with the correct datetime being found
        self.assertRegexpMatches(XML2, now1)

    def test_read_matrix_nexus(self):
        matrix,taxa = read_matrix("data/input/matrix.nex")
        expected_taxa = ['MRPOutgroup','A','B','B_b','C','D','E','F']
        expected_matrix = [
                            ["0","0","0","0","0","0"],
                            ["1","0","1","0","1","0"],
                            ["1","0","?","?","1","0"],
                            ["?","?","1","0","?","?"],
                            ["0","1","0","1","?","?"],
                            ["0","1","0","1","?","?"],
                            ["?","?","?","?","0","1"],
                            ["?","?","?","?","0","1"]
                          ]
        self.assertListEqual(expected_taxa,taxa)
        self.assertListEqual(expected_matrix,matrix)

    def test_read_matrix_tnt(self):
        matrix,taxa = read_matrix("data/input/matrix.tnt")
        expected_taxa = ['MRPOutgroup','A','B','B_b','C','D','E','F']
        expected_matrix = [
                            ["0","0","0","0","0","0"],
                            ["1","0","1","0","1","0"],
                            ["1","0","?","?","1","0"],
                            ["?","?","1","0","?","?"],
                            ["0","1","0","1","?","?"],
                            ["0","1","0","1","?","?"],
                            ["?","?","?","?","0","1"],
                            ["?","?","?","?","0","1"]
                          ]
        self.assertListEqual(expected_taxa,taxa)
        self.assertListEqual(expected_matrix,matrix)

    def test_read_matrix_nexus_p4(self):
        matrix,taxa = read_matrix("data/input/matrix_p4.nex")
        expected_taxa = ['MRPOutgroup','A','B','B_b','C','D','E','F']
        expected_matrix = [
                            ["0","0","0","0","0","0"],
                            ["1","0","1","0","1","0"],
                            ["1","0","?","?","1","0"],
                            ["?","?","1","0","?","?"],
                            ["0","1","0","1","?","?"],
                            ["0","1","0","1","?","?"],
                            ["?","?","?","?","0","1"],
                            ["?","?","?","?","0","1"]
                          ]
        self.assertListEqual(expected_taxa,taxa)
        self.assertListEqual(expected_matrix,matrix)

    def test_clean_data(self):
        XML = etree.tostring(etree.parse('data/input/clean_data.phyml',parser),pretty_print=True)
        XML = clean_data(XML)
        trees = obtain_trees(XML)
        self.assert_(len(trees) == 2)
        expected_trees = {'Hill_2011_2': '(A,B,(C,D,E));', 'Hill_2011_1': '(A, B, C, (D, E, F));'}
        for t in trees:
            self.assert_(_trees_equal(trees[t],expected_trees[t]))

        # check only one source remains
        names = get_all_source_names(XML)
        self.assert_(len(names) == 1)
        self.assert_(names[0] == "Hill_2011")
       
    def test_check_data(self):
        XML = etree.tostring(etree.parse('data/input/clean_data.phyml',parser),pretty_print=True)
        self.assertRaises(UninformativeTreeError,_check_data,XML)
        try:
            _check_data(XML)
        except UninformativeTreeError as e:
            self.assertRegexpMatches(e.msg,"contains only 2 taxa and is not informative")
            self.assertRegexpMatches(e.msg,"doesn't contain any clades and is not informative")

    def test_replace_genera(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        XML,generic,subs = replace_genera(XML,dry_run=True)
        self.assert_(XML == None)
        # Old STK gave the following subs
        # Gallus = Gallus gallus
        # Larus = Larus argentatus,Larus marinus
        # Struthio = Struthio camelus
        expected_genera = ['Gallus','Larus','Struthio']
        expected_subs = ['Gallus_gallus','Larus_argentatus,Larus_marinus','Struthio_camelus']
        self.assertListEqual(expected_genera,generic)
        self.assertListEqual(expected_subs,subs)

    def test_replace_genera2(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        XML,generic,subs = replace_genera(XML)
        # see above for answer
        taxa = get_all_taxa(XML)
        self.assertNotIn('Gallus',taxa)
        self.assertNotIn('Larus',taxa)
        self.assertNotIn('Struthio',taxa)
        self.assertIn('Gallus_gallus',taxa) # should be anyway :)
      

    def test_replace_genera_subs(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        XML,generic,subs = replace_genera(XML)
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".dat")
        f = open(temp_file, "w")
        i = 0
        for g in generic:
            f.write(g+" = "+subs[i]+"\n")
            i+=1
        f.close()
        old_taxa, new_taxa = parse_subs_file(temp_file)
        expected_old = ['Gallus','Larus','Struthio']
        expected_new = ['Gallus_gallus','Larus_argentatus,Larus_marinus','Struthio_camelus']                
        self.assertListEqual(expected_old,old_taxa)
        self.assertListEqual(expected_new,new_taxa)

    def test_get_all_siblings(self):
        t = _parse_tree("(A,B,C,D,E,F,G,H,I,J);")
        siblings = _get_all_siblings(t.node(1))
        expected = ["B","C","D","E","F","G","H","I","J"]
        self.assertListEqual(siblings,expected)
        siblings = _get_all_siblings(t.node(3)) # selects C - so tests we get left siblings too
        expected = ["A","B","D","E","F","G","H","I","J"]
        self.assertListEqual(siblings,expected)

    def test_get_weights(self):
        XML = etree.tostring(etree.parse('data/input/weighted_trees.phyml',parser),pretty_print=True)
        weights = get_weights(XML)
        expected = {"Baker_etal_2007_1":2, "Baptista_Visser_1999_1":1,
                "Baptista_Visser_1999_2":1}
        self.assertDictEqual(weights,expected)
        return

    def test_get_outgroups(self):
        XML = etree.tostring(etree.parse('data/input/weighted_trees.phyml',parser),pretty_print=True)
        outgroups = get_outgroup(XML)
        expected = {"Baker_etal_2007_1":['Jacana_jacana'],
                "Baptista_Visser_1999_1":['Uraeginthus_bengalus', 'Uraeginthus_cyanocephalus'],
                "Baptista_Visser_1999_2":['Uraeginthus_bengalus', 'Uraeginthus_cyanocephalus']}
        self.assertDictEqual(outgroups,expected)
        return

    def test_get_characters_used(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        characters = get_characters_used(XML)
        expected_characters = [('12S','molecular'),
         ('16S','molecular'), 
         ('ATPase 6','molecular'),
         ('ATPase 8','molecular'),
         ('Alleles','molecular'),
         ('Body size','morphological'),
         ('Breeding','behavioural'),
         ('COI','molecular'),
         ('COIII','molecular'),
         ('Calls','behavioural'),
         ('Displays','behavioural'),
         ('Molecular','molecular'),
         ('Morphometrics','morphological'),
         ('ND2','molecular'),
         ('ND3','molecular'),
         ('ND4','molecular'),
         ('ND5','molecular'),
         ('Osteology','morphological'),
         ('Parasites','morphological'),
         ('Plumage','morphological'),
         ('RAG1','molecular'),
         ('behaviour','behavioural'), # NOTE the repetition here :)
         ('behaviour','morphological'),
         ('cytb','molecular'),
         ('mt control region','molecular'),
         ('oology','morphological'),
         ('soft tissue','morphological'),
         ('tRNA-Lys','molecular')
             ]
        for c in characters:
            self.assert_(c in expected_characters)
        self.assert_(len(characters) == len(expected_characters))

    def test_create_taxonomy(self):
        XML = etree.tostring(etree.parse('data/input/create_taxonomy.phyml',parser),pretty_print=True)
        expected = {'Egretta tricolor': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'subkingdom': 'Bilateria', 'subclass': 'Neoloricata', 'class': 'Aves', 'phylum': 'Chordata', 'superphylum': 'Lophozoa', 'suborder': 'Ischnochitonina', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Protostomia', 'genus': 'Egretta', 'order': 'Pelecaniformes'}, 
                     'Gallus gallus': {'kingdom': 'Animalia', 'family': 'Phasianidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'superphylum': 'Lophozoa', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Protostomia', 'genus': 'Gallus', 'order': 'Galliformes'}, 
                      'Thalassarche melanophris': {'kingdom': 'Animalia', 'family': 'Diomedeidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'infraphylum': 'Gnathostomata', 'superclass': 'Tetrapoda', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'genus': 'Thalassarche', 'order': 'Procellariiformes'}}
        if (internet_on()):
            taxonomy = create_taxonomy(XML) # what if there's no internet?
            self.assertDictEqual(taxonomy, expected)
        else:
            print "WARNING: No internet connection found. Not check the create_taxonomy function"


def internet_on():
    import urllib2
    try:
        response=urllib2.urlopen('http://74.125.228.100',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False


if __name__ == '__main__':
    unittest.main()
 

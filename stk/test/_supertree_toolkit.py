import unittest
import math
import sys
import os
sys.path.insert(0,"../../")
sys.path.insert(0,"../")
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
from stk.supertree_toolkit import create_taxonomy, safe_taxonomic_reduction, subs_file_from_str
from stk.supertree_toolkit import amalgamate_trees, create_matrix, substitute_taxa
from stk.supertree_toolkit import substitute_taxa_in_trees, data_summary, taxonomic_checker, load_equivalents
from stk.supertree_toolkit import generate_species_level_data, data_overlap, data_independence, add_historical_event
from stk.supertree_toolkit import clean_data, replace_genera, create_subset, tree_from_taxonomy, check_data
from stk.supertree_toolkit import import_bibliography, export_bibliography
from lxml import etree
import StringIO
import tempfile
import re
import stk.stk_exceptions as excp
import stk.stk_phyml as stk_phyml
import stk.stk_trees as stk_trees
import stk.stk_util as stk_util
parser = etree.XMLParser(remove_blank_text=True)

class TestSTK(unittest.TestCase):

    def test_amalgamate_trees_anonymous(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        output_string = amalgamate_trees(XML,format="nexus",anonymous=True)
        trees = stk_phyml.get_all_trees(XML)
        # save the file and read it back in. Then we check correct format (i.e. readable) and
        # we can check the trees are correct
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        f = open(temp_file,"w")
        f.write(output_string)
        f.close()
        try:
            trees_read = stk_trees.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk_trees.trees_equal(trees_read[i],trees[names[i]]))

    def test_amalgamate_trees_nexus(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        output_string = amalgamate_trees(XML,format="nexus",anonymous=False)
        trees = stk_phyml.get_all_trees(XML)
        # save the file and read it back in. Then we check correct format (i.e. readable) and
        # we can check the trees are correct
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        f = open(temp_file,"w")
        f.write(output_string)
        f.close()
        try:
            trees_read = stk_trees.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk_trees.trees_equal(trees_read[i],trees[names[i]]))

    def test_amalgamate_trees_newick(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        output_string = amalgamate_trees(XML,format="newick")
        trees = stk_phyml.get_all_trees(XML)
        # save the file and read it back in. Then we check correct format (i.e. readable) and
        # we can check the trees are correct
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        f = open(temp_file,"w")
        f.write(output_string)
        f.close()
        try:
            trees_read = stk_trees.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk_trees.trees_equal(trees_read[i],trees[names[i]]))

    def test_amalgamate_trees_tnt(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        output_string = amalgamate_trees(XML,format="tnt")
        trees = stk_phyml.get_all_trees(XML)
        # save the file and read it back in. Then we check correct format (i.e. readable) and
        # we can check the trees are correct
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        f = open(temp_file,"w")
        f.write(output_string)
        f.close()
        try:
            trees_read = stk_trees.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk_trees.trees_equal(trees_read[i],trees[names[i]]))

    def test_amalgamate_trees_unknown_format(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        output_string = amalgamate_trees(XML,format="PHYXML")
        self.assert_(output_string==None)

    def test_create_nexus_matrix(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML,format="nexus")
        handle = StringIO.StringIO(matrix)
        
    def test_create_tnt_matrix(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML)

    def test_create_tnt_matrix_with_taxonomy(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        taxonomy = stk_trees.import_tree('data/input/paup_tree.tre')
        matrix = create_matrix(XML,taxonomy=taxonomy)
        self.assertRegexpMatches(matrix,'Mimus_gilvus')

    def test_create_nexus_matrix_quote(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML,format="nexus",quote=True)
        self.assert_(not matrix.find("'") == -1)

    def test_create_nexus_matrix_weights(self):
        XML = etree.tostring(etree.parse('data/input/weighted_trees.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML)
        self.assert_(matrix.find('ccode +[/1. 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27;'))
        self.assert_(matrix.find('ccode +[/2. 28 29;'))

    def test_create_nexus_matrix_outgroups(self):
        XML = etree.tostring(etree.parse('data/input/weighted_trees.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML,outgroups=True)
        self.assert_(matrix.find('Jacana_jacana') == -1)
        self.assert_(matrix.find('Uraeginthus_cyanocephalus') == -1)
        self.assert_(matrix.find('Uraeginthus_bengalus') == -1)

    def test_create_nexus_matrix(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML,format="nexus")
        handle = StringIO.StringIO(matrix)
        
    def test_create_tnt_matrix(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML)

    def test_create_tnt_matrix_with_taxonomy(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        taxonomy = stk_trees.import_tree('data/input/paup_tree.tre')
        matrix = create_matrix(XML,taxonomy=taxonomy)
        self.assertRegexpMatches(matrix,'Mimus_gilvus')

    def test_create_nexus_matrix_quote(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML,format="nexus",quote=True)
        self.assert_(not matrix.find("'") == -1)

    def test_create_nexus_matrix_weights(self):
        XML = etree.tostring(etree.parse('data/input/weighted_trees.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML)
        self.assert_(matrix.find('ccode +[/1. 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27;'))
        self.assert_(matrix.find('ccode +[/2. 28 29;'))

    def test_create_nexus_matrix_outgroups(self):
        XML = etree.tostring(etree.parse('data/input/weighted_trees.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML,outgroups=True)
        self.assert_(matrix.find('Jacana_jacana') == -1)
        self.assert_(matrix.find('Uraeginthus_cyanocephalus') == -1)
        self.assert_(matrix.find('Uraeginthus_bengalus') == -1)


    def test_check_data(self):
        """Tests the _check_data function
        """
        #this test should pass, but wrap it up anyway
        try:
            check_data(etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)); 
        except excp.InvalidSTKData as e:
            print e.msg
            self.assert_(False)
            return
        except excp.NotUniqueError as e:
            print e.msg
            self.assert_(False)
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
        matrix,taxa = stk_trees.read_matrix("data/input/matrix.nex")
        output, can_replace = safe_taxonomic_reduction(XML=None,matrix=matrix,taxa=taxa); 
        substitutions = subs_file_from_str(output)
        expected_can_replace = ["B","B_b","D","F"]
        expected_substitutions = ['A = B,B_b,A']
        self.assertListEqual(expected_can_replace,can_replace)
        self.assertListEqual(expected_substitutions,substitutions)


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

    
    def test_data_independence(self):
        XML = etree.tostring(etree.parse('data/input/check_data_ind.phyml',parser),pretty_print=True)
        expected_idents = [['Hill_Davis_2011_2', 'Hill_Davis_2011_1', 'Hill_Davis_2011_3'], ['Hill_Davis_2013_1', 'Hill_Davis_2013_2']]
        non_ind,subsets = data_independence(XML)
        expected_subsets = [['Hill_2011_1', 'Hill_2011_2']]
        self.assertListEqual(expected_subsets, subsets)
        self.assertListEqual(expected_idents, non_ind)

    def test_data_independence_2(self):
        XML = etree.tostring(etree.parse('data/input/check_data_ind.phyml',parser),pretty_print=True)
        expected_idents = [['Hill_Davis_2011_2', 'Hill_Davis_2011_1', 'Hill_Davis_2011_3'], ['Hill_Davis_2013_1', 'Hill_Davis_2013_2']]
        expected_subsets = [['Hill_2011_1', 'Hill_2011_2']]
        non_ind, subset, new_xml = data_independence(XML,make_new_xml=True)
        self.assertListEqual(expected_idents, non_ind)
        self.assertListEqual(expected_subsets, subset)
        # check the second tree has not been removed
        self.assertRegexpMatches(new_xml,re.escape('((A:1.00000,B:1.00000)0.00000:0.00000,F:1.00000,E:1.00000,(G:1.00000,H:1.00000)0.00000:0.00000)0.00000:0.00000;'))
        # check that the first tree is removed
        self.assertNotRegexpMatches(new_xml,re.escape('((A:1.00000,B:1.00000)0.00000:0.00000,(F:1.00000,E:1.00000)0.00000:0.00000)0.00000:0.00000;'))
        expected_weights = [str(1.0/3.0), str(1.0/3.0), str(1.0/3.0), str(0.5), str(0.5)]
        weights_in_xml = []
        # now check weights have been added to the correct part of the tree
        xml_root = stk_phyml.parse_xml(new_xml)
        # don't use stk_phyml.get_weights as it refactors for making the matrix
        i = 0
        for ei in expected_idents:
            for tree in ei:
                find = etree.XPath("//source_tree")
                trees = find(xml_root)
                for t in trees:
                    if t.attrib['name'] == tree:
                        # check len(trees) == 0
                        weights_in_xml.append(t.xpath("tree/weight/real_value")[0].text)
        self.assertListEqual(expected_weights,weights_in_xml) 
    

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
        keys = sorted(keys, key = len, reverse=True)
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


    def test_clean_data(self):
        XML = etree.tostring(etree.parse('data/input/clean_data.phyml',parser),pretty_print=True)
        XML = clean_data(XML)
        trees = stk_phyml.get_all_trees(XML)
        self.assert_(len(trees) == 2)
        expected_trees = {'Hill_2011_2': '(A,B,(C,D,E));', 'Hill_2011_1': '(A, B, C, (D, E, F));'}
        for t in trees:
            self.assert_(stk_trees.trees_equal(trees[t],expected_trees[t]))
        # check only one source remains
        names = stk_phyml.get_all_source_names(XML)
        self.assert_(len(names) == 1)
        self.assert_(names[0] == "Hill_2011")
    

    def test_check_data(self):
        XML = etree.tostring(etree.parse('data/input/clean_data.phyml',parser),pretty_print=True)
        self.assertRaises(excp.UninformativeTreeError,check_data,XML)
        try:
            check_data(XML)
        except excp.UninformativeTreeError as e:
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
        taxa = stk_phyml.get_all_taxa(XML)
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
        old_taxa, new_taxa = stk_util.load_subs_file(temp_file)
        expected_old = ['Gallus','Larus','Struthio']
        expected_new = ['Gallus_gallus','Larus_argentatus,Larus_marinus','Struthio_camelus']        
        self.assertListEqual(expected_old,old_taxa)
        self.assertListEqual(expected_new,new_taxa)


    def test_load_equivalents(self):
        csv_file = "data/input/equivalents.csv"
        expected = {'Turnix_sylvatica': [['Turnix_sylvaticus','Tetrao_sylvaticus','Tetrao_sylvatica','Turnix_sylvatica'],'yellow'],
                    'Xiphorhynchus_pardalotus':[['Xiphorhynchus_pardalotus'],'green'],
                    'Phaenicophaeus_curvirostris':[['Zanclostomus_curvirostris','Rhamphococcyx_curvirostris','Phaenicophaeus_curvirostris','Rhamphococcyx_curvirostr'],'yellow'],
                    'Megalapteryx_benhami':[['Megalapteryx_benhami'],'red']
                    }
        equivalents = load_equivalents(csv_file)
        self.assertDictEqual(equivalents, expected)


if __name__ == '__main__':
    unittest.main()
 

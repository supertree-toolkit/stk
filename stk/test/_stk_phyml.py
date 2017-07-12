#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2017, Jon Hill, Katie Davis
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
#    Jon Hill. jon.hill@york.ac.uk. 

import unittest
import math
import sys
# so we import local stk before any other central install
sys.path.insert(0,"../../")
from stk.stk_phyml import get_project_name, create_name, single_sourcename, all_sourcenames, get_all_source_names
from stk.stk_phyml import set_unique_names, create_tree_name, set_all_tree_names, get_all_characters
from stk.stk_phyml import get_publication_year_tree, get_characters_from_tree, get_character_types_from_tree
from stk.stk_phyml import get_characters_used, get_character_numbers, get_taxa_from_tree, get_fossil_taxa
from stk.stk_phyml import get_analyses_used, get_publication_years, get_all_trees, get_all_taxa, get_weights
from stk.stk_phyml import get_outgroup, load_phyml, add_weights, check_uniqueness, swap_tree_in_XML
from stk.stk_phyml import check_taxa, check_sources, parse_xml, sort_data, check_informative_trees
from stk.stk_phyml import find_trees_for_permuting, check_subs_against, get_all_tree_names, get_all_genera
import os
import stk.stk_exceptions as excp
import stk.stk_trees as stk_trees
from lxml import etree
from util import *
parser = etree.XMLParser(remove_blank_text=True)


xml_single = etree.parse("data/input/single_name.xml")
xml_single_c = etree.parse("data/output/single_name.xml")
xml_two = etree.parse("data/input/two_names.xml")
xml_two_c = etree.parse("data/output/two_names.xml")
xml_lots = etree.parse("data/input/lots.xml")
xml_lots_c = etree.parse("data/output/lots.xml")
xml_full = etree.parse("data/input/full_tree.phyml")
xml_full_c = etree.parse("data/output/full_tree.phyml")
non_unique_names = etree.parse("data/input/non_unique_names.phyml")

class TestPhyml(unittest.TestCase):

    @unittest.skip("FIX THIS")
    def test_load_phyml(self):
        self.assert_(False)

    def test_get_project_name(self):
        XML = etree.tostring(etree.parse('data/input/single_source.phyml',parser),pretty_print=True)
        name = get_project_name(XML)
        expected = "Test"
        self.assert_(expected == name)
        
        XML = etree.tostring(etree.parse('data/input/start_up.phyml',parser),pretty_print=True)
        name = get_project_name(XML)
        self.assert_(name == None)

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


    def test_get_all_tree_names(self):
        XML = etree.tostring(etree.parse('data/input/single_source_same_tree_name.phyml',parser),pretty_print=True)
        names = get_all_tree_names(XML)
        self.assertListEqual(names,['Hill_2011_2','Hill_2011_2'])

    @unittest.skip("FIX THIS")
    def test_set_unique_names(self):
        self.assert_(False)

    def test_name_tree(self):
        XML = etree.tostring(etree.parse('data/input/single_source_no_names.phyml',parser),pretty_print=True)
        xml_root = parse_xml(XML)
        source_tree_element = xml_root.xpath('/phylo_storage/sources/source/source_tree')[0]
        tree_name = create_tree_name(XML, source_tree_element)
        self.assert_(tree_name == 'Hill_2011_1')

    def test_all_name_tree(self):
        XML = etree.tostring(etree.parse('data/input/single_source_no_names.phyml',parser),pretty_print=True)
        new_xml = set_all_tree_names(XML)
        XML = etree.tostring(etree.parse('data/input/single_source.phyml',parser),pretty_print=True)
        self.assert_(isEqualXML(new_xml,XML))

    def test_all_rename_tree(self):
        XML = etree.tostring(etree.parse('data/input/single_source_same_tree_name.phyml',parser),pretty_print=True)
        new_xml = set_all_tree_names(XML,overwrite=True)
        XML = etree.tostring(etree.parse('data/output/single_source_same_tree_name.phyml',parser),pretty_print=True)
        self.assert_(isEqualXML(new_xml,XML))


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

    @unittest.skip("FIX THIS")
    def test_get_publication_year_tree(self):
        self.assert_(False)



    def test_taxa_from_characters(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        chars = get_characters_from_tree(XML,"Hill_Davis_2011_1")
        expected_chars = ['cytb','12S']
        self.assertListEqual(chars,expected_chars)

    def test_taxa_from_characters_sort(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        chars = get_characters_from_tree(XML,"Hill_Davis_2011_1",sort=True)
        expected_chars = ['12S','cytb']
        self.assertListEqual(chars,expected_chars)

    @unittest.skip("FIX THIS")
    def test_get_character_types_from_tree(self):
        self.assert_(False)


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

   
    def test_character_numbers(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        characters = get_character_numbers(XML)
        self.assert_(characters['feathers'] == 1)
        self.assert_(characters['12S'] == 2)
        self.assert_(characters['nonsense'] == 0) 


    def test_taxa_from_tree(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        taxa = get_taxa_from_tree(XML,"Hill_2011_1")
        expected_taxa = ['A','B','F_b','G_g']
        self.assertListEqual(taxa,expected_taxa)

    def test_taxa_from_tree_sort(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        taxa = get_taxa_from_tree(XML,"Hill_2011_1",sort=True)
        expected_taxa = ['A','B','F_b','G_g']
        self.assertListEqual(taxa,expected_taxa)


    def test_get_fossil_taxa(self):
        """ Check the fossil taxa function
        """
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        fossils = get_fossil_taxa(XML)
        expected_fossils = ['A','B']
        self.assertListEqual(fossils,expected_fossils)


    def test_analyses(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        analyses = get_analyses_used(XML)
        expected_analyses = ['Bayesian','Maximum Parsimony']
        self.assertListEqual(analyses,expected_analyses)

           
    def test_get_publication_years(self):
        XML = etree.tostring(etree.parse('data/input/check_fossils.phyml',parser),pretty_print=True)
        years = get_publication_years(XML)
        self.assert_(years[2011] == 2)
        self.assert_(years[2010] == 1)
        self.assert_(years[2009] == 0)  

        

    def test_find_trees_for_permuting(self):
        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        permute_trees = find_trees_for_permuting(XML)
        self.assert_(len(permute_trees) == 0)

    def test_find_trees_for_permuting(self):
        XML = etree.tostring(etree.parse('data/input/permute_trees.phyml',parser),pretty_print=True)
        permute_trees = find_trees_for_permuting(XML)
        self.assert_(len(permute_trees) == 4)
        self.assert_(permute_trees['Hill_2011_1'] == "((E%1,'G%1'),A,(G%2,(E%2,F,D,H,E%3)));")
        self.assert_(permute_trees['Davis_2011_1'] == '(Outgroup,(((((Leopardus_geoffroyi,Leopardus_pardalis),(Otocolobus_manul,Felis_magrita)),(Prionailurus_bengalensis,Leptailurus_serval)),(Catopuma_temmincki,(Caracal_caracal,Lynx_rufus))),((Acinonyx_jubatus,(Puma_concolor,(Panthera_tigris%1,Panthera_uncia))),(Panthera_onca,(Panthera_leo,Panthera_tigris%2)))));')
        self.assert_(permute_trees['Hill_Davis_2011_1'] == '(A, (B, (C, D, E%1, F, G, E%2, E%3)));')
        self.assert_(permute_trees['Hill_Davis_2011_2'] == "(A, (B, (C, D, 'E E%1', F, G, 'E E%2', 'E E%3')));")




    def test_insert_tree_XML(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        name = "Hill_Davis_2011_1"
        tree = "(a,b,c);"
        new_xml = swap_tree_in_XML(XML, tree, name)
        trees = get_all_trees(new_xml)
        # loop through all trees, checking them
        self.assert_(trees['Hill_2011_1'] == "((A:1.00000,B:1.00000)0.00000:0.00000,(F:1.00000,E:1.00000)0.00000:0.00000)0.00000:0.00000;")
        self.assert_(trees['Davis_2011_1'] == "((A:1.00000,B:1.00000)0.00000:0.00000,(C:1.00000,D:1.00000)0.00000:0.00000)0.00000:0.00000;")
        self.assert_(trees[name] == "(a,b,c);")

    def test_delete_tree_XML(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        name = "Hill_Davis_2011_1"
        trees = get_all_trees(XML)
        old_len = len(trees)
        new_xml = swap_tree_in_XML(XML, None, name)
        trees = get_all_trees(new_xml)
        # loop through all trees, checking them
        self.assert_(trees['Davis_2011_1'] == "((A:1.00000,B:1.00000)0.00000:0.00000,(C:1.00000,D:1.00000)0.00000:0.00000)0.00000:0.00000;")
        self.assert_(len(trees) == old_len-1)
        # check that no sources are empty


    def test_taxa_tree(self):
        """Tests the _check_taxa function
        """

        #this test should pass, but wrap it up anyway
        try:
            check_taxa(etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True));
        except excp.InvalidSTKData as e:
            print e.msg
            self.assert_(False)
            return
        self.assert_(True)

    def test_incorrect_taxa_tree(self):
        """Tests the _check_taxa function
        """
        try:
            check_taxa(etree.tostring(etree.parse('data/input/check_taxa.phyml',parser),pretty_print=True)); 
        except excp.InvalidSTKData:
            self.assert_(True)
            return
        self.assert_(False)

    @unittest.skip("FIX THIS")
    def test_parse_xml(self):
        self.assert_(False)

    @unittest.skip("FIX THIS")
    def test_check_informative_trees(self):
        self.assert_(False)

    def test_sort_data(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        xml_root = parse_xml(XML)
        xml_root = sort_data(xml_root)
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

    def test_check_sources(self):
        """Tests the _check_source function
        """
        #this test should pass, but wrap it up anyway
        try:
            # remove some sources first - this should pass
            XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
            name = "Hill_Davis_2011_1"
            new_xml = swap_tree_in_XML(XML, None, name)
            check_sources(new_xml); 
        except excp.InvalidSTKData as e:
            print e.msg
            self.assert_(False)
            return
        except excp.NotUniqueError as e:
            self.assert_(False)
            print e.msg
            return
        self.assert_(True)


    def test_delete_tree_XML_and_remove_source(self):
        XML = etree.tostring(etree.parse('data/input/clean_data.phyml',parser),pretty_print=True)
        names = ["Hill_2012_1","Hill_2012_2"]
        names.sort(reverse=True)
        trees = get_all_trees(XML)
        old_len = len(trees)
        new_xml = XML
        for name in names:
            new_xml = swap_tree_in_XML(new_xml, None, name, delete=True)

        trees = get_all_trees(new_xml)
        self.assert_(len(trees) == old_len-2)
        # check only one source remains
        names = get_all_source_names(new_xml)
        self.assert_(len(names) == 1)
        self.assert_(names[0] == "Hill_2011")

    def test_get_all_trees(self):
        XML = etree.tostring(etree.parse("data/input/single_source.phyml",parser),pretty_print=True)
        tree = get_all_trees(XML)
        # Tree key is source_name_tree_no, so we should have
        # Hill_2011_1
        expected_tree = '((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;'
        self.assert_(tree['Hill_2011_1'] == expected_tree)

    def test_get_all_taxa(self):
        XML = etree.tostring(etree.parse("data/input/single_source.phyml",parser),pretty_print=True)
        taxa_list = get_all_taxa(XML)
        expected_taxa = ['A_1','B_1','E_1','F_1','G_1','H_1']
        self.assert_(expected_taxa == taxa_list)

    def test_get_all_taxa_pretty(self):
        XML = etree.tostring(etree.parse("data/input/single_source.phyml",parser),pretty_print=True)
        taxa_list = get_all_taxa(XML,pretty=True)
        expected_taxa = ['A 1','B 1','E 1','F 1','G 1','H 1']
        self.assert_(expected_taxa == taxa_list)

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

    def test_add_weights(self):
        """Add weights to a bunch of trees"""
        XML = etree.tostring(etree.parse('data/input/check_data_ind.phyml',parser),pretty_print=True)
        # see above
        expected_idents = [['Hill_Davis_2011_2', 'Hill_Davis_2011_1', 'Hill_Davis_2011_3'], ['Hill_Davis_2013_1', 'Hill_Davis_2013_2']]
        # so the first should end up with a weight of 0.33333 and the second with 0.5
        for ei in expected_idents:
            weight = 1.0/float(len(ei))
            XML = add_weights(XML, ei, weight)

    def test_check_uniqueness(self):
        non_unique_names = etree.parse("data/input/non_unique_names.phyml")
        try:
            check_uniqueness(etree.tostring(non_unique_names))
        except excp.NotUniqueError:
            self.assert_(True)
            return
            
        self.assert_(False)

    def test_check_nonuniquess_pass(self):
        new_xml = etree.parse("data/input/full_tree.phyml")
        try:
            check_uniqueness(etree.tostring(new_xml))
        except:
            self.assert_(False)
            return
        self.assert_(True)


    def test_check_subs_adding(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        try:
            check_subs_against(XML,["Fred","Bob"])
        except excp.AddingTaxaWarning as detail:
            self.assert_(True,"Correctly identified incoming taxa")
            self.assertRegexpMatches(detail.msg,"Fred")
            return
        self.assert_(False)

    def test_check_subs_not_adding(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        try:
            check_subs_against(XML,["A","B_b"])
        except excp.AddingTaxaWarning:
            self.assert_(False)
            return
        self.assert_(True,"Correctly let the subs go")


if __name__ == '__main__':
    unittest.main()
 


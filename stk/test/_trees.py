import unittest
import math
import sys
sys.path.append("../")
from supertree_toolkit import import_tree, obtain_trees, get_all_taxa, _assemble_tree_matrix, create_matrix, _delete_taxon, _sub_taxon
from supertree_toolkit import _swap_tree_in_XML, substitute_taxa, get_taxa_from_tree, get_characters_from_tree
import os
from lxml import etree
from util import *
import StringIO
from Bio import Phylo
import numpy
from Bio import AlignIO

# our test dataset

standard_tre = "data/input/test_tree.tre"
single_source_input = "data/input/single_source.phyml"
expected_tree = '((Taxon_c:1.00000,(Taxon_a:1.00000,Taxon_b:1.00000)0.00000:0.00000)0.00000:0.00000,(Taxon_d:1.00000,Taxon_e:1.00000)0.00000:0.00000)0.00000:0.00000;'
parser = etree.XMLParser(remove_blank_text=True)

class TestImportTree(unittest.TestCase):

    def test_import_treeview(self):
        test_file = "data/input/treeview_test.tre"
        tree = import_tree(test_file)
        self.assert_(expected_tree+"\n" == tree)

    def test_import_mesquite(self):
        test_file = "data/input/mesquite_test.tre"
        tree = import_tree(test_file)
        self.assert_(expected_tree+"\n" == tree)

    def test_import_figtree(self):
        test_file = "data/input/figtree_test.tre"
        tree = import_tree(test_file)
        self.assert_(expected_tree+"\n" == tree)

    def test_import_dendroscope(self):
        test_file = "data/input/dendroscope_test.tre"
        tree = import_tree(test_file)
        print tree
        self.assert_(expected_tree+"\n" == tree)

    def test_import_macclade(self):
        test_file = "data/input/macclade_test.tre"
        tree = import_tree(test_file)
        self.assert_(expected_tree+"\n" == tree)

    def test_get_all_trees(self):
        XML = etree.tostring(etree.parse(single_source_input,parser),pretty_print=True)
        tree = obtain_trees(XML)
        # Tree key is source_name_tree_no, so we should have
        # Hill_2011_1
        expected_tree = '((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;'
        self.assert_(tree['Hill_2011_1'] == expected_tree)

    def test_get_all_taxa(self):
        XML = etree.tostring(etree.parse(single_source_input,parser),pretty_print=True)
        taxa_list = get_all_taxa(XML)
        expected_taxa = ['A_1','B_1','E_1','F_1','G_1','H_1']
        self.assert_(expected_taxa == taxa_list)

    def test_get_all_taxa_pretty(self):
        XML = etree.tostring(etree.parse(single_source_input,parser),pretty_print=True)
        taxa_list = get_all_taxa(XML,pretty=True)
        expected_taxa = ['A 1','B 1','E 1','F 1','G 1','H 1']
        self.assert_(expected_taxa == taxa_list)

    def test_assemble_tree_matrix(self):
        handle = StringIO.StringIO('((A,B),F,E,(G,H));')
        trees = list(Phylo.parse(handle, "newick"))
        tree = trees[0]
        matrix, taxa = _assemble_tree_matrix(tree)
        # this should give us:
        expected_matrix = numpy.array(
                          [[1, 1, 0],
                           [1, 1, 0],
                           [1, 0, 0], 
                           [1, 0, 0], 
                           [1, 0, 1],
                           [1, 0, 1]])
        expected_taxa = ['A','B','F','E','G','H']
        self.assert_(matrix.all() == expected_matrix.all())
        self.assert_(expected_taxa == taxa)

    def test_create_nexus_matrix(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML,format="nexus")
        handle = StringIO.StringIO(matrix)
        print matrix
        

    def test_create_tnt_matrix(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        matrix = create_matrix(XML)

    def test_delete_taxa(self):
        t = "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;"
        new_tree = _delete_taxon("H_1", t)
        self.assert_(new_tree == "((A_1:1.00000,B_1:1.00000)0.00:0.00000,F_1:1.00000,E_1:1.00000,G_1:1.00000)0.00:0.00000;\n")

    def test_delete_taxa_missing(self):
        t = "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;"
        new_tree = _delete_taxon("Fred", t)
        self.assert_(new_tree == "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;")

    def test_sub_taxa(self):
        t = "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;"
        new_tree = _sub_taxon("H_1", "blah", t)
        self.assert_(new_tree == "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,blah:1.00000)0.00000:0.00000)0.00000:0.00000;")

    def test_sub_taxa_missing(self):
        t = "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;"
        new_tree = _sub_taxon("Fred", "Blah",  t)
        self.assert_(new_tree == "((A_1:1.00000,B_1:1.00000)0.00000:0.00000,F_1:1.00000,E_1:1.00000,(G_1:1.00000,H_1:1.00000)0.00000:0.00000)0.00000:0.00000;")


    def test_insert_tree_XML(self):
        XML = etree.tostring(etree.parse('data/input/create_matrix.phyml',parser),pretty_print=True)
        name = "Hill_Davis_2011_1"
        tree = "(a,b,c);"
        new_xml = _swap_tree_in_XML(XML, tree, name)
        trees = obtain_trees(new_xml)
        # loop through all trees, checking them
        self.assert_(trees['Hill_2011_1'] == "((A:1.00000,B:1.00000)0.00000:0.00000,(F:1.00000,E:1.00000)0.00000:0.00000)0.00000:0.00000;")
        self.assert_(trees['Davis_2011_1'] == "((A:1.00000,B:1.00000)0.00000:0.00000,(C:1.00000,D:1.00000)0.00000:0.00000)0.00000:0.00000;")
        self.assert_(trees[name] == "(a,b,c);")

    def test_substitute_taxa_single(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, "A", "Fred")
        taxa = get_all_taxa(XML2)
        contains_Fred = False
        contains_A = False
        for t in taxa:
            if (t == 'Fred'):
                contains_Fred = True
            if (t == "A"):
                contains_A = True

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree

        # now need to check the XML for the taxon block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//taxon")
        taxa = find(xml_root)
        contains_Fred = False
        contains_A = False
        for t in taxa:
            name = t.attrib['name']
            if name == 'Fred':
                contains_Fred = True
            if name == 'A':
                contains_A = True

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree


    def test_delete_taxa_single(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, "A")
        taxa = get_all_taxa(XML2)
        contains_A = False
        for t in taxa:
            if (t == "A"):
                contains_A = True
        self.assert_(not contains_A) # we should not have A in a tree

        # now need to check the XML for the taxon block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//taxon")
        taxa = find(xml_root)
        contains_A = False
        for t in taxa:
            name = t.attrib['name']
            if name == 'A':
                contains_A = True


        self.assert_(not contains_A) # we should not have A in a tree



    def test_substitute_taxa_multiple(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A","B_b"], ["Fred","Bob"])
        taxa = get_all_taxa(XML2)
        contains_Fred = False
        contains_Bob = False
        contains_A = False
        contains_B = False
        for t in taxa:
            if (t == 'Fred'):
                contains_Fred = True
            if (t == "A"):
                contains_A = True
            if (t == 'Bob'):
                contains_Bob = True
            if (t == "B_b"):
                contains_B = True

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree
        self.assert_(contains_Bob)
        self.assert_(not contains_B) # we should not have B in a tree

        # now need to check the XML for the taxon block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//taxon")
        taxa = find(xml_root)
        contains_Fred = False
        contains_Bob = False
        contains_A = False
        contains_B = False
        for t in taxa:
            name = t.attrib['name']
            if name == 'Fred':
                contains_Fred = True
            if name == 'A':
                contains_A = True
            if name == 'Bob':
                contains_Bob = True
            if name == 'B_b':
                contains_B = True

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree
        self.assert_(contains_Bob)
        self.assert_(not contains_B) # we should not have B in a tree

    def test_substitute_taxa_multiple_sub1_del1(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A","B_b"], ["Fred",None])
        taxa = get_all_taxa(XML2)
        contains_Fred = False
        contains_A = False
        contains_B = False
        for t in taxa:
            if (t == 'Fred'):
                contains_Fred = True
            if (t == "A"):
                contains_A = True
            if (t == "B_b"):
                contains_B = True

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree
        self.assert_(not contains_B) # we should not have B in a tree
        
        # now need to check the XML for the taxon block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//taxon")
        taxa = find(xml_root)
        contains_Fred = False
        contains_A = False
        contains_B = False
        for t in taxa:
            name = t.attrib['name']
            if name == 'Fred':
                contains_Fred = True
            if name == 'A':
                contains_A = True
            if name == 'B_b':
                contains_B = True

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree
        self.assert_(not contains_B) # we should not have B in a tree

    def test_taxa_from_tree(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        taxa = get_taxa_from_tree(XML,"Hill_2011_1")
        expected_taxa = ['A','B','F','E']
        self.assertListEqual(taxa,expected_taxa)

    def test_taxa_from_tree_sort(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        taxa = get_taxa_from_tree(XML,"Hill_2011_1",sort=True)
        expected_taxa = ['A','B','E','F']
        self.assertListEqual(taxa,expected_taxa)

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
     
if __name__ == '__main__':
    unittest.main()
 

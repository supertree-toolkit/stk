import unittest
import math
import sys
sys.path.insert(0,"../../")
sys.path.insert(0,"../")
import os
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
from stk.supertree_toolkit import parse_subs_file, _check_data, _sub_taxa_in_tree, _trees_equal, substitute_taxa_in_trees
from stk.supertree_toolkit import check_subs, _tree_contains, _correctly_quote_taxa, _remove_single_poly_taxa
from stk.supertree_toolkit import _swap_tree_in_XML, substitute_taxa, get_all_taxa, _parse_tree, _delete_taxon
from stk.supertree_toolkit import _collapse_nodes, import_tree, subs_from_csv, _getTaxaFromNewick, obtain_trees
from lxml import etree
from util import *
from stk.stk_exceptions import *
from collections import defaultdict
import tempfile
parser = etree.XMLParser(remove_blank_text=True)
import re


class TestSubs(unittest.TestCase):

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

    def test_bad_subs_file2(self):
        """ Tests what happens when an incorrectly formatted subs file is passed in
        """

        #this test should die, so wrap it up...
        try:
            old_taxa, new_taxa = parse_subs_file('data/input/sub_files/bad_subs.txt'); 
        except UnableToParseSubsFile:
            self.assert_(True)
            return
        self.assert_(False)

    def test_csv_subs(self):
        """Tests the CSV subs parsing
        """
        second_sub = "Anomalopteryx_didiformis,Megalapteryx_benhami,Megalapteryx_didinus,Pachyornis_australis,Pachyornis_elephantopus,Pachyornis_mappini,Euryapteryx_curtus,Euryapteryx_geranoides,Emeus_crassus,Dinornis_giganteus,Dinornis_novaezealandiae"
        third_subs = "Avisaurus_archibaldi,Avisaurus_gloriae,Cathayornis,Concornis_lacustris,Enantiornis_leali,Eoalulavis,Gobipteryx_minuta,Iberomesornis,Lectavis_bretincola,Neuquenornis_volans,Noguerornis,Sinornis_santensis,Soroavisaurus_australis,Two_medicine_form,Yungavolucris_brevipedalis"
        
        old_taxa, new_taxa = subs_from_csv('data/input/sub_files/subs.csv')
        self.assert_(old_taxa[0] == "MRPoutgroup")
        self.assert_(new_taxa[0] == None)
        self.assert_(new_taxa[1] == second_sub);
        self.assert_(old_taxa[1] == "Dinornithidae")
        self.assert_(old_taxa[2] == "Enantiornithes")
        self.assert_(new_taxa[2] == third_subs)



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


    def test_delete_taxa_root(self):
        tree_1 = "((Artemia_salina),((Kempina_mikado,Lysiosquillina_maculata,Squilla_empusa),Anchistioides_antiguensis,Atyoida_bisulcata));"
        output = _delete_taxon("Artemia_salina",tree_1)
        expected_tree = "((Kempina_mikado,Lysiosquillina_maculata,Squilla_empusa),Anchistioides_antiguensis,Atyoida_bisulcata);"
        self.assert_(_trees_equal(output, expected_tree))


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

    def test_substitute_taxa_multiple_nonexistingtaxa(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A","B_b"], ["Fred","Bob,Grenville"], only_existing=True)
        taxa = get_all_taxa(XML2)
        contains_Fred = False
        contains_Bob = False
        contains_A = False
        contains_B = False
        contains_Grenville = False
        for t in taxa:
            if (t == 'Fred'):
                contains_Fred = True
            if (t == "A"):
                contains_A = True
            if (t == 'Bob'):
                contains_Bob = True
            if (t == "B_b"):
                contains_B = True
            if (t == "Grenville"):
                contains_Grenville = True

        self.assert_(not contains_Fred)
        self.assert_(contains_A) # should not be deleted
        self.assert_(not contains_Bob)
        self.assert_(contains_B) # should not be deleted
        self.assert_(not contains_Grenville)

        # now need to check the XML for the taxon block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//taxon")
        taxa = find(xml_root)
        contains_Fred = False
        contains_Bob = False
        contains_A = False
        contains_B = False
        contains_Grenville = False
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
            if (t == "Grenville"):
                contains_Grenville = True

        self.assert_(not contains_Fred)
        self.assert_(contains_A) # should not be deleted
        self.assert_(not contains_Bob)
        self.assert_(contains_B) # should not be deleted
        self.assert_(not contains_Grenville)


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

    def test_substitute_in_trees(self):
        trees = []
        trees.append("(A, B, (C, D), E, F, G);")
        trees.append("(A, B, (C, D), E, F, H);")
        trees.append("(A, B, (C, D), E, F, K);")
        trees.append("(A, B, (C, D), E, F, G, H, K, L);")

        new_trees = substitute_taxa_in_trees(trees,["G", "K"],["Boo", None])

        # we should end up with...
        expected_trees = []
        expected_trees.append("(A, B, (C, D), E, F, Boo);")
        expected_trees.append("(A, B, (C, D), E, F, H);")
        expected_trees.append("(A, B, (C, D), E, F);")
        expected_trees.append("(A, B, (C, D), E, F, Boo, H, L);")

        self.assertListEqual(expected_trees,new_trees)

    def test_substitute_in_trees_only_existing(self):
        trees = []
        trees.append("(A, B, (C, D), E, F, G);")
        trees.append("(A, B, (C, D), E, F, H);")
        trees.append("(A, B, (C, D), E, F, K);")
        trees.append("(A, B, (C, D), E, F, G, H, K, L);")

        new_trees = substitute_taxa_in_trees(trees,["G", "K"],["Boo", None],only_existing=True)

        # we should end up with...
        expected_trees = []
        expected_trees.append("(A, B, (C, D), E, F, G);")
        expected_trees.append("(A, B, (C, D), E, F, H);")
        expected_trees.append("(A, B, (C, D), E, F);")
        expected_trees.append("(A, B, (C, D), E, F, G, H, L);")

        self.assertListEqual(expected_trees,new_trees)

    def test_substitute_taxa_only_existing_generic_match(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A","F_b"], ["Fred",'G'],only_existing=True,generic_match=True)
        taxa = get_all_taxa(XML2)
        contains_Fred = False
        contains_G = False
        contains_F_b = False
        for t in taxa:
            if (t == 'Fred'):
                contains_Fred = True
            if (t == "G"):
                contains_G = True
            if (t == "F_b"):
                contains_F = True

        self.assert_(not contains_Fred) # No Fred
        self.assert_(not contains_F_b) # we should not have F_b in a tree
        self.assert_(contains_G) # we should have G in a tree
        
        # check the trees
        trees = obtain_trees(XML2)
        expected_tree = "((A,B),(G,G_g));"
        self.assert_(_trees_equal(expected_tree,trees['Hill_2011_1']))

    def test_delete_percent_taxa(self):
        tree = "(A%3, B, (C, D), E, F, G, (A%1, A%2));"
        new_tree = _sub_taxa_in_tree(tree,"A")
        expected_tree = "(B, (C, D), E, F, G);"
        self.assert_(_trees_equal(expected_tree,new_tree))

    def test_delete_and_collapse(self):
        tree = "(A%3, B, (C, D), E, F, G, (A%1, A%2));"
        new_tree = _sub_taxa_in_tree(tree,"B")
        expected_tree = "(A%1, (C, D), E, F, G, A%2);"
        self.assert_(_trees_equal(expected_tree,new_tree))


    def test_collapse_permute_tree(self):
        tree = "((Parapurcellia_silvicola, ((Austropurcellia_scoparia, Austropurcellia_forsteri), ((Pettalus_sp.%1, Pettalus_sp.%2), ((Purcellia_illustrans, Chileogovea_sp.), ((Neopurcellia_salmoni, Karripurcellia_harveyi), ((Aoraki_inerma, Aoraki_denticulata), (Rakaia_antipodiana, (Rakaia_stewartiensis, Rakaia_florensis)))))))), (((Stylocellus_lydekkeri, (Stylocellus_sp.%1, Stylocellus_sp.%2)), ((Stylocellus_sp.%3, Stylocellus_sp.%4), (Fangensis_insulanus, (Fangensis_spelaeus, Fangensis_cavernarum)))), (((Paramiopsalis_ramulosus, (Cyphophthalmus_sp., (Cyphophthalmus_gjorgjevici, Cyphophthalmus_duricorius))), ((Siro_valleorum, Siro_rubens), (Siro_acaroides, (Siro_kamiakensis, Siro_exilis)))), (Suzukielus_sauteri, (Parasiro_coiffaiti, ((Troglosiro_longifossa, Troglosiro_aelleni), (Metasiro_americanus, ((Huitaca_sp., (Neogovea_sp., Metagovea_sp.)), (Paragovia_sp.%1, (Paragovia_sp.%2, (Paragovia_sp.%3, Paragovia_sironoides)))))))))));"
        expected_tree = "((Parapurcellia_silvicola, ((Austropurcellia_scoparia, Austropurcellia_forsteri), (Pettalus_sp.%1, ((Purcellia_illustrans, Chileogovea_sp.), ((Neopurcellia_salmoni, Karripurcellia_harveyi), ((Aoraki_inerma, Aoraki_denticulata), (Rakaia_antipodiana, (Rakaia_stewartiensis, Rakaia_florensis)))))))), (((Stylocellus_lydekkeri, Stylocellus_sp.%1), (Stylocellus_sp.%3, (Fangensis_insulanus, (Fangensis_spelaeus, Fangensis_cavernarum)))), (((Paramiopsalis_ramulosus, (Cyphophthalmus_sp., (Cyphophthalmus_gjorgjevici, Cyphophthalmus_duricorius))), ((Siro_valleorum, Siro_rubens), (Siro_acaroides, (Siro_kamiakensis, Siro_exilis)))), (Suzukielus_sauteri, (Parasiro_coiffaiti, ((Troglosiro_longifossa, Troglosiro_aelleni), (Metasiro_americanus, ((Huitaca_sp., (Neogovea_sp., Metagovea_sp.)), (Paragovia_sp.%1, (Paragovia_sp.%2, (Paragovia_sp.%3, Paragovia_sironoides)))))))))));"
        new_tree = _collapse_nodes(tree);
        self.assert_(_trees_equal(expected_tree,new_tree))        



    def test_replace_poly_taxa(self):
        tree = "(A_a%1, A_b%1, (A_a%2, A_b%2, A_c, A_d));"
        new_tree = _sub_taxa_in_tree(tree,"A_a", "A_f")
        expected_tree = "(A_f%1, A_b%1, (A_f%2, A_b%2, A_c, A_d));"
        self.assert_(_trees_equal(expected_tree,new_tree))


    def old_stk_replace_taxa_tests(self):
        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);";
        tree1 = "((((replaced_taxon,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"
        tree2 = "((((Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"
        tree3 = "((((taxon_1,taxon_2,taxon_3,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"

        polytomy = "taxon_1,taxon_2,taxon_3"
        polytomy2 = "Skua_blah,Parasiticus_oops"
        polytomy3 = "Catharacta_chilensis,replaced_taxon"

        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta_maccormicki','replaced_taxon')
        self.assert_(_trees_equal(new_tree,tree1))
        
        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta_maccormicki')
        self.assert_(_trees_equal(new_tree,tree2), "Correctly deleted taxon")

        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta_maccormicki',polytomy)
        self.assert_(_trees_equal(new_tree,tree3),"Correctly replaced with polytomy");

        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta maccormicki')
        self.assert_(_trees_equal(new_tree, tree2), "Correctly deleted taxon with space in name");

        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta_Maccormicki');
        self.assert_((not _trees_equal(new_tree, tree2)), "Didn't delete taxon with incorrect case");
        self.assert_(_trees_equal(new_tree, original_trees), "Didn't delete taxon with incorrect case");

        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta maccormicki','replaced_taxon');
        self.assert_(_trees_equal(new_tree, tree1), "Correctly replaced taxon with spaces in name");

        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta_Maccormicki',polytomy);
        self.assert_((not _trees_equal(new_tree, tree3)), "Didn't replace taxon with incorrect case");
        self.assert_(_trees_equal(new_tree, original_trees), "Didn't replace taxon with incorrect case");

        # check for partial replacement which we don't want
        new_tree = _sub_taxa_in_tree(original_trees,'skua',polytomy2)
        self.assert_(_trees_equal(new_tree, original_trees), "Correctly skipped partial match")

        # checking for adding duplicate taxa
        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta_maccormicki',polytomy3)
        self.assert_(_trees_equal(new_tree, tree1), "Correctly substituted but no duplicates with polytomy");

        new_tree = _sub_taxa_in_tree(original_trees,"Catharacta_maccormicki",'Catharacta_chilensis')
        self.assert_(_trees_equal(new_tree, tree2), "Correctly substituted but no duplicates with single")


    def test_sub_quoted_taxa(self):

        quote_taxa_tree = "(taxa_1, 'taxa_n=taxa_2', taxa_3, taxa_4);";
        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);";
        polytomy4 = "taxon_1,taxon_1,taxon_2,taxon_3"
        tree3 = "(((((taxon_1,taxon_2,taxon_3),Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"
        
        # checking for correct subbing of quoted taxa
        new_tree = _sub_taxa_in_tree(quote_taxa_tree,"'taxa_n=taxa_2'",'taxa_2')
        self.assert_(_trees_equal(new_tree,"(taxa_1,taxa_2,taxa_3,taxa_4);"),"Correctly substituted quoted taxa") 

        # quoted with + in it
        new_tree = _sub_taxa_in_tree("(taxa_1, 'taxa_n+taxa_2', taxa_3, taxa_4);","'taxa_n+taxa_2'",'taxa_2');
        self.assert_(_trees_equal(new_tree,"(taxa_1,taxa_2,taxa_3,taxa_4);"),"Correctly substituted quoted taxa") 

        # don't sub partial match of quoted taxa
        new_tree = _sub_taxa_in_tree(quote_taxa_tree,"taxa_2",'taxa_8');
        answer = "(taxa_1,'taxa_n=taxa_2',taxa_3,taxa_4);"
        self.assert_(_trees_equal(new_tree, answer), "Didn't substitute part of quoted taxa")

        # don't sub in repeated taxa
        new_tree = _sub_taxa_in_tree(original_trees,'Catharacta_maccormicki',polytomy4)
        self.assert_(_trees_equal(new_tree, tree3), "Didn't add repeated names");

        # checking removal of quoted taxa
        new_tree = _sub_taxa_in_tree("(taxa_1, 'taxa_n+taxa_2', taxa_3, taxa_4);","'taxa_n+taxa_2'");
        self.assert_(_trees_equal(new_tree, "(taxa_1,taxa_3,taxa_4);"), "Dealt with quoted taxa");

        new_tree = _sub_taxa_in_tree("(taxa_1, 'taxa_n+taxa_2', 'taxa_3=taxa5', taxa_4);","'taxa_3=taxa5'");
        self.assert_(_trees_equal(new_tree, "(taxa_1,'taxa_n+taxa_2',taxa_4);"), "Dealt with double quoted tacxa");

        polytomy5 = "taxon_n,'taxon_n+taxon_2',taxon_2,taxon_3"
        tree_in = "(taxa_n, 'taxa_n+taxa_2', 'taxa_3=taxa5', taxa_4);"
        new_tree = _sub_taxa_in_tree(tree_in,"taxa_4", polytomy5)
        answer = "(taxa_n,'taxa_n+taxa_2','taxa_3=taxa5',(taxon_n,'taxon_n+taxon_2',taxon_2,taxon_3));"
        self.assert_(_trees_equal(new_tree, answer), "Dealt with double quoted taxa");


    def test_sub_bug_fixes(self):
        tree4 = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds),('Recurvirostridae=Charadriidae',Protopteryx_fengningensis))));";
        tree4_result = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds%1),(Modern_birds%2,Protopteryx_fengningensis))));"
        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"

        # This is a different result to the old STK, but is actualy correct - you're replacing
        # in a non-monophyletic group.
        new_tree = _sub_taxa_in_tree(tree4,"'Recurvirostridae=Charadriidae'",'Modern_birds');
        self.assert_(_trees_equal(new_tree, tree4_result), "Correct replacement of taxa that already exists");

        ## New bug: replacing with the same taxa 
        new_tree = _sub_taxa_in_tree(original_trees,"Catharacta_maccormicki",'Catharacta_maccormicki');
        self.assert_(_trees_equal(new_tree,original_trees), "Correct ignored taxa replaced with itself");
    
    
    def test_collapse_tree(self):

        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus);"

        ## Trying out new function to collapse clades when going from specific to generic
        tree1 = "(((Catharacta%1,(Catharacta%2,Stercorarius%1)),Stercorarius%2),Larus);"
        new_tree = _sub_taxa_in_tree(original_trees,"Catharacta_maccormicki",'Catharacta');
        new_tree = _sub_taxa_in_tree(new_tree, "Catharacta_chilensis",'Catharacta');
        new_tree = _sub_taxa_in_tree(new_tree, "Catharacta_antarctica",'Catharacta');
        new_tree = _sub_taxa_in_tree(new_tree, "Catharacta_skua",'Catharacta');
        new_tree = _sub_taxa_in_tree(new_tree, "Stercorarius_pomarinus",'Stercorarius');
        new_tree = _sub_taxa_in_tree(new_tree, "Stercorarius_parasiticus",'Stercorarius');
        new_tree = _sub_taxa_in_tree(new_tree, "Stercorarius_longicaudus",'Stercorarius');
        new_tree = _sub_taxa_in_tree(new_tree, "Larus_argentatus",'Larus');
        self.assert_(_trees_equal(new_tree, tree1), "Correctly collapse tree")


        hard_tree = "(Daphnia,Drosophila,Euphausia,Exopheticus,Petrolisthes,Pinnotherelia,Tritodynamia,(Ligia,(Armadillidium,Eocarcinus,Metapenaeus,((((((Himalayapotamon,Jasus,Polycheles,(Enoplometopus,((Pemphix,(((Thaumastocheles,(Acanthacaris,Enoplometopus1,Eryma,Homarus,Metanephrops,Nephropides,Nephrops,Nephropsis,Thaumastocheles1,Thaumastochelopsis,((Euastacus,(Astacoides,Geocharax,(Paranephrops,(Astacopsis,(Ombrastacoides,(Gramastacus,Cherax))))),(Parastacus,(Samastacus,Virilastacus))))))))))))))))))));";
        answer = "(Daphnia,Drosophila,Euphausia,Exopheticus,Petrolisthes,Pinnotherelia,Tritodynamia,(Ligia,(Armadillidium,Eocarcinus,Metapenaeus,(Himalayapotamon,Jasus,Polycheles,(Enoplometopus,(Pemphix,(Thaumastocheles,(Acanthacaris,Enoplometopus1,Eryma,Homarus,Metanephrops,Nephropides,Nephrops,Nephropsis,Thaumastocheles1,Thaumastochelopsis,(Euastacus,(Parastacidae%1,Geocharax,(Parastacidae%2,(Astacopsis,Parastacidae%3))),Parastacidae%4)))))))));";
        new_tree = _sub_taxa_in_tree(hard_tree,"Astacoides",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Astacoides1",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Cherax",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Cherax1",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Gramastacus",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Ombrastacoides",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Paranephrops",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Parastacus",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Samastacus",'Parastacidae');
        new_tree = _sub_taxa_in_tree(new_tree,"Virilastacus",'Parastacidae');
        self.assert_(_trees_equal(new_tree, answer), "Correctly collapse tree")

    def test_collapse_nodes(self):
        in_tree = "(taxa_a, (taxa_b, taxa_c), taxa_d, (taxa_e, taxa_h%3, (taxa_f, (taxa_g, taxa_h%1, taxa_h%2))));"
        answer = "(taxa_a, (taxa_b, taxa_c), taxa_d, (taxa_e, taxa_h%1, (taxa_f, (taxa_g, taxa_h%2))));"
        new_tree = _collapse_nodes(in_tree);
        self.assert_(_trees_equal(new_tree, answer), "Correctly collapse nodes")
        

    def test_specific_to_generic(self):
        """Checks the correct change of taxonomic level from specific to generic"""
        in_tree=import_tree("data/input/large_tree_snippet.tre")
        subs_old_taxa = ["Phylloscopus_trochilus", "Phylloscopus_brehmi", "Phylloscopus_canariensis", "Phylloscopus_collybita",
                         "Phylloscopus_sindianus", "Phylloscopus_fuligiventer", "Phylloscopus_fuscatus", "Phylloscopus_orientalis",
                         "Phylloscopus_bonelli", "Phylloscopus_sibilatrix", "Phylloscopus_yunnanensis", "Phylloscopus_subviridis", 
                         "Phylloscopus_chloronotus", "Phylloscopus_proregulus", "Phylloscopus_humei", "Phylloscopus_inornatus", 
                         "Phylloscopus_maculipennis", "Phylloscopus_pulcher", "Phylloscopus_trivirgatus", "Phylloscopus_sarasinorum", 
                         "Phylloscopus_amoenus", "Phylloscopus_poliocephalus", "Phylloscopus_presbytes","Phylloscopus_borealis",
                         "Phylloscopus_magnirostris","Phylloscopus_borealoides","Phylloscopus_tenellipes","Phylloscopus_emeiensis", 
                         "Phylloscopus_nitidus","Phylloscopus_plumbeitarsus","Phylloscopus_trochiloides","Phylloscopus_cebuensis", 
                         "Phylloscopus_coronatus","Phylloscopus_ijimae","Phylloscopus_ruficapillus","Phylloscopus_umbrovirens"]
        subs_new_taxa = ["Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus",
                         "Phylloscopus", "Phylloscopus", "Phylloscopus", "Phylloscopus"]
        new_tree = _sub_taxa_in_tree(in_tree,subs_old_taxa,subs_new_taxa);
        # Fixes a random bug where Phylloscopus0 would appear, followed by Phylloscopus00 in subsequent subs
        self.assert_(new_tree.find("Phylloscopus0") == -1)


    def test_not_replace_partial(self):
        quote_taxa_tree = "(taxa_1, taxa_n_taxa_2, taxa_3, taxa_4);";
        new_tree = _sub_taxa_in_tree(quote_taxa_tree,"taxa_2",'taxa_8');
        answer = "(taxa_1, taxa_n_taxa_2, taxa_3, taxa_4);"
        self.assert_(_trees_equal(new_tree, answer), "Didn't substitute part of taxa")

    def test_replace_with_quotes(self):
        quote_taxa_tree = "(taxa_1, taxa_2, 'taxa_(blah)_foo', taxa_4);"
        new_tree = _sub_taxa_in_tree(quote_taxa_tree,"taxa_2",'taxa_8');
        answer = "(taxa_1, taxa_8, 'taxa_(blah)_foo', taxa_4);"
        self.assert_(_trees_equal(new_tree, answer), "Did a sub with quoted taxa")

    def test_replace_with_quoted(self):
        quote_taxa_tree = "(taxa_1, taxa_2, 'taxa_(blah)_foo', taxa_4);"
        new_tree = _sub_taxa_in_tree(quote_taxa_tree,"taxa_(blah)_foo",'taxa_8');
        answer = "(taxa_1, taxa_2, taxa_8, taxa_4);"
        self.assert_(_trees_equal(new_tree, answer), "Did a sub on quoted taxa")
    
    def test_replace_with_quoted(self):
        quote_taxa_tree = "(taxa_1, taxa_2, 'taxa_(blah)_foo', taxa_4);"
        new_tree = _sub_taxa_in_tree(quote_taxa_tree,"taxa_(blah)_foo");
        answer = "(taxa_1, taxa_2, taxa_4);"
        self.assert_(_trees_equal(new_tree, answer), "Deleted quoted taxa")

    def test_check_subs_adding(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        try:
            check_subs(XML,["Fred","Bob"])
        except AddingTaxaWarning as detail:
            self.assert_(True,"Correctly identified incoming taxa")
            self.assertRegexpMatches(detail.msg,"Fred")
            return
        self.assert_(False)

    def test_check_subs_not_adding(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        try:
            check_subs(XML,["A","B_b"])
        except AddingTaxaWarning:
            self.assert_(False)
            return
        self.assert_(True,"Correctly let the subs go")


    def test_tree_contains_odd(self):
        tree = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus),
        (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))),
        (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi,
        ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes,
        (((Sphendononema_rugosa, 'Sphendononema guildingii%1', 'Sphendononema guildingii%2'),
        ('"Scutigera" nossibei', ('Scutigera coleoptrata%1', 'Scutigera coleoptrata%2', 'Scutigera coleoptrata%3'), (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola,
        (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))),
        ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx,
            Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata,
            Allothereua_bidenticulata, Allothereua_linderi, ('Allothereua maculata%1',
                Allothereua_maculata%2), (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2,
                    Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        self.assert_(_tree_contains('"Scutigera"_nossibei',tree))


    def test_subs_awkward(self):
        """Try subs with ( and " in them"""
        XML = etree.tostring(etree.parse('data/input/awkward_subs.phyml',parser),pretty_print=True)
        old_taxa, new_taxa = parse_subs_file('data/input/sub_files/awkward_subs.dat');
        self.assert_('"Scutigera"_nossibei' in old_taxa)
        self.assert_('Cryptops_(Trigonocryptops)_pictus' in old_taxa)
        self.assert_('Anopsobius_sp._nov._NSW' in old_taxa)
        XML2 = substitute_taxa(XML, old_taxa, new_taxa)
        taxa = get_all_taxa(XML2)
        self.assert_(not '"Scutigera"_nossibei' in taxa)
        self.assert_(not 'Cryptops_(Trigonocryptops)_pictus' in taxa)
        self.assert_(not 'Anopsobius_sp._nov._NSW' in taxa)
        self.assert_('Scutigera_nossibei' in taxa)
        self.assert_('Cryptops_pictus' in taxa)
        self.assert_('Anopsobius_wrighti' in taxa)


    def test_check_trees_with_quoted_subs(self):
        """Some datasets have quoted taxa with subs
        """

        tree = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, 'Sphendononema guildingii%1', 'Sphendononema guildingii%2'),  ('"Scutigera" nossibei', ('Scutigera coleoptrata%1', 'Scutigera coleoptrata%2', 'Scutigera coleoptrata%3'), (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola,  (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx,Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, ('Allothereua maculata%1', Allothereua_maculata%2), (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        tree2 = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii%1, Sphendononema_guildingii%2), ('"Scutigera" nossibei', (Scutigera_coleoptrata%1, Scutigera_coleoptrata%2, Scutigera_coleoptrata%3), (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, (Allothereua_maculata%1, Allothereua_maculata%2), (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        tree3 = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii), ('"Scutigera" nossibei', Scutigera_coleoptrata, (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, Allothereua_maculata, (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        collapsed_tree =  _correctly_quote_taxa(tree)
        self.assert_(_trees_equal(tree2, collapsed_tree))
        collapsed_tree = _collapse_nodes(collapsed_tree)
        collapsed_tree = _remove_single_poly_taxa(collapsed_tree) 
        self.assert_(_trees_equal(tree3, collapsed_tree))


    def test_remove_single_poly_taxa(self):
        """ Remove poly taxa where there's only one anyway """

        tree = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa%1, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii%1), ('"Scutigera" nossibei', Scutigerina_malagassa%2, Scutigera_coleoptrata%1, (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, Allothereua_maculata%1, (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        tree2 = """(Proteroiulus_fuscus, (((Scolopendra_viridis, Craterostigmus_tasmanianus), (Lithobius_variegatus_rubriceps, (Anopsobius_neozelanicus, Paralamyctes_validus))), (Madagassophora_hova, Scutigerina_malagassa%1, Scutigerina_cf._weberi, Scutigerina_weberi, ((Dendrothereua_homa, Dendrothereua_nubila), (Parascutigera_nubila, (Ballonema_gracilipes, (((Sphendononema_rugosa, Sphendononema_guildingii), ('"Scutigera" nossibei', Scutigerina_malagassa%2, Scutigera_coleoptrata, (Thereuopodina_sp._nov, Tachythereua_sp., (Pilbarascutigera_incola, (Seychellonema_gerlachi, (Thereuopoda_longicornis, Thereuopoda_clunifera)))))), ((Thereuonema_turkestana, Thereuonema_tuberculata), (Parascutigera_cf._sphinx, Parascutigera_latericia, Parascutigera_festiva, Allothereua_serrulata, Allothereua_bidenticulata, Allothereua_linderi, Allothereua_maculata, (Parascutigera_sp._QLD_3, Parascutigera_sp._QLD_2, Parascutigera_sp._QLD_1, Parascutigera_guttata))))))))));"""
        collapsed_tree = _remove_single_poly_taxa(tree)
        self.assert_(_trees_equal(tree2, collapsed_tree))


    def test_subspecies_sub(self):
        """ Checking the sub of sub species """

        tree1 = """(taxa_1, 'taxa 2', 'taxa (blah?) foo', bob);"""
        tree2 = """(taxa_1, taxa_2, taxa_8, bob);"""
        new_tree = _sub_taxa_in_tree(tree1,"taxa_(blah?)_foo",'taxa_8');
        self.assert_(_trees_equal(new_tree, tree2), "Did a sub on quoted odd taxon")
        tree1 = """(taxa_1, 'taxa 2', 'taxa blah?', bob);"""
        new_tree = _sub_taxa_in_tree(tree1,"taxa_blah?",'taxa_8');
        self.assert_(_trees_equal(new_tree, tree2), "Did a sub on quoted odd taxon")
        tree1 = """(taxa_1, 'taxa 2', 'taxa blah,sp2 nov', bob);"""
        new_tree = _sub_taxa_in_tree(tree1,"taxa_blah,sp2_nov",'taxa_8');
        self.assert_(_trees_equal(new_tree, tree2), "Did a sub on quoted odd taxon")

    def test_quoted_subin(self):
        """ sub in taxa that need quoting """
        tree1 = """(Thereuonema_turkestana, Thereuopodina, 'Thereuopodina, sp. nov.');"""
        answer1 = """(Thereuonema_turkestana, Thereuopodina_nov._sp., Thereuopodina_n._sp., Thereuopodina_queenslandica, Thereuopodina_sp._nov, 'Thereuopodina, sp. nov.')"""
        tree2 = """(Thereuonema_turkestana, Thereuopodina, Bob, Fred);"""
        answer2 = """(Thereuonema_turkestana, Thereuopodina_nov._sp., 'Thereuopodina,_sp._nov.', Thereuopodina_n._sp., Thereuopodina_queenslandica, Thereuopodina_sp._nov, Bob, Fred);"""
        sub_in = "'Thereuopodina,_sp._nov.','Thereuopodina_n._sp.','Thereuopodina_nov._sp.',Thereuopodina_queenslandica,'Thereuopodina_sp._nov'"
        new_tree = _sub_taxa_in_tree(tree1,"Thereuopodina",sub_in,skip_existing=True);
        self.assert_(answer1, new_tree)
        new_tree = _sub_taxa_in_tree(tree2,"Thereuopodina",sub_in,skip_existing=True);
        self.assert_(answer2, new_tree)

        


if __name__ == '__main__':
    unittest.main()
 

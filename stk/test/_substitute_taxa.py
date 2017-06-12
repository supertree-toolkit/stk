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
from stk.supertree_toolkit import generate_species_level_data
from lxml import etree
from util import *
from stk.stk_exceptions import *
from collections import defaultdict
import tempfile
parser = etree.XMLParser(remove_blank_text=True)
import re


class TestSubs(unittest.TestCase):





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
            if name == "Grenville":
                contains_Grenville = True

        self.assert_(not contains_Fred)
        self.assert_(contains_A) # should not be deleted
        self.assert_(not contains_Bob)
        self.assert_(contains_B) # should not be deleted
        self.assert_(not contains_Grenville)

    def test_substitute_taxa_multiple_taxablock(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A"], ["Bob,Grenville"])
        taxa = get_all_taxa(XML2)
        contains_Bob = False
        contains_A = False
        contains_Grenville = False
        for t in taxa:
            if (t == "A"):
                contains_A = True
            if (t == 'Bob'):
                contains_Bob = True
            if (t == "Grenville"):
                contains_Grenville = True

        self.assert_(not contains_A)
        self.assert_(contains_Bob)
        self.assert_(contains_Grenville)

        # now need to check the XML for the taxon block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//taxon")
        taxa = find(xml_root)
        contains_Bob = False
        contains_A = False
        contains_Grenville = False
        for t in taxa:
            name = t.attrib['name']
            if name == 'A':
                contains_A = True
            if name == 'Bob':
                contains_Bob = True
            if name == "Grenville":
                contains_Grenville = True

        self.assert_(not contains_A) # should not be deleted
        self.assert_(contains_Bob)
        self.assert_(contains_Grenville)

    def test_substitute_taxa_outgroup(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A"], ["Fred, Bob"])
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

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree
        self.assert_(contains_Bob)

        # now need to check the XML for the outgroup block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//outgroup")
        taxa = find(xml_root)
        contains_Fred = False
        contains_Bob = False
        contains_A = False
        for t in taxa:
            name = t.xpath("string_value")[0].text
            if 'Fred' in name:
                contains_Fred = True
            if 'A' in name:
                contains_A = True
            if 'Bob' in name:
                contains_Bob = True

        self.assert_(contains_Fred)
        self.assert_(not contains_A) # we should not have A in a tree
        self.assert_(contains_Bob)

    def test_delete_taxa_outgroup(self):
        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A"], None)
        taxa = get_all_taxa(XML2)
        contains_A = False
        for t in taxa:
            if (t == "A"):
                contains_A = True

        self.assert_(not contains_A) # we should not have A in a tree

        # now need to check the XML for the outgroup block has been altered
        xml_root = etree.fromstring(XML2)
        find = etree.XPath("//outgroup")
        taxa = find(xml_root)
        # we should have *no* outgroups now as A was the only one!
        self.assert_(len(taxa) == 0)

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

   
    def test_auto_subs_taxonomy(self):
        """test the automatic subs function with a simple test"""
        XML = etree.tostring(etree.parse('data/input/auto_sub.phyml',parser),pretty_print=True)
        taxonomy = {'Ardea goliath': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'superphylum': 'Ecdysozoa', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Protostomia', 'genus': 'Ardea', 'order': 'Pelecaniformes', 'species': 'Ardea goliath'}, 
                    'Pelecaniformes': {'kingdom': 'Animalia', 'phylum': 'Chordata', 'order': 'Pelecaniformes', 'class': 'Aves', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013'}, 'Gallus': {'kingdom': 'Animalia', 'family': 'Phasianidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'superphylum': 'Lophozoa', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Protostomia', 'genus': 'Gallus', 'order': 'Galliformes'}, 
                    'Thalassarche melanophris': {'kingdom': 'Animalia', 'family': 'Diomedeidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'infraphylum': 'Gnathostomata', 'superclass': 'Tetrapoda', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'genus': 'Thalassarche', 'order': 'Procellariiformes', 'species': 'Thalassarche melanophris'}, 
                    'Platalea leucorodia': {'kingdom': 'Animalia', 'subfamily': 'Plataleinae', 'family': 'Threskiornithidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'infraphylum': 'Gnathostomata', 'superclass': 'Tetrapoda', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'genus': 'Platalea', 'order': 'Pelecaniformes', 'species': 'Platalea leucorodia'}, 
                    'Gallus lafayetii': {'kingdom': 'Animalia', 'family': 'Phasianidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'superphylum': 'Lophozoa', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Protostomia', 'genus': 'Gallus', 'order': 'Galliformes', 'species': 'Gallus lafayetii'}, 
                    'Ardea humbloti': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'superphylum': 'Ecdysozoa', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Protostomia', 'genus': 'Ardea', 'order': 'Pelecaniformes', 'species': 'Ardea humbloti'}, 
                    'Gallus varius': {'kingdom': 'Animalia', 'family': 'Phasianidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'phylum': 'Chordata', 'superphylum': 'Lophozoa', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Protostomia', 'genus': 'Gallus', 'order': 'Galliformes', 'species': 'Gallus varius'}}
        XML = generate_species_level_data(XML, taxonomy)
        expected_XML = etree.tostring(etree.parse('data/output/one_click_subs_output.phyml',parser),pretty_print=True)
        trees = obtain_trees(XML) 
        expected_trees = obtain_trees(expected_XML)
        for t in trees:
            self.assert_(_trees_equal(trees[t], expected_trees[t]))

    def test_parrot_edge_case(self):
        """Random edge case where the tree dissappeared..."""
        trees = ["(((((((Agapornis_lilianae, Agapornis_nigrigenis), Agapornis_personata, Agapornis_fischeri), Agapornis_roseicollis), (Agapornis_pullaria, Agapornis_taranta)), Agapornis_cana), Loriculus_galgulus), Geopsittacus_occidentalis);"]
        answer = "(((((((Agapornis_lilianae, Agapornis_nigrigenis), Agapornis_personatus, Agapornis_fischeri), Agapornis_roseicollis), (Agapornis_pullarius, Agapornis_taranta)), Agapornis_canus), Loriculus_galgulus), Pezoporus_occidentalis);"
        new_taxa = ["Pezoporus occidentalis","Agapornis canus","Agapornis_pullaria","Apapornis_roseicollis","Agapornis_personata"]
        old_taxa = ["Geopsittacus_occidentalis","Agapornis_cana","Agapornis pullarius","Agapornis_roseicollis","Agapornis_personatus"]
        new_trees = substitute_taxa_in_trees(trees,old_taxa,new_taxa=new_taxa)
        self.assert_(answer, new_trees[0])

if __name__ == '__main__':
    unittest.main()
 

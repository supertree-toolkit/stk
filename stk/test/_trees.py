import unittest
import math
import sys
sys.path.append("../")
from supertree_toolkit import import_tree, obtain_trees 
import os
from lxml import etree
from util import *

# our test dataset
treeview_file = "data/input/treeview.tre"
standard_tre = "data/input/test_tree.tre"
expected_tree = "(Lauridromia_dehaani:1.00000,Paromola_japonica:1.00000,((Blepharipoda_occidentalis:1.00000,(Emerita_emeritus:1.00000,Lepidopa_californica:1.00000)0.00000:0.00000)0.00000:0.00000,((Pylocheles_macrops:1.00000,(Bythiopagurus_macroculus:1.00000,((Discorsopagurus_schmitti:1.00000,(Oedignathus_inermis:1.00000,Lithodes_santolla:1.00000)0.00000:0.00000)0.00000:0.00000,(Pagurus_bernhardus:1.00000,Pagurus_longicarpus:1.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000,((((Trizocheles_spinosus:1.00000,(Sympagurus_dimorphus:1.00000,Parapagurus_latimanus:1.00000)0.00000:0.00000)0.00000:0.00000,(Lomis_hirta:1.00000,(Aegla_uruguyana:1.00000,Aegla_violacea:1.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000,(Pseudomunida_fragilis:1.00000,(Kiwa_hirsuta:1.00000,(Eumunida_sternomaculata:1.00000,(Chirostylus_novaecaledoniae:1.00000,(Gastroptychus_novaezelandiae:1.00000,(Uroptychus_nitidus:1.00000,Uroptychus_scambus:1.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000,((Coenobita_compressus:1.00000,(Clibanarius_albidigitatus:1.00000,(Isocheles_pilosus:1.00000,Calcinus_obscurus:1.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000,((Leiogalathea_laevirostris:1.00000,(Munidopsis_bairdii:1.00000,(Galacantha_rostrata:1.00000,Shinkaia_crosnieri:1.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000,((Sadayoshia_sp.:1.00000,((Agononida_longipes:1.00000,Agononida_procera:1.00000)0.00000:0.00000,((Munida_gregaria:1.00000,Cervimunida_johni:1.00000)0.00000:0.00000,(Munida_quadrispina:1.00000,Pleuroncodes_monodon:1.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000,((Galathea_sp.:1.00000,Allogalathea_elegans:1.00000)0.00000:0.00000,(Porcellanella_triloba:1.00000,(Pachycheles_rudis:1.00000,Petrolisthes_armatus:1.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000)0.00000:0.00000;"
single_source_input = "data/input/single_source.phyml";
parser = etree.XMLParser(remove_blank_text=True)

class TestImportTree(unittest.TestCase):

    def test_import_treeview(self):
        tree = import_tree(treeview_file)
        self.assert_(expected_tree+"\n" == tree)

    #def test_import_standard_tre(self):
    #    tree = import_tree(standard_tre)
    #    print tree
    #    self.assert_(expected_tree+"\n" == tree)

    def test_get_all_trees(self):
        XML = etree.tostring(etree.parse(single_source_input,parser),pretty_print=True)
        tree = obtain_trees(XML)
        # Tree key is source_name_tree_no, so we should have
        # Hill_2011_1
        self.assert_(tree['Hill_2011_1'] == expected_tree)


if __name__ == '__main__':
    unittest.main()
 

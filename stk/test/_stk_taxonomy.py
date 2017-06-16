#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2013, Jon Hill, Katie Davis
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
import sys
sys.path.insert(0,"../../")
sys.path.insert(0,"../")
import os
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
from stk_taxonomy import get_taxonomy_for_taxon_eol, get_taxonomy_for_taxon_itis, get_taxonomy_for_taxon_worms, get_taxonomy_for_taxon_pbdb
from stk_taxonomy import create_taxonomy_from_taxa, create_extended_taxonomy, load_taxonomy, tree_from_taxonomy, taxonomic_checker_list
from stk_taxonomy import get_taxonomy_eol, get_taxonomy_worms, get_taxonomy_itis
from stk.stk_internals import internet_on
from stk.stk_trees import trees_equal
import stk.stk_phyml as stk_phyml
from lxml import etree
from util import *
parser = etree.XMLParser(remove_blank_text=True)

class TestSTKTaxonomy(unittest.TestCase):


    def test_create_taxonomy(self):
        XML = etree.tostring(etree.parse('data/input/create_taxonomy.phyml',parser),pretty_print=True)
        expected = {'Jeletzkytes criptonodosus': {'superfamily': 'Scaphitoidea', 'family': 'Scaphitidae', 'subkingdom': 'Metazoa', 'subclass': 'Ammonoidea', 'species': 'Jeletzkytes criptonodosus', 'phylum': 'Mollusca', 'suborder': 'Ancyloceratina', 'provider': 'paleobiology database', 'genus': 'Jeletzkytes', 'class': 'Cephalopoda'}, 'Thalassarche melanophris': {'kingdom': 'Animalia', 'family': 'Diomedeidae', 'class': 'Aves', 'phylum': 'Chordata', 'provider': 'species 2000 & itis catalogue of life: april 2013', 'species': 'Thalassarche melanophris', 'genus': 'Thalassarche', 'order': 'Procellariiformes'}, 'Egretta tricolor': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'class': 'Aves', 'phylum': 'Chordata', 'provider': 'species 2000 & itis catalogue of life: april 2013', 'species': 'Egretta tricolor', 'genus': 'Egretta', 'order': 'Pelecaniformes'}, 'Archaeopteryx lithographica': {'genus': 'Archaeopteryx', 'provider': 'paleobiology database'}}
        if (internet_on()):
            taxa = ['Archaeopteryx lithographica', 'Jeletzkytes criptonodosus', 'Thalassarche melanophris','Egretta tricolor'] 
            taxonomy = create_taxonomy_from_taxa(taxa,pref_db='eol',threadNumber=4)
            self.maxDiff = None
            self.assertDictEqual(taxonomy, expected)
        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the taxonomy_checker function"
        return



    def test_create_extended_taxonomy(self):
        XML = etree.tostring(etree.parse('data/input/create_taxonomy.phyml',parser),pretty_print=True)
        expected = {'Jeletzkytes criptonodosus': {'kingdom': 'Animalia', 'superfamily': 'Scaphitoidea', 'family': 'Scaphitidae', 'subkingdom': 'Metazoa', 'subclass': 'Ammonoidea', 'order': 'Ammonitida', 'phylum': 'Mollusca', 'suborder': 'Ancyloceratina', 'provider': 'paleobiology database', 'species': 'Jeletzkytes criptonodosus', 'genus': 'Jeletzkytes', 'class': 'Cephalopoda'}, 'Egretta tricolor': {'kingdom': 'Animalia', 'genus': 'Egretta', 'family': 'Ardeidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'order': 'Pelecaniformes', 'phylum': 'Chordata', 'superclass': 'Tetrapoda', 'provider': 'species 2000 & itis catalogue of life: april 2013', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'subfamily': 'Ardeinae', 'species': 'Egretta tricolor'}, 'Archaeopteryx lithographica': {'kingdom': 'Animalia', 'phylum': 'Chordata', 'provider': 'paleobiology database', 'genus': 'Archaeopteryx', 'species': 'Archaeopteryx lithographica', 'class': 'Aves'}, 'Thalassarche melanophris': {'kingdom': 'Animalia', 'family': 'Diomedeidae', 'subkingdom': 'Bilateria', 'class': 'Aves', 'order': 'Procellariiformes', 'phylum': 'Chordata', 'superclass': 'Tetrapoda', 'provider': 'species 2000 & itis catalogue of life: april 2013', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'genus': 'Thalassarche', 'species': 'Thalassarche melanophris'}}
        if (internet_on()):
            taxa = ['Archaeopteryx lithographica', 'Jeletzkytes criptonodosus', 'Thalassarche melanophris','Egretta tricolor'] 
            taxonomy = create_taxonomy_from_taxa(taxa,pref_db='eol',threadNumber=4)
            taxonomy = create_extended_taxonomy(taxonomy,pref_db='eol',threadNumber=4)
            self.maxDiff = None
            self.assertDictEqual(taxonomy, expected)
        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the taxonomy_checker function"
        return
    
    def test_taxonomy_checker(self):
        expected = {'Thalassarche_melanophrys': (['Thalassarche_melanophris', 'Thalassarche_melanophrys', 'Diomedea_melanophris', 'Thalassarche_[melanophrys', 'Diomedea_melanophrys'], 'amber'), 'Egretta_tricolor': (['Egretta_tricolor'], 'green'), 'Gallus_gallus': (['Gallus_gallus'], 'green')}
        taxa_list = ['Thalassarche_melanophrys', 'Egretta_tricolor', 'Gallus_gallus']
        if (internet_on()):
            equivs = taxonomic_checker_list(taxa_list)
            self.maxDiff = None
            self.assertDictEqual(equivs, expected)
        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the taxonomy_checker function"
        return

    def test_taxonomy_checker2(self):
        XML = etree.tostring(etree.parse('data/input/check_taxonomy_fixes.phyml',parser),pretty_print=True)
        if (internet_on()):
            # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
            taxa_list = stk_phyml.get_all_taxa(XML)
            equivs = taxonomic_checker_list(taxa_list)
            self.maxDiff = None
            self.assert_(equivs['Agathamera_crassa'][0][0] == 'Agathemera_crassa')
            self.assert_(equivs['Celatoblatta_brunni'][0][0] == 'Maoriblatta_brunni')
            self.assert_(equivs['Blatta_lateralis'][1] == 'amber')
        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the taxonomy_checker function"
        return

    def test_taxonomy_checker_common_name(self):
        if (internet_on()):
            # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
            taxa_list = ['Cardueline_Finches']
            equivs = taxonomic_checker_list(taxa_list)
            self.maxDiff = None
            self.assert_(equivs['Cardueline_Finches'][0][0] == 'Carduelinae')
        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the taxonomy_checker function"
        return

    def test_taxonomy_checker_common_name2(self):
        if (internet_on()):
            # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
            taxa_list = ['Chaffinches']
            equivs = taxonomic_checker_list(taxa_list)
            self.maxDiff = None
            self.assert_(equivs['Chaffinches'][0][0] == 'Fringilla')
        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the taxonomy_checker function"
        return


    def test_load_taxonomy(self):
        csv_file = "data/input/create_taxonomy.csv"
        expected = {'Egretta_tricolor': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'class': 'Aves', 'subkingdom': 'Bilateria', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'subclass': 'Neoloricata', 'species': 'Egretta tricolor', 'phylum': 'Chordata', 'suborder': 'Ischnochitonina', 'superphylum': 'Lophozoa', 'infrakingdom': 'Protostomia', 'genus': 'Egretta', 'order': 'Pelecaniformes'}, 'Gallus_gallus': {'kingdom': 'Animalia', 'superorder': 'Galliformes', 'family': 'Phasianidae', 'subkingdom': 'Bilateria', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'species': 'Gallus gallus', 'phylum': 'Chordata', 'superphylum': 'Lophozoa', 'infrakingdom': 'Protostomia', 'genus': 'Gallus', 'class': 'Aves'}, 'Egretta_garzetta': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'class': 'Aves', 'subkingdom': 'Bilateria', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'subclass': 'Neoloricata', 'species': 'Egretta garzetta', 'phylum': 'Chordata', 'suborder': 'Ischnochitonina', 'superphylum': 'Lophozoa', 'infrakingdom': 'Protostomia', 'genus': 'Egretta', 'order': 'Pelecaniformes'}, 'Thalassarche_melanophris': {'kingdom': 'Animalia', 'family': 'Diomedeidae', 'subkingdom': 'Bilateria', 'species': 'Thalassarche melanophris', 'order': 'Procellariiformes', 'phylum': 'Chordata', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'genus': 'Thalassarche', 'class': 'Aves'}, 'Jeletzkytes_criptonodosus': {'kingdom': 'Metazoa', 'superfamily': 'Scaphitidae', 'family': 'Scaphitidae', 'subclass': 'Cephalopoda', 'species': 'Jeletzkytes criptonodosus', 'suborder': 'Ammonoidea', 'provider': 'PBDB', 'class': 'Mollusca'}, 'Archaeopteryx_lithographica': {'family': 'Archaeopterygidae', 'subkingdom': 'Metazoa', 'subclass': 'Tetrapodomorpha', 'species': 'Archaeopteryx lithographica', 'suborder': 'Coelurosauria', 'provider': 'Paleobiology Database', 'genus': 'Archaeopteryx', 'class': 'Aves'}}
        taxonomy = load_taxonomy(csv_file)
        self.maxDiff = None
        self.assertDictEqual(taxonomy, expected)


    def test_create_tree_taxonomy(self):
        csv_file = "data/input/create_taxonomy.csv"
        taxonomy = load_taxonomy(csv_file)
        expected_tree = "(((Egretta_tricolor, Egretta_garzetta), Archaeopteryx_lithographica, Gallus_gallus, Thalassarche_melanophris), Jeletzkytes_criptonodosus);"
        tree = tree_from_taxonomy('class', taxonomy)
        self.assert_(trees_equal(tree,expected_tree))


    def test_get_taxonomy_for_taxon_eol(self):

        if (internet_on()):
            # Let's check an easy one!
            taxon = "Gallus gallus"
            expected = {'kingdom': 'Animalia', 'family': 'Phasianidae', 'class': 'Aves', 'phylum': 'Chordata', 'provider': 'species 2000 & itis catalogue of life: april 2013', 'species': 'Gallus gallus', 'genus': 'Gallus', 'order': 'Galliformes'}
            taxonomy = get_taxonomy_for_taxon_eol(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a subspecies
            taxon = "Gallus gallus bankiva"
            taxonomy = get_taxonomy_for_taxon_eol(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a null value
            taxon = "No chance!"
            expected = {}
            taxonomy = get_taxonomy_for_taxon_eol(taxon)
            self.assertEqual(taxonomy, expected)

        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the get_taxonomy_for_taxon_eol function"
        return

    def test_get_taxonomy_for_taxon_itis(self):

        if (internet_on()):
            # Let's check an easy one!
            taxon = "Gallus gallus"
            expected = {'kingdom': 'Animalia', 'genus': 'Gallus', 'family': 'Phasianidae', 'subkingdom': 'Bilateria', 'order': 'Galliformes', 'phylum': 'Chordata', 'superclass': 'Tetrapoda', 'species': 'Gallus gallus', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'subfamily': 'Phasianinae', 'class': 'Aves', 'provider': 'ITIS'}
            taxonomy = get_taxonomy_for_taxon_itis(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a subspecies
            taxon = "Gallus gallus bankiva"
            taxonomy = get_taxonomy_for_taxon_itis(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a null value
            taxon = "No chance!"
            expected = {}
            taxonomy = get_taxonomy_for_taxon_itis(taxon)
            self.assertEqual(taxonomy, expected)

        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the get_taxonomy_for_taxon_eol function"
        return



    def test_get_taxonomy_for_taxon_worms(self):

        if (internet_on()):
            # Let's check an easy one!
            taxon = "Delphinus delphis"
            expected = {'kingdom': 'Animalia', 'superfamily': 'Odontoceti', 'family': 'Delphinidae', 'infraorder': 'Cetacea', 'subclass': 'Theria', 'order': 'Cetartiodactyla', 'phylum': 'Chordata', 'superclass': 'Tetrapoda', 'suborder': 'Cetancodonta', 'provider': 'WoRMS', 'species': 'Delphinus delphis', 'subphylum': 'Vertebrata', 'genus': 'Delphinus', 'class': 'Mammalia'}
            taxonomy = get_taxonomy_for_taxon_worms(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a subspecies
            taxon = "Delphinus delphis delphis"
            taxonomy = get_taxonomy_for_taxon_worms(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a null value
            taxon = "No chance!"
            expected = {}
            taxonomy = get_taxonomy_for_taxon_worms(taxon)
            self.assertEqual(taxonomy, expected)

        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the get_taxonomy_for_taxon_eol function"
        return


    def test_get_taxonomy_for_taxon_pbdb(self):

        if (internet_on()):
            # Let's check an easy one!
            taxon = "Tyrannosaurus rex"
            expected = {'kingdom': 'Animalia', 'family': 'Tyrannosauridae', 'order': 'Avetheropoda', 'phylum': 'Chordata', 'provider': 'PBDB', 'species': 'Tyrannosaurus rex', 'class': 'Saurischia'}
            taxonomy = get_taxonomy_for_taxon_pbdb(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a null value
            taxon = "No chance!"
            expected = {}
            taxonomy = get_taxonomy_for_taxon_pbdb(taxon)
            self.assertEqual(taxonomy, expected)

        else:
            print bcolors.WARNING + "WARNING: "+ bcolors.ENDC+ "No internet connection found. Not checking the get_taxonomy_for_taxon_eol function"
        return


    def test_get_taxonomy_eol(self):
        taxonomy, start_level = get_taxonomy_eol({},'Balaenopteridae', verbose=False)
        taxa = taxonomy.keys()
        self.assertEqual(start_level, 'family')
        self.assert_('Balaenoptera bonaerensis' in taxa)
        self.assert_('Balaenoptera musculus' in taxa)



    def test_get_taxonomy_worms(self):
        taxonomy, start_level = get_taxonomy_worms({},'Balaenopteridae', verbose=False)
        taxa = taxonomy.keys()
        self.assertEqual(start_level, 'family')
        self.assert_('Balaenoptera bonaerensis' in taxa)
        self.assert_('Balaenoptera musculus' in taxa)

    def test_get_taxonomy_itis(self):
        taxonomy, start_level = get_taxonomy_itis({},'Balaenopteridae', verbose=False)
        taxa = taxonomy.keys()
        self.assertEqual(start_level, 'family')
        self.assert_('Balaenoptera bonaerensis' in taxa)
        self.assert_('Balaenoptera musculus' in taxa)

if __name__ == '__main__':
    unittest.main()
 



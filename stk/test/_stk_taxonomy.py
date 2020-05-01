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
def extractDictAFromB(A,B):
    return dict([(k,B[k]) for k in A.keys() if k in B.keys()])

class TestSTKTaxonomy(unittest.TestCase):

    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_create_taxonomy(self):
        XML = etree.tostring(etree.parse('data/input/create_taxonomy.phyml',parser),pretty_print=True)
        expected = {'Jeletzkytes_criptonodosus': {'species': 'Jeletzkytes criptonodosus'}, 'Thalassarche_melanophris': {'family': 'Diomedeidae', 'class': 'Aves', 'phylum': 'Chordata', 'species': 'Thalassarche melanophris', 'genus': 'Thalassarche', 'order': 'Procellariiformes'}, 'Egretta_tricolor': {'family': 'Ardeidae', 'class': 'Aves', 'phylum': 'Chordata', 'species': 'Egretta tricolor', 'genus': 'Egretta', 'order': 'Pelecaniformes'}, 'Archaeopteryx_lithographica': {'species': 'Archaeopteryx lithographica', 'genus': 'Archaeopteryx'}}
        taxa = ['Archaeopteryx lithographica', 'Jeletzkytes_criptonodosus', 'Thalassarche melanophris','Egretta tricolor'] 
        taxonomy = create_taxonomy_from_taxa(taxa,pref_db='eol',verbose=False,threadNumber=1)
        print taxonomy
        for taxon in expected:
            self.assertDictEqual(extractDictAFromB(expected[taxon],taxonomy[taxon]), expected[taxon])


    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_create_extended_taxonomy(self):
        XML = etree.tostring(etree.parse('data/input/create_taxonomy.phyml',parser),pretty_print=True)
        expected = {'Jeletzkytes_criptonodosus': {'family': 'Scaphitidae', 'order': 'Ammonitida', 'phylum': 'Mollusca', 'species': 'Jeletzkytes criptonodosus', 'genus': 'Jeletzkytes', 'class': 'Cephalopoda'}, 'Egretta_tricolor': { 'genus': 'Egretta', 'family': 'Ardeidae', 'class': 'Aves', 'order': 'Pelecaniformes', 'phylum': 'Chordata', 'subphylum': 'Vertebrata', 'subfamily': 'Ardeinae', 'species': 'Egretta tricolor'}, 'Archaeopteryx_lithographica': {'phylum': 'Chordata', 'genus': 'Archaeopteryx', 'species': 'Archaeopteryx lithographica', 'class': 'Aves'}, 'Thalassarche_melanophris': {'family': 'Diomedeidae', 'class': 'Aves', 'order': 'Procellariiformes', 'phylum': 'Chordata', 'subphylum': 'Vertebrata', 'genus': 'Thalassarche', 'species': 'Thalassarche melanophris'}}
        taxa = ['Archaeopteryx lithographica', 'Jeletzkytes criptonodosus', 'Thalassarche melanophris','Egretta tricolor'] 
        taxonomy = create_taxonomy_from_taxa(taxa,pref_db='eol',threadNumber=2)
        taxonomy = create_extended_taxonomy(taxonomy,pref_db='eol',threadNumber=2)
        for taxon in expected:
            self.assertDictEqual(extractDictAFromB(expected[taxon],taxonomy[taxon]), expected[taxon])

    
    @unittest.skipUnless(internet_on(), "requires internet connection")    
    def test_taxonomy_checker(self):
        expected = {'Thalassarche_melanophrys': (['Thalassarche_melanophris'], 'yellow'), 'Egretta_tricolor': (['Egretta_tricolor'], 'green'), 'Gallus_gallus': (['Gallus_gallus'], 'green')}
        taxa_list = ['Thalassarche_melanophrys', 'Egretta_tricolor', 'Gallus_gallus']
        equivs = taxonomic_checker_list(taxa_list)
        self.maxDiff = None
        self.assertDictEqual(equivs, expected)

    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_taxonomy_checker2(self):
        XML = etree.tostring(etree.parse('data/input/check_taxonomy_fixes.phyml',parser),pretty_print=True)
        # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
        taxa_list = stk_phyml.get_all_taxa(XML)
        equivs = taxonomic_checker_list(taxa_list)
        self.maxDiff = None
        self.assert_(equivs['Agathamera_crassa'][0][0] == 'Agathemera_crassa')
        self.assert_(equivs['Celatoblatta_brunni'][0][0] == 'Maoriblatta_brunni')
        self.assert_(equivs['Blatta_lateralis'][1] == 'amber')


    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_taxonomy_check_worms(self):
        # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
        taxa_list = ['Rhineodon_typus', 'Rhincodon_typus','Rhin_typussfgsfg','whale shark'] #whale shark + random
        equivs = taxonomic_checker_list(taxa_list, pref_db='worms')
        self.maxDiff = None
        self.assert_(equivs['Rhineodon_typus'][0][0] == 'Rhincodon_typus')
        self.assert_(equivs['Rhincodon_typus'][0][0] == 'Rhincodon_typus')
        self.assert_(equivs['Rhineodon_typus'][1] == 'yellow')
        self.assert_(equivs['Rhincodon_typus'][1] == 'green')
        self.assert_(equivs['Rhin_typussfgsfg'][1] == 'red')
        self.assert_(equivs['whale shark'][0][0] == 'Rhincodon_typus')
        self.assert_(equivs['whale shark'][1] == 'amber') # wor,s returns 2 results, both whale shark, but this makes it amber


    #@unittest.skipUnless(internet_on(), "requires internet connection")
    @unittest.skip("EOL have broken this")
    def test_taxonomy_checker_common_name(self):
        # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
        taxa_list = ['Cardueline_Finches']
        equivs = taxonomic_checker_list(taxa_list)
        self.maxDiff = None
        print equivs
        self.assert_(equivs['Cardueline_Finches'][0][0] == 'Carduelinae')


    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_taxonomy_checker_common_name2(self):
        # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
        taxa_list = ['Chaffinches']
        equivs = taxonomic_checker_list(taxa_list)
        self.maxDiff = None
        self.assert_(equivs['Chaffinches'][0][0] == 'Fringilla_coelebs')


    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_taxonomy_checker_subgenus(self):
        # This test is a bit dodgy as it depends on EOL's server speed. Run it a few times before deciding it's broken.
        taxa_list = ['Bombus_affinis']
        equivs = taxonomic_checker_list(taxa_list)
        self.maxDiff = None
        self.assert_(equivs['Bombus_affinis'][0][0] == 'Bombus_affinis')


    def test_load_taxonomy(self):
        csv_file = "data/input/create_taxonomy.csv"
        expected = {'Egretta_tricolor': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'class': 'Aves', 'subkingdom': 'Bilateria', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'subclass': 'Neoloricata', 'species': 'Egretta_tricolor', 'phylum': 'Chordata', 'suborder': 'Ischnochitonina', 'superphylum': 'Lophozoa', 'infrakingdom': 'Protostomia', 'genus': 'Egretta', 'order': 'Pelecaniformes'}, 'Gallus_gallus': {'kingdom': 'Animalia', 'superorder': 'Galliformes', 'family': 'Phasianidae', 'subkingdom': 'Bilateria', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'species': 'Gallus_gallus', 'phylum': 'Chordata', 'superphylum': 'Lophozoa', 'infrakingdom': 'Protostomia', 'genus': 'Gallus', 'class': 'Aves'}, 'Egretta_garzetta': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'class': 'Aves', 'subkingdom': 'Bilateria', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'subclass': 'Neoloricata', 'species': 'Egretta_garzetta', 'phylum': 'Chordata', 'suborder': 'Ischnochitonina', 'superphylum': 'Lophozoa', 'infrakingdom': 'Protostomia', 'genus': 'Egretta', 'order': 'Pelecaniformes'}, 'Thalassarche_melanophris': {'kingdom': 'Animalia', 'family': 'Diomedeidae', 'subkingdom': 'Bilateria', 'species': 'Thalassarche_melanophris', 'order': 'Procellariiformes', 'phylum': 'Chordata', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'infrakingdom': 'Deuterostomia', 'subphylum': 'Vertebrata', 'genus': 'Thalassarche', 'class': 'Aves'}, 'Jeletzkytes_criptonodosus': {'kingdom': 'Metazoa', 'superfamily': 'Scaphitidae', 'family': 'Scaphitidae', 'subclass': 'Cephalopoda', 'species': 'Jeletzkytes_criptonodosus', 'suborder': 'Ammonoidea', 'provider': 'PBDB', 'class': 'Mollusca'}, 'Archaeopteryx_lithographica': {'family': 'Archaeopterygidae', 'subkingdom': 'Metazoa', 'subclass': 'Tetrapodomorpha', 'species': 'Archaeopteryx_lithographica', 'suborder': 'Coelurosauria', 'provider': 'Paleobiology Database', 'genus': 'Archaeopteryx', 'class': 'Aves'}}
        taxonomy = load_taxonomy(csv_file)
        self.maxDiff = None
        self.assertDictEqual(taxonomy, expected)


    def test_create_tree_taxonomy(self):
        csv_file = "data/input/create_taxonomy.csv"
        taxonomy = load_taxonomy(csv_file)
        expected_tree = "(((Egretta_tricolor, Egretta_garzetta), Archaeopteryx_lithographica, Gallus_gallus, Thalassarche_melanophris), Jeletzkytes_criptonodosus);"
        tree = tree_from_taxonomy('class', taxonomy)
        self.assert_(trees_equal(tree,expected_tree))


    def test_create_tree_taxonomy_single(self):
        taxonomy = {'Egretta_tricolor': {'kingdom': 'Animalia', 'family': 'Ardeidae', 'class': 'Aves', 'subkingdom': 'Bilateria', 'provider': 'Species 2000 & ITIS Catalogue of Life: April 2013', 'subclass': 'Neoloricata', 'species': 'Egretta tricolor', 'phylum': 'Chordata', 'suborder': 'Ischnochitonina', 'superphylum': 'Lophozoa', 'infrakingdom': 'Protostomia', 'genus': 'Egretta', 'order': 'Pelecaniformes'}}
        expected_tree = "(Egretta_tricolor);"
        tree = tree_from_taxonomy('class', taxonomy)
        self.assert_(trees_equal(tree,expected_tree))

    def test_create_tree_taxonomy_complex(self):
        taxonomy = load_taxonomy("data/input/test_make_tree.csv")
        expected_tree = "(Egretta_tricolor);"
        tree = tree_from_taxonomy('class', taxonomy)
        print tree
        self.assert_(trees_equal(tree,expected_tree))


    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_get_taxonomy_for_taxon_eol(self):
        # Let's check an easy one!
        taxon = "Gallus gallus"
        expected = {'kingdom': 'Animalia', 'family': 'Phasianidae', 'class': 'Aves', 'phylum': 'Chordata', 'provider': 'species 2000 & itis catalogue of life: april 2013', 'species': 'Gallus gallus', 'genus': 'Gallus', 'order': 'Galliformes'}
        taxonomy = get_taxonomy_for_taxon_eol(taxon)
        self.assert_(taxonomy['family'], expected['family'])
        self.assert_(taxonomy['class'], expected['class'])
        self.assert_(taxonomy['genus'], expected['genus'])


        # Now a subspecies
        taxon = "Gallus gallus bankiva"
        taxonomy = get_taxonomy_for_taxon_eol(taxon)
        self.assert_(taxonomy['family'], expected['family'])
        self.assert_(taxonomy['class'], expected['class'])
        self.assert_(taxonomy['genus'], expected['genus'])

        # Now a null value
        taxon = "No chance!"
        expected = {'species': 'No chance!'}
        taxonomy = get_taxonomy_for_taxon_eol(taxon)
        self.assertEqual(taxonomy, expected)


    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_get_taxonomy_for_taxon_itis(self):
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
        expected = {'species': 'No chance!'}
        taxonomy = get_taxonomy_for_taxon_itis(taxon)
        self.assertEqual(taxonomy, expected)



    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_get_taxonomy_for_taxon_worms(self):
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
        expected = {'species': 'No chance!'}
        taxonomy = get_taxonomy_for_taxon_worms(taxon)
        self.assertEqual(taxonomy, expected)

    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_get_taxonomy_for_taxon_pbdb(self):
            # Let's check an easy one!
            taxon = "Tyrannosaurus rex"
            expected = {'genus': 'Tyrannosaurus', 'family': 'Tyrannosauridae', 'order': 'Avetheropoda', 'phylum': 'Chordata', 'provider': 'PBDB', 'species': 'Tyrannosaurus rex', 'class': 'Saurischia'}
            taxonomy = get_taxonomy_for_taxon_pbdb(taxon)
            self.assertEqual(taxonomy, expected)

            # Now a null value
            taxon = "No chance!"
            expected = {'species': 'No chance!'}
            taxonomy = get_taxonomy_for_taxon_pbdb(taxon)
            self.assertEqual(taxonomy, expected)

    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_get_taxonomy_eol(self):
        taxonomy, start_level = get_taxonomy_eol({},'Balaenopteridae', verbose=False)
        taxa = taxonomy.keys()
        self.assertEqual(start_level, 'family')
        self.assert_('Balaenoptera bonaerensis' in taxa)
        self.assert_('Balaenoptera musculus' in taxa)

    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_get_taxonomy_worms(self):
        taxonomy, start_level = get_taxonomy_worms({},'Balaenopteridae', verbose=False)
        taxa = taxonomy.keys()
        self.assertEqual(start_level, 'family')
        self.assert_('Balaenoptera bonaerensis' in taxa)
        self.assert_('Balaenoptera musculus' in taxa)
    
    
    @unittest.skipUnless(internet_on(), "requires internet connection")
    def test_get_taxonomy_itis(self):
        taxonomy, start_level = get_taxonomy_itis({},'Balaenopteridae', verbose=False)
        taxa = taxonomy.keys()
        self.assertEqual(start_level, 'family')
        self.assert_('Balaenoptera bonaerensis' in taxa)
        self.assert_('Balaenoptera musculus' in taxa)

if __name__ == '__main__':
    unittest.main()
 



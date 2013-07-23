import unittest
import math
import sys
sys.path.insert(0,"../../")
sys.path.insert(0,"../")
import os
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
from stk.supertree_toolkit import _parse_subs_file, _check_data
from stk.supertree_toolkit import _swap_tree_in_XML, substitute_taxa, get_all_taxa
from lxml import etree
from util import *
from stk.stk_exceptions import *
from collections import defaultdict
import tempfile
parser = etree.XMLParser(remove_blank_text=True)
import re

# Class to test all those loverly internal methods
# or stuff that doesn't fit within the other tests

class TestSubs(unittest.TestCase):

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
        except UnableToParseSubsFile:
            self.assert_(True)
            return
        self.assert_(False)

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

    def old_stk_replace_taxa_tests:
        original_trees = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
        quote_taxa_tree = "(taxa_1, 'taxa_n=taxa_2', taxa_3, taxa_4)";
        tree1 = "((((replaced_taxon,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
        tree2 = "((((Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
        tree3 = "((((taxon_1,taxon_2,taxon_3,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
        tree4 = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds),('Recurvirostridae=Charadriidae',Protopteryx_fengningensis))))";
        tree4_result = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds),Protopteryx_fengningensis)))";


        polytomy = ("taxon_1","taxon_2","taxon_3");
        polytomy2 = ("Skua_blah","Parasiticus_oops");
        polytomy3 = ("Catharacta_chilensis","replaced_taxon");
        polytomy4 = ("taxon_1","taxon_1","taxon_2","taxon_3");

        XML = etree.tostring(etree.parse('data/input/sub_taxa.phyml',parser),pretty_print=True)
        XML2 = substitute_taxa(XML, ["A","B_b"], ["Fred",None])
        taxa = get_all_taxa(XML2)

        replace_taxon_tree(\@input_trees,'Catharacta_maccormicki',['replaced_taxon']);
        is ($input_trees[0], $tree1, "Correctly replaced taxon");

@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_maccormicki');
is ($input_trees[0], $tree2, "Correctly deleted taxon");

@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_maccormicki',\@polytomy);
is ($input_trees[0], $tree3, "Correctly replaced with polytomy");

@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta maccormicki');
is ($input_trees[0], $tree2, "Correctly deleted taxon with space in name");

@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_Maccormicki');
isnt ($input_trees[0], $tree2, "Didn't delete taxon with incorrect case");

@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta maccormicki',['replaced_taxon']);
is ($input_trees[0], $tree1, "Correctly replaced taxon with spaces in name");

@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_Maccormicki',\@polytomy);
isnt ($input_trees[0], $tree3, "Didn't replace taxon with incorrect case");

# check for partial replacement which we don't want
@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Skua',\@polytomy2);
is ($input_trees[0], $original_trees[0], "Correctly skipped partial match");

# checking for adding duplicate taxa
@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_maccormicki',\@polytomy3);
is ($input_trees[0], $tree1, "Correctly substituted but no duplicates with polytomy");


@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_maccormicki',['Catharacta_chilensis']);
is ($input_trees[0], $tree2, "Correctly substituted but no duplicates with single");

# checking for correct subbing of quoted taxa
@input_trees = @quote_taxa_tree;
Bio::STK::replace_taxon_tree(\@input_trees,"'taxa_n=taxa_2'",['taxa_2']);
my $answer = "(taxa_1,taxa_2,taxa_3,taxa_4)";
is ($input_trees[0], $answer, "Correctly substituted quoted taxa");
# quoted with + in it
$input_trees[0] = "(taxa_1, 'taxa_n+taxa_2', taxa_3, taxa_4)";
Bio::STK::replace_taxon_tree(\@input_trees,"'taxa_n+taxa_2'",['taxa_2']);
$answer = "(taxa_1,taxa_2,taxa_3,taxa_4)";
is ($input_trees[0], $answer, "Correctly substituted quoted taxa 2");

# don't sub partial match of quoted taxa
@input_trees = @quote_taxa_tree;
Bio::STK::replace_taxon_tree(\@input_trees,"taxa_2",['taxa_8']);
$answer = "(taxa_1,'taxa_n=taxa_2',taxa_3,taxa_4)";
is ($input_trees[0], $answer, "Didn't substitute part of quoted taxa");

# don't sub in repeated taxa
@input_trees = @original_trees;
Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_maccormicki',\@polytomy4);
is ($input_trees[0], $tree3, "Didn't add repeated names");

# checking removal of quoted taxa
# this check actually *hides* a bug in Bio::NEXUS
$quote_taxa_tree[0] = "(taxa_1, 'taxa_n+taxa_2', taxa_3, taxa_4)";
@input_trees = @quote_taxa_tree;
Bio::STK::replace_taxon_tree(\@input_trees,"'taxa_n+taxa_2'");
$answer = "(taxa_1,taxa_3,taxa_4)";
is ($input_trees[0], $answer, "Remove quoted taxa");

# this check exposes a bug in Bio::NEXUS
$quote_taxa_tree[0] = "(taxa_1, 'taxa_n+taxa_2', 'taxa_3=taxa5', taxa_4)";
@input_trees = @quote_taxa_tree;
Bio::STK::replace_taxon_tree(\@input_trees,"'taxa_3=taxa5'");
$answer = "(taxa_1,'taxa_n+taxa_2',taxa_4)";
is ($input_trees[0], $answer, "Remove quoted taxa");
# in Bio::NEXUS::Node->prune(), there's a search on taxa to check if they 
# should be included in the tree. This is called when making a tree and after exclude_otus, etc.
# Any taxa that are quoted in the NEWICK string have their quotes stripped when creating a
# Nexus object. In prune() we have:
# if ( $OTUlist =~ m/\s+$name\s+/ ) {
# with OTUlist containing a space-seperated list of taxa and name is the current node (i.e. taxa)
# If name contains meta characters, such as +, then the search will fail and the taxa will
# be excluded from the OTU list and hence from the tree. The solution is to quotemeta $name before
# using it in a search. Makes me wonder where this might crop up elsewhere.

my @polytomy5 = ("taxon_n","'taxon_n+taxon_2'","taxon_2","taxon_3");
$quote_taxa_tree[0] = "(taxa_n, 'taxa_n+taxa_2', 'taxa_3=taxa5', taxa_4)";
@input_trees = @quote_taxa_tree;
Bio::STK::replace_taxon_tree(\@input_trees,"taxa_4",\@polytomy5);
$answer = "(taxa_n,'taxa_n+taxa_2','taxa_3=taxa5',taxon_n,'taxon_n+taxon_2',taxon_2,taxon_3)";
is ($input_trees[0], $answer, "Added polytomy with quoted taxa");

Bio::STK::replace_taxon_tree(\@tree4,"'Recurvirostridae=Charadriidae'",['Modern_birds']);
is ($tree4[0], $tree4_result, "Correct replacement of taxa that already exists");

# New bug: replacing with the same taxa 
@input_trees = @original_trees;
$tree1 = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
Bio::STK::replace_taxon_tree(\@input_trees,"Catharacta_maccormicki",['Catharacta_maccormicki']);
is ($input_trees[0], $tree1, "Correct ignored taxa replaced with itself");

# Trying out new function to collapse clades when going from specific to generic
@input_trees = @original_trees;
$tree1 = "(((Catharacta,(Catharacta1,Stercorarius)),Stercorarius1),Larus)";
Bio::STK::replace_taxon_tree(\@input_trees,"Catharacta_maccormicki",['Catharacta'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Catharacta_chilensis",['Catharacta'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Catharacta_antarctica",['Catharacta'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Catharacta_skua",['Catharacta'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Stercorarius_pomarinus",['Stercorarius'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Stercorarius_parasiticus",['Stercorarius'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Stercorarius_longicaudus",['Stercorarius'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Larus_argentatus",['Larus'],1);
is ($input_trees[0], $tree1, "Correctly collapse tree");

my @hard_tree;
$hard_tree[0] = "(Daphnia,Drosophila,Euphausia,Exopheticus,Petrolisthes,Pinnotherelia,Tritodynamia,(Ligia,(Armadillidium,Eocarcinus,Metapenaeus,((((((Himalayapotamon,Jasus,Polycheles,(Enoplometopus,((Pemphix,(((Thaumastocheles,(Acanthacaris,Enoplometopus1,Eryma,Homarus,Metanephrops,Nephropides,Nephrops,Nephropsis,Thaumastocheles1,Thaumastochelopsis,((Euastacus,(Astacoides,Geocharax,(Paranephrops,(Astacopsis,(Ombrastacoides,(Gramastacus,Cherax))))),(Parastacus,(Samastacus,Virilastacus))))))))))))))))))))";
@input_trees = @hard_tree;
$tree1 = "(Daphnia,Drosophila,Euphausia,Exopheticus,Petrolisthes,Pinnotherelia,Tritodynamia,(Ligia,(Armadillidium,Eocarcinus,Metapenaeus,(Himalayapotamon,Jasus,Polycheles,(Enoplometopus,(Pemphix,(Thaumastocheles,(Acanthacaris,Enoplometopus1,Eryma,Homarus,Metanephrops,Nephropides,Nephrops,Nephropsis,Thaumastocheles1,Thaumastochelopsis,(Euastacus,(Parastacidae,Geocharax,(Parastacidae2,(Astacopsis,Parastacidae1))),Parastacidae3)))))))))";
Bio::STK::replace_taxon_tree(\@input_trees,"Astacoides",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Astacoides1",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Cherax",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Cherax1",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Gramastacus",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Ombrastacoides",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Paranephrops",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Parastacus",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Samastacus",['Parastacidae'],1);
Bio::STK::replace_taxon_tree(\@input_trees,"Virilastacus",['Parastacidae'],1);
is ($input_trees[0], $tree1, "Correctly collapse tree");
        


if __name__ == '__main__':
    unittest.main()
 

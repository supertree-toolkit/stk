#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 18;

use lib 'lib';
use Bio::STK;

my @original_trees;

$original_trees[0] = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";

my @quote_taxa_tree;
$quote_taxa_tree[0] = "(taxa_1, 'taxa_n=taxa_2', taxa_3, taxa_4)";

my @input_trees = @original_trees;
my $tree1 = "((((replaced_taxon,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
my $tree2 = "((((Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
my $tree3 = "((((taxon_1,taxon_2,taxon_3,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
my @tree4;
$tree4[0] = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds),('Recurvirostridae=Charadriidae',Protopteryx_fengningensis))))";
my $tree4_result = "(Apsaravis,Hesperornis,Ichthyornis,(Vegavis_iaai,(('Cathartidae=Ciconiidae',Modern_birds),Protopteryx_fengningensis)))";
 

my @polytomy = ("taxon_1","taxon_2","taxon_3");
my @polytomy2 = ("Skua_blah","Parasiticus_oops");
my @polytomy3 = ("Catharacta_chilensis","replaced_taxon");
my @polytomy4 = ("taxon_1","taxon_1","taxon_2","taxon_3");

Bio::STK::replace_taxon_tree(\@input_trees,'Catharacta_maccormicki',['replaced_taxon']);
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



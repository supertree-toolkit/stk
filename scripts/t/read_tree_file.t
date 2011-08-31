#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 10;

use lib 'lib';
use Bio::STK;

my $tree1 = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
my $tree2 = "((A,B),(C,D))";
my @trees3;
$trees3[0] = "(((A,B),(C,D)),((E,F),(G,H)))";
$trees3[1] = "(((((((A,B),C),D),E),F),G),H)";
$trees3[2] = "(A,B,C,D,E,F,G,H)";

my @tree_loaded = Bio::STK::read_tree_file('t/data/tree1.tre');
is ($tree_loaded[0], $tree1, "Read in Translated tree correctly");

@tree_loaded = Bio::STK::read_tree_file('t/data/tree2.tre');
is ($tree_loaded[0], $tree2, "Read in Newick tree correctly");

@tree_loaded = Bio::STK::read_tree_file('t/data/trees-multiple.tre');
is (@tree_loaded, 3, "Loaded in the right number of trees from multiple tree file");
my $i = 0;
foreach my $tree (@tree_loaded) {
    is ($trees3[$i], $tree, "Loaded tree $i correctly");
    $i++;
}
#this test should die, so wrap it up...
eval {
    Bio::STK::read_tree_file('t/data/test_data/nonsense.tre'); 
};
ok($@, 'Croaked correctly');
like($@, qr/Error \- specified tree file does not exist:/, '... and it is the correct exception');
# so should this one
eval {
    Bio::STK::read_tree_file('t/data/treeview.tre'); 
};
ok($@, 'Croaked correctly');
like($@, qr/Error loading tree file.*It exists, but is not truely compliant with the NEXUS format/, '... and it is the correct exception');


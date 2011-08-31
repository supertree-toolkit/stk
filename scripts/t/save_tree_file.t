#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 13;

use lib 'lib';
use Bio::STK;

my @tree1;
$tree1[0] = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
my @trees3;
$trees3[0] = "(((A,B),(C,D)),((E,F),(G,H)))";
$trees3[1] = "(((((((A,B),C),D),E),F),G),H)";
$trees3[2] = "(A,B,C,D,E,F,G,H)";
my @tree_quoted;
$tree_quoted[0] = "(a,b,'c=d',e,f)";

ok (Bio::STK::save_tree_file('t/data/tree1_check.tre', \@tree1), "Saved file 1 OK");
my @tree_loaded = Bio::STK::read_tree_file('t/data/tree1_check.tre');
is ($tree_loaded[0], $tree1[0], "Saved file correctly");
unlink 't/data/tree1_check.tre';

ok (Bio::STK::save_tree_file('t/data/tree3_check.tre', \@trees3), "Saved file 3 OK");
@tree_loaded = Bio::STK::read_tree_file('t/data/tree3_check.tre');
is (@tree_loaded, 3, "Loaded in the right number of trees from multiple tree file");
my $i = 0;
foreach my $tree (@tree_loaded) {
    is ($trees3[$i], $tree, "Loaded tree $i correctly");
    $i++;
}
unlink 't/data/tree3_check.tre';

ok (Bio::STK::save_tree_file('t/data/tree1_check.tre', \@tree1, ['tree_test']), "Saved tree with name");
my ($file) = 't/data/tree1_check.tre';
my ($f);
open( $f, "<", $file ) || die " Can't open file $file, quitting.\n";
my $lines = do { local $/; <$f> };
ok($lines =~ m/tree_test/,"Found tree name");
ok($lines !~ m/inode/,"No internal node names");
unlink 't/data/tree1_check.tre';

Bio::STK::save_tree_file('t/data/tree1_check.tre', \@tree_quoted);
@tree_loaded = Bio::STK::read_tree_file('t/data/tree1_check.tre');
is ($tree_loaded[0],$tree_quoted[0],"Quoted tree saved ok");

unlink 't/data/tree1_check.tre';

#this test should die, so wrap it up...
eval {
    Bio::STK::save_tree_file('t/data/thisdirectorydoesnotexist/tree1_check.tre', \@tree_quoted);
};
ok($@, 'Croaked correctly');
like($@,  qr/Error saving tree file/,'... and it is the correct exception');

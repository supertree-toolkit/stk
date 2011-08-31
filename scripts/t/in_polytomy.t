#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 6;

use lib 'lib';
use Bio::STK;

my $tree_1 = "(taxa_1,taxa_2,taxa_3)";
my $tree_2 = "(taxa_1,taxa_2,taxa_3,(taxa_4,taxa_5))";
my $tree_3 = "(taxa_3,taxa_2,taxa_1)";
my $tree_4 = "(taxa_1,taxa_2,(taxa_3,taxa_4))";
my $tree_5 = "(taxa_1,(taxa_2,(taxa_3,taxa_4)))";
my $tree_6 = "(taxa_4,taxa_2,taxa_3,taxa_1,taxa_5)";



ok (Bio::STK::in_polytomy('taxa_1',$tree_1),"Polytomy: taxa at start");
ok (Bio::STK::in_polytomy('taxa_1',$tree_2),"Polytomy: taxa at start, more complex tree");
ok (Bio::STK::in_polytomy('taxa_1',$tree_3),"Polytomy: taxa at end");
ok (!Bio::STK::in_polytomy('taxa_1',$tree_4),"No polytomy");
ok (!Bio::STK::in_polytomy('taxa_1',$tree_5),"No polytomy");
ok (Bio::STK::in_polytomy('taxa_1',$tree_6),"Big polytomy");


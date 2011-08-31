#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 2;

use lib 'lib';
use Bio::STK;


my $tree1 = "t/data/tree1.tre";
my $tree2 = "t/data/tree2.tre";

ok(Bio::STK::tree_equals($tree1, $tree1),"Compared trees correctly");
ok(!Bio::STK::tree_equals($tree1, $tree2),"Found unequal trees correctly");

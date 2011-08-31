#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 5;

use lib 'lib';
use Bio::STK;

my $file1 = "t/data/incorrect_tree1.tre";
my $file2 = "t/data/tree1.tre";
my $file3 = "t/data/trees-multiple.tre";

# check we catch an incorrectly formatted tree
ok (!Bio::STK::check_tree_file($file1), "Correctly ID incorrect format");

# check some correctly formatted trees
ok (Bio::STK::check_tree_file($file2), "Correctly ID correct format");
ok (Bio::STK::check_tree_file($file3), "Correctly ID correct format");

# check a non-existant file croaks
#this test should die, so wrap it up...
eval {
    Bio::STK::check_tree_file('t/data/thisdirectorydoesnotexist/tree1_check.tre');
};
ok($@, 'Croaked correctly');
like($@,  qr/File .* not found/,'... and it is the correct exception');


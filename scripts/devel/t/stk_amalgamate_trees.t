#!/usr/bin/perl -w

use strict;
use Test::More tests => 12;
use File::Compare qw(compare_text);
use File::Copy;
# this contains tests for checking things like the man page works
# 
# *******   Total number of tests will increase by 5 *********
#
require "standard_tests.pl";

chdir ('../../exec');
# standard tests to check everything works ok
# These are actually checked at the bottom of this test file
# We throw away the output
# Standard labelled output
my $output = `perl stk_amalgamate_trees.pl --dir ../devel/test_dataset/standard --output ../devel/t/data/amalgamate_trees/standard.tre`;
# standard, anon output
$output = `perl stk_amalgamate_trees.pl --dir ../devel/test_dataset/standard -a --output ../devel/t/data/amalgamate_trees/standard_anon.tre`;
# tree-only, labelled output
$output = `perl stk_amalgamate_trees.pl --dir ../devel/test_dataset/tree_only --output ../devel/t/data/amalgamate_trees/tree_only.tre`;
# tree-only, anon output
$output = `perl stk_amalgamate_trees.pl --dir ../devel/test_dataset/tree_only -a --output ../devel/t/data/amalgamate_trees/tree_only_anon.tre`;
# do we get the right output if we don't specify the output file?
$output = `perl stk_amalgamate_trees.pl --dir ../devel/test_dataset/tree_only`;


# check some of the features of the script now - these are "standard" across all scripts
standard_tests("stk_amalgamate_trees");

# now check some of the script-specific functions
# We must have a directory specified.
$output = `perl stk_amalgamate_trees.pl -a --output ../devel/t/data/amalgamate_trees/tree_only_anon.tre`;
like($output,  qr/You must specify a directory/,'Got correct error message');
# verbose working?
$output = `perl stk_amalgamate_trees.pl --dir ../devel/test_dataset/tree_only -v --output temp.tre`;
like($output, qr/Processing tree files.../,'Some verbose output occurred');


# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}
ok ( compare_text("../devel/t/data/amalgamate_trees/standard.tre","../devel/t/correct/amalgamate_trees/standard.tre",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Standard named OK');
ok ( compare_text("../devel/t/data/amalgamate_trees/standard_anon.tre","../devel/t/correct/amalgamate_trees/standard_anon.tre",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Standard anon OK');
ok ( compare_text("../devel/t/data/amalgamate_trees/tree_only.tre","../devel/t/correct/amalgamate_trees/tree_only.tre",sub {munge $_[0] ne munge $_[1]} ) == 0, 'tree_only OK');
ok ( compare_text("../devel/t/data/amalgamate_trees/tree_only_anon.tre","../devel/t/correct/amalgamate_trees/tree_only_anon.tre",sub {munge $_[0] ne munge $_[1]} ) == 0, 'tree_only_anon OK');
ok ( compare_text("../devel/test_dataset/tree_only/all_trees.tre","../devel/t/correct/amalgamate_trees/tree_only.tre",sub {munge $_[0] ne munge $_[1]} ) == 0, 'tree_only OK with default file name');


unlink("../devel/t/data/amalgamate_trees/standard.tre");
unlink("../devel/t/data/amalgamate_trees/standard_anon.tre");
unlink("../devel/test_dataset/standard/key.txt");
unlink("../devel/t/data/amalgamate_trees/tree_only.tre");
unlink("../devel/t/data/amalgamate_trees/tree_only_anon.tre");
unlink("../devel/test_dataset/tree_only/all_trees.tre");
unlink("temp.tre");
unlink("../devel/t/data/tree_permutation/permutation.tre_permute");



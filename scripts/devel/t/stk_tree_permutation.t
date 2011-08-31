#!/usr/bin/perl -w

use strict;
use Test::More tests => 2;
use File::Compare qw(compare_text);

chdir ('../../exec');
my $output = `perl stk_tree_permutation.pl -v --file ../devel/t/data/tree_permutation/test.tre`;

# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}
ok ( compare_text("../devel/t/data/tree_permutation/test.tre_permute","../devel/t/correct/tree_permutation/test.tre_permute",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Permutation OK');

unlink("../devel/t/data/tree_permutation/test.tre_permute");

# Thanks to Laura K. Saila for providing the data and spotting this bug
$output = `perl stk_tree_permutation.pl -v --file ../devel/t/data/tree_permutation/permutation.tre`;
ok ( compare_text("../devel/t/data/tree_permutation/permutation.tre_permute","../devel/t/correct/tree_permutation/permutation.tre_permute",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Permutation OK');

unlink("../devel/t/data/tree_permutation/permute.tre_permute");



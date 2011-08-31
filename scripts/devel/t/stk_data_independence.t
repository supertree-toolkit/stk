#!/usr/bin/perl -w

use strict;
use Test::More tests => 1;
use File::Compare qw(compare_text);
use File::Copy;

chdir ('../../exec');
my $output = `perl stk_data_independence.pl --dir ../devel/test_dataset/standard`;

move("../devel/test_dataset/standard/duplication.dat","../devel/t/data/data_independence/duplication.dat") or die ("Couldn't copy output");

# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}

ok ( compare_text("../devel/t/data/data_independence/duplication.dat","../devel/t/correct/data_independence/duplication.dat", sub {munge $_[0] ne munge $_[1]} ) == 0, 'Output OK');


unlink("../devel/t/data/data_independence/duplication.dat");


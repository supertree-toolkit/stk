#!/usr/bin/perl -w

use strict;
use Test::More tests => 2;
use File::Compare qw(compare_text);

chdir ('../../exec');
my $output = `perl stk_create_matrix.pl --dir ../devel/t/data/create_matrix --output ../devel/t/data/create_matrix/MRPmatrix.nex --format Nexus`;

# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//;
    }
    return $line;
}

ok ( compare_text("../devel/t/data/create_matrix/MRPmatrix.nex","../devel/t/correct/create_matrix/MRPmatrix.nex", sub { munge $_[0] ne munge $_[1] } ) == 0, 'MRP matrix created OK');
unlink("../devel/t/data/create_matrix/MRPmatrix.nex");

$output = `perl stk_create_matrix.pl --dir ../devel/t/data/create_matrix --output ../devel/t/data/create_matrix/Matrix.tnt`;
ok ( compare_text("../devel/t/data/create_matrix/Matrix.tnt","../devel/t/correct/create_matrix/Matrix.tnt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Hening86 matrix created OK');

unlink("../devel/t/data/create_matrix/Matrix.tnt");


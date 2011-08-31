#!/usr/bin/perl -w

use strict;
use Test::More tests => 4;
use File::Compare qw(compare_text);

chdir ('../../exec');
my $output = `perl stk_data_summary.pl --dir ../devel/test_dataset/standard --output ../devel/t/data/data_summary/xml_file.txt --taxatreematrix`;
$output = `perl stk_data_summary.pl --dir ../devel/test_dataset/tree_only --output ../devel/t/data/data_summary/tree_file.txt`;
# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}

# Check summary files are OK
ok ( compare_text("../devel/t/data/data_summary/xml_file.txt","../devel/t/correct/data_summary/xml_file.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Standard data summary OK');
ok ( compare_text("../devel/t/data/data_summary/tree_file.txt","../devel/t/correct/data_summary/tree_file.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Tree only summary OK');

# Check the data availability data are OK
ok ( compare_text("../devel/test_dataset/standard/taxa_tree_matrix.txt","../devel/t/correct/data_summary/taxa_tree_matrix.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Taxa-Tree matrix OK');
ok ( compare_text("../devel/test_dataset/standard/data_availability_matrix.txt","../devel/t/correct/data_summary/data_availability_matrix.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Data availability matrix OK');


unlink("../devel/t/data/data_summary/tree_file.txt");
unlink("../devel/t/data/data_summary/xml_file.txt");
unlink("../devel/test_dataset/standard/data_availability_matrix.txt");
unlink("../devel/test_dataset/standard/taxa_tree_matrix.txt");

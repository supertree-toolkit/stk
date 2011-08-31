#!/usr/bin/perl -w

use strict;
use lib "../../lib";
use Bio::STK;
use Test::More tests => 10;
use File::Remove qw(remove);
use File::Compare qw(compare_text);

chdir ('../../exec');
# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//;
    }
    return $line;
}

# test 1
my $output = `perl stk_search_data.pl --dir ../devel/test_dataset/standard/ --anterm MP --output ../devel/t/data/search_data/output.txt`;
ok ( compare_text("../devel/t/data/search_data/output.txt","../devel/t/correct/search_data/output.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Search for analysis OK');

# check for fossil terms, all, some, none
$output = `perl stk_search_data.pl --dir ../devel/test_dataset/standard/ --fossil all --output ../devel/t/data/search_data/output_all.txt`;
ok ( compare_text("../devel/t/data/search_data/output_all.txt","../devel/t/correct/search_data/output_all.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Search for fossil all');
$output = `perl stk_search_data.pl --dir ../devel/test_dataset/standard/ --fossil some --output ../devel/t/data/search_data/output_some.txt`;
ok ( compare_text("../devel/t/data/search_data/output_some.txt","../devel/t/correct/search_data/output_some.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Search for fossil some');
$output = `perl stk_search_data.pl --dir ../devel/test_dataset/standard/ --fossil none --output ../devel/t/data/search_data/output_none.txt`;
ok ( compare_text("../devel/t/data/search_data/output_none.txt","../devel/t/correct/search_data/output_none.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Search for fossil none');

# check copy data is OK
$output = `perl stk_search_data.pl -v --dir ../devel/test_dataset/standard/ --anterm MP --copy search_data`;
# grab all xml files
my @xml_files = Bio::STK::find_xml_files("search_data");
my $nXML      = @xml_files;
# grab all tree files
my @tree_files = Bio::STK::find_tree_files("search_data");
my $nTRE       = @tree_files;
is ( $nTRE, 9, "Correct number of tree files copied");
is ( $nXML, 9, "Correct number of XML files copied");

# check for no errors in copied data
$output = `perl stk_check_data.pl -v --dir search_data`;
like ($output, qr/Checks finished...Found 0 errors/, "Data copied is correct");

# check for decent output if nothing found
$output = `perl stk_search_data.pl --dir ../devel/test_dataset/standard --taxterm NothingWillMatchThis`;
like($output, qr/Didn't find anything/, "Correct output when nothing found");

# check $only option
$output = `perl stk_search_data.pl --dir ../devel/test_dataset/standard --charterm Molecular --only  --output ../devel/t/data/search_data/only_output.txt`;

ok ( compare_text("../devel/t/data/search_data/only_output.txt","../devel/t/correct/search_data/only_test.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Only output OK');



# Bug 16
$output = `perl stk_search_data.pl --dir ../devel/test_dataset/special_cases/bug16/ --taxterm Arthrodyptes`;
# output should contain the XML file
like($output, qr/Ksepka_etal_2006_1_corr.xml/, "Found data");

# clean up
remove \1, "search_data/";
unlink("../devel/t/data/search_data/output.txt");
unlink("../devel/t/data/search_data/output_none.txt");
unlink("../devel/t/data/search_data/output_all.txt");
unlink("../devel/t/data/search_data/output_some.txt");
unlink("../devel/t/data/search_data/only_output.txt");


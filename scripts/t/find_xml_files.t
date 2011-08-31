#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 14;

use lib 'lib';
use Bio::STK;

my $length;
my @files;
eval {
    @files = Bio::STK::find_xml_files('t/data/test_data/');
    $length = @files;
};

is ($length, 11, "Found correct number of XML files");
foreach my $t (@files) {
    like($t, qr/\.xml$/, 'Checking for .xml files only');
}
#this test should die, so wrap it up...
eval {
    Bio::STK::find_xml_files('t/data/test_data/tree1.dat'); 
};
ok($@, 'Croaked correctly');
like($@, qr/Error \- specified directory does not exist:/, '... and it is the correct exception');


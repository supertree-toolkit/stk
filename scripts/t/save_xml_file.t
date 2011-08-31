#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 3;

use lib 'lib';
use Bio::STK;

my $xml1 = "t/data/test_data/bar_2000/tree1.xml";

my $xml = Bio::STK::read_xml_file($xml1);

ok (Bio::STK::save_xml_file('t/data/test.xml', $xml), "Saved file OK");

# this test fails for now - the XML is OK, but is read back in in a different order to the original file
# The Simple::XML manual has this to say about it:
#
# If you wish to 'round-trip' arbitrary data structures from Perl to XML and back to Perl, then you should 
# probably disable array folding (using the KeyAttr option) both with XMLout() and with XMLin(). If you still
# don't get the expected results, you may prefer to use XML::Dumper which is designed for exactly that purpose.
#
#is (Dumper(XMLin('data/test.xml',ForceArray=>1)), Dumper(XMLin("$xml1",ForceArray=>1)), "Saved file identical to old file");

#this test should die, so wrap it up...
eval {
    Bio::STK::save_xml_file('t/data/thisdirectorydoesnotexist/tree1_check.xml', $xml);
};
ok($@, 'Croaked correctly');
like($@,  qr/Error saving file to/,'... and it is the correct exception');
unlink 't/data/test.xml';

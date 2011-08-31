#!/usr/bin/perl -w

use strict;
use warnings;
use Data::Dumper;
use Test::More tests => 3;
use XML::Simple;

use lib 'lib';
use Bio::STK;

my $xml1 = "t/data/test_data/bar_2000/tree1.xml";

is (Dumper(Bio::STK::read_xml_file($xml1)), Dumper(XMLin("$xml1",ForceArray=>1)), "Read in file correctly");

#this test should die, so wrap it up...
eval {
    Bio::STK::read_xml_file('t/data/test_data/nonsense.dat'); 
};
ok($@, 'Croaked correctly');
like($@, qr/Error \- specified XML file does not exist:/, '... and it is the correct exception');

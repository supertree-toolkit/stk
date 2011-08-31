#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 4;

use lib 'lib';
use Bio::STK;

ok (Bio::STK::xml_contains_analysis('mp','t/data/test_data/bar_2000/tree1.xml'),"Found lowercase 'mp'");
ok (Bio::STK::xml_contains_analysis('MP','t/data/test_data/bar_2000/tree1.xml'),"Found upper case 'MP'");

my $xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
ok (Bio::STK::xml_contains_analysis('MP',$xml),"Found data using XML hash");

ok (!Bio::STK::xml_contains_analysis('WE',$xml),"Didn't find spurious analyses");


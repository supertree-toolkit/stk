#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 13;

use lib 'lib';
use Bio::STK;

ok (Bio::STK::xml_contains_character('molecular','t/data/test_data/bar_2000/tree1.xml'),"Found lowercase 'molecular'");
ok (Bio::STK::xml_contains_character('Molecular','t/data/test_data/bar_2000/tree1.xml'),"Found sentence case 'Molecular'");

my $xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
ok (Bio::STK::xml_contains_character('Molecular',$xml),"Found data using XML hash");
ok (Bio::STK::xml_contains_character('Morphological',$xml),"Found morphological data");
ok (!Bio::STK::xml_contains_character('Other',$xml),"Didn't find other data");
ok (Bio::STK::xml_contains_character('feathers',$xml),"Found specific morphological data");
ok (!Bio::STK::xml_contains_character('bones',$xml), "Didn't find 'bones'");
# should return false as there are two types of data
ok(!Bio::STK::xml_contains_character('Molecular',$xml,1),"Correctly restricted data search");

$xml = Bio::STK::read_xml_file('t/data/test_data/Bloggs_1999/tree_5/tree5.xml');
ok (Bio::STK::xml_contains_character('Molecular',$xml,1),"Found exclusive data");
ok (!Bio::STK::xml_contains_character('Other',$xml,1),"Didn't find data when only flag on");

$xml = Bio::STK::read_xml_file('t/data/test_data/Foo_2005/Tree_1/tree6_1.xml');
ok (Bio::STK::xml_contains_character('Plumage',$xml,1),"Found exclusive actual characters");
ok (!Bio::STK::xml_contains_character('Bones',$xml,1),"Didn't find data when only flag on");

# exclusive character type
ok (Bio::STK::xml_contains_character('molecular','t/data/test_data/Bloggs_1999/tree_5/tree5.xml',1),
    "Found 'molecular' in exclusive search");


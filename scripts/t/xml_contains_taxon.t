#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 11;

use lib 'lib';
use Bio::STK;

ok (Bio::STK::xml_contains_taxon('Campylorhamphus falcularius','t/data/test_data/bar_2000/tree1.xml'),"Found standard taxa");
ok (Bio::STK::xml_contains_taxon('Campylorhamphus_falcularius','t/data/test_data/bar_2000/tree1.xml'),"Found taxa with underscore");
ok (!Bio::STK::xml_contains_taxon('Campylorhamphus FALcularius','t/data/test_data/bar_2000/tree1.xml'),"Did not find taxa with incorrect case");
ok (!Bio::STK::xml_contains_taxon('Campylorhamphus falclarius','t/data/test_data/bar_2000/tree1.xml'),"Correctly didn't find taxa");

my $xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
ok (Bio::STK::xml_contains_taxon('Campylorhamphus falcularius',$xml),"Found standard taxa using XML");

ok (Bio::STK::xml_contains_taxon("'Campylorhamphus falcularius'",$xml),"Found taxa with quotes");

$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius',"'a+b'");
ok (Bio::STK::xml_contains_taxon("'a+b'",$xml),"Found taxa with quotes");

# partial matches
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
ok (Bio::STK::xml_contains_taxon("Lepidocolaptes",$xml,1),"Found generic partial match");
ok (Bio::STK::xml_contains_taxon("obsoletus",$xml,1),"Found specific partial match");
ok (!Bio::STK::xml_contains_taxon("fwdfwf",$xml,1),"Didn't find random characters in partial match");
ok (!Bio::STK::xml_contains_taxon("falcularius",$xml,0),"Enforce a full match");

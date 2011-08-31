#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 10;

use lib 'lib';
use Bio::STK;

my $xml1 = "t/data/test_data/Fred_2001/tree_2/tree2.xml";
my $xml2 = "t/data/test_data/Fred_2001/tree_3/tree3.xml";
my $xml3 = "t/data/test_data/Fred_2001/tree_4/tree4.xml";
my $xml4 = "t/data/test_data/Fred_2001/tree_1/tree1.xml";

is (Bio::STK::contains_fossils($xml1), 0, "No fossils");
is (Bio::STK::contains_fossils($xml2), 1, "All fossils");
is (Bio::STK::contains_fossils($xml3), 2, "Some fossils");
is (Bio::STK::contains_fossils($xml4), -1, "Missing fossil data");

# same tests with data
my $xml_data = Bio::STK::read_xml_file($xml1);
is (Bio::STK::contains_fossils($xml_data), 0, "No fossils");
$xml_data = Bio::STK::read_xml_file($xml2);
is (Bio::STK::contains_fossils($xml_data), 1, "All fossils");
$xml_data = Bio::STK::read_xml_file($xml3);
is (Bio::STK::contains_fossils($xml_data), 2, "Some fossils");
$xml_data = Bio::STK::read_xml_file($xml4);
is (Bio::STK::contains_fossils($xml_data), -1, "Missing fossil data");

# crap data
my $data_loaded = Bio::STK::contains_fossils("ThisIsARandomString");
ok(!defined($data_loaded), "Correctly spotted non-xml/non-file");

# really bad data
$data_loaded = Bio::STK::contains_fossils(["ThisIsARandomString"]);
ok(!defined($data_loaded), "Correctly spotted non-xml/non-file");




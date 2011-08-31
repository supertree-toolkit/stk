#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 3;

use lib 'lib';
use Bio::STK;

my $xml1 = "t/data/test_data/bar_2000/tree1.xml";
is(Bio::STK::get_treefile($xml1),'tree1.tre',"Read in tree file location correctly");

my $xml_data = Bio::STK::read_xml_file("t/data/full_source.xml");
is(Bio::STK::get_treefile($xml_data),'tree1.tre',"Read in tree file location correctly from data");

my $tree_loaded = Bio::STK::get_treefile("ThisIsARandomString");
ok(!defined($tree_loaded), "Correctly spotted non-xml/non-file");



#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 4;

use lib 'lib';
use Bio::STK;

my $xml1 = "t/data/test_data/Fred_2001/tree_2/tree2.xml";
my $xml2 = "t/data/test_data/Fred_2001/tree_3/tree3.xml";
my $xml3 = "t/data/test_data/Fred_2001/tree_4/tree4.xml";

is (Bio::STK::get_analysis($xml1), 'Baysian', "File 1");
is (Bio::STK::get_analysis($xml2), 'ML', "File 2");
is (Bio::STK::get_analysis($xml3), 'MP', "File 3");

my $analysis_loaded = Bio::STK::get_analysis("ThisIsARandomString");
ok(!defined($analysis_loaded), "Correctly spotted non-xml/non-file");



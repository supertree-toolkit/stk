#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 13;

use lib 'lib';
use Bio::STK;

my $file = "t/data/test_data/Fred_2001/tree_4/tree4.xml";
my $xml = Bio::STK::read_xml_file($file);

#analyses
ok (Bio::STK::contains_data(['MP'],$file), "Analyses from File");
ok (Bio::STK::contains_data(['MP'],$xml), "Analyses from XML");

#taxa
ok (Bio::STK::contains_data(['Scytalopus parvirostris'],$file), "Taxa from file");
ok (Bio::STK::contains_data(['Scytalopus parvirostris'],$xml), "Taxa from data");

#characters
ok (Bio::STK::contains_data(['cytb'],$file), "Specific characters from file");
ok (Bio::STK::contains_data(['molecular'],$file), "General characters from file");
ok (Bio::STK::contains_data(['cytb'],$xml), "Specific characters from data");
ok (Bio::STK::contains_data(['molecular'],$xml), "General characters from data");

# array versions
my @search = ("MP","Molecular","cytb");
ok (Bio::STK::contains_data(\@search,$file), "Array of data from file");
ok (Bio::STK::contains_data(\@search,$xml), "Array of data from data");

my @neg_search = ("FC", "moles", "fiddlesticks");
ok (!Bio::STK::contains_data(\@neg_search,$file), "Array of data not in XML from file");
ok (!Bio::STK::contains_data(\@neg_search,$xml), "Array of data not in XML from data");

my $data_loaded = Bio::STK::contains_data(["ThisIsARandomString"]);
ok(!defined($data_loaded), "Correctly spotted non-xml/non-file");



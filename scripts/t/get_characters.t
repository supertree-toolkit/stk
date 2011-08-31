#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 9;

use lib 'lib';
use Bio::STK;

my %expected = (Molecular => [ "cytb", "ND2", "ND3" ],
                Morphological => [ "feathers" ],
                );

my $xml1 = "t/data/test_data/bar_2000/tree1.xml";

my %obtained = Bio::STK::get_characters($xml1);

is ($obtained{Molecular}[0], $expected{Molecular}[0], "Characters 1 from file OK");
is ($obtained{Molecular}[1], $expected{Molecular}[1], "Characters 2 from file OK");
is ($obtained{Molecular}[2], $expected{Molecular}[2], "Characters 3 from file OK");
is ($obtained{Morphological}[0], $expected{Morphological}[0], "Characters 4 from file OK");

my $xml_data = Bio::STK::read_xml_file("t/data/test_data/bar_2000/tree1.xml");
%obtained = Bio::STK::get_characters($xml_data);

is ($obtained{Molecular}[0], $expected{Molecular}[0], "Characters 1 from data OK");
is ($obtained{Molecular}[1], $expected{Molecular}[1], "Characters 2 from data OK");
is ($obtained{Molecular}[2], $expected{Molecular}[2], "Characters 3 from data OK");
is ($obtained{Morphological}[0], $expected{Morphological}[0], "Characters 4 OK");

my $characters_loaded = Bio::STK::get_characters("ThisIsARandomString");
ok(!defined($characters_loaded), "Correctly spotted non-xml/non-file");



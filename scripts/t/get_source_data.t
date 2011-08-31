#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 28;

use lib 'lib';
use Bio::STK;

my %expected = (year => '2000',
                volume => '119',
                pages => '621-640',
                journal => 'Auk',
                title => 'Molecular systematics and the role of the "Varzea"-"Terra-firme" ecotone in the diversification of Xiphorhynchus woodcreepers (Aves: Dendrocolaptidae).',
                author => 'Bar, A.',
                editor => 'Editor',
                booktitle => 'A title',
                publisher => 'A publisher',
                );

my $xml1 = "t/data/full_source.xml";
my %obtained = Bio::STK::get_source_data($xml1);

is ($obtained{year}, $expected{year}, "File year OK");
is ($obtained{volume}, $expected{volume}, "File volume OK");
is ($obtained{pages}, $expected{pages}, "File pages OK");
is ($obtained{journal}, $expected{journal}, "File journal OK");
is ($obtained{title}, $expected{title}, "File title OK");
is ($obtained{author}, $expected{author}, "File author OK");
is ($obtained{booktitle},$expected{booktitle} , "File booktitle OK");
is ($obtained{publisher}, $expected{publisher}, "File publisher OK");
is ($obtained{editor}, $expected{editor}, "File editor OK");


# same tests, but with xml hash
my $xml_data = Bio::STK::read_xml_file("t/data/full_source.xml");
%obtained = Bio::STK::get_source_data($xml_data);

is ($obtained{year}, $expected{year}, "Data year OK");
is ($obtained{volume}, $expected{volume}, "Data volume OK");
is ($obtained{pages}, $expected{pages}, "Data pages OK");
is ($obtained{journal}, $expected{journal}, "Data journal OK");
is ($obtained{title}, $expected{title}, "Data title OK");
is ($obtained{author}, $expected{author}, "Data author OK");
is ($obtained{booktitle},$expected{booktitle} , "Data booktitle OK");
is ($obtained{publisher}, $expected{publisher}, "Data publisher OK");
is ($obtained{editor}, $expected{editor}, "Data editor OK");

my $source_loaded = Bio::STK::get_source_data("ThisIsARandomString");
ok(!defined($source_loaded), "Correctly spotted non-xml/non-file");

# run through testing the part empty hashes code
my $xml2 = "t/data/no_source.xml";
%obtained = Bio::STK::get_source_data($xml2);
is ($obtained{year}, undef, "Empty year OK");
is ($obtained{volume}, undef, "Empty volume OK");
is ($obtained{pages}, undef, "Empty pages OK");
is ($obtained{journal}, undef, "Empty journal OK");
is ($obtained{title}, undef, "Empty title OK");
is ($obtained{author}, undef, "Empty author OK");
is ($obtained{booktitle}, undef, "Empty booktitle OK");
is ($obtained{publisher}, undef, "Empty publisher OK");
is ($obtained{editor}, undef, "Empty editor OK");


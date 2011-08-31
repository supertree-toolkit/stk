#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 3;

use lib 'lib';
use Bio::STK;

my @taxa1 = 
('Campylorhamphus falcularius',
'Campylorhamphus procurvoides',
'Campylorhamphus trochilirostris',
'Dendrexetastes rufigula',
'Dendrocolaptes certhia',
'Glyphorynchus spirurus',
'Hylexetastes perrotii',
'Lepidocolaptes albolineatus',
'Lepidocolaptes angustirostris',
'Lepidocolaptes fuscus',
'Nasica longirostris',
'Sittasomus griseicapillus',
'Xiphocolaptes promeropirhynchus',
'Xiphorhynchus erythropygius',
'Xiphorhynchus flavigaster',
'Xiphorhynchus guttatus',
'Xiphorhynchus kienerii',
'Xiphorhynchus lachrymosus',
'Xiphorhynchus obsoletus',
'Xiphorhynchus ocellatus',
'Xiphorhynchus pardalotus',
'Xiphorhynchus picus',
'Xiphorhynchus spixii',
'Xiphorhynchus susurrans',
'Xiphorhynchus triangularis');

my @taxa_loaded = Bio::STK::taxa_from_xml('t/data/test_data/bar_2000/tree1.xml');
ok(compare_arrays(\@taxa_loaded, \@taxa1), "Correct taxa in xml using file");

my $xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
@taxa_loaded = Bio::STK::taxa_from_xml($xml);
ok(compare_arrays(\@taxa_loaded, \@taxa1), "Correct taxa in xml using xml");

undef @taxa_loaded;
@taxa_loaded = Bio::STK::taxa_from_xml("ThisIsARandomString");
ok(!defined($taxa_loaded[0]), "Correctly spotted non-tree/non-file");


sub compare_arrays {
	my ($first, $second) = @_;
	no warnings;  # silence spurious -w undef complaints
	return 0 unless @$first == @$second;
	for (my $i = 0; $i < @$first; $i++) {
	    return 0 if $first->[$i] ne $second->[$i];
	}
	return 1;
} 

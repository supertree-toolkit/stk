#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 13;

use lib 'lib';
use Bio::STK;

# note ORDER of taxa is important - they are added on to the end of the array by the replace
# function, not where the original taxon was
my @list1 = (
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
        'Xiphorhynchus triangularis',
        'replaced taxon',
        );
my @list2 = (
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
        'Xiphorhynchus triangularis',
        );
my @list3 = (
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
        'Xiphorhynchus triangularis',
        'taxon 1',
        'taxon 2',
        'taxon 3',
        );
my @list4 = (
        'Campylorhamphus falcularius',
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
        'Xiphorhynchus triangularis',
        );
               
my @polytomy = ("taxon_1","taxon_2","taxon_3");      
my @list5 = (
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
        'Xiphorhynchus triangularis',
        'a=b',
        );
my @list6 = (
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
        'Xiphorhynchus triangularis',
        'Campylorhamphus falcularius',
        );
my @list7 = (
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
        'Xiphorhynchus triangularis',
        'a+b',
        );
my @list8 = (
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
        'Xiphorhynchus triangularis',
      );

my $xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius','replaced_taxon');
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list1), "Correctly replaced taxon");

$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
my $nTaxa = $xml->{Taxa}->[0]->{number};
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius');
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list2), "Correctly deleted taxon");
# did we change the number?
is ($xml->{Taxa}->[0]->{number}, $nTaxa-1, "Number of taxa altered OK");


$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius',@polytomy);
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list3), "Correctly replaced with polytomy");

# check for case
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'campylorhamphus Falcularius');
ok (!compare_arrays($xml->{Taxa}->[0]->{List}, \@list2), "Didn't delete 'incorrect-cased' taxon");

# check for presence of _
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus_falcularius');
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list2), "Correctly deleted taxon with _ in name");

# check for replacing only full taxon names
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus');
# should *not* replace
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list4), "Didn't replace partial taxon");


# check for duplicated taxa are not swapped in
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius','Campylorhamphus procurvoides');
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list2), "Did not replace with an existing taxon");

# check that a ploytomy containing some duplicated taxa only gets the non-duplicated taxa
push (@polytomy, 'taxon_1');
push (@polytomy, 'Campylorhamphus procurvoides');
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius',@polytomy);
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list3), "Correctly replaced with polytomy, but didn't add duplicats");

# check that incoming taxa that are quoted are dealt with
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius',"'a=b'");
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list5), "Correctly replaced quoted taxa");
Bio::STK::replace_taxon_xml($xml,"'a=b'",'Campylorhamphus falcularius');
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list6), "Correctly replaced quoted taxa");

# quoted taxa with +
$xml = Bio::STK::read_xml_file('t/data/test_data/bar_2000/tree1.xml');
Bio::STK::replace_taxon_xml($xml,'Campylorhamphus falcularius',"'a+b'");
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list7), "Correctly replaced quoted taxa");
Bio::STK::replace_taxon_xml($xml,"'a+b'");
ok (compare_arrays($xml->{Taxa}->[0]->{List}, \@list8), "Correctly replaced quoted taxa");


sub compare_arrays {
	my ($first, $second) = @_;
	no warnings;  # silence spurious -w undef complaints
	return 0 unless @$first == @$second;
	for (my $i = 0; $i < @$first; $i++) {
	    return 0 if $first->[$i] ne $second->[$i];
	}
	return 1;
}  

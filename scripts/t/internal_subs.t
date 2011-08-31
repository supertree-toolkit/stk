#!/usr/bin/perl -w

# These subs are extensively tested using the other tests, but here
# are a few basic tests to ensure 100% coverage and to aid future debugging
# and refactoring

use strict;
use warnings;
use Test::More tests => 19;

use lib 'lib';
use Bio::STK;

# these are crap tests - read_tree_file calls the internal subs how can we use that
# to test they are working!?
# TO DO: call bio::nexus routines directly
my $tree1 = 't/data/tree2.tre';
my @trees = Bio::STK::read_tree_file($tree1);
my $nexus = Bio::STK::_create_nexus_object(\@trees);
my @trees2 = Bio::STK::_get_tree_array($nexus);
ok(compare_arrays(\@trees,\@trees2),"Created nexus object correctly");

$nexus = Bio::STK::_load_nexus($tree1);
@trees = Bio::STK::_get_tree_array($nexus);
ok(compare_arrays(\@trees,\@trees2),"Loaded nexus object correctly");

eval {
    Bio::STK::_load_nexus('t/data/thisdirectorydoesnotexist/tree1_check.tre');
};
ok($@, 'Croaked correctly');
like($@,  qr/Error \- specified tree file does not exist/,'... and it is the correct exception');

my $tree_string = $trees[0];
is(Bio::STK::_file_or_tree($tree_string),1,"Correctly ID tree string");

is(Bio::STK::_file_or_tree($tree1),2,"Correctly ID file");
is(Bio::STK::_file_or_tree('blahblah'),0,"Correctly ID nonsense");
is(Bio::STK::_file_or_tree(undef),0,"Correctly ID undefined variable");
is(Bio::STK::_file_or_tree(['blahblah']),0,"Correctly ID nonsense");
is(Bio::STK::_file_or_tree("(A, B, C, D)"),1,"Correctly ID tree string with spaces");

is(Bio::STK::_file_or_tree("t/data/test_data/bar_2000/tree1.xml"),2,"Correctly ID xml file");
my $xml_data = Bio::STK::read_xml_file("t/data/test_data/bar_2000/tree1.xml");
is(Bio::STK::_file_or_xml($xml_data),1,"Correctly ID xml hash");
my %hash;
$hash{blah} = 'boo!';
is(Bio::STK::_file_or_xml(\%hash),0,"Correctly ID non-xml hash");
$hash{Taxa} = "some";
is(Bio::STK::_file_or_xml(\%hash),0,"Correctly ID non-xml hash with just taxa");
$hash{Source} = "some";
is(Bio::STK::_file_or_xml(\%hash),0,"Correctly ID non-xml hash with just taxa and source");
undef %hash;
$hash{TreeFile} = "some";
is(Bio::STK::_file_or_xml(\%hash),0,"Correctly ID non-xml hash with just treefile");
is(Bio::STK::_file_or_xml('blahblah'),0,"Correctly ID nonsense");
is(Bio::STK::_file_or_xml(undef),0,"Correctly ID undefined variable");
is(Bio::STK::_file_or_xml(['blahblah']),0,"Correctly ID nonsense");


sub compare_arrays {
	my ($first, $second) = @_;
	no warnings;  # silence spurious -w undef complaints
	return 0 unless @$first == @$second;
	for (my $i = 0; $i < @$first; $i++) {
	    return 0 if $first->[$i] ne $second->[$i];
	}
	return 1;
} 

#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 7;

use lib 'lib';
use Bio::STK;

my @taxa1 = ("Catharacta maccormicki","Catharacta chilensis","Catharacta antarctica","Catharacta skua","Stercorarius pomarinus","Stercorarius parasiticus","Stercorarius longicaudus","Larus argentatus");
my @taxa2 = ("A","B","C","D","E","F","G","H");
my @taxa3 = ("A","B","C","D");
my @taxa4 = ("'A=R'","B","C", "D");

my @taxa_loaded = Bio::STK::taxa_from_tree('t/data/tree1.tre');
ok(compare_arrays(\@taxa1, \@taxa_loaded), "Correct taxa loaded");

@taxa_loaded = Bio::STK::taxa_from_tree('t/data/tree2.tre');
ok(compare_arrays(\@taxa3, \@taxa_loaded), "Correct taxa loaded");

@taxa_loaded = Bio::STK::taxa_from_tree('t/data/tree3.tre');
ok(compare_arrays(\@taxa4, \@taxa_loaded), "Correct taxa loaded");

@taxa_loaded = Bio::STK::taxa_from_tree('t/data/trees-multiple.tre');
ok(compare_arrays(\@taxa2, \@taxa_loaded), "Correct taxa loaded");

# test with tree strings
my @trees = Bio::STK::read_tree_file('t/data/tree1.tre');
@taxa_loaded = Bio::STK::taxa_from_tree($trees[0]);
ok(compare_arrays(\@taxa1, \@taxa_loaded), "Correct taxa from tree string");

# checking extra whitespace removed
@taxa_loaded = Bio::STK::taxa_from_tree("(A, B, C, D)");
ok(compare_arrays(\@taxa3, \@taxa_loaded), "Correct taxa from tree string with whitespace");

undef @taxa_loaded;
@taxa_loaded = Bio::STK::taxa_from_tree("ThisIsARandomString");
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

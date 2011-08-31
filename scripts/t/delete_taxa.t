#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 3;

use lib 'lib';
use Bio::STK;

my @original_trees;

$original_trees[0] = "((((Catharacta_maccormicki,Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";

my @input_trees = @original_trees;
my $tree1 = "((((Catharacta_chilensis,Catharacta_antarctica),(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
my $tree2= "(((Catharacta_antarctica,(Catharacta_skua,Stercorarius_pomarinus)),Stercorarius_parasiticus,Stercorarius_longicaudus),Larus_argentatus)";
 
my @to_delete = ("Catharacta_maccormicki","Catharacta_chilensis");
my @to_delete_nounderscores = ("Catharacta maccormicki","Catharacta chilensis");


@input_trees = @original_trees;
Bio::STK::delete_taxa(\@input_trees,['Catharacta_maccormicki']);
is ($input_trees[0], $tree1, "Correctly deleted taxon");

@input_trees = @original_trees;
Bio::STK::delete_taxa(\@input_trees,\@to_delete);
is ($input_trees[0], $tree2, "Correctly deleted taxa");


@input_trees = @original_trees;
Bio::STK::delete_taxa(\@input_trees,\@to_delete_nounderscores);
is ($input_trees[0], $tree2, "Correctly deleted taxa");


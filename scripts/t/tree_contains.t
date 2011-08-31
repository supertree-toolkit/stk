#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 8;

use lib 'lib';
use Bio::STK;

ok (Bio::STK::tree_contains('Catharacta_maccormicki','t/data/tree1.tre'),"Found standard taxa");
ok (Bio::STK::tree_contains('Catharacta maccormicki','t/data/tree1.tre'),"Found taxa with spaces");
ok (!Bio::STK::tree_contains('Catharacta_Maccormicki','t/data/tree1.tre'),"Correctly spotted taxa with incorrect case");
ok (!Bio::STK::tree_contains('Catharacta_mccormicki','t/data/tree1.tre'),"Correctly didn't find taxa");
ok (Bio::STK::tree_contains("'taxa_n=taxa_2'","(taxa1,'taxa_n=taxa_2',taxa3)"), "Found quoted taxa");
ok (!Bio::STK::tree_contains("taxa_2","(taxa1,'taxa_n=taxa_2',taxa3)"), "Didn't find part of quoted taxa");
ok (Bio::STK::tree_contains("'Grouse+Turkeys'","('Grouse+Turkeys',taxa1,taxa2)"),"Found quoted taxa with +");
ok (Bio::STK::tree_contains("sub_species_1","(sub_species_1,taxa1,taxa2)"),"Found quoted taxa with +");


#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 13;

use lib 'lib';
use Bio::STK;

my @old_taxa;
my @new_taxa;
my $second_sub = "Anomalopteryx didiformis,Megalapteryx benhami,Megalapteryx didinus,Pachyornis australis,Pachyornis elephantopus,Pachyornis mappini,Euryapteryx curtus,Euryapteryx geranoides,Emeus crassus,Dinornis giganteus,Dinornis novaezealandiae";
my $edge1 = "taxa2,taxa3,taxa2,taxa4";
my $edge2 = "taxa11,'taxa12=taxa13','taxa14+taxa15'";
my $edge3 = "some_thing";
my $edge2In = "'taxa9+taxa10'";
my $edge4In = "'already=quoted'";
my $bad2 = "taxa5,taxa6";
my $edge4 =  "taxa3,taxa6,taxa4,taxa5";

Bio::STK::read_taxa_file('t/data/read_taxa_file/subs1.txt', \@old_taxa, \@new_taxa);
is ($old_taxa[0], "MRPoutgroup", "Read empty sub");
is ($new_taxa[1], $second_sub, "Read new taxa standard sub");

undef @old_taxa;
undef @new_taxa;

Bio::STK::read_taxa_file('t/data/read_taxa_file/subs_edge.txt', \@old_taxa, \@new_taxa);
is ($old_taxa[1], $edge2In, "Read old taxa with +");
is ($old_taxa[3], $edge4In, "Read old taxa with = and already quoted");
is ($new_taxa[0], $edge1, "Read new taxa with spaces");
is ($new_taxa[1], $edge2, "Read new taxa with + and =");
is ($new_taxa[2], $edge3, "Read line with tabs not spaces");
is ($new_taxa[4], $edge4, "Read wrapped line with terminating comma OK");
is ($new_taxa[5], $edge4, "Read wrapped line without terminating comma OK");
is ($new_taxa[6], $edge4, "Read wrapped line with comma on next line OK");

#this test should die, so wrap it up...
eval {
    Bio::STK::read_taxa_file('t/data/test_data/nonsense.dat'); 
};
ok($@, 'Croaked correctly');
like($@, qr/Read_Taxa_File: Can't read file/, '... and it is the correct exception');

undef @old_taxa;
undef @new_taxa;

# crap file, contains mistakes
Bio::STK::read_taxa_file('t/data/read_taxa_file/bad_subs.txt', \@old_taxa, \@new_taxa);
is ($new_taxa[1], $bad2, "Read dodgy file ok");




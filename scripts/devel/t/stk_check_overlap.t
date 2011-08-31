#!/usr/bin/perl -w

use strict;
use Test::More tests => 6;
use File::Compare qw(compare_text);
use File::Copy;

chdir ('../../exec');
my $output = `perl stk_check_overlap.pl --dir ../devel/test_dataset/standard --graphic`;
$output = `perl stk_check_overlap.pl --dir ../devel/test_dataset/standard --nCluster=3 --graphic`;

# move output to correct dir...
move("../devel/test_dataset/standard/key.csv","../devel/t/data/check_overlap/key.csv") or die ("Couldn't copy key");
move("../devel/test_dataset/standard/tree2.dot","../devel/t/data/check_overlap/tree2.dot") or die ("Couldn't copy tree2.dor");
move("../devel/test_dataset/standard/tree3.dot","../devel/t/data/check_overlap/tree3.dot") or die ("Couldn't copy tree3.dot");

# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//;
    }
    return $line;
}


ok ( compare_text("../devel/t/data/check_overlap/key.csv","../devel/t/correct/check_overlap/key.csv",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Key OK');
ok ( compare_text("../devel/t/data/check_overlap/tree2.dot","../devel/t/correct/check_overlap/tree2.dot",sub {munge $_[0] ne munge $_[1]} ) == 0, 'tree2.dot ok');
ok ( compare_text("../devel/t/data/check_overlap/tree3.dot","../devel/t/correct/check_overlap/tree3.dot",sub {munge $_[0] ne munge $_[1]} ) == 0, 'tree3.dot ok');

# check non-graphical output
$output = `perl stk_check_overlap.pl --dir ../devel/test_dataset/standard > ../devel/t/data/check_overlap/standard_out.txt`;
ok ( compare_text("../devel/t/data/check_overlap/standard_out.txt","../devel/t/correct/check_overlap/standard_out.txt",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Non graphical output ok');


# check compressed graphical output
$output = `perl stk_check_overlap.pl --dir ../devel/test_dataset/standard --graphic --compressed`;
move("../devel/test_dataset/standard/key-compressed.csv","../devel/t/data/check_overlap/key-compressed.csv") or die ("Couldn't copy key");
move("../devel/test_dataset/standard/tree2-compressed.dot","../devel/t/data/check_overlap/tree2-compressed.dot") or die ("Couldn't copy tree2.dor");
ok ( compare_text("../devel/t/data/check_overlap/tree2-compressed.dot","../devel/t/correct/check_overlap/tree2-compressed.dot",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Compressed dot file ok');
# checking the key file is more tricky as the order in which files appear is non-deterministic, depending
# on how Graph traverses the tree. Instead let's check that the files that should be in the same 
# cluster are in the same cluster
# Construct a hash of tree files and the cluster they should be in:
my %correct_cluster = (
    '../devel/test_dataset/standard/Allende_etal_2001/Allende_etal_2001com.tre' => 0,
    '../devel/test_dataset/standard/Aleixo_2002/Aleixo2002com.tre' => 1,
    '../devel/test_dataset/standard/Baptista_etal_1999/Tree 1/Baptista_etal_1999_corr.tre' =>2,
    '../devel/test_dataset/standard/Baker_etal_2005/Baker_etal_2005com.tre' => 3,
    '../devel/test_dataset/standard/Aliabadian_etal_2007/Tree 2/Aliabadian_etal_2007_2_corr.tre' => 4,
    '../devel/test_dataset/standard/Aliabadian_etal_2007/Tree 1/Aliabadian_etal_2007_1_corr.tre' => 4,
    '../devel/test_dataset/standard/Barber_etal_2004/Tree 1/Barber_etal_2004_corr.tre' => 5,
    '../devel/test_dataset/standard/Aragon_etal_1999/Aragon_etal_1999com1_2.tre' => 6,
    '../devel/test_dataset/standard/Aragon_etal_1999/Tree 3/Aragon_etal_1999_3_corr.tre' =>6,
    '../devel/test_dataset/standard/Baker_etal_2007b/Tree 1/Baker_etal_2007b_corr.tre'=>7,
    '../devel/test_dataset/standard/Andersson_1999b/Tree 1/Andersson_1999b_1_corr.tre'=>7,
    '../devel/test_dataset/standard/Andersson_1999b/Tree 2/Andersson_1999b_2_corr.tre'=>7,
    '../devel/test_dataset/standard/Andersson_1999a/Tree 1/Andersson_1999a_corr.tre'=>7,
    '../devel/test_dataset/standard/Baker_Strauch_1988/Tree 1/Baker_Strauch_1988_corr.tre'=>7,
    '../devel/test_dataset/standard/Baker_etal_2007a/Tree 1/Baker_etal_2007a_corr.tre'=>7,
    '../devel/test_dataset/standard/Baker_etal_2006/Tree 1/Baker_etal_2006_corr.tre'=>8,
    '../devel/test_dataset/standard/Bertelli_etal_2006/Tree 2/Bertelli_etal_2006_2_corr.tre'=>8,
    '../devel/test_dataset/standard/Bertelli_etal_2006/Tree 3/Bertelli_etal_2006_3_corr.tre'=>8,
    '../devel/test_dataset/standard/Bertelli_etal_2006/Tree 1/Bertelli_etal_2006_1_corr.tre'=>8,
    '../devel/test_dataset/standard/Barhoum_Burns_2002/Tree 1/Barhoum_Burns_2002_corr.tre'=>9
);
open DATA, "../devel/t/data/check_overlap/key-compressed.csv";
my %current_answer;
while( <DATA> ) {
    my @elements = split /,/, $_;
    if($elements[0] !~ m/Node number/i) {
        chomp $elements[1];
        $current_answer{ $elements[1] } = $elements[0];
    }
}
close DATA;
# now compare hashes
ok (eq_hash(\%current_answer, \%correct_cluster), "Obtain correct clustering");

unlink("../devel/t/data/check_overlap/tree2.dot");
unlink("../devel/t/data/check_overlap/tree3.dot");
unlink("../devel/t/data/check_overlap/key.csv");
unlink("../devel/t/data/check_overlap/tree2-compressed.dot");
unlink("../devel/t/data/check_overlap/standard_out.txt");
unlink("../devel/t/data/check_overlap/key-compressed.csv")

#!/usr/bin/perl -w

use strict;
use Test::More tests => 18;
use File::Compare qw(compare_text);
use File::Copy;
use File::Copy::Recursive qw(dircopy);
use File::Remove qw(remove);

chdir ('../../exec');
# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}

# copy data
dircopy("../devel/test_dataset/standard/","../devel/t/data/replace_taxa/standard") 
    or die ("Couldn't copy data");
copy("../devel/t/data/replace_taxa/tree1.tre","../devel/t/data/replace_taxa/temp.tre") 
    or die ("Couldn't copy tree1.tre");

# check OK with file
my $output = `perl stk_replace_taxa.pl --file ../devel/t/data/replace_taxa/temp.tre --old Xiphocolaptes_promeropirhynchus --new replaced_taxon`;
ok ( compare_text("../devel/t/data/replace_taxa/temp.tre","../devel/t/correct/replace_taxa/temp.tre", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Replaced in file OK');

# check OK with dir
$output = `perl stk_replace_taxa.pl --dir ../devel/t/data/replace_taxa/standard --old Xiphocolaptes_promeropirhynchus --new replaced_taxon`;
$output = `perl stk_data_summary.pl --dir ../devel/t/data/replace_taxa/standard`;
# check that the taxa have gone!
unlike( $output, qr/Xiphocolaptes promeropirhynchus/ , 'Xiphocolaptes promeropirhynchus not there');
like( $output, qr/replaced taxon/ , 'replaced taxon is there');

unlink("../devel/t/data/replace_taxa/temp.tre");

# checking quoted taxa are subbed OK
copy("../devel/t/data/replace_taxa/tree2.tre","../devel/t/data/replace_taxa/temp.tre") 
    or die ("Couldn't copy tree2.tre");
$output = `perl stk_replace_taxa.pl --file ../devel/t/data/replace_taxa/temp.tre --taxa ../devel/t/data/replace_taxa/taxa.txt`;
ok ( compare_text("../devel/t/data/replace_taxa/temp.tre","../devel/t/correct/replace_taxa/tree2.tre", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Replaced in file OK');

# clean up
remove \1, "../devel/t/data/replace_taxa/standard/";
unlink("../devel/t/data/replace_taxa/temp.tre");

# special_cases/tree_replace_bug
# On creating the Mesozoic birds dataset, one tree was not getting old, quoted, taxa substituted when the replacement
# was already in the tree. The XML file works properly, so the check is simply to compare the two taxa lists
dircopy("../devel/test_dataset/special_cases/tree_replace_bug/data","../devel/test_dataset/special_cases/tree_replace_bug/test") 
    or die ("Couldn't copy data");
$output =`perl stk_replace_taxa.pl --dir ../devel/test_dataset/special_cases/tree_replace_bug/test/ --taxa ../devel/test_dataset/special_cases/tree_replace_bug/test/subs.txt`;
$output = `perl stk_check_data.pl --dir ../devel/test_dataset/special_cases/tree_replace_bug/test`;
like ( $output, qr/Checks finished...Found 0 errors/, "No errors found");
# clean up
remove \1, "../devel/test_dataset/special_cases/tree_replace_bug/test";

# special_cases/bug1
# This bug presented when using a taxa subs file which contained taxa like x=y in the replacement
# list. These were unquoted. Several routines needed tweaking (and tests added to the library test suite)
# before it was finally fixed. The error was easily picked up with check_data, so we're going to do the
# replcement as reported and then check_data - we should get no errors
dircopy("../devel/test_dataset/special_cases/bug1/data/","../devel/test_dataset/special_cases/bug1/test") 
    or die ("Couldn't copy data");
$output =`perl stk_replace_taxa.pl --dir ../devel/test_dataset/special_cases/bug1/test/ --taxa ../devel/test_dataset/special_cases/bug1/subs1.txt`;
$output = `perl stk_data_summary.pl --dir ../devel/test_dataset/special_cases/bug1/test`;
# check that the taxa have gone!
unlike( $output, qr/Neornithes/ , 'Neornithes not there');
unlike( $output, qr/Enantiornithes/ , 'Enantiornithes not there');

like( $output, qr/'Pelecanoididae=Procellariidae'/ , 'Quoted taxon (=) is there');
like( $output, qr/'Eurostopodidae\+Steatornithidae'/ , 'Quoted taxon (+) is there');

$output = `perl stk_check_data.pl --dir ../devel/test_dataset/special_cases/bug1/test`;
like ( $output, qr/Checks finished...Found 0 errors/, "No errors found");

# doing the same for subs2, which contains quoted taxa as "old_taxa"
$output =`perl stk_replace_taxa.pl --dir ../devel/test_dataset/special_cases/bug1/test/ --taxa ../devel/test_dataset/special_cases/bug1/subs2.txt`;
$output = `perl stk_data_summary.pl --dir ../devel/test_dataset/special_cases/bug1/test`;
# check that the taxa have gone!
unlike( $output, qr/Cathartidae=Ciconiidae/ , 'Cathartidae=Ciconiidae not there');
unlike( $output, qr/Balaenicipitidae/ , 'Balaenicipitidae not there');

$output = `perl stk_check_data.pl --dir ../devel/test_dataset/special_cases/bug1/test`;
like ( $output, qr/Checks finished...Found 0 errors/, "No errors found");


remove \1, "../devel/test_dataset/special_cases/bug1/test/";

# special_cases/bug6
# This bug presented in a single tree: some subs were not carried out, but check_data reported far fewer
# taxa in the tree than were there (76 vs 475). How, why and wtf!
# Turns out, this substitution resulted in an errant node that had the name "0". This was being added
# to the tree as :0, which was in turn messing up the tree_contains and taxa_from_tree functions
dircopy("../devel/test_dataset/special_cases/bug6/data/","../devel/test_dataset/special_cases/bug6/test") 
    or die ("Couldn't copy data");
$output =`perl stk_replace_taxa.pl --dir ../devel/test_dataset/special_cases/bug6/test/ --taxa ../devel/test_dataset/special_cases/bug6/subs4.txt`;
$output = `perl stk_data_summary.pl --dir ../devel/test_dataset/special_cases/bug6/test`;

# this is the taxa that was failed to be replaced in the tree file
unlike( $output, qr/Mesitornithidae/ , 'Mesitornithidae not there');
like( $output, qr/Mesitornis/ , 'Mesitornis is there');

$output = `perl stk_check_data.pl --dir ../devel/test_dataset/special_cases/bug6/test`;
like ( $output, qr/Checks finished...Found 0 errors/, "No errors found");

remove \1, "../devel/test_dataset/special_cases/bug6/test/";

# special_cases/subspecies
dircopy("../devel/test_dataset/special_cases/sub_species/data","../devel/test_dataset/special_cases/sub_species/test") 
    or die ("Couldn't copy data");
$output =`perl stk_replace_taxa.pl --dir ../devel/test_dataset/special_cases/sub_species/test/ --taxa ../devel/test_dataset/special_cases/sub_species/test/NameSubs.txt`;
$output = `perl stk_data_summary.pl --dir ../devel/test_dataset/special_cases/sub_species/test`;

# this is the taxa that was failed to be replaced in the tree file
unlike( $output, qr/Bleda_notatus_ugandae/ , 'Sub species is gone');

$output = `perl stk_check_data.pl --dir ../devel/test_dataset/special_cases/sub_species/test`;
like ( $output, qr/Checks finished...Found 0 errors/, "No errors found");

remove \1, "../devel/test_dataset/special_cases/sub_species/test/";

#!/usr/bin/perl -w

use strict;
use Test::More tests => 7;
use File::Compare;
use File::Copy;
use File::Copy::Recursive qw(dircopy);
use File::Remove qw(remove);

chdir ('../../exec');

dircopy("../devel/test_dataset/standard/","../devel/t/data/clean_data/standard") 
    or die ("Couldn't copy data");
my $output = `perl stk_clean_data.pl --dir ../devel/t/data/clean_data/standard -v`;
# some output? There should be...
ok ( defined($output), 'Got output OK' );
like ( $output, qr/Should have deleted 0 files in total/ , 'Deleted no files from a standard dataset');

dircopy("../devel/test_dataset/tree_only/","../devel/t/data/clean_data/tree_only") 
    or die ("Couldn't copy data");
$output = `perl stk_clean_data.pl --dir ../devel/t/data/clean_data/tree_only -v`;
# some output? There should be...
ok ( defined($output), 'Got output OK' );
like ( $output, qr/No XML files found - did you specify the correct directory/ , 'Correct error on tree only dataset');
# clean up
remove \1, "../devel/t/data/clean_data/tree_only/";

dircopy("../devel/test_dataset/special_cases/not_enough_taxa","../devel/t/data/clean_data/standard/not_enough_taxa") 
    or die ("Couldn't copy test data");
# Need to remove the .svn directory from our dataset
remove \1, "../devel/t/data/clean_data/standard/not_enough_taxa/.svn";
remove \1, "../devel/t/data/clean_data/standard/not_enough_taxa/Tree 1/.svn";
$output = `perl stk_clean_data.pl --dir ../devel/t/data/clean_data/standard -v`;
# some output? There should be...
ok ( defined($output), 'Got output OK' );
like ( $output, qr/Should have deleted 3 files in total/ , 'Deleted files from a standard dataset');
opendir(DIR, "../devel/t/data/clean_data/standard/") or die $!;
my $bad_dir = "not_enough_taxa";
my $got_it = 0;
while (my $file = readdir(DIR)) {
    if ($file =~ m|$bad_dir|) {
        $got_it = 1;
        last;
    }
    $got_it = 0;
}
ok ($got_it eq 0, "Didn't find directory with too few taxa");
remove \1, "../devel/t/data/clean_data/standard/";


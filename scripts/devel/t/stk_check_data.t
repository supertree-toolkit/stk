#!/usr/bin/perl -w

use strict;
use Test::More tests => 12;
use File::Compare;
use File::Copy;

chdir ('../../exec');
my $output = `perl stk_check_data.pl --dir ../devel/test_dataset/standard -v`;

# some output? There should be...
ok ( defined($output), 'Got output OK' );
like ( $output, qr/Checks finished...Found 0 errors/ , 'Output fromstandard dataset OK');
like ($output, qr/There were 20 tree files and 20 XML files checked/, "Correct number of files checked");


$output = `perl stk_check_data.pl --dir ../devel/test_dataset/tree_only -v`;

# some output? There should be...
ok ( defined($output), 'Got output OK' );

like ( $output, qr/Checks finished...Found 0 errors/ , 'Output from trees only OK');

# check for special cases
#
# duplicate taxa
$output = `perl stk_check_data.pl --dir ../devel/test_dataset/special_cases/Duplicate_taxa -v`;
ok ( defined($output), 'Got output OK' );

like ( $output, qr/tre\s*Duplicate taxon: / , 'Duplicate taxon found in tree file');

like ( $output, qr/xml\s*Duplicate taxon: / , 'Duplicate taxon found in XML file');

# invalid nexus file
$output = `perl stk_check_data.pl --dir ../devel/t/data/check_data/ -v`;
like ( $output, qr/Error with parsing/ , 'Incorrectly written NEXUS file flagged');
# above also contains a TNT file
like ( $output, qr/File contains TNT formatting error/ , 'Incorrectly written TNT file flagged');

# check the right number of trees are printed for an "empty" dir
$output = `perl stk_check_data.pl --dir ../devel/t/data/check_data/empty -v`;
like ( $output, qr/There were 0 tree files and 0 XML files checked/ , 'Empty directory check ok');
like ($output, qr/No tree or XML files found/, "Error message displayed");



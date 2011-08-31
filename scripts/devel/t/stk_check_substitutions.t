#!/usr/bin/perl -w

use strict;
use Test::More tests => 4;
use File::Compare qw(compare_text);

chdir ('../../exec');
my $output = `perl stk_check_substitutions.pl --file ../devel/t/data/check_substitutions/subs_test.txt --output ../devel/t/data/check_substitutions/output.txt`;

# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}
ok ( compare_text("../devel/t/data/check_substitutions/output.txt","../devel/t/correct/check_substitutions/output.txt",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Subs file summary OK');

$output = `perl stk_check_substitutions.pl --file ../devel/test_dataset/special_cases/Duplicate_taxa/subs_dup.txt --output ../devel/t/data/check_substitutions/output.txt`;
ok ( compare_text("../devel/t/data/check_substitutions/output.txt","../devel/t/correct/check_substitutions/dup_subs.txt",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Found duplicate taxa ok');

$output = `perl stk_check_substitutions.pl --file ../devel/test_dataset/special_cases/Duplicate_taxa/subs_dup.txt`;

like ( $output,qr/Found duplicate taxa being substituted in taxa1: taxa2/, 'Found duplicate taxa ok');

$output = `perl stk_check_substitutions.pl --file ../devel/t/data/check_substitutions/subs_test.txt --output`;
# check the output file is there
ok (-e "../devel/t/data/check_substitutions/checks.txt", "Found check.txt when output specified");

unlink("../devel/t/data/check_substitutions/checks.txt");
unlink("../devel/t/data/check_substitutions/output.txt");

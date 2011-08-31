#!/usr/bin/perl -w

use strict;
use Test::More tests => 8;
use File::Compare qw(compare_text);
use File::Copy;
use File::Copy::Recursive qw(dircopy);
use File::Remove qw(remove);


chdir ('../../exec');
dircopy("../devel/test_dataset/standard/","../devel/t/data/replace_genera/standard") 
    or die ("Couldn't copy data");

my $output = `perl stk_replace_genera.pl --dir ../devel/t/data/replace_genera/standard --output ../devel/t/data/replace_genera/subs.txt`;
# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}

ok ( compare_text("../devel/t/data/replace_genera/subs.txt","../devel/t/correct/replace_genera/subs.txt", sub { munge $_[0] ne munge $_[1] } ) == 0, 'Generated subs file OK');


$output = `perl stk_replace_genera.pl --dir ../devel/t/data/replace_genera/standard`;

$output = `perl stk_replace_genera.pl --dir ../devel/t/data/replace_genera/standard --higher`;
# check that the generic taxa have gone!
unlike( $output, qr/Gallus/ , 'Gallus not there');
unlike( $output, qr/Larus/ , 'Larus not there');
unlike( $output, qr/Struthio/ , 'Struthio not there');

$output = `perl stk_check_data.pl --dir ../devel/t/data/replace_genera/standard`;
# some output? There should be...
ok ( defined($output), 'Got output from data check OK' );
like ( $output, qr/Checks finished...Found 0 errors/ , 'Data checked out ok');


# this is a subtle bug introduced by allowing partial matches in XML searches,
# in particular xml_contains_taxa. If we have a generic replacement then the xml 
# gets replaced if it contains a specific taxa of the same genus, even if the
# genus does not occur at generic level. This is not what we want.
# This is really a test of the xml_contains_taxa subroutine, but this is how it shows up
# so we use the above subs file, and run the replace_taxa script on the folder
dircopy("../devel/test_dataset/special_cases/generic/data","../devel/test_dataset/special_cases/generic/test") 
    or die ("Couldn't copy data");
$output = `perl stk_replace_taxa.pl --dir ../devel/test_dataset/special_cases/generic/test --taxa ../devel/t/data/replace_genera/subs.txt`;
$output = `perl stk_check_data.pl --dir ../devel/test_dataset/special_cases/generic/test`;
ok ( defined($output), 'Got output from data check OK' );
like ( $output, qr/Checks finished...Found 0 errors/ , 'Data checked out ok');

remove \1, "../devel/t/data/replace_genera/standard/";
remove \1, "../devel/test_dataset/special_cases/generic/test/";
unlink("../devel/t/data/replace_genera/subs.txt");

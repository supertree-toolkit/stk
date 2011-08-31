#!/usr/bin/perl -w

use strict;
use Test::More tests => 13;
use File::Compare;
use File::Path qw(make_path remove_tree);

chdir ('../../exec');
# create a scratch space
make_path("../devel/t/data/create_directories/tmp/");
my $output = `perl stk_create_dirs.pl --dir ../devel/t/data/create_directories/tmp --bib ../devel/test_dataset/standard/refs.bib -v`;

# some output? There should be...
ok ( defined($output), 'Got output OK' );
like ( $output, qr/Created 15 directories and XML files/ , 'Output from standard dataset OK');
unlike ($output , qr/Error/, 'No errors produced');

# Check that the XML files contain titles and such like
# We can use the check_data script, but ignore the missing tree file
# error - we know there aren't any
$output = `perl stk_check_data.pl --dir ../devel/t/data/create_directories/tmp`;
unlike ($output , qr/Missing author data/, 'All XML contained authors');
unlike ($output , qr/Missing year data/, 'All XML contained years');
unlike ($output , qr/Missing a title/, 'All XML contained titles');

# Now let's check a single XML more thouroughly. It should be well-formed
# and contain the data we think it does. We'll pick one of the files
# that should have had a letter appended to is, just to make sure
# Also added more latex into this reference to check things
my $raw_data;
{
local $/;
my $data_file="../devel/t/data/create_directories/tmp/andersson_1999a/andersson_1999a.xml";
open(DAT, $data_file) || die("Could not open file!");
$raw_data=<DAT>;
close(DAT);
}
like ($raw_data, qr/\<Author\>Andersson, M.\<\/Author\>/, "Correct author");
like ($raw_data, qr/\<Title\>Hybridisation and skua phylogeny.\<\/Title\>/, "Correct title");
like ($raw_data, qr/\<Journal\>Proceedings of the Royal Society of London B\<\/Journal\>/, "Correct journal");
like ($raw_data, qr/\<Author\>Andersson, M.\<\/Author\>/, "Correct author");
like ($raw_data, qr/\<Pages>1579-1585\<\/Pages\>/,"Correct pages");
like ($raw_data, qr/\<Volume>266\<\/Volume\>/,"Correct volume");
like ($raw_data, qr/\<Year\>1999\<\/Year\>/,"Correct year");

# clean up
# Rather than delete each directory by hand, clear the folder
remove_tree('../devel/t/data/create_directories/tmp' );


#!/usr/bin/perl -w

use strict;
use Test::More tests => 2;
use File::Compare qw(compare_text);
use File::Copy;

chdir ('../../exec');
# sub for comparing files ignoring line returns and leading/trailing whitespace
sub munge($) {
    my $line = $_[0];
    for ($line) {
        $line =~ s/\r//; 
    }
    return $line;
}

# fix treeview file
copy("../devel/t/data/fix_treefiles/tree1.tre","../devel/t/data/fix_treefiles/temp.tre") 
    or die ("Couldn't copy tree1.tre");
my $output = `perl stk_fix_treefiles.pl --file ../devel/t/data/fix_treefiles/temp.tre`;
ok ( compare_text("../devel/t/data/fix_treefiles/temp.tre","../devel/t/correct/fix_treefiles/temp.tre",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Fixing treeview file');
unlink("../devel/t/data/fix_treefiles/temp.tre");

# fix TNT file
copy("../devel/t/data/fix_treefiles/tnt.tre","../devel/t/data/fix_treefiles/temp.tre") 
    or die ("Couldn't copy tnt.tre");
$output = `perl stk_fix_treefiles.pl --file ../devel/t/data/fix_treefiles/temp.tre`;
ok ( compare_text("../devel/t/data/fix_treefiles/temp.tre","../devel/t/correct/fix_treefiles/tnt.tre",sub {munge $_[0] ne munge $_[1]} ) == 0, 'Fixing TNT file');
unlink("../devel/t/data/fix_treefiles/temp.tre");


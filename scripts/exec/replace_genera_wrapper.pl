#!/usr/bin/perl w

use Getopt::Long;
use lib "../lib";
use Bio::STK;
use strict;

# get args
my $dir         = '';

# standard help messages
my $man  = '';
my $help = '';
my $verbose = '';
my $gen_taxa = '';

## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    verbose    => \$verbose,
    'dir=s'    => \$dir,
    'taxa=s'   => \$gen_taxa,
);

# check if directory exists
unless ( -d $dir ) {
    die("Error - specified directory does not exist: $dir\n");
}

my @treefiles = Bio::STK::find_tree_files($dir);
my @xmlfiles  = Bio::STK::find_xml_files($dir);

foreach my $file (@treefiles) {
    print("\t$file...\n") if $verbose;
    my @args = ("/usr/bin/perl", "stk_replace_taxa.pl", "\-\-file", $file, "\-\-taxa", $gen_taxa);
    system(@args);
}

foreach my $file (@xmlfiles) {
    print("\t$file...\n") if $verbose;
    my @args = ("/usr/bin/perl", "stk_replace_taxa.pl", "\-\-file", $file, "\-\-taxa", $gen_taxa);
    system(@args);
}

print "Done!\n";


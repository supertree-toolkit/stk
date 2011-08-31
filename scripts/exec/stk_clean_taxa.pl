#!/usr/bin/perl -w
#
#    STK - Perl tools to help process data for Supertree construction
#    Copyright (C) 2009, Jon Hill and Katie Davis. All rights reserved.
#    Email: jon.hill@imperial.ac.uk or k.davis@udcf.gla.ac.uk
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

use Getopt::Long;
use File::Spec::Functions;
use File::Basename;
use Pod::Usage;
use lib "../lib";
use Bio::STK;
use strict;

# get args
my $dir = '';

# standard help messages
my $man     = 0;
my $help    = 0;
my $verbose = '';
my $output  = 0;
my $taxa_file = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'      => \$help,
    man           => \$man,
    verbose       => \$verbose,
    'output:s'    => \$output,
    'file:s'      => \$taxa_file,
    'dir=s'       => \$dir
) or pod2usage(2);
pod2usage(2) if $help;
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}

if ( $output ne 0 ) {
    if ( $output eq '' ) {
        $output = File::Spec->catfile( $dir, "error.txt" );
    }
    open STDOUT, ">$output";
}


# grab all tree files
my @tree_files = Bio::STK::find_tree_files($dir);
my $nTRE       = @tree_files;
my %tree_cache;
# cache taxa
foreach my $file (@tree_files){
    my @trees = Bio::STK::read_tree_file($file)
    $tree_cache{$file} = $tree[0];
}

my @taxa;
if ($taxa_list = '') {
    # read taxa list file - one taxa per line
    @taxa = Bio::STK::get_taxa_list($dir); 
} else {
    open TAXALIST, "<$file";
    foreach $line (<TAXAFILE>) {
        chomp($line);              # remove the newline from $line.
        $line =~ s/ /_/;
        push @taxa, $line;
    }
}


open FILE, ">taxa_data.csv";
# print headers
print FILE "Name,Number of trees,% trees,Number in Polytomy,% polytomy, Diff\n";

# loop over taxa list and report number found
foreach my $taxon (@taxa) {

    my $nFound = 0;
    my $nPolytomies = 0;
    $taxon =~ s/ /_/;
    foreach my $file (@tree_files){
        my $tree = $tree_cache{$file};
        if ( $tree =~ m/$taxon/ ) {
            $nFound++;
        }
        # assumption that each tree file contains one tree
        if ( Bio::STK::in_polytomy($taxon, $tree)) {
            $nPolytomies++;
        }
    }
    my $percentTrees = $nFound/$nTRE * 100.0;
    my $percentagePolytomies = $nPolytomies/$nFound * 100.0;
    my $diff = $nFound - $nPolytomies;
    print FILE "$taxon,$nFound,$percentTrees,$nPolytomies,$percentagePolytomies,$diff\n";
    print "$taxon,$nFound,$percentTrees,$nPolytomies,$percentagePolytomies,$diff\n";
}

close FILE;

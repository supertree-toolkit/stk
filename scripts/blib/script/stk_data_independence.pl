#!/usr/bin/perl -w

eval 'exec /usr/bin/perl -w -S $0 ${1+"$@"}'
    if 0; # not running under some shell
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

=head1 Data Independence



=head1 SYNOPSIS

data_independence.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing XML files. Required
   --verbose         print verbose messages

=head1 OPTIONS 

=over 4

=item B<--dir>

a directory which contains XML files. B<Required>.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Data Independence> checks that source data do not actually contain the same data - that is they are
independent of each other. For supertree construction, the source data must be independent, which for
current protocols means that they cannot contain the same taxa (or subset
of taxa) and not use the same data for the analysis. This script checks the taxonomic overlap of each study
with every other study and if the taxa are the same (or one source set in wholly contained
within another) checks the original source data. If these are the same, the two source
studies are flagged as being potentially non-independent. 

Output is a Tab-delimited file which contains the potential non-independencies. This can be loaded into
Excel or similar. The data is grouped by the type of character used. The final column contains the 
treefile for each XML file, followed by any potential dependent trees. 

This script requires XML files to function - no XML, no checks.

=head1 REQUIRES

Perl 5.004, Bio::STK::*, Getopt::Long; File::Spec::Functions;

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

use Getopt::Long;
use File::Spec::Functions;
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
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?' => \$help,
    man      => \$man,
    verbose  => \$verbose,
    'dir=s'  => \$dir
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}

# some general vars
my @characters;
my @taxa;

print("Scanning $dir...\n");

my @files = Bio::STK::find_xml_files($dir);

if ( @files == 0 ) {
    print("Did not find any XML files in $dir. Exiting.\n");
    exit;
}

# create a 2D array of data
my @all_data;
my @temp;

foreach my $file (@files) {

    print("Processing $file...\n") if $verbose;

    # Get and store characters
    my %c = Bio::STK::get_characters($file);

    # sort characters, such that we can compare later
    my @chars;
    while ( my ( $key, $value ) = each(%c) ) {

        # remember that each value is an array
        push( @chars, @{$value} );
    }

    # create a : seperated string for storage
    my $char_string = $chars[0] . ":";
    for ( my $k = 1; $k < @chars; $k++ ) {
        $char_string = $char_string . $chars[$k] . ":";
    }
    print("\tProcessed characters\n") if $verbose;

    # get and store taxa (from XML)
    my @t = Bio::STK::taxa_from_xml($file);

    # sort taxa, such that we can compare later
    @t = sort @t;
    my $taxa_string = $t[0] . ":";
    for ( my $k = 1; $k < @t; $k++ ) {
        $taxa_string = $taxa_string . $t[$k] . ":";
    }
    print("\tProcessed taxa\n") if $verbose;

    # get and store source data
    my %source_data = Bio::STK::get_source_data($file);

    undef @temp;
    $temp[0] = $source_data{'author'};
    $temp[1] = $source_data{'year'};

    # might be a book or journal
    if ( $source_data{'title'} ne '' ) {
        $temp[2] = $source_data{'title'};
    }
    elsif ( $source_data{'booktitle'} ne '' ) {
        $temp[2] = $source_data{'booktitle'};
    }
    else {
        $temp[2] = 'No title';
    }
    $temp[3]  = $source_data{'journal'};
    $temp[4]  = $source_data{'volume'};
    $temp[5]  = $source_data{'pages'};
    $temp[6]  = $char_string;
    $temp[7]  = Bio::STK::get_analysis($file);
    $temp[8]  = $taxa_string;
    $temp[9]  = $file;
    $temp[10] = "";

    print("\tProcessed source information\n") if $verbose;

    push @all_data, [@temp];
}

# sort array based on characters
our @sorted_data = sort { lc $a->[6] cmp lc $b->[6] } @all_data;

my $prevChar = "";

my $output;
my $last_block_index = 0;

print("Checking dependence of data\n") if $verbose;

$output = File::Spec->catfile( $dir, 'duplication.dat' );
open( FILE, ">$output" );
print FILE
    "Authors\tYear\tTitle\tSource\tVoume\tPages\tCharacters\tAnalysis\tPossible Overlap\n";

for my $i ( 0 .. $#sorted_data ) {
    $sorted_data[$i][10] = $sorted_data[$i][9] . ": ";
    unless ( lc $prevChar eq lc $sorted_data[$i][6] ) {
        if ($prevChar) {
            &sortTaxa( $last_block_index, $i );
        }
        $last_block_index = $i;
    }
    $prevChar = lc $sorted_data[$i][6];
}

# need to do last block
&sortTaxa( $last_block_index, $#sorted_data + 1 );
for my $i ( 0 .. $#sorted_data ) {
    unless ( lc $prevChar eq lc $sorted_data[$i][6] ) {
        print FILE "\n";
    }
    print FILE
        "$sorted_data[$i][0]\t$sorted_data[$i][1]\t$sorted_data[$i][2]\t$sorted_data[$i][3]\t$sorted_data[$i][4]\t$sorted_data[$i][5]\t$sorted_data[$i][6]\t$sorted_data[$i][7]\t$sorted_data[$i][10]\n";
    $prevChar = lc $sorted_data[$i][6];
}

close(FILE);

print("Done: data saved to $output\n");

# end main program

# sort taxa
# taxa are in array location 8.
sub sortTaxa {

    # input is indices to use
    my $start = $_[0];
    my $end   = $_[1];

    # local variables
    my $i;
    my $j;
    my $k;
    my $iter;
    my @temp_taxa_list;
    my @taxa_data;

    $end--;

    #print "Performing taxa search on block $start to $end\n";

    # data is in the form of a string of taxa names sperated by :
    # place in 2d array for sorting
    for $i ( $start .. $end ) {
        @temp_taxa_list = split( /:/, $sorted_data[$i][8] );
        @temp_taxa_list = sort @temp_taxa_list;
        my $length = @temp_taxa_list;

        push @taxa_data, [@temp_taxa_list];
        undef @temp_taxa_list;
    }

    my $length1 = @taxa_data;
    my $short   = 0;
    my $long    = 0;

    for ( $iter = 0; $iter < $length1 - 1; $iter++ ) {
        for ( $i = $iter + 1; $i < $length1; $i++ ) {
            my $length_t1 = $taxa_data[$i];
            my $length_t2 = $taxa_data[$iter];
            my $matched   = 0;
            if ( $#{$length_t1} < $#{$length_t2} ) {
                my $short = $#{$length_t1} + 1;
                my $long  = $#{$length_t2} + 1;
                for ( $j = 0; $j < $short; $j++ ) {
                    for ( $k = 0; $k < $long; $k++ ) {
                        if ( $taxa_data[$iter][$k] eq $taxa_data[$i][$j] ) {
                            $matched++;
                        }
                    }
                }
                if ( $matched == $short ) {
                    $sorted_data[ $start + $i ][10] =
                          $sorted_data[ $start + $i ][10] . "\t"
                        . $sorted_data[ $start + $iter ][9];
                }
            }
            else {
                my $long  = $#{$length_t1} + 1;
                my $short = $#{$length_t2} + 1;
                for ( $j = 0; $j < $short; $j++ ) {
                    for ( $k = 0; $k < $long; $k++ ) {
                        if (   defined( $taxa_data[$i][$j] )
                            && defined( $taxa_data[$iter][$k] )
                            && ( $taxa_data[$i][$j] eq $taxa_data[$iter][$k] ) )
                        {
                            $matched++;
                        }
                    }
                }
                if ( $matched == $short ) {
                    $sorted_data[ $start + $i ][10] =
                          $sorted_data[ $start + $i ][10] . "\t"
                        . $sorted_data[ $start + $iter ][9];
                }
            }
        }
    }

}


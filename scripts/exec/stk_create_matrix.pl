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

=head1 Create Matrix



=head1 SYNOPSIS

create_matrix.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing Tree files. Required
   --verbose         print verbose messages
   --output          output MRP file
   --format          output format. Defaults to Hening86.

=head1 OPTIONS 

=over 4

=item B<--dir>

a directory which contains tree files. B<Required>.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--output>

Output file for MRP matrix. Defaults to Matrix.tnt in C<dir>.

=item B<--format>

Sepcify the output format. Current Nexus and Hening86 are supported. The default is Hening86

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Create Matrix> creates an MRP matrix from all tree files contained in a directory. The script uses 
standard MRP coding.

The script is  based on that of Bininda-Emonds et al. (2005), SuperMRP.pl, but there
is no support for Purvis coding, weights, etc. If you need those, use SuperMRP instead.

=head2 References

Bininda-Emonds, O.R.P., R.M.D. Beck, and A. Purvis. 2005. 
Getting to the roots of matrix representation. Systematic Biology 54(4):668-672.

=head1 REQUIRES

Perl 5.004, Bio::STK::*, Getopt::Long, Pod::Usage

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

use Getopt::Long;
use Pod::Usage;
use File::Spec::Functions;
use lib "../lib";
use Bio::STK;
use strict;

# get args
my $dir = '';

# standard help messages
my $man     = 0;
my $help    = 0;
my $verbose = '';
my $output  = '';
my $format  = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    verbose    => \$verbose,
    'output=s' => \$output,
    'dir=s'    => \$dir,
    'format=s' => \$format
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}


# set up default output file if none given
if ( $output eq '' ) {
    $output = catfile( $dir, "Matrix.tnt" );
}

# check output format
if ($format eq '') {
    $format = "Hening86";
} else {
    print $format;
    if ($format ne "Hening86" and
        $format ne "Nexus") {
            print "Error - invalid format specified. --format should be either Nexus or Hening86\n";
            pod2usage(2);
            exit();
    }
}

# grab all tree files
print("Scanning $dir for tree files...\n");
my @tree_files = Bio::STK::find_tree_files($dir);
my $nTRE       = @tree_files;

#grab list of unique taxa
my @taxa  = Bio::STK::get_taxa_list($dir);
my $nTaxa = @taxa;
# add underscores to taxa names
for ( my $t = 0; $t < $nTaxa; $t++ ) {
    $taxa[$t] =~ s/ /_/g;    
}

print("Unique taxa:\n") if $verbose;
if ($verbose) {
    for ( my $t = 0; $t < $nTaxa; $t++ ) {
        print("\t$taxa[$t]\n");
    }
}

my @charState;    # nothing but a bunch of 0's and 1's (and ?'s)...
my @charset;
my $nChar       = 0;
my $lastCharSet = 0;

foreach my $file (@tree_files) {

    my @trees = Bio::STK::read_tree_file($file);

    print("Adding trees from $file...\n") if $verbose;

    foreach my $tree (@trees) {
        my $chars = '';
        $chars .= ( $lastCharSet + 1 );
        my $nClades = ( $tree =~ tr/(// );

        if ( $nClades == 1 ) {
            push( @charset, $chars );
            next;    # nothing useful in this tree
        }
        else {
            $chars .= "-" . ( $lastCharSet + $nClades - 1 );
            $lastCharSet = $lastCharSet + $nClades - 1;
            push( @charset, $chars );
        }

        my $cladeID      = 0;
        my $currentClade = 0;
        my %parent;
        my %open;
        my %start;
        my %finish;
        my %present;
        my $pos = 0;

        # loop over characters in the string to create clades
        while ( $pos < length($tree) ) {

            # new clade
            if ( substr( $tree, $pos, 1 ) eq '(' ) {

                # start a new clade
                $cladeID++;
                $parent{$cladeID}    = $currentClade;
                $currentClade        = $cladeID;
                $open{$currentClade} = 1;
                $start{$cladeID}     = $pos;

            }
            elsif ( substr( $tree, $pos, 1 ) eq ')' ) {

                # reached the end of the current clade, move up one
                $open{$currentClade} = 0;
                my $oldCurrent = $currentClade;
                $currentClade = $parent{$oldCurrent};
                $finish{$oldCurrent} = $pos;
            }
            elsif ( substr( $tree, $pos, 1 ) eq ',' ) {

                # skip...we want taxa....

            }
            else {

                # ...and we found taxa

                my $offset = 0;

                # find out how many chars we have to skip to end of taxa
                until (
                           substr( $tree, $pos + $offset, 1 ) eq '('
                        or substr( $tree, $pos + $offset, 1 ) eq ')'
                        or substr( $tree, $pos + $offset, 1 ) eq ','
                        or $pos + $offset >= length($tree)
                    )
                {
                    $offset++;
                }

                # add taxa to any open clades
                for ( my $clade = 2; $clade <= $cladeID; $clade++ ) {
                    if ( $open{$clade} ) {
                        $present{ substr( $tree, $pos, $offset ) }{$clade} = 1;
                    }
                }
                $pos += $offset - 1;
            }
            $pos++;
        }

    # we now have which taxa are in which clades and their positions in the tree
    # need to use these to construct matrix

        # loop over all taxa
        for ( my $t = 0; $t < $nTaxa; $t++ ) {

            # this tree contains this taxa
            if ( Bio::STK::tree_contains( $taxa[$t], $tree ) ) {

                # loop over clades in this tree
                for ( my $c = 2; $c <= $nClades; $c++ ) {
                    if ( $present{ $taxa[$t] }{$c} ) {
                        $charState[$t] .= '1';
                    }
                    else {
                        $charState[$t] .= '0';
                    }
                }

                # taxon not in this tree, add ? for all clades
            }
            else {
                $charState[$t] .= "?" x ( $nClades - 1 );
            }
        }
    }
}

$nChar = length( $charState[0] );
$nTaxa++; # we have an outgroup

if ($format eq "Nexus") {
    open( fDATA, ">$output" );
    print fDATA "#nexus\n\nbegin data;\n";
    print fDATA "\tdimensions ntax = $nTaxa nchar = $nChar;\n";

    print fDATA "\tformat missing = ?";
    print fDATA ";\n";
    print fDATA "\n\tmatrix\n\n";

    print fDATA "MRP_outgroup\t"; 
    for ( my $i = 0; $i < $nChar; $i++ ) {
        print fDATA "0";
    }
    print fDATA "\n";
    for ( my $i = 0; $i < @taxa; $i++ ) {
        print fDATA "$taxa[$i]\t$charState[$i]\n";
    }
    print fDATA "\t;\nend;\n\n";
    print fDATA "begin sets;\n";
    my $i = 1;
    foreach my $c (@charset) {
        print fDATA "\tcharset tree_$i = $c;\n";
        $i++;
    }
    print fDATA "end;\n\n";
} elsif ($format eq "Hening86") {
    open( fDATA, ">$output" );
    print fDATA "xread\n";
    print fDATA "$nChar $nTaxa\n";

    print fDATA "MRP_outgroup\t"; 
    for ( my $i = 0; $i < $nChar; $i++ ) {
        print fDATA "0";
    }
    print fDATA "\n";
    for ( my $i = 0; $i < @taxa; $i++ ) {
        print fDATA "$taxa[$i]\t$charState[$i]\n";
    }
    print fDATA ";\n\n";
    print fDATA "procedure /;\n";
} else {
    print "Error: Unknown file format given. See options for valid formats\n";
}

print "Matrix created in: $output\n";


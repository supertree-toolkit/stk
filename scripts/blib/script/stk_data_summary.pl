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

=head1 Data Summary



=head1 SYNOPSIS

data_summary.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing Tree files. Required
   --taxatreematrix  create data availability matrices
   --verbose         print verbose messages
   --output          output to a file, rather than standard output

=head1 OPTIONS 

=over 4

=item B<--dir>

A directory which contains XML/Tree files. B<Required>.

=item B<--taxatreematrix>

Create two file which allow data availability plots to be created.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--output>

Write the data summary to file, rather than standard output. Defaults to C<data_summary.txt> in C<dir>.

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Data Summary> chreates a summary of data generated from both tree and XML files which
is useful when writing manuscripts. Statistics such as the number of trees, the characters 
used, the taxa included, etc are output.

Note that the output depends on whether XML I<and> Tree file are found, or just Tree files.
The aim is to generate the data usually found in paper (e.g. we used 100 trees, from 185 papers, 
containing 500 taxa).

There is an assumption here that the XML and Treefiles live in the same directory. Therefore,
specify tha topmost directory where both can be reached. This won't work where, for example,
there are two directories containing treefiles and there's one directory containing XML files
underneath them, e.g.
 data_dir/
    tree_original/
    tree_processed/
    xml_files/

Supplying C<data_dir> will not work correctly.  

The C<--taxatreematrix> flag creates two additional files in the C<data_dir>:
data_availability_matrix.txt
taxa_tree_matrix.txt

These two files allow visualisation of the data. The former is comparable to the
popular visualisation of the data availability in molecular studies where
genes are plotted against species, with the speices sampled by many genes
occur at the origin and they are ranked by the number of genes available. The latter
file keeps the order of the trees and the taxa (alphabetical in both cases). This allows
individual trees or taxa to be identified. A simple plotting script can be used to
visualise these files.

=head1 REQUIRES

Perl 5.004, Bio::STK::*, Getopt::Long; Pod::Usage; Carp::*

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

use Getopt::Long;
use Pod::Usage;
use Carp;
use lib "../lib";
use Bio::STK;
use strict;

# get args
my $dir = '';

# standard help messages
my $man     = '';
my $help    = '';
my $verbose = '';
our $output = 0;
my $taxaTreeMatrix = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'       => \$help,
    man            => \$man,
    verbose        => \$verbose,
    taxatreematrix => \$taxaTreeMatrix,
    'output:s'     => \$output,
    'dir=s'        => \$dir
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}

if ( $output ne 0) {
    if ( $output eq '' ) {
        $output = File::Spec->catfile( $dir, "data_summary.txt" );
    }
}

print("Scanning $dir...\n");

our %taxa_per_tree;
our %taxa_count_per_tree;

data_summary($dir);

sub data_summary {

    my ($dir) = @_;

    # check if directory exists
    unless ( -d $dir ) {
        croak("Error - specified directory does not exist: $dir\n");
    }

    # here's where our data lives...
    my @taxa;
    my $nTrees;
    my $nTaxa;
    my $nFossils = 0;
    my @analysis_types;
    my @years;
    my $start_year;
    my $end_year;
    my $nAllFossils = 0;
    my $nAnalyses;
    my @chars;
    my %char_count;
    my %char_count_perc;
    my %mol_char_per_year;
    my %morph_char_per_year;
    my %other_char_per_year;
    my $matrixFile = File::Spec->catfile( $dir, "taxa_tree_matrix.txt" );

    my @treefiles  = Bio::STK::find_tree_files($dir);
    my @xmlfiles   = Bio::STK::find_xml_files($dir);
    my $nXML       = @xmlfiles;
    my $nTreeFiles = @treefiles;

    # let's get the data from treefiles first
    unless ( $nTreeFiles > 0 ) {
        croak("No tree files in the directory supplied: $dir\n");
    }

    print("Processing treefiles...\n") if $verbose;

# we could use the "get_taxa" function in STK, but we need to count the number of trees
# and get the taxa. Plus we can have verbose output too :)
    foreach my $file (@treefiles) {
        print("\t$file...\n") if $verbose;
        my @t = Bio::STK::read_tree_file($file);
        $nTrees += @t;
        undef @t;
        @t = Bio::STK::taxa_from_tree($file);
        my $nTaxa = @t;
        push( @taxa, @t );
        foreach my $taxon (@t) {
            $taxa_count_per_tree{$taxon}++;
        }
        $taxa_per_tree{$file} = $nTaxa;
    }

    # unique-ify the taxa
    my %saw;
    undef %saw;
    @taxa  = grep( !$saw{$_}++, @taxa );
    @taxa  = sort(@taxa);
    $nTaxa = @taxa;

    print("Processing XML files...\n") if $verbose;

    # now we deal with the XML files
    if ( $nXML > 0 ) {
        print STDOUT ("-------------------------------------------\n\n");
        foreach my $file (@xmlfiles) {
            print("\t$file...\n") if $verbose;

            my $f = Bio::STK::contains_fossils($file);

            # do they contain fossils?
            if ( $f > 0 ) {
                $nFossils++;
            }

            if ( $f == 1 ) {
                $nAllFossils++;
            }

            # Analysis type
            push( @analysis_types, Bio::STK::get_analysis($file) );

            my %source_data = Bio::STK::get_source_data($file);
            my $year = $source_data{'year'};
            push( @years, $year);

            my %characters = Bio::STK::get_characters($file);
            while ( my ( $key, $value ) = each(%characters) ) {
                if ($key eq "Molecular") {
                    $mol_char_per_year{$year}++;
                } elsif ($key eq "Morphological") {
                    $morph_char_per_year{$year}++
                } else {
                    $other_char_per_year{$year}++
                }
                
                # remember that each value is an array
                push( @chars, @{$value} );
            }

        }

        # lets work out the % trees that use each character type

        # unique-ify characters - slightly longer way to do lower case comparisons
        my %seen = ();
        my @uniq_chars = ();
        foreach my $item (@chars) {
            $item = lc $item;
            unless ($seen{$item}) {
                # if we get here, we have not seen it before
                $seen{$item} = 1;
                push(@uniq_chars, $item);
            }
        }
        my $total_chars = @chars;

        # now go through unique chars and count
        foreach my $uc (@uniq_chars) {
            $char_count{$uc} = 0;
            foreach my $c (@chars) {
                if ( $c eq $uc ) {
                    $char_count{$uc}++;
                }
            }
        }


        # work out percentages
        foreach my $uc (@uniq_chars) {
            $char_count_perc{$uc} = $char_count{$uc} / $total_chars * 100;
        }

        # unique-ify the analyses
        undef %saw;
        @analysis_types = grep( !$saw{$_}++, @analysis_types );
        @analysis_types = sort(@analysis_types);
        $nAnalyses      = @analysis_types;

        # get the year span
        @years      = sort(@years);
        $start_year = $years[0];
        $end_year   = $years[-1];
    }

    # print data summary
    if ($output) {
        open STDOUT, ">$output";
    }

    print STDOUT ("\n============================================\n");
    print STDOUT ("Summary of data in $dir\n");
    print STDOUT ("============================================\n\n");

    print STDOUT ("Number of taxa:       $nTaxa\n");
    print STDOUT ("Number of tree files: $nTreeFiles\n");
    print STDOUT ("Number of trees:      $nTrees\n");

    # only print these if there are XMl files
    if ( $nXML > 0 ) {
        printf STDOUT (
            "There are %i tree(s) (%.2f%%) that contain fossil taxa\n",
            $nFossils, $nFossils / $nTrees * 100
        );
        print STDOUT ("$nAllFossils tree(s) contain just fossil taxa\n");
        print STDOUT ("Data spans: $start_year - $end_year\n");
        print STDOUT (
            "$nAnalyses type(s) of analyses were used to create source data\n");
        print STDOUT ("-------------------------------------------\n\n");
        print STDOUT ("Character Data:\n");

        # character data
        foreach my $value (
            sort { $char_count_perc{$a} <=> $char_count_perc{$b} }
            keys %char_count
            )
        {
            printf STDOUT ( "    %-25s: %10.5f, %10.5f\n", $value, $char_count_perc{$value}, $char_count{$value}  );
        }

    }

    if ( $nXML > 0 ) {
        print STDOUT ("-------------------------------------------\n\n");
        print STDOUT ("Trees per year $dir\n");
        my(%count);
        foreach my $value (@years) {
            $count{$value}++;
        }
        for (my $i=$start_year;$i<=$end_year;$i++) {
            if (defined $count{$i}) {
                print STDOUT ("$i: $count{$i}\n");
            } else {
                print STDOUT ("$i: 0\n");
            }
        }
        print STDOUT ("-------------------------------------------\n\n");        
        print STDOUT ("Characters per year $dir\n");
        print STDOUT ("Year,Mol,Morph,Other\n");
        for (my $i=$start_year;$i<=$end_year;$i++) {
            print STDOUT ("$i,");
            if (defined $mol_char_per_year{$i} ) {
                print STDOUT ("$mol_char_per_year{$i},");
            } else {
                print STDOUT ("0,");
            }            
            if (defined $morph_char_per_year{$i} ) {
                print STDOUT ("$morph_char_per_year{$i},");
            } else {
                print STDOUT ("0,");
            }
            if (defined $other_char_per_year{$i} ) {
                print STDOUT ("$other_char_per_year{$i}\n");
            } else {
                print STDOUT ("0\n");
            }
        }
        print STDOUT ("-------------------------------------------\n\n");
        
        print STDOUT ("List of Analyses in $dir\n");
        foreach my $a (@analysis_types) {
            print STDOUT ("$a\n");
        }
        print STDOUT ("-------------------------------------------\n\n");
        print STDOUT ("List of Characters in $dir\n");
        foreach my $key ( sort { lc $a cmp lc $b } keys(%char_count) ) {
            print "$key\n";
        }


    }

    print STDOUT ("-------------------------------------------\n\n");
    print STDOUT ("List of Taxa in $dir\n");
    foreach my $taxon (@taxa) {
        $taxon =~ s/_/ /;
        print STDOUT ("$taxon");
        #$taxon =~ s/ /_/;
        #print STDOUT ("$taxa_count_per_tree{$taxon}\n");
    }

    print STDOUT ("\n-------------------------------------------\n\n");
    if ($output) {
        close STDOUT;
    }

    if ($taxaTreeMatrix and $nXML > 0) {
        open MATRIX, ">$matrixFile";
        print MATRIX "Tree File";
        foreach my $taxon (@taxa) {
            $taxon =~ s/_/ /g;
            print MATRIX ",$taxon";
        }
        print MATRIX "\n";

        my %study_names = Bio::STK::get_short_study_name(@xmlfiles);
        my $nGallus = 0;
        for my $file (
                sort { $study_names{$a} cmp $study_names{$b} }
                keys %study_names
            )
        {
            my $ref = $study_names{$file};
            my $xml = Bio::STK::read_xml_file($file);
            my $treeFile = $xml->{TreeFile}->[0];
            my @taxa_xml = Bio::STK::taxa_from_xml($xml);
            my %taxa_found;
            foreach my $taxon (@taxa_xml) {
                $taxon =~ s/ /_/;
                $taxa_found{$taxon}++;
            }
            my $nFound = @taxa_xml;
            my $nTaxa = @taxa;
            print MATRIX "$ref:$treeFile";
            foreach my $taxon (@taxa) {
                $taxon =~ s/ /_/;
                if (defined $taxa_found{$taxon}) {
                    print MATRIX ",1";
                } else {
                    print MATRIX ",0";
                }
            }
            print MATRIX "\n";

        }

        $matrixFile = File::Spec->catfile( $dir, "data_availability_matrix.txt" );
        open MATRIX2, ">$matrixFile" || die;
        print MATRIX2 "Tree File";
        # taxa are reverse sorted depending on how many trees they appear in
        foreach my $taxon (sort hashValueDescendingNumTaxa (keys(%taxa_count_per_tree))) {
            print MATRIX2 ",$taxon";
            
        }
        print MATRIX2 "\n";

       
        # reverse sort tree based on the number of taxa they have
        foreach my $file (sort hashValueDescendingNumTrees (keys(%taxa_per_tree))) {
            my @taxa_this_file = Bio::STK::taxa_from_tree($file);
            my %taxa_found;
            foreach my $taxon (@taxa_this_file) {
                $taxon =~ s/ /_/;
                $taxa_found{$taxon}++;
            }
            my $nFound = @taxa_this_file;
            print MATRIX2 "$file";
            # taxa are reverse sorted depending on how many trees they appear in
            foreach my $taxon (sort hashValueDescendingNumTaxa (keys(%taxa_count_per_tree))) {
                $taxon =~ s/ /_/;
                if (defined $taxa_found{$taxon}) {
                    print MATRIX2 ",1";
                } else {
                    print MATRIX2 ",0";
                }
            }
            print MATRIX2 "\n";

        }

    }

    close MATRIX2;
    close MATRIX;
    return;

}


sub hashValueDescendingNumTrees {
   $taxa_per_tree{$b} <=> $taxa_per_tree{$a};
}
sub hashValueDescendingNumTaxa {
   $taxa_count_per_tree{$b} <=> $taxa_count_per_tree{$a};
}


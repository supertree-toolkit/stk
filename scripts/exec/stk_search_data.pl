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

=head1 Search Data



=head1 SYNOPSIS

search_data [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing XML or tree files. Required
   --verbose         print verbose messages
   --output          direct output to file instead of STDOUT
   --copy            copy all files resulting from search into a directory
   --charterm        a character term to search for 
   --anterm          an analysis term to search for
   --taxterm         a taxa to search for
   --anyterm         search for data for a term in either character, analysis, or taxa
   --fossil          none|all|some
   --only            restrict results to B<only> containing the search term. Character term only.
   --year            search for data from a particular year

=head1 OPTIONS 

=over 4

=item B<--dir>

a directory which contains XML and/or tree files. B<Required>.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--output> 

Directs output to file instead of STDOUT.
If a filename is given, output is directed there, otherwise it is directed
to results.txt in the C<dir>ectory.

=item B<--copy>

Copy the files that are matched in the search to a new directory. If a directory 
name is given, the files are copied there. If this directory does not exist
it is created. If no name is given, the files will be copied into a directory
called C<seach_results> in C<dir>ectory.

=item B<--charterm>

A character term to search for. Specify multiple C<--charterm>s to perform OR searches

=item B<--anterm>

An analysis term to search for. Specify multiple C<--anterm>s to perform OR searches

=item B<--taxterm>

A taxa to search for. Specify multiple C<--taxterm>s to perform OR searches

=item B<--anyterm>

A term to search for. Specify multiple C<--anyterm>s to perform OR searches.
This will search all of taxa, characters and analyses.

=item B<--fossil>

Search for either C<none>, C<some> or C<all> fossil-based data. 

=item B<--year>

Search for a particular year. Must be a four digit year.

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Search Data> allows the data directory to be searched for taxa, characters or analyses.
The results can be printed to screen or the Tree/XML files copied into a new directory.
The executable is useful for extracting subsets of data, for example all source trees 
generated using molecular data. XML files are required as the searches are carried on

Characters can be specified, e.g. cytb or rag1, or can be generic characters, e.g. Molecular or 
Morphological.

Taxonomic searches search only taxa contained in the data - this script does not understand
taxonomy, so search for "Galliformes" will not return any results unless a tree contains a
terminal node "Galliformes"

All searches are case insensitive. If multilpe terms are searchd an "OR" search will be carried out

=head1 REQUIRES

Perl 5.004, Bio::STK::*, Getopt::Long; File::Spec::Functions;

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

# to do
# - add AND searches

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
my $copy    = 0;
my @charterm;
my @anterm;
my @taxterm;
my @anyterm;
my @yearterm;
my $fossil = '';
my $only = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'     => \$help,
    man          => \$man,
    verbose      => \$verbose,
    'output:s'   => \$output,
    'dir=s'      => \$dir,
    'copy:s'     => \$copy,
    'charterm=s' => \@charterm,
    'anterm=s'   => \@anterm,
    'taxterm=s'  => \@taxterm,
    'anyterm=s'  => \@anyterm,
    'fossil=s'   => \$fossil,
    'year=s'     => \@yearterm,
    'only'       => \$only,
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}


# check we have *something* to search for...
unless (   @charterm
        || @anterm
        || @taxterm
        || @anyterm 
        || $fossil 
        || @yearterm)
{
    print("Nothing to search for!\n");
    pod2usage(1);
    die();
}

# check fossil is one of permitted values
unless ($fossil eq '' or $fossil eq 'none' or $fossil eq 'all' or $fossil eq 'some') {
    print("fossil flag should be either 'some', 'none' or 'all'\n");
    die();
}

if ( $output ne 0 ) {
    if ( $output eq '' ) {
        $output = File::Spec->catfile( $dir, "results.txt" );
    }
    open STDOUT, ">$output";
}

if ( $copy ne 0 ) {
    my @dirs;
    $dirs[0] = $dir;
    if ( $copy eq '' ) {
        $dirs[1] = "search_results";
        $copy = File::Spec->catdir(@dirs);
        mkdir $copy || die("Error making results directory $!\n");
    }

    # check if dir exists and if it's empty
    # if it's not empty warn the user and give them chance to quit
    if ( -d $copy ) {
        my @xml_files  = Bio::STK::find_xml_files($copy);
        my @tree_files = Bio::STK::find_tree_files($copy);
        if ( @tree_files > 0 or @xml_files > 0 ) {
            print("********************************************************\n");
            print("*   WARNING: specified dir to copy into is not empty.  *\n");
            print("* Exit the program (Ctrl-C) if you did not expect this.*\n");
            print("*      Files may be copied over, if you continue.      *\n");
            print("********************************************************\n");
            sleep(3);
        }
    }
    else {
        mkdir $copy || die("Error making results directoy $!\n");
    }
}

# grab all xml files
my @xml_files = Bio::STK::find_xml_files($dir);
my $nXML      = @xml_files;
our %short_names = Bio::STK::get_short_study_name(@xml_files);

# if xml - check syntax and contain minimal data
if ( $nXML > 0 ) {
    print("\nScanning XML files...\n") if $verbose;

    my @analysesFound;
    my @charactersFound;
    my @taxaFound;
    my @anyFound;
    my @yearFound;
    my $fossilsFound;

    foreach my $file (@xml_files) {

        print("$file...\n") if $verbose;

        # go through each search
        # we can''t just lump the terms together and do a "anyterms"
        # search as data *may* overlap and the user *may* not want that
        my $i = 0;
        for my $needle (@anterm) {
            if ( Bio::STK::xml_contains_analysis( $needle, $file ) ) {

                # copy data
                if ( $copy ne 0 ) {
                    copy_data( $file, $copy );
                }

                # or add to output
                $analysesFound[$i] .= "\t$file\n";
                $i++;
            }
        }
        $i = 0;
        for my $needle (@charterm) {
            if ( Bio::STK::xml_contains_character( $needle, $file, $only ) ) {
                if ( $copy ne 0 ) {
                    copy_data( $file, $copy );
                }

                $charactersFound[$i] .= "\t$file\n";
                $i++;
            }
        }
        $i = 0;
        for my $needle (@taxterm) {
            if ( Bio::STK::xml_contains_taxon( $needle, $file, 1 ) ) {
                if ( $copy ne 0 ) {
                    copy_data( $file, $copy );
                }

                $taxaFound[$i] .= "\t$file\n";
                $i++;
            }
        }        
        $i = 0;
        for my $needle (@yearterm) {
            if ( Bio::STK::xml_from_year( $needle, $file, 1 ) ) {
                if ( $copy ne 0 ) {
                    copy_data( $file, $copy );
                }

                $yearFound[$i] .= "\t$file\n";
                $i++;
            }
        }

        $i = 0;
        if ( Bio::STK::contains_data( \@anyterm, $file ) ) {
            if ( $copy ne 0 ) {
                copy_data( $file, $copy );
            }

            $anyFound[$i] .= "\t$file\n";
            $i++;
        }
        if ($fossil eq 'none') {
            if ( Bio::STK::contains_fossils( $file ) == 0 ) {

                # copy data
                if ( $copy ne 0 ) {
                    copy_data( $file, $copy );
                }

                # or add to output
                $fossilsFound .= "\t$file\n";
            }
        } elsif ($fossil eq 'all') {
            if ( Bio::STK::contains_fossils( $file ) == 1 ) {

                # copy data
                if ( $copy ne 0 ) {
                    copy_data( $file, $copy );
                }

                # or add to output
                $fossilsFound .= "\t$file\n";
            }
        } elsif ($fossil eq 'some') {
            if ( Bio::STK::contains_fossils( $file ) == 2 ) {

                # copy data
                if ( $copy ne 0 ) {
                    copy_data( $file, $copy );
                }

                # or add to output
                $fossilsFound .= "\t$file\n";
            }
        } 
    }

    # print output
    print("\n\n   Found the following\n");
    print("==========================\n\n");
    my $i = 0;
    if (@anyterm) { print("Found in 'any' field:\n-----------------\n"); }
    for my $term (@anyterm) {
        print("$term:\n");
        if (!$anyFound[$i]) {
          print ("\tDidn't find anything\n");
        } else {
          print("$anyFound[$i]");
        }
        $i++;
    }

    $i = 0;
    if (@anterm) { print("Found in 'analysis' field:\n-----------------\n"); }
    for my $term (@anterm) {
        print("$term:\n");
        if (!$analysesFound[$i]) {
          print ("\tDidn't find anything\n");
        } else {
          print("$analysesFound[$i]");
        }
    }

    $i = 0;
    if (@charterm) {
        print("Found in 'character' field:\n-----------------\n");
    }
    for my $term (@charterm) {
        print("$term:\n");
        if (!$charactersFound[$i]) {
          print ("\tDidn't find anything\n");
        } else {
          print("$charactersFound[$i]");
        }
        $i++
    }

    $i = 0;
    if (@taxterm) { print("Found in 'taxa' field:\n-----------------\n"); }
    for my $term (@taxterm) {
        print("$term:\n");
        if (!$taxaFound[$i]) {
          print ("\tDidn't find anything\n");
        } else {
          print("$taxaFound[$i]");
        }
        $i++
    }

    $i = 0;
    if (@yearterm) { print("Found data from year:\n-----------------\n"); }
    for my $term (@yearterm) {
        print("$term:\n");
        if (!$yearFound[$i]) {
          print ("\tDidn't find anything\n");
        } else {
          print("$yearFound[$i]");
        }
        $i++
    }

    $i = 0;
    if ($fossil) { 
      print("Found the following fossil attributes $fossil:\n-----------------\n");
      print("$fossilsFound");
    }

    print("\n\n");

    if ( $copy ne 0 ) {
        print("Files that match search have been copied to $copy\n");
        print("Run the check_data script on this now\n");
    }

}
else {
    die( "Only XML files can be searched - the directory should contain some!\n"
    );
}

sub copy_data {

    my ( $xml_file, $destination ) = @_;

    # make dir inside destination, based on author_year
    my $xml = Bio::STK::read_xml_file($xml_file);

    # new directory to copy stuff into
    my $study_dir = $short_names{$xml_file};

    # append the storage dir to destination dir
    my @dirs;
    $dirs[0] = $destination;
    $dirs[1] = $study_dir;
    my $dir = File::Spec->catdir(@dirs);

    # sort out treefile
    my ( $filename, $t_dir, $suffix ) = fileparse( $xml_file, qr{\.xml} );
    my $treefile = $xml->{TreeFile}->[0];
    $treefile =~ s|\\|/|;
    my $full_tree_file =
                    File::Spec->catfile( $t_dir, $treefile );
    my ( $tree_filename, $tree_dir, $tree_suffix ) =
        fileparse( $full_tree_file, qr{\.tre} );

    # create the "new" file name
    my $new_xml_file = File::Spec->catfile( $dir, $filename . $suffix );
    my $new_tree_file =
        File::Spec->catfile( $dir, $tree_filename . $tree_suffix );
    $treefile = $tree_filename . $tree_suffix;

    # directory may exist - if so we don't need to create
    # e.g. if there are several trees to a study
    if ( -d $dir ) {

        # check if tree and xml file exists
        # e.g. if the data is stored with a XML per dir
        # and we're storing with numerous XMLs per author
        if ( -e $new_xml_file ) {
            my $i = 0;

            # change names to prevent overwrite
            while ( ( -e $new_xml_file ) || ( -e $new_tree_file ) ) {
                $i++;
                $new_xml_file =
                    File::Spec->catfile( $dir, $filename . $i . $suffix );

                # edit tree filename to match XML (i.e. with digit in)
                $treefile = $tree_filename . $i . $tree_suffix;
                $new_tree_file = File::Spec->catfile( $dir, $treefile );
            }
        }
    }
    else {
        mkdir $dir;
    }

    # edit xml to point to new treefile
    $xml->{TreeFile}->[0] = $treefile;

    # *save* XML to keep changes to <treefile> and copy in tree file
    if ( Bio::STK::save_xml_file( $new_xml_file, $xml ) ) {

        # save succeeded - copy tree file
        File::Copy::copy( $full_tree_file, $new_tree_file )
            || die("Error copying tree file $!\n");
    }
    else {
        print(
            "Copying XML from:\n$xml_file\nto:\n$new_xml_file\n failed. Some files may have been copied\n"
        );
        die("Aborting\n");
    }
}

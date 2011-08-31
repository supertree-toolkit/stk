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

=head1 Check Data


=head1 SYNOPSIS

check_data.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing XML files. Required
   --verbose         print verbose messages
   --output          direct output to file instead of STDOUT

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

Directs output to file instead of STDOUT. If a filename is given, output is directed there, otherwise it is directed
to error.txt in the c<dir>ectory.

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Check Data> checks that the data in C<dir> is valid. For a directory of tree files
this means checking that all tree files are valid NEXUS files. For a directory of XML
files this means check for XML correctness and contain the minimum amount of data. 
For a directory of both tree and XML files the two file types are validated and 
cross-checked against each other. Tests carried out are:

=over 8

=item * Matching files - each tree file should have a matching XML file (or more correctly, each XML file should have a matching tree file)

=item * Matching taxa - the tree and XML files should contain the same taxa

=back

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
my $remove = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    verbose    => \$verbose,
    'output:s' => \$output,
    'dir=s'    => \$dir,
    remove     => \$remove
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

my $files_with_errors = '';

# grab all xml files
my @xml_files = Bio::STK::find_xml_files($dir);
my $nXML      = @xml_files;

# grab all tree files
my @tree_files = Bio::STK::find_tree_files($dir);
my $nTRE       = @tree_files;

my $totalErrors = 0;

# if xml - check syntax and contain minimal data
if ( $nXML > 0 ) {
    print("\nChecking XML files...\n") if $verbose;
    foreach my $file (@xml_files) {

        # number of errors
        my $nErrors = 0;
        my $xml;
        my $error_string = '';

        # can we read it in OK
        eval { $xml = Bio::STK::read_xml_file($file); };

        # oh oh! Error reading xml file!
        if ($@) {
            $error_string .= "\tError with parsing\n";
            $nErrors++;
        }

        # load succeeded - check for minimal info
        if ($xml) {

            # contains author
            if ( $xml->{Source}->[0]->{Author}->[0] eq '' ) {
                $error_string .= "\tMissing author data\n";
                $nErrors++;
            }

            # contains year
            if ( $xml->{Source}->[0]->{Year}->[0] eq '' ) {
                $error_string .= "\tMissing year data\n";
                $nErrors++;
            }

            my $nTaxa = 0;
            # contains taxa
            if (not defined (@{ $xml->{Taxa}->[0]->{List} })) {
                $error_string .= "\tMissing a taxa list\n";
                $nErrors++;
            } else {		
		        my @taxa_names = Bio::STK::taxa_from_xml($xml);
		        $nTaxa = @taxa_names;
                if( $nTaxa < 1 ) {
                    $error_string .= "\tMissing taxa list\n";
                    $nErrors++;
	            } else {
                    # check for duplicate taxa names
                    @taxa_names = sort @taxa_names;
                    my $last_taxon = '';
                    for my $taxon (@taxa_names) {
                        if ( $taxon eq $last_taxon ) {
                            $error_string .= "\tDuplicate taxon: $taxon\n";
                            $nErrors++;
                        }
                        $last_taxon = $taxon;
                    }
                }
	    }

            # contains correct number of taxa
            if ( $xml->{Taxa}->[0]->{number} != $nTaxa )
            {
                $error_string .= "\tIncorrect taxa number\n";
                $nErrors++;
            }

            # contains fossil info
            my $fossil = Bio::STK::contains_fossils($file);
            if ( $fossil < 0 ) {
                $error_string .= "\tIncorrect fossil information\n";
                $nErrors++;
            }

            # contains characters
            my $contains_characters = 0;
            for my $type (@Bio::STK::character_types) {
                if (defined(
                        $xml->{Characters}->[0]->{$type}->[0]->{'number'}
                    )
                    )
                {
                    $contains_characters = 1;
                }
            }
            if ( !$contains_characters ) {
                $error_string .= "\tMissing characters\n";
                $nErrors++;
            }

            # contains title
            if ( $xml->{Source}->[0]->{Title}->[0] eq '' ) {
                $error_string .= "\tMissing a title\n";
                $nErrors++;
            }

            # contains a valid tree file
            if ( $xml->{TreeFile}->[0] eq '' ) {
                $error_string .= "\tMissing a treefile\n";
                $nErrors++;
            }
            else {

                # which exists!
                # get directory part of xml file
                my ( $filename, $dir, $suffix ) = fileparse($file);

                # full path to tree file
                my $treefile = $xml->{TreeFile}->[0];
                $treefile =~ s|\\|/|;
                my $full_tree_file =
                    File::Spec->catfile( $dir, $treefile );
                unless ( -e $full_tree_file ) {
                    $error_string .= "\tTreefile does not exist: $full_tree_file\n";
                    $nErrors++;
                }
            }
        }

        if ( $nErrors > 0 or $verbose ) {
            print
                "\n----------------------------------------------------------\n";
            print "File: $file\n";
            print "$error_string";
            $files_with_errors .= "$file\n" if ( $nErrors > 0 );
        }

        $totalErrors += $nErrors;
    }

}

# if tree - check syntax
if ( $nTRE > 0 ) {
    print("\nChecking Tree files...\n") if $verbose;
    foreach my $file (@tree_files) {

        # number of errors
        my $nErrors = 0;
        my @trees;
        my $error_string = '';

        # can we read it in OK
        eval { @trees = Bio::STK::read_tree_file($file); };

        # oh oh! Error reading file!
        if ($@ ne '' ) {
            $error_string .= "\tError with parsing\n";
            $nErrors++;
        }

        # check for taxa
        my @taxa;
        # wrap this up - it might be invalid!
        eval { @taxa = Bio::STK::taxa_from_tree($file); };
        my $nTaxa = @taxa;
        if (!$@ && $nTaxa < 2) {
            $error_string .= "\tFile contains $nTaxa taxa - we expect at least 2 taxa\n";
            $nErrors++;
        }

        # TNT output trees that contain "begin trees ;" with a space between "trees" and ";"
        # Check for this and warn the user
        # You should also get the above error with this too
        open(CF, "<$file");
        while(<CF>) {
            if ($_ =~ m/begin trees \;/i) {
                $error_string .= "\tFile contains TNT formatting error - check for 'begin trees \;' - note the space. Try the stk_fix_treefiles.pl script.\n";
                $nErrors++;
                last; # no point continuing
            }
        }
        close(CF);

        # check for duplicate taxa
        for my $tree (@trees) {
            my @taxlabels;

            # we can't use taxa_from_tree as this returns unique taxa
            # and therefore removes duplicate taxa

            # we have a Newick string - extract name using reg exp magic
            # then use split to create array on ,
            # first let's remove ( & ), labels and '
            # Note: Seems quicker to do these seperately, rather than in 1 regexp
            $tree =~ s/\(//g;
            $tree =~ s/\)//g;
            $tree =~ s/\:.*$//g;
            $tree =~ s/\'//g;
            @taxlabels = split( ',', $tree );
            @taxlabels = sort(@taxlabels);
            my $last_taxa = '';

            for my $taxa (@taxlabels) {
                if ( $taxa eq $last_taxa ) {
                    $error_string .= "\tDuplicate taxon: $taxa\n";
                    $nErrors++;
                }
                $last_taxa = $taxa;
            }
        }

        if ( $nErrors > 0 or $verbose ) {
            print
                "\n----------------------------------------------------------\n";
            print "File: $file\n";
            print "$error_string";
            $files_with_errors .= "$file\n" if ( $nErrors > 0 );
        }

        $totalErrors += $nErrors;
    }

}

# if xml & tree - check integrity
if ( $nTRE > 0 && $nXML > 0 ) {
    print("\nChecking Treefiles against XML files...\n") if $verbose;
    foreach my $file (@xml_files) {

        # number of errors
        my $nErrors = 0;
        my $xml;
        my $error_string = '';

        eval { $xml = Bio::STK::read_xml_file($file); };

        # load succeeded - check for minimal info
        if ($xml) {

            # grab tree file from xml
            my $tree_file = $xml->{TreeFile}->[0];
            $tree_file =~ s|\\|/|;

            # get directory part of xml file
            my ( $filename, $dir, $suffix ) = fileparse($file);

            # full path to tree file
            my $full_tree_file = File::Spec->catfile( $dir, $tree_file );

            # only do the checks if the treefile exists, otherwise there's no point!
            if ( -e $full_tree_file ) {

                # get taxa from XML
                my @xml_taxa = Bio::STK::taxa_from_xml($file);
                # strip any ' ' from names - taxa in XML *may* have
                # them around dodgy names...
                for (my $i=0; $i < @xml_taxa; $i++) {
                    $xml_taxa[$i] =~ s/'//g;
                }


                # get taxa from tree
                my @tre_taxa = Bio::STK::taxa_from_tree($full_tree_file);
                # strip any ' ' from names - taxa in tree files *must* have them
                # around dodgy names - therefore get rid of them to compare to
                # taxa from XML file
                for (my $i=0; $i < @tre_taxa; $i++) {
                    $tre_taxa[$i] =~ s/'//g;
                }

                # check taxa
                @xml_taxa = sort @xml_taxa;
                @tre_taxa = sort @tre_taxa;

                # series of nested if's to do the tests
                if ( @tre_taxa != @xml_taxa ) {
                    my $nTre = @tre_taxa;
                    my $nXml = @xml_taxa;
                    $error_string
                        .= "\tNumber of taxa don't match - Tree: $nTre - XML: $nXml\n";

                    # print formatted list for ease of checking
                    if ($verbose) {
                        for ( my $i = 0; $i < @tre_taxa; $i++ ) {
                            $error_string
                                .= sprintf( "\t\t%21.20s   |   %21.20s\n",
                                $tre_taxa[$i], $xml_taxa[$i] );
                        }
                    }
                    $nErrors++;
                }
                else {
                    for ( my $i = 0; $i < @xml_taxa; $i++ ) {
                        if ( $xml_taxa[$i] ne $tre_taxa[$i] ) {
                            $error_string
                                .= "\tTaxa don't match: XML:$xml_taxa[$i] TRE:$tre_taxa[$i]\n";
                            $nErrors++;
                        }
                    }
                }
            }
            else {
                $error_string .= "No tree files found\n";
                $nErrors++;
            }

            if ( $nErrors > 0 or $verbose ) {
                print
                    "\n----------------------------------------------------------\n";
                print "File: $file (Tree: $full_tree_file)\n";
                print "$error_string";
                $files_with_errors .= "$file:$tree_file\n" if ( $nErrors > 0 );
            }

            $totalErrors += $nErrors;

        }

    }
}

print "\n\nChecks finished...Found $totalErrors errors\n";
print "There were $nTRE tree files and $nXML XML files checked\n";
if ($nTRE == 0 and $nXML ==0) {
    $totalErrors++;
    $files_with_errors .= "No tree or XML files found. Possible reasons:\n";
    $files_with_errors .= "  - did you check the right directory?\n";
    $files_with_errors .= "  - do your tree files have a .tre extension?\n";
}

if ( $totalErrors > 10 or $verbose ) {
    print "------------------------------------------\n";
    print "            Error Summary                 \n";
    print "------------------------------------------\n";
    print $files_with_errors;
    if ( $totalErrors == 0 ) {
        print("No errors found\n");
    }
}


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

=head1 Amalgamate Trees

=head1 SYNOPSIS

stk_amalgamate_trees.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing Tree/XML files. Required
   --verbose         print verbose messages
   --output          output file. Default is 'all_trees.tre' in C<dir>
   --anon            anonymise data

=head1 OPTIONS 

=over 4

=item B<--dir>

a directory which contains tree (and XML) files. B<Required>.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--output>

Where to save output. Default is 'all_trees.tre' in the C<dir>.

=item B<--anon>

The C<--anon> flag to name trees tree_1...tree_n. A key file will be written
in C<dir> linking either author names or treefile names to each anonymised tree.
Without this flag, tree are named after the tree authors and year published, 
e.g. SmithAndJones_1999 if XML files are available, or the tree filename without
the suffix .tre, the prefix C<dir>, and all non-standard characters repolaceed with
underscores, e.g. trees_SmithAndJones_1999

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Amalgamate Trees> creates a single tree file with all trees from C<dir>. This is useful
when sharing your data as it is the version of the data that has most compatibility with other 
software. If XML files are present trees will be named using the author_year convention. 
If XML files are not present the trees will be after the tree file name.
The C<--anon> flag to name trees tree_1...tree_n. A key file will be written
in C<dir> linking either author names or treefile names to each anonymised tree.

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
use lib '../lib';
use Bio::STK;
use strict;

# standard help messages
my $man     = '';
my $help    = '';
my $verbose = '';
my $anon    = '';
my $output  = '';
my $dir     = '';

# Parse options and print usage if there is a syntax error,
# or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    verbose    => \$verbose,
    anon       => \$anon,
    'output=s' => \$output,
    'dir=s'    => \$dir
) or pod2usage(2);
pod2usage(1) if ($help);
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n\n");
    pod2usage(1);
    exit();
}

if ( $output eq '' ) {
    $output = File::Spec->catfile( $dir, 'all_trees.tre' );
}

# grab all xml files
my @xml_files = Bio::STK::find_xml_files($dir);
my $nXML      = @xml_files;

# grab all tree files
my @tree_files = Bio::STK::find_tree_files($dir);
my $nTRE       = @tree_files;

if ($nTRE == 0) {
	die("Didn't find any tree files!");
}
# two different things here
#   - no xml: loops over trees and stick together - treename based on filename
#   - xml: loop over xml and get trees via them, we can construct author list then

# tree only first
if ( $nXML == 0 ) {

    print("Processing tree files...\n") if $verbose;

    my @trees;
    my @names;
    my @key;

    my $i = 1;
    foreach my $file (@tree_files) {

        print("\t$file\n") if $verbose;

        my @t = Bio::STK::read_tree_file($file);
        push( @trees, @t );

        # we need to know how many trees there are
        my $nTree = @t;
        for ( my $j = 1; $j <= $nTree; $j++ ) {
            if ($anon) {

                # add to store and key for later
                push( @names, "tree_$i" );
                $key[$i] = $file;
            }
            else {
                my ( $filename, $dir, $suffix ) = fileparse($file);

                $filename = $filename . "_$j";

                # add to store
                push( @names, $filename );
            }
            $i++;
        }
    }
    unless ( Bio::STK::save_tree_file( $output, \@trees, \@names ) ) {
        die("Error saving amalgamated file to: $output\n");
    }
    print("Saved tree file to $output\n") if $verbose;

    if ($anon) {

        #save key file
        my $file = File::Spec->catfile( $dir, 'key.txt' );
        open( FILE, ">", $file )
            || die " Can't open key file $file, quitting.\n";
        print FILE "Tree number\tFilename\n";
        for ( my $j = 1; $j < @key; $j++ ) {
            print FILE "$j\t$key[$j]\n";
        }

        print("Saved key file to $file\n") if $verbose;
        close FILE;
    }

}
else {

    # xmls contain data too...
    my @trees;
    my @names;
    my @key;

    my $i         = 1;
    my $tree_n    = 1;
    my $last_name = '';

    print("Processing file...\n") if $verbose;

    my %short_study_names = Bio::STK::get_short_study_name(@xml_files);

    foreach my $file (@xml_files) {

        print("\t$file\n") if $verbose;

        my $xml;
        $xml = Bio::STK::read_xml_file($file);

        my $tree_name = $short_study_names{$file};
        if ( $last_name eq $short_study_names{$file} ) {
            $tree_n++;
        }
        else {
            $tree_n = 1;
        }
        $tree_name = $short_study_names{$file} . '_tree_' . $tree_n;
        $last_name = $short_study_names{$file};

        # full path to tree file
        my ( $filename, $t_dir, $suffix ) = fileparse($file);
        my $treefile = $xml->{TreeFile}->[0];
        $treefile =~ s|\\|/|;
        my $full_tree_file =
           File::Spec->catfile( $t_dir, $treefile );

        my @t = Bio::STK::read_tree_file($full_tree_file);
        push( @trees, @t );

        # we need to know how many trees there are
        my $nTree = @t;

        for ( my $j = 1; $j <= $nTree; $j++ ) {
            if ($anon) {

                # add to store and key for later
                push( @names, "tree_$i" );
                $key[$i] = $short_study_names{$file} . "\t" . $file;
            }
            else {

                # add to store
                push( @names, $tree_name );
            }
            $i++;
        }
    }

    unless ( Bio::STK::save_tree_file( $output, \@trees, \@names ) ) {
        die("Error saving amalgamated file to: $output\n");
    }
    print("Saved tree file to $output\n") if $verbose;

    if ($anon) {

        #save key file
        my $file = File::Spec->catfile( $dir, 'key.txt' );
        open( FILE, ">", $file )
            || die " Can't open key file $file, quitting.\n";
        print FILE "Tree number\tAuthors\tFilename\n";
        for ( my $j = 1; $j < @key; $j++ ) {
            print FILE "$j\t$key[$j]\n";
        }

        print("Saved key file to $file\n") if $verbose;
        close FILE;
    }

}


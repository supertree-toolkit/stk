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

=head1 Replace Genera



=head1 SYNOPSIS

stk_replace_genera.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing XML/Tree files. Required
   --verbose         print verbose messages. Sets C<--higher>, but substitutions are done.
   --higher          print higher taxa to screen. No substitutions will be done.
   --output          writes substitutions carried out to taxa substituion file (specify). No substitutions will be done.

=head1 OPTIONS 

=over 4

=item B<--dir>

a directory which contains tree and/or XML files. B<Required>.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--higher>

Prints the higher (non-specific) taxa to screen. No substitutions will be done

=item B<--output>

Writes what substitutions will be done by the script to taxa substitution file. The default
location is the data_directory/generic_subs.txt. This file is in the same file format used 
in L<STK Replace Taxa>. No substitutions will be done.

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Replace Genera> is used when creating trees at specific level following the protocol
of Davis (2008). Any taxon that are at generic level only are replaced by a polytomy
of specific names from the rest of the data set.

An example is if a data set contains I<Gallus gallus> and I<Gallus lafayetii> will have
I<Gallus> replaced where it occurs as a generic taxon with a polytomy containing 
I<Gallus gallus> and I<Gallus lafayetii>.

There is an assumption here that the XML and Treefiles live in the same directory. Therefore,
specify the topmost directory where both can be reached. This won't work where, for example,
there are two directories containing treefiles and there's one directory containing XML files
underneath them, e.g.
 data_dir/
    tree_original/
    tree_processed/
    xml_files/

Supplying C<data_dir> will not work correctly. 

Also, make sure that the data is consistant, i.e. run the Data Check script first and make
sure the data passses.

=head1 REQUIRES

Perl 5.004, Bio::STK::*, Getopt::Long; Pod::Usage; Carp::*

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

use Getopt::Long;
use Data::Dumper;
use Pod::Usage;
use Carp;
use lib "../lib";
use Bio::STK;
use strict;

# get args
my $dir         = '';
my $view_higher = '';
my $verbose     = '';
my $output      = '';

# standard help messages
my $man  = '';
my $help = '';

## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    higher     => \$view_higher,
    verbose    => \$verbose,
    'output=s' => \$output,
    'dir=s'    => \$dir
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}

# check if directory exists
unless ( -d $dir ) {
    die("Error - specified directory does not exist: $dir\n");
}

unless ( $view_higher or $output ) {

    # Print warning - CTL C to quit unless nothing will be overwritten...
    print("********************************************************\n");
    print("*    WARNING: This program writes over existing data.  *\n");
    print("* If you have not backed-up, hit CTRL-C NOW and do it! *\n");
    print("********************************************************\n");


    # let's give folk a chance to quit...
    # note - don't want to add "press any key to continue" as we want batch mode...
    # and I prefer this to adding a "--batch" flag
    sleep(3);
} else {
    if ( $output eq '' ) {
        $output = File::Spec->catfile( $dir, "generic_subs.txt" );
    }
}

my @treefiles = Bio::STK::find_tree_files($dir);
my @xmlfiles  = Bio::STK::find_xml_files($dir);

# we assume here that the XML and tree files are consistant - i.e.
# run the data_check script first
# we grab taxa from the tree files
my @taxa = Bio::STK::get_taxa_list($dir);

my @substitutions;
my @higher_taxa;

# now find generic taxa and create a substitution list
print("Finding all generic taxa...\n") if $verbose;
for ( my $i = 0; $i < @taxa; $i++ ) {

    my $substitute_taxa = "";

    # underscore in name - specific taxa
    unless ( $taxa[$i] =~ m/ / ) {

        push( @higher_taxa, $taxa[$i] );
        my $current_taxa = $taxa[$i];
        for ( my $j = $i + 1; $j < @taxa; $j++ ) {
            if ( $taxa[$j] =~ m/$current_taxa / ) {
                $substitute_taxa .= ',' . $taxa[$j];
            }
        }

        if ( $substitute_taxa eq ',' or $substitute_taxa eq '' ) {

            # no specific taxa found of that genera
            pop(@higher_taxa);
        }
        else {

            # lose the first comma
            $substitute_taxa = substr $substitute_taxa, 1;
            push( @substitutions, $substitute_taxa );
        }
    }
}

# let's do some basic checks....
# 1) There should be same number in higher and substitutions
if ( @higher_taxa != @substitutions ) {
    die("Number of higher taxa do not match substitutions found\n");
}

# 2) no substitions should be empty...i.e. no higher taxa replaced
for ( my $i = 0; $i < @substitutions; $i++ ) {
    if ( $substitutions[$i] eq '' or $substitutions[$i] eq ',' ) {
        die("Empty substitution found: $i which corresponds to $higher_taxa[$i]\n"
        );
    }
}

# print higher (non-specific) taxa
if ( $view_higher or $verbose ) {
    my @h = sort(@higher_taxa);
    print "============ Printing generic taxa ===========\n\n";
    for ( my $i = 0; $i < @h; $i++ ) {
        print "$h[$i]\n";
    }

}

# save substitution file if required
if ($output) {
    open OUT, ">$output";
    for ( my $i = 0; $i < @higher_taxa; $i++ ) {
        print OUT "$higher_taxa[$i] = $substitutions[$i]\n";
    }
    close(OUT);
    print("Subs file written to $output\n");
}

if ( $view_higher or $output ) {

    # don't actually do anything...
    exit(0);
}

print("Processing tree files...\n") if $verbose;
foreach my $file (@treefiles) {

    print("\t$file...\n") if $verbose;

    my @trees        = Bio::STK::read_tree_file($file);
    my @taxa_in_tree = Bio::STK::taxa_from_tree($file);
    my %in_tree;
    for (@taxa_in_tree) { $in_tree{$_} = 1 }

    my $altered = 0;

TAXA: for ( my $j = 0; $j < @higher_taxa; $j++ ) {

        unless ( $in_tree{ $higher_taxa[$j] } ) {
            next TAXA;
        }

        $altered = 1;

        # prepare polytomy
        my @substitute_taxa = split( /,/, $substitutions[$j] );

        # go through substitutions of this tree and check that one of the
        # substitutions does not already exist in the taxa list
        my @temp_taxa;
        for ( my $k = 0; $k < @substitute_taxa; $k++ ) {

            unless ( $in_tree{ $substitute_taxa[$k] } ) {
                push( @temp_taxa, $substitute_taxa[$k] );
            }
        }
        undef @substitute_taxa;
        @substitute_taxa = @temp_taxa;
        undef @temp_taxa;

        my $string = "\t\tSubbing: $higher_taxa[$j] = "
            . join( ', ', @substitute_taxa ) . "\n";
        print $string if $verbose;

        Bio::STK::replace_taxon_tree( \@trees, $higher_taxa[$j],
            \@substitute_taxa );
    }
    if ($altered) {
        unless ( Bio::STK::save_tree_file( $file, \@trees ) ) {
            die("Error saving $file\n");
        }
    }
}

# do the same for XML files...
if ( @xmlfiles > 0 ) {

    print("Processing XML files...\n") if $verbose;
    foreach my $file (@xmlfiles) {

        my $altered = 0;
        print("\t$file...\n") if $verbose;
        my $xml         = Bio::STK::read_xml_file($file);
        my @taxa_in_xml = Bio::STK::taxa_from_xml($file);

        my %in_xml;
        for (@taxa_in_xml) { $in_xml{$_} = 1 }

    TAXA: for ( my $j = 0; $j < @higher_taxa; $j++ ) {

            unless ( $in_xml{ $higher_taxa[$j] } ) {
                next TAXA;
            }
            $altered = 1;

            # prepare polytomy
            my @substitute_taxa = split( /,/, $substitutions[$j] );

            # go through substitutions of this tree and check that one of the
            # substitutions does not already exist in the taxa list
            my @temp_taxa;
            for ( my $k = 0; $k < @substitute_taxa; $k++ ) {

                #$substitute_taxa[$k] =~ s/_/ /g;
                unless ( $in_xml{ $substitute_taxa[$k] } ) {
                    push( @temp_taxa, $substitute_taxa[$k] );
                }
            }
            undef @substitute_taxa;
            @substitute_taxa = @temp_taxa;
            undef @temp_taxa;

            my $string = "\t\tSubbing: $higher_taxa[$j] = "
                . join( ', ', @substitute_taxa ) . "\n";
            print "$string" if $verbose;

            Bio::STK::replace_taxon_xml( $xml, $higher_taxa[$j],
                @substitute_taxa );
        }
        if ($altered) {
            unless ( Bio::STK::save_xml_file( $file, $xml ) ) {
                die("Error saving $file\n");
            }
        }
    }
}

print "All done!\n";

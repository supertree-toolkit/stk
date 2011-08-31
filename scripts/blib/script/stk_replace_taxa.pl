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

=head1 Replace Taxa

=head1 SYNOPSIS

stk_replace_taxa.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory in which replacements should occur 
   --file            file in which replacments should occur
   --taxa            file specifying which substitions to carry out            
   --old             taxon to be replaced
   --new             the new taxon. May be omitted, in which case old taxon is removed
   --verbose         verbose messages
   --reverse         the taxa file will contain taxa to keep with this flag on

One of C<dir> or C<file> is required. One of C<old> or C<taxa> is required.

=head1 OPTIONS 

=over 4

=item B<--dir>

A directory which contains tree files that require replacing.

=item B<--file>

The file (tree or XML) which has taxa that require replacing

=item B<--taxa>

A file containing the substitutions to be made. See full documentation for details

=item B<--old>

The old taxa to be replaced. Note that spaces in the taxon name must be replaced with _

=item B<--new>

The new taxa. Note that spaces in the taxon name must be replaced with _. If blank, C<old> will be deleted.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=back

One of C<file> or C<dir> must be specified. Either C<taxa> or C<old> must also be specified. 
C<new> can be ommitted to replace the original taxon.

=head1 DESCRIPTION

B<Replace Taxa> replaces a single taxon or multiple taxa with either
another taxon or multiple taxa as a polytomy. Replacement is done
on both tree files and XML files (if present). If a file is specified
only that file has the taxa replaced. 

A taxon can be deleted by specifying a blank new taxon.

All taxon names are B<case sensitive>.

Multiple replacements are achieved by supplying a "taxa file". This lists
"old taxa" and "new taxa" on individual lines in the file, seperated by an "="
sign. For example:
 old_taxon = new_taxon
 old_taxon2 = new_taxon1, new_taxon2, new_taxon3
 old_taxon3 = 

The first line above does a simple substitution for C<old_taxon> with C<new_taxon>.
The second line replaces C<old_taxon2> with a polytomy of C<new_taxon1>, C<new_taxon2>
and, C<new_taxon3> in a tree file and a simple substitution in an XML file. The third line
removes C<old_taxon3>. Note there are spaces B<either> side of the equals sign. These
spaces B<must> occur or the file is invalid.

In addition, the underscores (which are required for the tree file) are required here
also. However, they will be replaced by spaces in the XML file.

The script works on either a single file or directory of files (including subdirectories).

B<Warning>: This script simply overwrites existing data - please back up data before using it.

=head1 EXAMPLES

Remove all instances of "MRPOutgroup" from a dataset
 
 perl stk_replace_taxa.pl --dir /home/data/phylogenies --old MRPOutgroup

Replace taxa_1 with taxa_2 within a single tree file

 perl stk_replace_taxa.pl --file /home/data/tree1.tre --old taxa_1 --new taxa_2

=head1 REQUIRES

Perl 5.004, Carp::*, Bio::STK::*, Getopt::Long; Pod::Usage;

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

use Getopt::Long;
use Pod::Usage;
use lib "../lib";
use Bio::STK;
use Carp;
use strict;

my $man  = 0;
my $help = 0;

# get args...
my $dir       = '';
my $file      = '';
my $verbose   = '';
my $reverse   = '';
my $taxa_file = '';
my @old_taxa;
my @new_taxa;
my @keep_taxa;
$old_taxa[0] = '';

## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?' => \$help,
    man      => \$man,
    verbose  => \$verbose,
    'reverse|rev'  => \$reverse,
    'dir=s'  => \$dir,
    'file=s' => \$file,
    'old=s'  => \$old_taxa[0],
    'new=s'  => \$new_taxa[0],
    'taxa=s' => \$taxa_file
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2,
           -noperldoc => 1 ) if $man;

# check options
# check if both file and dir are specified. A check for at least one is
# done below.
if ( $dir eq '' && $file eq '' ) {
    die("Specify one of dir or file, not both\n");
    pod2usage();
}
if ( $old_taxa[0] eq '' && $taxa_file eq '' ) {
    die("Specifiy either an old taxa to replace or a taxa substitution file\n");
    pod2usage();
}

# check for at least old_taxon or a taxa file, new may be blank
if ( !defined( $old_taxa[0] ) && !defined($taxa_file) ) {
    die "You need to define one of new or taxa file. Exiting\n";a
    pod2uasge();
}

# Print warning - CTL C to quit
print("********************************************************\n");
print("*   WARNING: This program writes over existing data.   *\n");
print("* If you have not backed-up, hit CTRL-C NOW and do it! *\n");
print("********************************************************\n");

# let's give folk a chance to quit...
# note - don't want to add "press any key to continue" as we want batch mode...
# and I prefer this to adding a "--batch" flag
#...then again maybe a batch flag would be better with a "press enter to continue"?
sleep(3);


my $subs_file = 0;
my $ok        = 1;
# get all tree files
my @treefiles;
my $nTreesAltered = 0;
my @xmlfiles;
my $nXmlAltered   = 0;


if ( $file ne '' ) {
  if ($file =~ m/\.tre/) {
      push (@treefiles, $file);
  }
  if ($file =~ m/\.xml/) {
      push (@xmlfiles, $file);
  }
  print("Reading file $file...\n");
} elsif ($dir ne '')  {

    print("Scanning $dir...\n") if $verbose;
    
    # get all tree files
    @treefiles = Bio::STK::find_tree_files($dir);
    @xmlfiles  = Bio::STK::find_xml_files($dir);

} else {
    print("Specify one of dir or file\n");
    exit(0);
}

print("Starting substitutions...\n");

# construct substitutes if taxa file is specified
if ( defined $taxa_file && $taxa_file ne '' && !$reverse) {
    print("Scanning $taxa_file for substitutions to carry out...\n") if $verbose;
    undef @old_taxa;
    undef @new_taxa;
    Bio::STK::read_taxa_file($taxa_file, \@old_taxa, \@new_taxa);
    $subs_file = 1;
    if ($verbose) {
        print ("-------------- Substitutions from taxa file ---------------\n");
        # print summary
        print ("+----------------+---------------------------------+------+\n");
        print ("|  Old taxon     | New taxa (taxon)                |   N  |\n");
        print ("+----------------+---------------------------------+------+\n");

        for ( my $i = 0; $i < @old_taxa; $i++ ) {
            my @temp_new = split( /,/, $new_taxa[$i] );
            my $length = @temp_new;
            if ( $length > 1 ) {
                printf("| %14.14s | %14.14s...%14.14s | %4.4i |\n",$old_taxa[$i], $temp_new[0], $temp_new[ $length - 1 ], $length);
            } elsif ( $length == 1 ) {
                printf("| %14.14s | %31.31s | %4.4i |\n",$old_taxa[$i], $temp_new[0], $length);
            } else {
                printf("| %14.14s |         --deletion--            |   0  |\n",$old_taxa[$i]);
            }
        } 
        print ("+----------------+---------------------------------+------+\n");
        print ("\n");

    }
}
if ( defined $taxa_file && $taxa_file ne '' && $reverse ) {
    print("Scanning $taxa_file for substitutions to carry out...\n");
    open TAXALIST, "<$taxa_file";
    foreach my $line (<TAXALIST>) {
        chomp($line);              # remove the newline from $line.
        $line =~ s/^\s+//;
        $line =~ s/\s+$//; 
        $line =~ s/_/ /;
        push @keep_taxa, $line;
	    print "$line\n" if $verbose
    }
    foreach my $tree (@treefiles) {


    	# now invert the list, so we build up a subs file, deleting taxa not here
    	my @trees = Bio::STK::read_tree_file($tree);
    	my @taxa  = Bio::STK::taxa_from_tree($tree);
    	print "$tree\n" if $verbose;
        my @delete_me;
      	foreach my $taxon (@taxa) {
            unless (grep {$_ eq $taxon} @keep_taxa ) {
                print "Replacing $taxon\n" if $verbose;
            	# unless the taxon is in the keep taxa list, add a sub that deletes is
            	$taxon =~ s/ /_/g;
                push(@delete_me, $taxon); 
            }
        }
        Bio::STK::delete_taxa(\@trees,\@delete_me);

        if ( !Bio::STK::save_tree_file( $tree, \@trees ) ) {
            die("Could not save file: $tree\n");
        }
    }

    foreach my $xml (@xmlfiles) {

    	# now invert the list, so we build up a subs file, deleting taxa not here
        my $xml_data = Bio::STK::read_xml_file($xml);
    	my @taxa  = Bio::STK::taxa_from_xml($xml_data);
    	print "$xml\n" if $verbose;
      	foreach my $taxon (@taxa) {
            unless (grep {$_ eq $taxon} @keep_taxa ) {
            	# unless the taxon is in the keep taxa list, add a sub that deletes is
	        Bio::STK::replace_taxon_xml($xml_data,$taxon);
            }
        }

        if ( !Bio::STK::save_xml_file( $xml, $xml_data ) ) {
            die("Could not save file: $xml\n");
        }
        
    }

    exit;

}

# replace taxa in treefiles
foreach my $tree (@treefiles) {
       
    my @trees = Bio::STK::read_tree_file($tree);
    my @taxa  = Bio::STK::taxa_from_tree(@trees);
    my $altered = 0;

    print("Replacing in $tree...\n");

    # loop over subs file
    for ( my $i = 0; $i < @old_taxa; $i++ ) {

        my $replace = $old_taxa[$i];
        $replace =~ s/_/ /g;
        my @temp_new;
        # construct temp_new array, which may be from taxa_file,
        # the new flag, or be undefined. This last case means a
        # removal of old_taxa
        if ($subs_file) {
            if (defined $new_taxa[$i]) {
              @temp_new = split( /,/, $new_taxa[$i] );
            }
        } else {
            $temp_new[0] = $new_taxa[0];
        }
        my $is_in_tree = 0;
        foreach my $t (@trees) {
            if (Bio::STK::tree_contains($old_taxa[$i],$t)) {
               $is_in_tree = 1;
            }
        }
        # check if taxa is in the tree file
        if ( $is_in_tree ) {
            Bio::STK::replace_taxon_tree( \@trees, $old_taxa[$i], \@temp_new );
            $altered = 1;
            print("\tReplacing $old_taxa[$i]\n") if $verbose;
        }
    }
        
    if ( $altered ) {
        if ( !Bio::STK::save_tree_file( $tree, \@trees ) ) {
            die("Could not save file: $tree\n");
        }
        $nTreesAltered++;
    }
}

# replace taxa in XML
foreach my $xml_file (@xmlfiles) {
    
    my $xml = Bio::STK::read_xml_file($xml_file);
    my $altered = 0;

    print("Replacing in $xml_file...\n");

    # loop over subs file
    for ( my $i = 0; $i < @old_taxa; $i++ ) {

        my @temp_new;
        # construct temp_new array, which may be from taxa_file,
        # the new flag, or be undefined. This last case means a
        # removal of old_taxa
        if ($subs_file) {
            if (defined $new_taxa[$i]) {
              @temp_new = split( /,/, $new_taxa[$i] );
            }
        } else {
            $temp_new[0] = $new_taxa[0];
        }

        # check if taxa is in the tree file
        if ( Bio::STK::xml_contains_taxon( $old_taxa[$i], $xml ) ) {
            Bio::STK::replace_taxon_xml( $xml, $old_taxa[$i], @temp_new );
            $altered = 1;
            print("\tReplacing $old_taxa[$i]\n") if $verbose;
        }
    }
        
    if ( $altered ) {
        if ( !Bio::STK::save_xml_file( $xml_file, $xml ) ) {
            die("Could not save file: $xml_file\n");
        }
        $nXmlAltered++;
    }
}

print("Finished substituions\n--------------------\n") if $verbose;

if ($subs_file) {
    print("Sucessfully replaced taxa from $taxa_file from $dir.\n");
} else {
    print("Sucessfully replaced $old_taxa[0] from $dir.\n");
}
print("Replaced taxa in $nTreesAltered tree files");
if ( @xmlfiles > 0 ) {
    print(" and in $nXmlAltered XML files");
}
print("\n");


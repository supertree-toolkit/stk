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

=head1 Tree Permutation



=head1 SYNOPSIS

tree_permutation.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --file            a file that contains polyphyletic taxa. REQUIRED
   --verbose         print verbose messages
   
=head1 OPTIONS 

=over 4

=item B<--file>

a file which contains specially notation for polyphyly 

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=back

=head1 DESCRIPTION

B<Tree Permutation> generates multilpe trees based on a single input tree.
The input tree contains specially noted taxa which are polyphyletic or
are, perhaps sub-species, which need to be removed.

Taxa are denoted by % symbol at the end of the name.

A single file is output.

=head1 REQUIRES

Perl 5.004, Carp::*, Bio::STK::*, Getopt::Long;

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
use strict;

# get args
my $file    = '';
my $man     = 0;
my $help    = 0;
my $verbose = '';

## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?' => \$help,
    man      => \$man,
    verbose  => \$verbose,
    'file=s' => \$file
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($file eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}


my $ret = 0;

if ( $file eq '' ) {
    die "You need to specify a file with notation for polyphyletic taxa.\n";
}

# shared variables with permute function
our ( @trees, $tree_s );
our ( $duplicate_taxa, $temp_tree, $uniqueTaxa );
our $counting = 0;
our ( @numbers_nu, @uniqueNames, @trees_saved );

# local vars
my @names_d;
my @names;
my @tree = Bio::STK::read_tree_file($file);

# need to change any space to _ and ' need to be removed
$tree[0] =~ s/^\s+//;
$tree[0] =~ s/\s/_/g;
$tree[0] =~ s/\'//g;

# get taxa
my @names_r;
@names_r = Bio::STK::taxa_from_tree($file);

foreach my $name (@names_r) {
    if ( $name =~ m/%/ ) {

        # strip number and %
        $name =~ m/(.*)%\d/i;

        # will keep previous pushes
        push( @names_d, $1 );
        push( @names,   $1 );
    }
    elsif ( $name =~ m/\w+/ ) {
        push( @names, $name );
    }
}

# make duplicated names unique
# my $prev        = "ThereWillNotBeATaxonWithThisName!";
# my @names_d_u   = grep( $_ ne $prev && ( ($prev) = $_ ), @names_d );
my %sen       = ();
my @names_d_u = grep { !$sen{$_}++ } @names_d;
my %seen      = ();
@uniqueNames = grep { !$seen{$_}++ } @names;

# find numbers of each name
$uniqueTaxa = @uniqueNames;
print("There are $uniqueTaxa unique taxa\n") if $verbose;
$duplicate_taxa = @names_d_u;

print "$duplicate_taxa duplicates Found...\n" if $verbose;
print "Taxa\tNumber of Duplicates\n"          if $verbose;
for ( my $i = 0; $i < $uniqueTaxa; $i++ ) {
    my $count = 0;
    print $uniqueNames[$i], "\t" if $verbose;
    foreach my $name (@names_r) {
        if ( $name =~ m/%/ ) {
            $name =~ m/(.*)%\d/i;
            if ( $1 eq $uniqueNames[$i] ) {
                $count++;
            }
        }
    }
    $numbers_nu[$i] = $count;
    print $numbers_nu[$i], "\n" if $verbose;
}

&permute( 0, $tree[0] );

my $nOutput = @trees_saved;

print("Created $nOutput trees\n") if $verbose;

# need to check that trees are not equal to each other
my @remove_list;
for ( my $i = 0; $i < $nOutput; $i++ ) {
    my $tree = $trees_saved[$i];
    print("\t$tree\n") if $verbose;
    for ( my $j = $i + 1; $j < $nOutput; $j++ ) {
        if ( Bio::STK::tree_equals( $tree, $trees_saved[$j] ) ) {

            # remove $j tree
            push( @remove_list, $j );
        }
    }
}
my $nRemove = @remove_list;
print("Removing $nRemove trees as they are identical to others...\n")
    if $verbose;

# now remove trees
# note what we need to do is adjust the previous index as we remove
# elements - this is what notch does.
my $notch = 0;
foreach my $remove (@remove_list) {
    splice( @trees_saved, $remove - $notch, 1 );
    $notch++;
}

$nOutput = @trees_saved;

if ( Bio::STK::save_tree_file( $file . "_permute", \@trees_saved ) ) {
    print "Successfully saved $nOutput trees to $file._permute.\n";
}

sub permute {
 
    my $i        = 0;
    my $n        = $_[0];
    my $temp     = $_[1];
    my $tempTree = $temp;

    if ( $n < $uniqueTaxa && $numbers_nu[$n] == 0 ) {
        &permute( ( $n + 1 ), $tempTree );
    }
    else {
        if ( $n < $uniqueTaxa ) {
            for ( $i = 1; $i <= $numbers_nu[$n]; $i++ ) {
                if ($tempTree) {
                    undef $tempTree;
                }
                $tempTree = $temp;
                my $t = $temp;
                $t =~ s/\(|\)//g;
                my @taxa = split( ',', $t );

                #print "doing iteration $n,$i, starting from $tempTree\n";
                # iterate over nodes
                foreach my $name (@taxa) {
                    my $index = index( $name, '%' );
                    my $short_name = substr( $name, 0, $index );
                    my $current_unique_name = $uniqueNames[$n];
                    $current_unique_name =~ s/ /_/;
                    #print "$name - $index - $short_name - $current_unique_name\n";
                    if ( $index > 0 and $short_name eq $current_unique_name )
                    {
                        if ( $name ne $current_unique_name . "%" . $i ) {
                            my @t;
                            $t[0] = $tempTree;
                            Bio::STK::replace_taxon_tree( \@t, $name );

                            $tempTree = $t[0];
                            $tempTree =~ s/:\d+//g;
                        }
                    }
                }
                if ( $n < $uniqueTaxa ) {
                    &permute( ( $n + 1 ), $tempTree );
                }
            }
        }
        else {

            # remove any remaining %\d from tree
            my $tempTree = $_[1];
            $tempTree =~ s/\%\d+//g;
            print "Adding tree to store: $tempTree from iteration $n,$i\n"
                if $verbose;
            push( @trees_saved, $tempTree );
        }
    }
}

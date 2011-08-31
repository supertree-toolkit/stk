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

=head1 Check Overlap




=head1 SYNOPSIS

check_overlap.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing Tree files. Required
   --verbose         print verbose messages
   --nCluster        number of taxa that trees must share. Default value is 2.
   --graphic         output a "dot" file that can be loaded into GraphViz
   --compressed      output a "dot" file where clusters are shown, rather than individual trees

=head1 OPTIONS 

=over 4

=item B<--dir>

A directory which contains tree files.

=item B<--nCluster>

The number of taxa required for trees to "cluster".

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--graphic>

Ouput a "dot" file that can be loaded into GraphViz to produce a graphical representation of the connectivity.
A key file (key.csv) is also output containing the legend for the graphic

=item B<--compressed>

Large datasets can produce "dot" files too large for neato to produce a graphic. If this is the case, using this
option produce a graph of "clusters" of trees only, where a node represents a cluster of trees.

=back

C<dir> scans all subdirectories also, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Check Overlap> checks that trees in a directory have sufficient taxonomic
overlap to be used as source trees in supertree construction. Each tree must
contain at least two taxon also contained in another tree (Nixon, 1996). 

Check Overlap checks that a dataset fulfils this criterion. A single "cluster" of
connected trees is the ideal output as this means all trees share at least two common
taxa with at least one other tree. The minimum requirement for overlap to occur can be 
changed to create "more connected" data. Any trees that do not share the minimum number of taxa
with at least one other tree should be removed fro the dataset. A warning is printed is more
than one cluster is found.

If more than one cluster is found, you should use the C<--graphic> option to visualise the
data connectivity. For large datasets, the C<--compressed> flag should also be used. 
The C<--graphic>> output creates input for GraphViz, a free program that can display the
overlap graphically. The C<--compressed> flag produces output where "clusters" are 
represented by nodes. By definition, there will be no edges on this graph.
Without this flag, each node is a tree, with edges between 
nodes representing minimal connectivity.

Nixon, K., Carpenter, J., 1996. On simultaneous analysis. 
Cladistics 12, 221-241. 

=head1 REQUIRES

Perl 5.004, Carp::*, Bio::STK::*, Getopt::Long, Graph::*, Graph::Writer::Dot;

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

use Getopt::Long;
use Pod::Usage;
use Carp;
use File::Spec::Functions;
use lib "../lib";
use Bio::STK;
use Graph;
use Graph::Writer::Dot;
use strict;

# get args
my $dir      = '';
my $nCluster = 2;

# standard help messages
my $man  = '';
my $help = '';
our $verbose = '';
our $compressed = '';
our $graphic_output = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'     => \$help,
    man          => \$man,
    verbose      => \$verbose,
    'dir=s'      => \$dir,
    'nCluster=i' => \$nCluster,
    'compressed' => \$compressed,
    'graphic'    => \$graphic_output
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}

# run overlap function on DIR
if ( defined $nCluster ) {
    check_overlap( $dir, $nCluster );
}
else {
    check_overlap($dir);
}


sub check_overlap {

    my ( $dir, $nCluster ) = @_;
    my @taxa;
    my $number = 0;
    my @counting;
    my $graph = Graph->new();

    if ( !$nCluster ) {
        $nCluster = 2;
    }

    unless ( -d $dir ) {
        croak("Directory $dir does not exist\n");
    }

    my @treefiles = Bio::STK::find_tree_files($dir);

    foreach my $file (@treefiles) {

        print("Reading taxa from $file...\n") if $verbose;
        my @taxaList = Bio::STK::taxa_from_tree($file);
        $taxa[$number] = [@taxaList];
        $number++;
        my $length = @taxaList;
        push( @counting, $length );
    }

    my $taxaCount = @taxa;
    my $cols      = 0;
    my @tempArray;
    my %hash;
    for ( my $i = 0; $i < $taxaCount; $i++ ) {
        undef @tempArray;

        my $count = 0;
        $cols = $counting[$i];
        for ( my $j = 0; $j < $cols; $j++ ) {
            $tempArray[$j] = $taxa[$i][$j];
        }
        $hash{$_}++ foreach @tempArray;
    }

    # go through the array and match trees that have more than nCluster taxa in common
    my @matches;
    our @totalMatches; # needed by recursive function below
    print("Creating matches...\n") if $verbose;
    for ( my $i = 0; $i < $number; $i++ ) {
        print("Processing tree number $i...\n") if $verbose;
        for ( my $j = 0; $j < $i + 1; $j++ ) {
            $matches[$j] = 0;
        }
        for ( my $j = $i + 1; $j < $number; $j++ ) {
            my $cols1 = $counting[$i];
            my $cols2 = $counting[$j];
            my $count = 0;
            for ( my $n = 0; $n < $cols1; $n++ ) {
                for ( my $m = 0; $m < $cols2; $m++ ) {
                    if ( $taxa[$i][$n] eq $taxa[$j][$m] ) {
                        $count++;
                    }
                }
            }
            $matches[$j] = $count;
        }
        $totalMatches[$i] = [@matches];
        undef(@matches);
    }
    
    # construct graph - node=tree, edge=satisfies minimum taxa connectivity
    # First add all nodes
    for ( my $i = 0; $i < $number; $i++ ) {
        $graph->add_vertex($i);
    }
    # now add edges between nodes
    for ( my $i = 0; $i < $number; $i++ ) {
        for ( my $j = 0; $j < $number; $j++ ) {
            if ($totalMatches[$i][$j] >= $nCluster) {
                $graph->add_edge($i,$j);
            }
        }
    }

    # we want an undirected graph, so...
    my $undirected = $graph->undirected_copy_graph;

    my @cc = $undirected->connected_components();
    my $nClusters = @cc;

    # report results
    if ($nClusters == 1) {
        print "\n======== OK ========\n";
        print "There was only $nClusters cluster found.\n";
        print "Your data are sufficiently well connected by $nCluster or more taxa\n";
        print "---------------------------------------------------------------------\n";
    } else {
        print "\n======== WARNING ========\n";
        print "There were $nClusters clusters found, which means some trees are not\n";
        print "connected by $nCluster or more taxa. You may need to remove the trees\n";
        print "that are not connected to the main group of connected trees.\n";
        
        if (not $graphic_output) {
            print "\nRun this script again with --graphic (and --compressed if the data are large)\n";
            print "to see which trees are not sufficiently well connected\n";
        }
        print "---------------------------------------------------------------------\n";
    }
    
    # standard graphic output
    if ($graphic_output) {
            if (not $compressed) {
                # print out a key to the numbers that appear in the dot file (later)
                # this allows the numbers in the dot file to be linked to a paper and tree
                # The compressed format has a different key file syntax
                my $out = catfile( $dir, "key.csv" );
                print("Creating key file for $number trees. Key saved to $out\n")
                    if $verbose;
                open( FILE, ">$out" ) or die "Can't open key file";
                print FILE "Node number, tree file\n";
                for ( my $i = 0; $i < $number; $i++ ) {
                    print FILE "$i,$treefiles[$i]\n";
                }
                close(FILE);
                $out = catfile( $dir, "tree$nCluster.dot" );
                print("Constructing dot file...\n") if $verbose;
                my $writer = Graph::Writer::Dot->new();
                $writer->write_graph($undirected, $out);
                print "Saved cluster graph output into the file 'tree$nCluster.dot' in $dir \n";
                print "with corresponding key file: key.csv\n";

            } else {
                # compressed format - instead of showing each tree, only show "clusters" of trees
                # This will be, by definition, just unconnected nodes. We can scale the size by the 
                # number of trees in each "cluster"
                my $cluster_graph = Graph->new();
                my $key = catfile( $dir, "key-compressed.csv" );
                print("Creating key file for $number trees. Key saved to $key\n")
                    if $verbose;
                open( FILEK, ">$key" ) or die "Can't open key file";
                print FILEK "Node number, tree file\n";

                my $out = catfile( $dir, "tree$nCluster-compressed.dot" );
                print("Constructing compressed dot file...\n") if $verbose;  
                my $cluster = 0;
                foreach my $c (@cc) {
                    foreach my $i (@{$c}) {
                        print FILEK "$cluster,$treefiles[$i]\n";
                    }
                    $cluster_graph -> add_vertex($cluster);
                    $cluster++;
                }
                close FILEK;
                my $writer = Graph::Writer::Dot->new();
                $writer->write_graph($cluster_graph, $out);
                print "Saved cluster graph output into the file 'tree$nCluster-compressed.dot' in $dir \n";
                print "with corresponding key file: key-compressed.csv\n";
            }
    }

    return 1;

}


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

=head1 Check Substitutions



=head1 SYNOPSIS

check_substitutions.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --file            substitutions file
   --dir             directory that contains the data
   --verbose         verbose messages
   --output          output to file rather than standard out

=head1 OPTIONS 

=over 4

=item B<--dir>

A directory of tree and optionally XML files

=item B<--file>

A substitutions file to check

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--output>

File to send output to

=back

You must specify a C<file>. If C<dir> is also specified the taxa within the substitution
file are checked against the taxa in the dataset. Any taxa in the subs file that are
not in the data set are flagged.

=head1 DESCRIPTION

B<Check Substitutions> ensures that a substitution file as used in replace_taxa.pl is
of the correct format. Additionally, if a dataset is specified, it checks the
substitutions that would be made by replace_taxa.pl are alreday in the data.

For example, if your substitution file contains:
taxa_1 = fred, foo, bar

taxa_1 would be replaced with a polytomy of fred, foo, bar. Specifying a dataset
ensures that fred, foo, and bar are in the data - i.e. you are not introducing 
additional taxa into the dataset. You may B<want> to do this and hence why replace_taxa.pl
does allow this, but this is generally not a good idea, and this script checks you really
mean this action.

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
my $dir     = '';
my $file    = '';
my $verbose = '';
my $output  = 0;

## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    verbose    => \$verbose,
    'dir=s'    => \$dir,
    'file=s'   => \$file,
    'output:s' => \$output,
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($file eq '' ) {
    print("You must specify a file to check\n");
    pod2usage(2);
    exit();
}

GetOptions();

# check options
# a file should be specified
if ( $file eq '' ) {
    die("A file to check must be specified\n");
}

print $output;
if ( $output ne 0 ) {
    if ( $output eq '' ) {
        if ($dir ne '') {
            $output = File::Spec->catfile( $dir, "checks.txt" );
        } else {
            # grab the directory where $file lives
            my ($volume,$directories,$f) = File::Spec->splitpath( $file );
            $output = File::Spec->catfile( $directories, "checks.txt" );
        }
    }
}
print STDOUT "Checking substitution file $file...\n";
if ($output) {
    print STDOUT "Will save output to $output\n";
}

# create arrays
# read in substitutions file and create arrays
my @new_taxa;
my @old_taxa;
my $nSubs = Bio::STK::read_taxa_file($file,\@old_taxa,\@new_taxa);

# work out total number of taxa involved here
my $nTaxa = 0;
for ( my $i = 0; $i < @new_taxa; $i++ ) {
    my @temp_new = split( /,/, $new_taxa[$i] );
    $nTaxa += @temp_new;
}

# print data summary
if ($output) {
    open STDOUT, ">$output";
}

print STDOUT ("\n============================================\n");
print STDOUT ("Summary of substitution file: $file\n");
print STDOUT ("============================================\n\n");

# did this work? Does it match what the user thought?
if ( @new_taxa != $nSubs ) {
    print(
        "Something went wrong reading the file, see below to check everything is as expected\n"
    );
}

# print table
print STDOUT ("Number of subs:       $nSubs\n");
print STDOUT ("Number of new taxa:   $nTaxa\n");

# print summary
print STDOUT ("+----------------+---------------------------------+------+\n");
print STDOUT ("|  Old taxon     | New taxa (taxon)                |   N  |\n");
print STDOUT ("+----------------+---------------------------------+------+\n");

for ( my $i = 0; $i < @old_taxa; $i++ ) {
    my @temp_new = split( /,/, $new_taxa[$i] );
    my $length = @temp_new;
    if ( $length > 1 ) {
        printf STDOUT (
            "| %14.14s | %14.14s...%14.14s | %4.4i |\n",
            $old_taxa[$i], $temp_new[0], $temp_new[ $length - 1 ], $length
        );
    }
    elsif ( $length == 1 ) {
        printf STDOUT (
            "| %14.14s | %31.31s | %4.4i |\n",
            $old_taxa[$i], $temp_new[0], $length
        );
    }
    else {
        printf STDOUT (
            "| %14.14s |         --deletion--            |   0  |\n",
            $old_taxa[$i]
        );
    }
}
print STDOUT ("+----------------+---------------------------------+------+\n");
print STDOUT "\n\n\n";

print STDOUT "Checking for duplicated taxa in a single substitution...\n";
# check if duplicated taxa are listed in a single substitution
my $nDupes = 0;
for ( my $i = 0; $i < @new_taxa; $i++ ) {
    my @temp_new = split( /,/, $new_taxa[$i] );
    @temp_new = sort(@temp_new);
    my $last_taxa = '';
    foreach my $taxa (@temp_new) {
      if ($taxa eq $last_taxa) {
        $nDupes++;
        print STDOUT "\tFound duplicate taxa being substituted in $old_taxa[$i]: $taxa\n";
      }
      $last_taxa = $taxa;
    }
}
if ($nDupes == 0){
    print ("Found none - data OK\n");
}

print STDOUT "\n\n";

# if dir is set, then check current taxa
if ( $dir ne '' ) {

    print STDOUT ("\n============================================\n");
    print STDOUT ("Checking new taxa are already in dataset in $dir\n");
    print STDOUT ("============================================\n\n");

    my @taxa = Bio::STK::get_taxa_list($dir);

# we need to "add" generic taxa (i.e. if we have Gallus gallus in the data
# we also need to add Gallus) as the subs file might have genera in (to save listing
# a load of species!).
    my @higher_taxa;
    for ( my $i = 0; $i < @taxa; $i++ ) {
        if ( $taxa[$i] =~ m/ / ) {
            my $genus = substr( $taxa[$i], 0, index( $taxa[$i], ' ' ) );
            push( @higher_taxa, $genus );
        }
    }

    push( @taxa, @higher_taxa );
    my %saw;
    undef %saw;
    @taxa = grep( !$saw{$_}++, @taxa );
    @taxa = sort(@taxa);
    my %in_data;
    for (@taxa) { $in_data{$_} = 1 }

    my @all_new;

    # uniqify taxa from subs file
    for ( my $i = 0; $i < @new_taxa; $i++ ) {
        my @temp_new = split( /,/, $new_taxa[$i] );
        push( @all_new, @temp_new );
    }

    undef %saw;
    @all_new = grep( !$saw{$_}++, @all_new );
    @all_new = sort(@all_new);

    foreach my $taxa (@all_new) {

        # might have spaces in the subs file
        #$taxa =~ s/ /_/g;
        unless ( $in_data{$taxa} ) {
            print("\tDid not find $taxa in data. Is this a synonym?\n");
        }
    }

}

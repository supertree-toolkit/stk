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

=head1 Amalgamate Trees

=head1 SYNOPSIS

stk_amalgamate_trees.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --file            Tree file. Required
   --verbose         print verbose messages
   --output          output file. Default is to overwrite input tree

=head1 OPTIONS 

=over 4

=item B<--file>

a tree file with no taxa block. B<Required>.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=item B<--output>

Where to save output. Default is to overwite input file.

=back

=head1 DESCRIPTION

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
my $output  = '';
my $file    = '';

# Parse options and print usage if there is a syntax error,
# or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    verbose    => \$verbose,
    'output=s' => \$output,
    'file=s'    => \$file
) or pod2usage(2);
pod2usage(1) if ($help);
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($file eq '' ) {
    print("You must specify a file\n\n");
    pod2usage(1);
    exit();
}

my @t = Bio::STK::read_tree_file($file);

if ($output eq '') {
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

    unless ( Bio::STK::save_tree_file( $file, \@t ) ) {
        die("Error saving file to: $file\n");
    }


} else {
    unless ( Bio::STK::save_tree_file( $output, \@t ) ) {
        die("Error saving file to: $output\n");
    }
}


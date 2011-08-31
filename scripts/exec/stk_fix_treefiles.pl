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

=head1 Fix Treefiles



=head1 SYNOPSIS

fix_treefiles.pl [options]


 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing Tree files to fix
   --file            a file to fix
   --verbose         print verbose messages

=head1 OPTIONS 

=over 4

=item B<--dir>

A directory which contains tree files that require fixing.

=item B<--file>

A file to fix.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK


=head1 DESCRIPTION

B<Fix Treefiles> is a simple script to fix some common problems with tree files created
using various programs. 

TreeView (Page, 1996):
TreeView create a tree with the following description:

 UTREE * tree_1 = ((1,(2,(3,(4,5)))),(6,7));

UTREE * is not a supported part of the NEXUS format (as far as Bio::NEXUS
(Hladish et. al., 2007) is concerned). stk_check_data.pl will report a formatting error with
a file like this, so this script will fix this by replacingthe above with:

 tree_1 = [&u] ((1,(2,(3,(4,5)))),(6,7));

TNT (Goloboff et al, 2008):
Outputed NEXUS tree files from TNT contain "begin trees ;" with a space bewteen the "trees" and
the ";". Bio::NEXUS does not recognise this as the begining of a tree block and skips
all the trees. stk_check_data.pl will pick this error up, removing the space.

The script works on either a file or directory.

=head2 References

Goloboff, P. A. and Farris, J. S. and Nixon, K. C., 2008.
TNT, a free program for phylogenetic analysis. Cladistics 24 (5),
774-786. DOI: 10.1111/j.1096-0031.2008.00217.x

Hladish, T., Gopalan, V., Liang, C., Qiu, W., Yang, P., Stoltzfus, A., 2007. 
Bio::Nexus: A Perl API for the Nexus format for comparative biological data. 
BMC Bioinformatics 8, 191. 

Page, R.D.M., 1996. Treeview: An application to display phylogenetic trees on 
personal computers. Computer Applications in the Biosciences 12, 357-358. 

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
use Carp;
use strict;

# get args
my $dir     = '';
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
    'dir=s'  => \$dir,
    'file=s' => \$file
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

my $ret = 0;

if ( $dir eq '' && $file eq '' ) {
    print "You need to specify a directory or a file to fix\n";
    pod2usage();
    die();
}

if ( $file ne '' ) {
    $ret = fix_treeview_files($file);
    $ret = fix_tnt_files($file);

}
elsif ( $dir ne '' ) {
    my @treefiles = Bio::STK::find_tree_files($dir);
    foreach my $tree (@treefiles) {
        fix_treeview_files($tree);
        fix_tnt_files($tree);
        $ret++;
    }
}

print("Sucessfully fixed tree files.\nProcessed $ret trees\n");

sub fix_tnt_files {

    my ($file) = @_;
    my $text;
    my $n = 0;

    unless ( -e $file ) {
        croak("File $file not found\n");
    }

    {
        local ( $/, *FH );
        open( FH, $file ) or die "Could not load in file $file: $!\n";
        $text = <FH>;
        close FH;
    }

    if ( $text =~ m/begin trees \;/i ) {

        print("Fixing $file\n") if $verbose;

        # search and replace "UTREE * name =" with "tree name = "
        $text =~ s/begin trees \;/begin trees\;/i;

        open( my $fh, ">$file" )
            || croak("can't create $file $!");
        print $fh $text;
        close(FH);
        $n++;
    }
    else {
        print("TNT fix: $file OK\n") if $verbose;
        $n++ if $verbose;  # does this make sense? Only report the files printed
                           # or those that are fixed if not verbose output?
    }

    return $n;
}
;


sub fix_treeview_files {

    my ($file) = @_;
    my $text;
    my $n = 0;

    unless ( -e $file ) {
        croak("File $file not found\n");
    }

    {
        local ( $/, *FH );
        open( FH, $file ) or die "Could not load in file $file: $!\n";
        $text = <FH>;
        close FH;
    }

    if ( $text =~ m/UTREE\s?\*\s?(.+)\s?=\s/ ) {

        print("Fixing $file\n") if $verbose;

        # search and replace "UTREE * name =" with "tree name = "
        $text =~ s/UTREE\s?\*\s?(.+)\s?=\s/TREE $1 = [&u] /i;

        open( my $fh, ">$file" )
            || croak("can't create $file $!");
        print $fh $text;
        close(FH);
        $n++;
    }
    else {
        print("Treeview fix: $file OK\n") if $verbose;
        $n++ if $verbose;  # does this make sense? Only report the files printed
                           # or those that are fixed if not verbose output?
    }

    return $n;

}
;

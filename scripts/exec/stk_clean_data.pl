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

=head1 Clean Data


=head1 SYNOPSIS

clean_data.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing XML files. Required
   --dryrun          dry run only
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

=item B<--dryrun>

Don't delete the directories, but list them instead.

=back

If C<dir> is specified all subdirectories will also be scanned, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Clean Data> deletes directories within the dataset that contain less than three
taxa. The check is made on the XML file only. Run the check_data script first
to ensure your data is as you expect. The script takes care of checking 
sub-directories of an author/paper directory before deleting the author/paper
directory.

Note that hidden files (such as those from SVN or CVS) are a problem for the
last part of this script where empty directories are deleted. If your dataset
contains hidden files, then the directories will not get deleted.

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
use File::Find;
use Pod::Usage;
use File::Remove qw(remove);
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
my $dryrun = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
    verbose    => \$verbose,
    'output:s' => \$output,
    'dir=s'    => \$dir,
    dryrun     => \$dryrun
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
my $nDeleted = 0;
my @to_delete;

if ( $nXML > 0 ) {
    print("\nScanning XML files...\n") if $verbose;
    foreach my $file (@xml_files) {

        my $xml = Bio::STK::read_xml_file($file);
        # grab current directory from file
        my($filename, $directories, $suffix) = fileparse($file);
        if ($xml) {
            my $nTaxa = 0;
            my $no_taxa = 0;
            if (not defined (@{ $xml->{Taxa}->[0]->{List} })) {
                $no_taxa = 1;
            }
            # contains taxa
		    if (not $no_taxa) {
                my @taxa_names = Bio::STK::taxa_from_xml($xml);
		        $nTaxa = @taxa_names;
            }

            if( $nTaxa < 3 ) {
                # grab any files in the directory where the current
                # xml file resides
                opendir(DIR, $directories);
                while (my $item = readdir(DIR)) {
                    next unless (-f "$directories/$item");
                    push @to_delete, "$directories/$item";
                }
            }
        }
    }

    foreach my $file (@to_delete) {
        if ($dryrun) {
            print "Will delete: $file \n";
        } else {
            remove $file;
        }
    }

    # now need to clean up empty directories
    if (not $dryrun) {
        chdir($dir);
        # will remove only empty directories
        finddepth(sub { rmdir $_ if -d }, '.');
    }
} else {
    print("No XML files found - did you specify the correct directory?\n");
    exit;
}
$nDeleted = @to_delete;
print("Should have deleted $nDeleted files in total\n");


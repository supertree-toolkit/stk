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

=head1 Create Bibliography



=head1 SYNOPSIS

create_bibliography.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             directory containing XML files. Required
   --verbose         print verbose messages
   --output          direct output to specified file

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
Directs output to the specified file. If this flag is not turned on the
output is put in refs.bib in C<dir>.

=back

Specifing C<dir> will search all subdirectories also, apart from those
excluded by STK.

=head1 DESCRIPTION

B<Create Bibliography> will generate a bibtex file from the source references in the dataset. This script will
only work when XML files are present in the directory. A single reference is generated for each unique title
contained; in other words, if a source study has multiple tree files, each with a XML file, only one source
reference will be generated. A unique reference key is also generated to make for easy citing.

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
my $output  = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'   => \$help,
    man        => \$man,
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


if ( $output eq '' ) {
    $output = File::Spec->catfile( $dir, "refs.bib" );
}
open FILE, ">$output";

# grab all xml files
my @xml_files   = Bio::STK::find_xml_files($dir);
my %short_names = Bio::STK::get_short_study_name(@xml_files);
my $last_ref    = '';
my $bibtex      = '';

for my $file (
    sort { $short_names{$a} cmp $short_names{$b} }
    keys %short_names
    )
{

    my $ref = $short_names{$file};
    print "$ref\n";
    next if ( $last_ref eq $ref );

    print "Parsing $file...\n" if $verbose;

    my $xml = Bio::STK::read_xml_file($file);

    my $bibtex_entry = '';

    # easiest way to tell if it's a book or not is to check
    # the book title
    my $booktitle = $xml->{Source}->[0]->{Booktitle}->[0];

    # book or article?
    if ( ref( $xml->{Source}->[0]->{Booktitle}->[0] ) ne "HASH" ) {
        $bibtex_entry .= '@BOOK{';
    }
    else {
        $bibtex_entry .= '@ARTICLE{';
    }

    # add key
    $bibtex_entry .= $ref . ",\n";

    # add author
    # Bit tricky - proper format is Last, F. N. and Next, G. and ...
    # This catches most, but some will need editing by hand
    my $authors = $xml->{Source}->[0]->{Author}->[0];
    # Tries to insert the correct "and" where XML contains Surname, F., 
    $authors =~ s/\., /\. and /g;
    # replaces AND with and
    $authors =~ s/ AND / and /g;
    # This catches the case N. Surname, H. Smith
    $authors =~ s/(\w\. \w+), (\w\. \w+)/$1 and $2/g;
    # This catches the case N. Surname, H. I. Smith
    $authors =~ s/(\w\. \w+), (\w\. \w\. \w+)/$1 and $2/g;
    # This catches the case N. Surname, H. I. M. Smith
    $authors =~ s/(\w\. \w+), (\w\. \w\. \w\. \w+)/$1 and $2/g;
    # Sort out format like Last, I. N. Last2, I. N. Last3 I. N.
    $authors =~ s/(\w+, (\w\. )+) (\w)+,/$1 and $3/g;
    # remove extra commas
    $authors =~ s/, and/ and/g;
    $bibtex_entry
        .= "\tauthor = \"" . $authors . "\",\n";

    # add common article details
    $bibtex_entry .= "\tyear = \"" . $xml->{Source}->[0]->{Year}->[0] . "\",\n";
    # Note the {} - retain capitalisation
    $bibtex_entry .= "title = {" . $xml->{Source}->[0]->{Title}->[0] . "},\n";
    $bibtex_entry .= "\tpages = \"" . $xml->{Source}->[0]->{Pages}->[0] . "\",\n";

    if ( ref( $xml->{Source}->[0]->{Booktitle}->[0] ) ne "HASH" ) {
        $bibtex_entry .= "\tbooktitle = {"
            . $xml->{Source}->[0]->{Booktitle}->[0] . "},\n";

        # we should have publisher details in the XML
        # we should have editors in the XML
    }
    else {
        $bibtex_entry
            .= "\tjournal = \"" . $xml->{Source}->[0]->{Journal}->[0] . "\",\n";
        $bibtex_entry
            .= "\tvolume = \"" . $xml->{Source}->[0]->{Volume}->[0] . "\",\n";
        if ( $xml->{Source}->[0]->{Number}->[0] ) {
            $bibtex_entry
                .= "\tnumber = \"" . $xml->{Source}->[0]->{Number}->[0] . "\",\n";
        }

    }
    $bibtex_entry .= "}\n";
    # remove any ampersands
    $bibtex_entry =~ s/\&/\\&/;

    $bibtex = $bibtex . $bibtex_entry;

    $last_ref = $ref;
}

print "Saving bibtex file to $output\n" if $verbose;
print FILE $bibtex;

close FILE;

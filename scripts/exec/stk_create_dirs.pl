#!/usr/bin/perl -w
#
#    STK - Perl tools to help process data for Supertree construction
#    Copyright (C) 2010, Jon Hill and Katie Davis. All rights reserved.
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

=head1 Create Directories

=head1 SYNOPSIS

create_dirs.pl [options]

 Options:
   --help            brief help message
   --man             full documentation
   --dir             path to the storage dir. Required
   --verbose         print verbose messages
   --output          output to a file, rather than standard output
   --bib             BibTex file. Required

=head1 OPTIONS 

=over 4

=item B<--dir>

Path to the storage dir. The database will be created here. B<Required>.

=item B<--bib>

A BibTex file from which directory names and the base XML file will be created. B<Required>.

=item B<--help>

Print a brief help message and exits.

=item B<--man>

Prints the manual page and exits.

=item B<--verbose>

Print verbose messages

=back

=head1 DESCRIPTION

The script takes a BibTex file and creates the database structure. The directories will have
the following format:
Base_Dir/
	Author_year/author_year.xml
	Author2_year/author_year.xml
	...
	AuthorN_year/author_year.xml

The XML files will be created with the correct bibliographic metadata, such 
as journal details and paper titles.

=head1 REQUIRES

Perl 5.004, Bio::STK::*, Getopt::Long; Pod::Usage; Carp::*; Text::BibTex

=head1 FEEDBACK

All feedback (bugs, feature enhancements, etc.) are all greatly appreciated. 

=head1 AUTHORS

 Jon Hill (jon.hill@imperial.ac.uk)
 Katie Davis (k.davis@udcf.gla.ac.uk)

=cut

use Getopt::Long;
use Pod::Usage;
use Carp;
use lib "../lib";
use Bio::STK;
use strict;
use Text::BibTeX;
# get args
my $dir = '';

# standard help messages
my $man     = '';
my $help    = '';
my $verbose = '';
my $bib = '';
## Parse options and print usage if there is a syntax error,
## or if usage was explicitly requested.
GetOptions(
    'help|?'       => \$help,
    man            => \$man,
    verbose        => \$verbose,
    'bib=s'        => \$bib,
    'dir=s'        => \$dir
) or pod2usage(2);
pod2usage(2) if ( $help );
pod2usage( -verbose => 2 ,
          -noperldoc => 1 ) if $man;

if ($dir eq '' ) {
    print("You must specify a directory\n");
    pod2usage(2);
    exit();
}
if ($bib eq '' ) {
    print("You must specify a bibliography file\n");
    pod2usage(2);
    exit();
}

   
my $bibfile = new Text::BibTeX::File $bib;
my $nEntries = 0;

while (my $entry = new Text::BibTeX::Entry $bibfile) {
	next unless $entry->parse_ok;

	# extract authors and years and other data
        my $year = $entry->get ('year');
	my @authors = $entry->split ('author');
        my @names = $entry->names ('author');
	my $nAuthors = @authors;
	my $publisher;
	my $booktitle;
	my $title;
	my $vol;
	my $journal;
	my $editor;
	my $pages = $entry->get ('pages');
	if ($entry->exists ('publisher')) {
		$publisher = $entry->get ('publisher');
		$booktitle = $entry->get ('booktitle');
		$editor = $entry->get ('editor');
		$title = '';
		$journal = '';
		$vol = '';
	} else {
		$publisher = '';
		$booktitle = '';
		$editor = '';
		$title = $entry->get ('title');	
		$vol = $entry->get ('volume');
		$journal = $entry->get ('journal');
	}
	# remove latex stuff
	$journal =~ s/\{//g;
	$journal =~ s/\}//g;
	$pages =~ s/\{//g;
	$pages =~ s/\}//g;
	$title =~ s/\{//g;
	$title =~ s/\}//g;
	$booktitle =~ s/\{//g;
	$booktitle =~ s/\}//g;
	$publisher =~ s/\{//g;
	$publisher =~ s/\}//g;

	# construct "short name"
	# Smith_2002
        # Smith_Jones_2002
        # Smith_etal_2002
        my $short_name;
        if ($nAuthors == 1) {
		# $names->part returns a list - even if there is only one, so pull out the first
		# last name token
		my @last_names = $names[0]->part ('last');
		$short_name = $last_names[0];
		# may contain {} as these are allowed in bibtex, but
                # we don't really want them in filenames and directory names
                # That would be icky and probably screw up all the rest of the scripts
		$short_name =~ s/\{//g;
		$short_name =~ s/\}//g;
		# replace spaces with underscores, e.g. if a van Damme comes out (pun intended)
                $short_name =~ s/ /_/g;
		# append year!
		$short_name .= "_".$year;
	} elsif ($nAuthors == 2) {
		my @last_names = $names[0]->part ('last');
		$short_name = $last_names[0];
		@last_names = $names[1]->part ('last');
        	$short_name .= "_" . $last_names[0];
		# as above remove nasty characters and append year
		$short_name =~ s/\{//g;
		$short_name =~ s/\}//g;
                $short_name =~ s/ /_/g;
		$short_name .= "_".$year;
	} else {
		my @last_names = $names[0]->part ('last');
		$short_name = $last_names[0];
		$short_name =~ s/\{//g;
		$short_name =~ s/\}//g;
                $short_name =~ s/ /_/g;
		# append et_al
		$short_name .= "_et_al";
		# append year!
		$short_name .= "_".$year;
	}
	# lower case it all - gets rid of any irregularities in the bibtex file
	$short_name = lc($short_name);
	# create directory
	# However, first check if the same directory name exists, if so
	# fiddle with name - adding an a, b, c, d, etc
	my $success = 0;
        my $letter = "a";
	my $directory;
	while (not $success) {
		$directory = File::Spec->catdir( $dir, $short_name );
		if (-e $directory) { 
			$short_name = $short_name . $letter; 
			$letter++;
		} else { 
			mkdir $directory || die "Error creating ".$short_name;
			$success = 1;
		}
	}

	if ($verbose) {print "Creating $directory: ";}

	# create XML file
	# add bibliographic info
        # We create an XML hash and stuff data in,
        # then save :)
        my %xml =  (
		Notes => { },
 		Analysis => {Type => []},
 		Characters => {},
                Taxa => {List => {},
                         number => '0',
                         fossil => 'none'
                        },
                Source => {
			Year => [$year],
                	Publisher => [$publisher],
			Volume => [$vol],
			Editor => [$editor],
			Pages => [$pages],
			Booktitle => [$booktitle],
			Journal => [$journal],
			Title => [$title],
			Author => [$entry->get('author')]
                            },
                TreeFile => { }

                      );
	my $xml_file = 	File::Spec->catfile( $directory, $short_name.".xml" );
	print "$xml_file\n" if $verbose;
	Bio::STK::save_xml_file($xml_file, \%xml);	
	$nEntries++;

}

print "Created $nEntries directories and XML files. Go add your data\n";

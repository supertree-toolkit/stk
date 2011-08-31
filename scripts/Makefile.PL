use 5.00000;
use ExtUtils::MakeMaker;

check_optional($_) for qw(Pod::Simple::Wiki File::Remove Test::Pod File::Compare File::Copy File::Copy::Recursive);

# See lib/ExtUtils/MakeMaker.pm for details of how to influence
# the contents of the Makefile that is written.
WriteMakefile(
    'NAME'         => 'Bio::STK',
    'VERSION_FROM' => 'lib/Bio/STK.pm', # finds $VERSION	
    'PREREQ_PM'    => { 
		# XXX we don't *need* the following releases.
		# WriteMakefile doesn't seem to have a way to
		# indicate optional dependencies, so we'll just
		# ignore them
		#'Clone::PP'  => 1.02, 
		#'Test::Deep' => 0		
		'Test::More' => 0,
		'XML::Simple' => 0,
        'File::Find' => 0,
        'File::Spec::Functions' => 0,
        'File::Copy' => 0,
        'Bio::NEXUS' => 0.72,
        'Pod::Usage' => 0,
        'Getopt::Long' => 0,
        'Carp' => 0,
        'Graph' => 0.81,
        'Graph::Writer::Dot' =>1.03,
	},
    'EXE_FILES' => [ 
        'exec/stk_amalgamate_trees.pl',
        'exec/stk_check_data.pl',
        'exec/stk_check_overlap.pl',
        'exec/stk_check_substitutions.pl',
        'exec/stk_create_matrix.pl',
        'exec/stk_data_independence.pl',
        'exec/stk_data_summary.pl',
        'exec/stk_fix_treefiles.pl',
        'exec/stk_replace_genera.pl',
        'exec/stk_replace_taxa.pl',
        'exec/stk_tree_permutation.pl',
        'exec/stk_search_data.pl',
        'exec/STK-XML.jar',
	],
    'PL_FILES' => {},
    'ABSTRACT' => 'Bio::STK - A toolkit for manipulating source data for supertree analysis',
    'AUTHOR'   => 'Jon Hill <jon.hill@imperial.ac.uk>',
    'dist'     => {
		'COMPRESS' => 'gzip', 
		'SUFFIX'   => 'gz'
    },
);



sub check_optional {
	my $class = shift;
	my $path = $class;
	$path =~ s/::/\//g;
	$path .= '.pm';
	eval { require $path };
	if ( $@ ) {
		print STDERR <<"WARNING_NOT_INSTALLED";
*** You don't seem to have $class installed.
This means some functionality (e.g. full test suites) won't be
available (though core functionality will be).
		
WARNING_NOT_INSTALLED
		
	}
}

# override the install subroutine to add the installation
# of the config file for STK-XML
#sub MY::install {
#    package MY; # so that "SUPER" works right
#    my $inherited = shift->SUPER::install(@_);
#    $inherited =~ s/pure_perl_install :: all/pure_perl_install :: all\n\tcp _check.cfg ~\/\\/;
#    $inherited;
#}


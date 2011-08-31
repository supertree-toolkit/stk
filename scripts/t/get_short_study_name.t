#!/usr/bin/perl -w

use strict;
use warnings;
use Test::More tests => 18;

use lib 'lib';
use Bio::STK;

# err, this will fail before the actual find_xml_files test script
# if the script wun in alphabetical order!
my @xml_files = Bio::STK::find_xml_files('t/data/get_short_study_name');

my %shortnames = Bio::STK::get_short_study_name(@xml_files);

is ($shortnames{'t/data/get_short_study_name/Aleixo_2002/Aleixo_2002_1_corr.xml'}, "aleixo_2002", "Checking name 1");
is ($shortnames{'t/data/get_short_study_name/Aliabadian_etal_2007/Tree 1/Aliabadian_etal_2007_1_corr.xml'}, "aliabadian_etal_2007", "Checking name 2");
is ($shortnames{'t/data/get_short_study_name/Aliabadian_etal_2007/Tree 2/Aliabadian_etal_2007_2_corr.xml'}, "aliabadian_etal_2007", "Checking name 3");
is ($shortnames{'t/data/get_short_study_name/Allende_etal_2001/Allende_etal_2001_1_corr.xml'}, "allende_etal_2001", "Checking name 4");
is ($shortnames{'t/data/get_short_study_name/Andersson_1999a/Tree 1/Andersson_1999a_corr.xml'}, "andersson_1999a", "Checking name 5");
is ($shortnames{'t/data/get_short_study_name/Andersson_1999b/Tree 1/Andersson_1999b_1_corr.xml'}, "andersson_1999b", "Checking name 6");
is ($shortnames{'t/data/get_short_study_name/Andersson_1999b/Tree 2/Andersson_1999b_2_corr.xml'}, "andersson_1999b", "Checking name 7");
is ($shortnames{'t/data/get_short_study_name/Aragon_etal_1999/Aragon_etal_1999_1_corr.xml'}, "aragon_etal_1999", "Checking name 8");
is ($shortnames{'t/data/get_short_study_name/Aragon_etal_1999/Tree 3/Aragon_etal_1999_3_corr.xml'}, "aragon_etal_1999", "Checking name 9");
is ($shortnames{'t/data/get_short_study_name/Baker_Strauch_1988/Tree 1/Baker_Strauch_1988_corr.xml'}, "baker_strauch_1988", "Checking name 10");
is ($shortnames{'t/data/get_short_study_name/Baker_etal_2006/Tree 1/Baker_etal_2006_corr.xml'}, "baker_etal_2006", "Checking name 11");
is ($shortnames{'t/data/get_short_study_name/Baker_etal_2007a/Tree 1/Baker_etal_2007a_corr.xml'}, "baker_etal_2007a", "Checking name 12");
is ($shortnames{'t/data/get_short_study_name/Baker_etal_2007b/Tree 1/Baker_etal_2007b_corr.xml'}, "baker_etal_2007b", "Checking name 13");
is ($shortnames{'t/data/get_short_study_name/Mayr_2005/Tree 1/Mayr_2005_corr.xml'}, "mayr_2005a", "Checking name 14");
is ($shortnames{"t/data/get_short_study_name/Mayr_2005a/Tree 1/Mayr_2005a_corr.xml"}, "mayr_2005b", "Checking name 15");
is ($shortnames{'t/data/get_short_study_name/Mayr_2005b/Tree 1/Mayr_2005b_corr.xml'}, "mayr_2005c", "Checking name 16");
is ($shortnames{'t/data/get_short_study_name/Mayr_2005c/Tree 1/Mayr_2005c_corr.xml'}, "mayr_2005d", "Checking name 17");
is ($shortnames{'t/data/get_short_study_name/Mayr_2005d/Tree 1/Mayr_2005d_corr.xml'}, "mayr_2005e", "Checking name 18");


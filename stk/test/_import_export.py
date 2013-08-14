#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2011, Jon Hill, Katie Davis
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
#
#    Jon Hill. jon.hill@imperial.ac.uk. 

import unittest
import math
import sys
# so we import local stk before any other
sys.path.insert(0,"../../")
# for debug, etc
sys.path.append("../../stk_gui/stk_gui/")

from stk.stk_import_export import export_to_old, import_old_data
from stk.supertree_toolkit import _parse_xml
import os
from lxml import etree
from util import *
import shutil
from stk.stk_exceptions import *
import tempfile
import debug
import schema
from SchemaValidator import *
debug.SetDebugLevel(0)


class TestImportExport(unittest.TestCase):

    def test_import_data(self):
        
        # Our validator object
        validator = SchemaValidator(rootDir = "data")

        phyml = import_old_data('data/input/old_stk_test/',verbose=False)
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".phyml")
        f = open(temp_file,"w")
        f.write(phyml)
        f.close()
        validator.ValidateOptionFile(os.path.join("../../../schema", "phylo_storage.rng"),temp_file)
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        validator.Reset()
        failures = []
        for phyml_file in optionErrors:
            # We expect there to be missing taxon elements in the XML
            # as the user must fill these in, so check missing attributes, etc OK
            # and skip the missing element
            added_eles = optionErrors[phyml_file][1]
            for err in added_eles:
                if (err == "/phylo_storage/sources/source/source_tree/taxa_data/mixed_fossil_and_extant/taxon" and
                        len(optionErrors[phyml_file][0])+len(optionErrors[phyml_file][2])+len(optionErrors[phyml_file][3]) == 0):
                    continue
                failures.append(phyml_file)
        self.assert_(len(failures) == 0)
        os.remove(temp_file)
        
        
        # parse XML and check various things
        XML = _parse_xml(phyml)
        name = XML.xpath('/phylo_storage/project_name/string_value')[0].text
        self.assert_(name == "old_stk_test")

        # check numebr of souces
        find = etree.XPath('//source')
        sources = find(XML)
        self.assert_(len(sources) == 15)

        # check names of sources:
        expected_names = [
                'Allende_etal_2001',
                'Andersson_1999b',
                'Baker_etal_2006',
                'Aleixo_2002',
                'Bertelli_etal_2006',
                'Baker_etal_2007b',
                'Aragon_etal_1999',
                'Baker_etal_2007a',
                'Aliabadian_etal_2007',
                'Baker_Strauch_1988',
                'Barhoum_Burns_2002',
                'Barber_Peterson_2004',
                'Baker_etal_2005',
                'Andersson_1999a',
                'Baptista_etal_1999'
                ]
        for s in sources:
            name = s.attrib['name']
            self.assert_(name in expected_names)
            if name == "Bertelli_etal_2006":
                # this source publication has three trees, let's check that is the case!
                find = etree.XPath('source_tree')
                trees = find(s)
                self.assert_(len(trees) == 3)
            if name == "Baptista_etal_1999":
                volume = s.xpath('.//bibliographic_information/article/volume/string_value')[0].text
                self.assert_(volume == "140")


        # check total number of characters

    def test_export_data(self):
        XML = etree.tostring(etree.parse("data/input/old_stk_input.phyml"))
        try:
            shutil.rmtree('data/output/old_stk_test')
        except:
            next
        export_to_old(XML,'data/output/')
        import filecmp
        d = filecmp.dircmp('data/input/old_stk_test','data/output/old_stk_test')
        self.assert_(len(d.left_only) == 0)
        self.assert_(len(d.right_only) == 0)
        # now check you get an error when doing this again
        try:
            export_to_old(XML,'data/output/')
        except STKImportExportError:
            self.assert_(True)
        except:
            self.assert_(False)
        else:
            self.assert_(False)
        
        try:
            shutil.rmtree('data/output/old_stk_test')
        except:
            return

            

if __name__ == '__main__':
    unittest.main()
 

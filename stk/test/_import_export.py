import unittest
import math
import sys
sys.path.append("../../")
from stk.stk_import_export import export_to_old, import_old_data
from stk.supertree_toolkit import _parse_xml
import os
from lxml import etree
from util import *
import shutil
from stk.stk_exceptions import *


class TestImportExport(unittest.TestCase):

    def test_import_data(self):
        try:
            phyml = import_old_data('data/input/old_stk_test/',verbose=False)
        except STKImportExportError as e:
            print e.msg
            self.assert_(False) # fail the test

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
                'Aleixo_2002',
                'Aragon_etal_1999',
                'Aliabadian_etal_2007',
                'Andersson_1999a',
                ]
        # names are sorted now, so...
        expected_names = sorted(expected_names)

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
        # now check your get an error when doing this again
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
 

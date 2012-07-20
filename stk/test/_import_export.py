import unittest
import math
import sys
sys.path.insert(0,"../../")
from stk.stk_import_export import export_to_old, import_old_data
from stk.supertree_toolkit import _parse_xml
import os
from lxml import etree
from util import *
import shutil
from stk.stk_exceptions import *


class TestImportExport(unittest.TestCase):

    def test_import_data(self):
        phyml = import_old_data('data/input/old_stk_test/',verbose=False)
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
                'Baptista_Visser_1999'
                ]
        for s in sources:
            name = s.attrib['name']
            self.assert_(name in expected_names)
            if name == "Bertelli_etal_2006":
                # this source publication has three trees, let's check that is the case!
                find = etree.XPath('source_tree')
                trees = find(s)
                self.assert_(len(trees) == 3)

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
 

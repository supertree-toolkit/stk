import unittest
import math
import sys
sys.path.append("../")
from supertree_toolkit import _check_uniqueness
import os
from lxml import etree
from util import *
import stk_exceptions

# Class to test all those loverly internal methods
# or stuff that doesn't fit within the other tests

class TestSetSourceNames(unittest.TestCase):

    def test_check_uniqueness(self):
        non_unique_names = etree.parse("data/input/non_unique_names.phyml")
        try:
            _check_uniqueness(etree.tostring(non_unique_names))
        except stk_exceptions.NotUniqueError:
            self.assert_(True)
            return
            
        self.assert_(False)

    def test_check_nonuniquess_pass(self):
        new_xml = etree.parse("data/input/full_tree.xml")
        try:
            _check_uniqueness(etree.tostring(new_xml))
        except:
            self.assert_(False)
            return
            
        self.assert_(True)


  
if __name__ == '__main__':
    unittest.main()
 

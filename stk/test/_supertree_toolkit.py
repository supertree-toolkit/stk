import unittest
import math
import sys
sys.path.append("../")
from supertree_toolkit import _check_uniqueness
import os
from lxml import etree
from util import *

# Class to test all those loverly internal methods
# or stuff that doesn't fit within the other tests

class TestSetSourceNames(unittest.TestCase):

    def test_check_uniqueness(self):
        non_unique_names = etree.parse("data/input/non_unique_names.phyml")
        try:
            new_xml = _check_uniqueness(etree.tostring(non_unique_names))
        except NotUniqueError:
            self._assert(True)
        except:
            self_assert(False)



  
if __name__ == '__main__':
    unittest.main()
 

import unittest
import math
import sys
sys.path.append("../")
from supertree_toolkit import import_tree 
import os
from lxml import etree
from util import *

# our test dataset
newick_file = "/home/jhill1/test.nex"

class TestImportTree(unittest.TestCase):

    def test_import_singletree(self):
        trees = import_tree(newick_file)
        self.assert_(answer == trees)

if __name__ == '__main__':
    unittest.main()
 

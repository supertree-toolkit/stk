#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2017, Jon Hill, Katie Davis
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

import unittest
import os
import sys
import tempfile
from subprocess import call, STDOUT
sys.path.insert(0,"../../")
import stk
from lxml import etree
FNULL = open(os.devnull, 'w')

parser = etree.XMLParser(remove_blank_text=True)

# A bunch of tests that replicate the tests in _supertree_toolkit
# and check the CLI is still essentially working (i.e. no screw ups)
# There's no much intelligent in these tests, so they're not run in the Makefile
# Run this if and only if you have edited stk CLI
#
# Here endeth the preaching

class TestSTK(unittest.TestCase):

    def test_amalgamate_trees_anonymous(self):

        XMLF = 'data/input/old_stk_input.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        return_code = call(["../stk","export_trees", "-f", "nexus", "--overwrite", "--anonymous", XMLF, temp_file])
        self.assert_(return_code == 0)


        XML = etree.tostring(etree.parse(XMLF,parser),pretty_print=True)
        trees = stk.get_all_trees(XML)
        try:
            trees_read = stk.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk.trees_equal(trees_read[i],trees[names[i]]))


    def test_amalgamate_trees_nexus(self):

        XMLF = 'data/input/old_stk_input.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        return_code = call(["../stk","export_trees", "-f", "nexus", "--overwrite", XMLF, temp_file])
        self.assert_(return_code == 0)


        XML = etree.tostring(etree.parse('data/input/old_stk_input.phyml',parser),pretty_print=True)
        trees = stk.get_all_trees(XML)
        try:
            trees_read = stk.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk.trees_equal(trees_read[i],trees[names[i]]))


    def test_amalgamate_trees_newick(self):

        XMLF = 'data/input/old_stk_input.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        return_code = call(["../stk","export_trees", "-f", "newick", "--overwrite", XMLF, temp_file])
        self.assert_(return_code == 0)

        XML = etree.tostring(etree.parse(XMLF,parser),pretty_print=True)
        trees = stk.get_all_trees(XML)
        try:
            trees_read = stk.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk.trees_equal(trees_read[i],trees[names[i]]))


    def test_amalgamate_trees_tnt(self):

        XMLF = 'data/input/old_stk_input.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        return_code = call(["../stk","export_trees", "-f", "tnt", "--overwrite", XMLF, temp_file])
        self.assert_(return_code == 0)

        XML = etree.tostring(etree.parse(XMLF,parser),pretty_print=True)
        trees = stk.get_all_trees(XML)
        try:
            trees_read = stk.import_trees(temp_file)
        except:
            self.assert_(False)
            # we should get no error
        os.remove(temp_file)
        self.assert_(len(trees)==len(trees_read))
        names = trees.keys()
        for i in range(0,len(trees)):
            self.assert_(stk.trees_equal(trees_read[i],trees[names[i]]))


    def test_amalgamate_trees_unknown_format(self):
        XMLF = 'data/input/old_stk_input.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tre")
        return_code = call(["../stk","export_trees", "-f", "BOB", "--overwrite", XMLF, temp_file], stdout=FNULL, stderr=STDOUT)
        self.assert_(return_code != 0)


    def test_create_matrix(self):
        XMLF = 'data/input/create_matrix.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tnt")
        return_code = call(["../stk","create_matrix", "-f", "hennig", "--overwrite", XMLF, temp_file])
        self.assert_(return_code == 0)

    def test_create_matrix_weights(self):
        XMLF = 'data/input/weighted_trees.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tnt")
        return_code = call(["../stk","create_matrix", "-f", "hennig", "--overwrite", "--remove_outgroups", XMLF, temp_file])
        self.assert_(return_code == 0)

    def test_create_tnt_matrix_with_taxonomy(self):
        XMLF = 'data/input/create_matrix.phyml'
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tnt")
        return_code = call(["../stk","create_matrix", "-f", "hennig", "--overwrite", "--taxonomy", "data/input/paup_tree.tre", XMLF, temp_file])
        self.assert_(return_code == 0)


if __name__ == '__main__':
    unittest.main()
 

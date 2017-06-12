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
#    Jon Hill. jon.hill@york.ac.uk. 

import unittest
import math
import sys
# so we import local stk before any other central install
sys.path.insert(0,"../../")
from stk.stk_internals import locate, replace_utf, internet_on, uniquify, removeNonAscii, sort_sub_taxa, sub_deal_with_existing_only
import os
import stk.stk_exceptions as excp
from lxml import etree
from util import *
parser = etree.XMLParser(remove_blank_text=True)

import sys

class TestInternals(unittest.TestCase):

    def test_replace_utf(self):
        string = u"\u00C6\u00D0\u00FE\u2018"
        expected = "AEDth'"
        new = replace_utf(string)
        self.assert_(expected == new)

    def test_uniquify(self):
        list1 = ['bob', 'bob', 'bobby', 'boberalla']
        expected = ['bob', 'bobby', 'boberalla']
        self.assertItemsEqual(uniquify(list1), expected)

    def test_uniquify_dict(self):
        dict1 = {'bob': 1, 'Bob': 2, 'bob': 3, 'bobby': 4}
        expected = {'Bob': 2, 'bob': 3, 'bobby': 4}
        self.assertItemsEqual(uniquify(dict1), expected)

    def test_sort_sub_taxa(self):
        
        # string -> array
        old_taxon = 'bob'
        expected = ['bob']
        old, new = sort_sub_taxa(old_taxon, None)
        self.assertItemsEqual(expected, old)

        # same for new
        old, new = sort_sub_taxa(old_taxon, old_taxon)
        self.assertItemsEqual(expected, new)

        # list -> list
        old, new = sort_sub_taxa(expected, None)
        self.assertItemsEqual(expected, old)

        try:
            sort_sub_taxa(old_taxon, ['bobby', 'bunbun'])
            self.assert_(False)  # shouldn't run this as above should raise exception
        except excp.UnableToParseSubsFile:
            self.assert_(True)

    def test_sub_dealing_with_existing_only(self):
        existing_taxa = ['A_a', 'B_b', 'C_c', 'D_d', 'E_e', 'F_f', 'G_g']
        new_taxa = ["A_a, A_b", 'B_a', 'G_g']
        old_taxa = ['A_a', 'B_b', 'F_f']
        nnew_taxa = sub_deal_with_existing_only(existing_taxa, old_taxa, new_taxa, generic_match=False)
        expected = ['A_a', 'G_g']
        self.assertItemsEqual(expected, nnew_taxa)

        nnew_taxa = sub_deal_with_existing_only(existing_taxa, old_taxa, new_taxa, generic_match=True)
        expected = ["A_a, A_b", 'B_a', 'G_g']
        self.assertItemsEqual(expected, nnew_taxa)

    def test_locate(self):
        pattern = "*.tre"
        files = list(locate(pattern, "data/input")) # convert to list for testing
        cwd = os.getcwd()
        self.assertIn(os.path.join(cwd,"data","input","multiple_trees.tre"), files)
        self.assertIn(os.path.join(cwd,"data","input","mrca.tre"), files)

    def test_removeNonAscii(self):
        stringy = u"hello a\u00C6\u00D0b\u00FE\u2018c"
        new_stringy = removeNonAscii(stringy)
        self.assert_(new_stringy == "hello abc")

    
if __name__ == '__main__':
    unittest.main()




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
from stk.supertree_toolkit import import_tree, obtain_trees, get_all_taxa, _assemble_tree_matrix, create_matrix, _delete_taxon, _sub_taxon
from stk.supertree_toolkit import _swap_tree_in_XML, substitute_taxa
import os
from lxml import etree
from util import *
import io
import numpy
import stk.p4 as p4

import sys
sys.path.append("../../stk_gui/stk_gui/")

from SchemaValidator import *
import debug
import schema

# This test class checks that all the phyml and xml stubs in the test directories
# are valid against the current schema. We can therefore ensure all other tests are tested
# against the current schema - they might pass if the schema is changed, but this one won't

# Add a phyml or xml to this list if you know
# it's not valid and the main test will ignore it, but it will be checked in the check against schema only test
ignore_list = ["data/input/start_up.phyml", # contains only a stub
               "data/output/bib_import_single_article_doi.phyml", # contains only a valid bibliography
               "data/output/bib_import_single_article.phyml", # contains only a valid bibliography
               "data/output/bib_import_single_book.phyml", # contains only a valid bibliography
               "data/output/bib_import_utf8.phyml", # contains only a valid bibliography
               "data/input/old_stk_input_data_summary_test.phyml", # partial data set
               "data/input/bib_export_no_pages.phyml",# invalid data
               "data/input/single_source_no_names.phyml", # no tree names
              ]


# set to one to see more output from the validation
debug.SetDebugLevel(0)

# Our validator object
validator = SchemaValidator(rootDir = "data")

# The unit tests proper
class TestSchema(unittest.TestCase):

    def test_validation_input_phyml(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "input", depth = 1, extension = "phyml", xmlRootNode = "phylo_storage")
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in list(optionErrors.keys()):
            if not filename in ignore_list:
                failures.append(filename)
        if (len(failures) > 0):
            print(failures)
        self.assertTrue(len(failures) == 0)

    def test_validation_output_phyml(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "output", depth = 1, extension = "phyml", xmlRootNode = "phylo_storage")
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in list(optionErrors.keys()):
            if not filename in ignore_list:
                failures.append(filename)
        if (len(failures) > 0):
            print(failures)
        self.assertTrue(len(failures) == 0)

    def test_validation_input_stubs(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "input", depth = 1, extension = None, xmlRootNode = "sources")
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in list(optionErrors.keys()):
            if not filename in ignore_list:
                failures.append(filename)
        if (len(failures) > 0):
            print(failures)
        self.assertTrue(len(failures) == 0)
    
    def test_validation_output_stubs(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "output", depth = 1, extension = None, xmlRootNode = "sources")
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in list(optionErrors.keys()):
            if not filename in ignore_list:
                failures.append(filename)
        if (len(failures) > 0):
            print(failures)
        self.assertTrue(len(failures) == 0)

    def test_validation_output_phyml_partials(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "output", depth = 1, extension = "phyml", xmlRootNode = "phylo_storage", ignoreValidXMLCheck=True)
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in list(optionErrors.keys()):
            failures.append(filename)
        self.assertTrue(len(failures) == 0)
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "input", depth = 1, extension = "phyml", xmlRootNode = "phylo_storage", ignoreValidXMLCheck=True)
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in list(optionErrors.keys()):
            failures.append(filename)
        if (len(failures) > 0):
            print(failures)
        self.assertTrue(len(failures) == 0)



if __name__ == '__main__':
    unittest.main()




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
import StringIO
import numpy
import stk.p4 as p4

import glob
import os
import sys
import xml.dom.minidom
import xml.parsers.expat

sys.path.append("../../stk_gui/stk_gui/")

import debug
import schema

# This test class checks that all the phyml and xml stubs in the test directories
# are valid against the current schema. We can therefore ensure all other tests are tested
# against the current schema - they might pass if the schema is changed, but this one won't

# Add a phyml or xml to this list if you know
# it's not valid and the tests will ignore it
ignore_list = ["data/input/start_up.phyml",
              ]



debug.SetDebugLevel(0)

# This is a our schema test class - see below for the unit tests
class SchemaValidator:
  def __init__(self, rootDir):
    self._rootDir = rootDir
    self.Reset()
    
    return
    
  def Reset(self):
    self._passes = 0
    self._optionErrors = {}
    
    return
    
  def TestXmlFiles(self, testDir, depth):
    debug.dprint("Checking xml files:", 1)
    for filename in self._TestFiles("xml", testDir, depth):
      try:
        xmlParse = xml.dom.minidom.parse(filename)
        debug.dprint(filename + " : Pass", 0)
        self._passes += 1
      except xml.parsers.expat.ExpatError:
        debug.dprint(filename + " : Fail", 0)
        self._optionErrors[filename] = xml.parsers.expat.ExpatError
    
    return
    
  def ValidateOptionsFiles(self, schemafile, testDir, depth, extension = None, xmlRootNode = None):
    debug.dprint("Validating options file against schema: " + schemafile, 1)
  
    schemafile = os.path.join(self._rootDir, schemafile)
    sch = schema.Schema(schemafile)

    if not extension is None:
      debug.dprint("Testing files with extension: " + extension, 0)
      for filename in self._TestFiles(extension, testDir, depth): 
        optionsTree = sch.read(filename)
        lost_eles, added_eles, lost_attrs, added_attrs = sch.read_errors()
        if len(lost_eles) + len(added_eles) + len(lost_attrs) + len(added_attrs) == 0 and optionsTree.valid:
          debug.dprint(filename + " : Pass", 0)
          self._passes += 1
        else:
          debug.dprint(filename + " : Fail", 0)
          self._optionErrors[filename] = (lost_eles, added_eles, lost_attrs, added_attrs)
          
    if not xmlRootNode is None:
      debug.dprint("Testing xml files with root node: " + xmlRootNode, 1)
      for filename in self._TestFiles("xml", testDir, depth):
        try:
          xmlParse = xml.dom.minidom.parse(filename)
        except xml.parsers.expat.ExpatError:
          debug.dprint(filename + " : Fail", 0)
          self._optionErrors[filename] = (0,0,0,0)
          continue
        rootEles = xmlParse.getElementsByTagName(xmlRootNode)
        if len(rootEles) == 0:
          continue
        optionsTree = sch.read(filename,root=xmlRootNode,stub=True)
        lost_eles, added_eles, lost_attrs, added_attrs = sch.read_errors()
        if len(lost_eles) + len(added_eles) + len(lost_attrs) + len(added_attrs) == 0:
          debug.dprint(filename + " : Pass", 0)
          self._passes += 1
        else:
          debug.dprint(filename + " : Fail", 0)
          self._optionErrors[filename] = (lost_eles, added_eles, lost_attrs, added_attrs)
    
    return
    
  def _TestFiles(self, extension, testDir, depth):
    filenames = []
    baseDir = os.path.join(self._rootDir, testDir)
    for i in range(depth + 1):
      filenames += glob.glob(os.path.join(baseDir, "*." + extension))
      baseDir = os.path.join(baseDir, "*")
    
    return filenames
    
  def Passes(self):
    return self._passes
    
  def OptionErrors(self):
    return self._optionErrors

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
        for filename in optionErrors.keys():
            if not filename in ignore_list:
                failures.append(filename)
                print filename, optionErrors[filename]
        self.assert_(len(failures) == 0)

    def test_validation_output_phyml(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "output", depth = 1, extension = "phyml", xmlRootNode = "phylo_storage")
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in optionErrors.keys():
            if not filename in ignore_list:
                failures.append(filename)
        self.assert_(len(failures) == 0)

    def test_validation_input_stubs(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "input", depth = 1, extension = None, xmlRootNode = "sources")
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in optionErrors.keys():
            if not filename in ignore_list:
                failures.append(filename)
        self.assert_(len(failures) == 0)
    
    def test_validation_output_stubs(self):
        validator.Reset()
        validator.ValidateOptionsFiles(schemafile = os.path.join("../../../schema", "phylo_storage.rng"), testDir = "output", depth = 1, extension = None, xmlRootNode = "sources")
        passes = validator.Passes()
        optionErrors = validator.OptionErrors()
        failures = []
        for filename in optionErrors.keys():
            if not filename in ignore_list:
                failures.append(filename)
        self.assert_(len(failures) == 0)

if __name__ == '__main__':
    unittest.main()




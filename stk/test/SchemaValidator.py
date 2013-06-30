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

import debug
import schema
import os
import glob
import xml.dom.minidom
import xml.parsers.expat
from lxml import etree

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
        debug.dprint(filename + " : Pass", 1)
        self._passes += 1
      except xml.parsers.expat.ExpatError:
        debug.dprint(filename + " : Fail", 1)
        self._optionErrors[filename] = xml.parsers.expat.ExpatError
    
    return
  
  def ValidateOptionFile(self, schemafile, filename, xmlRootNode=None,ignoreValidXMLCheck=False):
    debug.dprint("Validating options file against schema: " + schemafile, 1)
  
    schemafile = os.path.join(self._rootDir, schemafile)
    self.sch = schema.Schema(schemafile)
    self._TestSingle_file(filename,ignoreValidXMLCheck)

    
  def ValidateOptionsFiles(self, schemafile, testDir, depth, extension = None, xmlRootNode = None, ignoreValidXMLCheck=False):
    debug.dprint("Validating options file against schema: " + schemafile, 1)
  
    schemafile = os.path.join(self._rootDir, schemafile)
    self.sch = schema.Schema(schemafile)

    if not extension is None:
      debug.dprint("Testing files with extension: " + extension, 1)
      for filename in self._TestFiles(extension, testDir, depth): 
        self._TestSingle_file(filename,ignoreValidXMLCheck)
          
    if not xmlRootNode is None:
      debug.dprint("Testing xml files with root node: " + xmlRootNode, 1)
      for filename in self._TestFiles("xml", testDir, depth):
        try:
          xmlParse = xml.dom.minidom.parse(filename)
        except xml.parsers.expat.ExpatError:
          debug.dprint(filename + " : Fail", 1)
          self._optionErrors[filename] = (0,0,0,0)
          continue
        rootEles = xmlParse.getElementsByTagName(xmlRootNode)
        if len(rootEles) == 0:
          continue
        optionsTree = self.sch.read(filename,root=xmlRootNode,stub=True)
        lost_eles, added_eles, lost_attrs, added_attrs = self.sch.read_errors()
        if len(lost_eles) + len(added_eles) + len(lost_attrs) + len(added_attrs) == 0:
          debug.dprint(filename + " : Pass", 1)
          self._passes += 1
        else:
          debug.dprint(filename + " : Fail", 1)
          self._optionErrors[filename] = (lost_eles, added_eles, lost_attrs, added_attrs)
    
    return
    
  def _TestSingle_file(self, filename,ignoreValidXMLCheck=False):
    optionsTree = self.sch.read(filename)
    lost_eles, added_eles, lost_attrs, added_attrs = self.sch.read_errors()
    if (ignoreValidXMLCheck):
        if len(lost_eles) + len(lost_attrs) == 0:
          debug.dprint(filename + " : Pass", 1)
          self._passes += 1
        else:
          debug.dprint(filename + " : Fail", 1)
          self._optionErrors[filename] = (lost_eles, added_eles, lost_attrs, added_attrs)
    else:
        if len(lost_eles) + len(added_eles) + len(lost_attrs) + len(added_attrs) == 0 and optionsTree.valid:
          debug.dprint(filename + " : Pass", 1)
          self._passes += 1
        else:
          debug.dprint(filename + " : Fail", 1)
          self._optionErrors[filename] = (lost_eles, added_eles, lost_attrs, added_attrs)    


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


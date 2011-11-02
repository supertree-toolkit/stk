#!/usr/bin/env python
#
#    Supertree Toolkit. SOftware for managing and manipulating sources
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

import os
import sys
import math
import numpy 
from lxml import etree
import yapbib.biblist as biblist
import string

# supertree_toolkit is the backend for the STK. Loaded by both the GUI and
# CLI, this contains all the functions to actually *do* something
#
# All functions take XML and a list of other arguments, process the data and return
# it back to the user interface handler to save it somewhere

def create_name(authors, year):
    """ From a list of authors and a year construct a sensible
    source name.
    Input: authors - list of last (family, sur) names (string)
           year - the year (string)
    Output: source_name - (string)"""

    source_name = None
    if (len(authors) == 1):
        # single name: name_year
        source_name = authors[0] + "_" + year
    elif (len(authors) == 2):
        source_name = authors[0] + "_" + authors[1] + "_" + year
    else:
        source_name = authors[0] + "_etal_" + year

    return source_name


def single_sourcename(XML):
    """ Create a sensible source name based on the 
    bibliographic data.
    xml_root should contain the xml_root etree for the source that is to be
    altered only"""

    xml_root = etree.fromstring(XML)

    authors_ele = xml_root[0][0][0]
    authors = []
    for ele in authors_ele.iter():
        if (ele.tag == "family_name"):
            authors.append(ele.xpath('string_value')[0].text)

    year = str(xml_root.xpath('source_publication/article/year/integer_value')[0].text)
    source_name = create_name(authors, year)

    attributes = xml_root.attrib
    attributes["name"] = source_name

    XML = etree.tostring(xml_root)

    # Return the XML stub with the correct name
    return XML

def all_sourcenames(XML):
    """
    Create a sensible sourcename for all sources in the current
    dataset. 
    """

    # Find all "source" trees

    for s in sources:
        # pull XML stub
        new_s = single_sourcename(s)
        # insert into XML

    return XML

def import_bibliography(XML, bibfile):    
    
    # Out bibliography parser
    b = biblist.BibList()

    xml_root = etree.fromstring(XML)

    # Track back along xpath to find the sources where we're about to add a new source
    element = xml_root.xpath('sources')[0]
    while (element.tag != 'sources'):
        element = element.getparent()

    if (bibfile == None):
        return XML

    failed = False
    try: 
        b.import_bibtex(bibfile)
    except: 
        failed=True

    items= b.sortedList[:]

    for entry in items:
        # for each bibliographic entry, create the XML stub and
        # add it to the main XML
        it= b.get_item(entry)
        xml_snippet = it.to_xml()
        # turn this into an etree
        publication = etree.fromstring(xml_snippet)

        #source_name = single_sourcename(etree.tostring(publication))
        source_name = "temp"
        # create top of source
        source = etree.Element("source", name=source_name)

        # now attach our publication
        source.append(publication)

        # now create tail of source
        characters = etree.SubElement(source,"character_data")
        analyses = etree.SubElement(source,"analyses_used")
        tree = etree.SubElement(source,"tree_data")

        # append our new source to the main tree
        element.append(source)

    # sort sources in alphabetical order
    XML = etree.tostring(xml_root)
    print XML
    return XML

################ PRIVATE FUNCTIONS ########################



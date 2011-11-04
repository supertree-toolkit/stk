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

    find = etree.XPath("//authors")
    authors_ele = find(xml_root)[0]
    authors = []
    for ele in authors_ele.iter():
        if (ele.tag == "surname"):
            authors.append(ele.xpath('string_value')[0].text)
    
    find = etree.XPath("//year/integer_value")
    year = find(xml_root)[0].text
    source_name = create_name(authors, year)

    attributes = xml_root.attrib
    attributes["name"] = source_name

    XML = etree.tostring(xml_root,pretty_print=True)

    # Return the XML stub with the correct name
    return XML

def all_sourcenames(XML):
    """
    Create a sensible sourcename for all sources in the current
    dataset. 
    """

    xml_root = etree.fromstring(XML)

    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    for s in sources:
        xml_snippet = etree.tostring(s,pretty_print=True)
        xml_snippet = single_sourcename(xml_snippet)
        parent = s.getparent()
        ele_T = etree.fromstring(xml_snippet)
        parent.replace(s,ele_T)

    XML = etree.tostring(xml_root,pretty_print=True)
    # gah: the replacement has got rid of line breaks for some reason
    XML = string.replace(XML,"</source><source ", "</source>\n    <source ")
    XML = string.replace(XML,"</source></sources", "</source>\n  </sources")    
    return XML

def import_bibliography(XML, bibfile):    
    
    # Out bibliography parser
    b = biblist.BibList()

    xml_root = etree.fromstring(XML)
    
    # Track back along xpath to find the sources where we're about to add a new source
    sources = xml_root.xpath('sources')[0]
    sources.tail="\n      "
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
        # create top of source
        source = etree.Element("source")
        # now attach our publication
        source.append(publication)
        new_source = single_sourcename(etree.tostring(source,pretty_print=True))
        source = etree.fromstring(new_source)

        # now create tail of source
        s_tree = etree.SubElement(source, "source_tree")
        s_tree.tail="\n      "
       
        characters = etree.SubElement(s_tree,"character_data")
        c_data = etree.SubElement(characters,"character")
        attributes_c = c_data.attrib
        attributes_c['type'] = "molecular"
        attributes_c['name'] = "12S"
        analyses = etree.SubElement(s_tree,"analyses_used")
        a_data = etree.SubElement(analyses,"analysis")
        attributes_a = a_data.attrib
        attributes_a['name'] = "Maximum Parsimony"
        tree = etree.SubElement(s_tree,"tree_data")
        tree_string = etree.SubElement(tree,"string_value")
        attributes = tree_string.attrib
        attributes["lines"] = "1"
        tree_string.text = "Insert your tree here"

        source.tail="\n      "

        # append our new source to the main tree
        sources.append(source)

    # do we have any empty (define empty?) sources? - i.e. has the user
    # added a source, but not yet filled it in?
    # I think the best way of telling an empty source is to check all the
    # authors, title, tree, etc and checking if they are empty tags
    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    for s in sources:
        xml_snippet = etree.tostring(s,pretty_print=True)
        if ('<string_value lines="1"/>' in xml_snippet and\
            '<integer_value rank="0"/>' in xml_snippet):

            parent = s.getparent()
            parent.remove(s)

    # sort sources in alphabetical order
    XML = etree.tostring(xml_root,pretty_print=True)
    
    return XML

################ PRIVATE FUNCTIONS ########################



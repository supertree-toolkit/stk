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

def single_sourcename(XML):
    """ Create a sensible source name based on the 
    bibliographic data.
    XML should contain the XML tree for the source that is to be
    altered only"""

    xml_root = etree.fromstring(xml)

    # Check we got some XML
    if (len(xml_root.xpath(xpath)) == 0):
        # Error handling!

        return

    # Track back along xpath to find the source element where we're going to set the name
    element = xml_root.xpath(xpath)[0]
    while (element.tag != 'source'):
        element = element.getparent()

    # get author 1
    author1 = element.xpath('source_publication/author[0]')
    if (author1):
        #check for author 2
        author2 = element.xpath('source_publication/author[1]')
        if (author2):
            # add etal
            author1 = author1+"_etal"
        year = element.xpath('source_publication/year')
        author_year = author1+"_"+year
    else:
        return

    attributes = element.attrib
    attributes["name"] = author_year

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

    print bibfile
    if (bibfile == None):
        return XML

    failed = False
    try: 
        b.import_bibtex(bibfile)
    except: 
        failed=True

    items= b.sortedList[:]
    print items

    for entry in items:
        # for each bibliographic entry, create the XML stub and
        # add it to the main XML
        it= b.get_item(entry)
        authors = it.get_listnames_last()
        year = it.get_field('year')
        title = it.get_field('title')
        journal = it.get_field('journal')
        volume = it.get_field('volume')
        pages = it.get_field('firstpage') + "-" + it.get_field('lastpage')
        booktitle = it.get_field('booktitle')

        

    return XML

################ PRIVATE FUNCTIONS ########################



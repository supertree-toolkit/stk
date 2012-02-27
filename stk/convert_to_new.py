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

from Bio import Phylo
from StringIO import StringIO
import os
import sys
import math
import re
import numpy 
from lxml import etree
import argparse
import parser
import re
import supertree_toolkit
from copy import deepcopy

####################################################
#
# Convert a PHYML file from the new supertree tool kit
# to the old data format, including XML, tre, files, etc
#
####################################################


def main():

    parser = argparse.ArgumentParser(
         description="""convert_to_new converts and old STK dataset (directory-based) to the new PHYML format"""
                     )

    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports as we go",
            default=False
            )

    # positional args:
    parser.add_argument(
            'input_dir',
            help="A directory where the output will be stored"
            )
    parser.add_argument(
            'phyml_file',
            help="The PHYML file to be converted"
            )

    args = parser.parse_args()
    input_dir = str(args.input_dir)
    # strip trailing path separator if one
    if (input_dir.endswith(os.path.sep)):
        t = input_dir[0:-1]
        input_dir = t
    phyml_file = str(args.phyml_file)
    verbose = args.verbose

    # check template dir exists
    if (not os.path.exists(input_dir)):
        print "Your input directory does not exist or you don't have permissions to read it"
        sys.exit(-1)

    # Parse the file and away we go:
    base_xml = """<?xml version='1.0' encoding='utf-8'?>
<phylo_storage>
  <project_name>
    <string_value lines="1"/>
  </project_name>
  <sources>
  </sources>
  <history/>
</phylo_storage>"""
    xml_root = etree.fromstring(base_xml)
    find = etree.XPath("//sources")
    sources = find(xml_root)[0]
    # add the project name from the input directory
    xml_root.xpath("/phylo_storage/project_name/string_value")[0].text = os.path.basename(input_dir)

    # for each XML
    nXML = 0;
    for xml in locate('*.xml', input_dir):
        # parse XML
        print xml
        current_xml = etree.parse(xml)
        # convert into PHYML
        new_source = convert_to_phyml_source(current_xml)

        # This is now the source_tree portion of the XML
        source_tree = convert_to_phyml_sourcetree(current_xml, xml)
         
        # add into PHYML sources element
        append_to_source, already_in = already_in_data(new_source,sources)
        if (not already_in):
            # append tree to current source
            new_source.append(deepcopy(source_tree))
            sources.append(deepcopy(new_source)) # deepcopy otherwise it'll add the same one several times :|
        else:
            # we need to find the correct source and append the source_tree to this
            print append_to_source
            append_to_source.append(deepcopy(source_tree))
            

        nXML += 1

    if (nXML == 0):
        print "Didn't find any XML files in this directory"
        sys.exit(-1)

    # create all sourcenames
    phyml = supertree_toolkit.all_sourcenames(etree.tostring(xml_root))

    # run data check
    try:
        supertree_toolkit._check_data(phyml)
    except:
        print "Error with creating data"
        sys,exit(-1)

    # save file
    f = open(phyml_file,'w')
    f.write(phyml)
    f.close()

    return

def already_in_data(new_source,sources):
    """
    Is the new source already in the dataset?

    Determine this by searching for the paper title
    """

    find = etree.XPath('//title/string_value')
    new_source_title = find(new_source)[0].text
    current_sources = find(sources)
    for title in current_sources:
        t = title.text
        if t == new_source_title:
            return title.getparent().getparent().getparent().getparent(), True

    return None, False

def locate(pattern, root=os.curdir):
    """Locate all files matching the pattern with the root dir and
    all subdirectories
    """
    import fnmatch
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files,pattern):
            yield os.path.join(path, filename)


def convert_to_phyml_source(xml_root):
    """ Converts old STK XML to a new STK source XML block
    ready for insertion into a PHYML tree
    """

    # parse XML file and extract necessary info
    find = etree.XPath("//Source")
    Source = find(xml_root)[0]
    input_author = Source.xpath('Author')[0].text
    input_title = Source.xpath('Title')[0].text
    input_year = Source.xpath('Year')[0].text
    input_journal = Source.xpath('Journal')[0].text
    input_volume = Source.xpath('Volume')[0].text
    input_pages = Source.xpath('Pages')[0].text
    input_booktitle = Source.xpath('Booktitle')[0].text
    input_editor = Source.xpath('Editor')[0].text
    input_publisher = Source.xpath('Publisher')[0].text
  
    author_list = []
    # split the string using ',', then stich together is needed
    a = input_author.lower()
    authors_t = a.split(',')
    authors_temp = []
    for a in authors_t:
        authors_temp.extend(a.split(' and '))

    if (len(authors_temp) > 1):
        i = 0
        while i<len(authors_temp):
            if (i+1 < len(authors_temp)):
                m = re.search(r'.', authors_temp[i+1])
                if (m != None):
                    # next token contains a full stop so is probably an initial
                    author_list.append(str.strip(authors_temp[i+1]) + " " + str.strip(authors_temp[i]))
                    i += 2
                else:
                    author_list.append(authors_temp[i])
                    i += 1
            else:
                i += 1
    else:
        author_list = input_author.split(' and ')

    phyml_root = etree.Element("source")
    publication = etree.SubElement(phyml_root,"source_publication")
    # does it contain a booktitle?
    contains_booktitle = False
    if (contains_booktitle):
        article = etree.SubElement(publication,"book")
    else:
        article = etree.SubElement(publication,"article")

    authors = etree.SubElement(article,"authors")

    # now parse authors into something sensible
    # authors - parse into full author names, then use nameparse to extract first and last
    for a in author_list:
        o = parser.HumanName(a)
        a = etree.SubElement(authors,'author')
        surname = etree.SubElement(a,'surname')
        string = etree.SubElement(surname,'string_value')
        string.attrib['lines'] = "1"
        string.text = o.last
        first = etree.SubElement(a,'other_names')
        string = etree.SubElement(first,'string_value')
        string.attrib['lines'] = "1"
        string.text = o.first

    # title and the publication data 
    title = etree.SubElement(article,"title")
    string = etree.SubElement(title,"string_value")
    string.attrib['lines'] = "1"
    string.text = input_title
    year = etree.SubElement(article,"year")
    integer = etree.SubElement(year,"integer_value")
    integer.attrib['rank'] = "0"
    integer.text = input_year
    journal = etree.SubElement(article,"journal")
    string = etree.SubElement(journal,"string_value")
    string.attrib['lines'] = "1"
    string.text = input_journal
    pages = etree.SubElement(article,"pages")
    string = etree.SubElement(pages,"string_value")
    string.attrib['lines'] = "1"
    string.text = input_pages


    return phyml_root


def convert_to_phyml_sourcetree(input_xml, xml_file):
    """ Extract the source_tree data from the old-style XML
    and create an XML tree inthe new style. We leave it to the
    main program to check that we append or add the source
    """
    

    # get tree filename from current_xml
    find_treefiles = etree.XPath('//TreeFile')
    treefile = find_treefiles(input_xml)[0].text
    # now stick on the root path of the XML to get the full path of the treefile
    cur_dir = os.path.split(xml_file)[0]
    tree = supertree_toolkit.import_tree(os.path.join(cur_dir,treefile))
    # all other data
    find_mol = etree.XPath('//Characters/Molecular/Type')
    find_morph = etree.XPath('//Characters/Morphological/Type')
    find_behave = etree.XPath('//Characters/Behavioural/Type')
    find_other = etree.XPath('//Characters/Other/Type')
    # analysis   
    input_comments = input_xml.xpath('/SourceTree/Notes')[0].text
    input_analysis = input_xml.xpath('/SourceTree/Analysis/Type')[0].text
    
    # construct new XML
    source_tree = etree.Element("source_tree")
    character_data = etree.SubElement(source_tree,"character_data")
    # loop over characters add correctly
    chars = find_mol(input_xml)
    for c in chars:
        new_char = etree.SubElement(character_data,"character")
        new_char.attrib['type'] = "molecular"
        new_char.attrib['name'] = c.text
    chars = find_morph(input_xml)
    for c in chars:
        new_char = etree.SubElement(character_data,"character")
        new_char.attrib['type'] = "morphological"
        new_char.attrib['name'] = c.text
    chars = find_behave(input_xml)
    for c in chars:
        new_char = etree.SubElement(character_data,"character")
        new_char.attrib['type'] = "behavioural"
        new_char.attrib['name'] = c.text
    chars = find_other(input_xml)
    for c in chars:
        new_char = etree.SubElement(character_data,"character")
        new_char.attrib['type'] = "other"
        new_char.attrib['name'] = c.text
    # analysis
    analysis_data = etree.SubElement(source_tree,"analysis_used")
    analysis_type = etree.SubElement(analysis_data,"analysis")
    analysis_type.attrib['name'] = input_analysis
    # tree data
    tree_data = etree.SubElement(source_tree,"tree_data")
    string = etree.SubElement(tree_data,"string_value")
    string.attrib["lines"] = "1"
    string.text = tree
    # comment
    comment = etree.SubElement(source_tree,"comment")
    comment.text = input_comments
    
    return source_tree

if __name__ == "__main__":
    main()


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

from Bio import Phylo
from StringIO import StringIO
import os
import sys
import math
import re
import numpy 
from lxml import etree
import argparse

####################################################
#
# Convert a PHYML file from the new supertree tool kit
# to the old data format, including XML, tre, files, etc
#
####################################################


def main():

    parser = argparse.ArgumentParser(
         description="""convert_to_old converts PHYML files to the data format used"""+
                     """by the first version of the STK"""
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
            'output_dir',
            help="A directory where the output will be stored"
            )
    parser.add_argument(
            'phyml_file',
            help="The PHYML file to be converted"
            )

    args = parser.parse_args()
    output_dir = str(args.output_dir)
    phyml_file = str(args.phyml_file)
    verbose = args.verbose

    # check template dir exists
    if (not os.path.exists(output_dir)):
        print "Your output directory does not exist or you don't have permissions to read it"
        sys.exit(-1)

    # Parse the file and away we go:
    xml_root = etree.parse(phyml_file)

    # First get project name and create the directory
    find = etree.XPath("//project_name")
    project_name = find(xml_root)[0].xpath("string_value")[0].text
    project_name.replace(' ','_')
    project_dir = os.path.join(output_dir,project_name)
    try:
        os.mkdir(project_dir)
    except OSError:
        print "Directory already exists."
        print "Please check you are trying to output into the correct directory. If so remove "+project_dir
        sys.exit(-1)
    except:
        print "Error making project directory: "+os.path.join(output_dir,project_name)
        sys.exit(-1)

    # Loop through the sources
    find = etree.XPath("//source")
    find_trees = etree.XPath("//source_tree")
    sources = find(xml_root)
    for s in sources:
        # Make directory
        name = s.attrib['name']
        if (verbose):
            print "----\nWorking on:" +name
        if (name == '' or name == None):
            print "One of the sources does not have a valid name. Aborting. Sorry about the mess"
            sys.exit(-1)

        source_dir = os.path.join(project_dir,name)
        os.mkdir(source_dir)
        # for this source, grab each tree_source and create the sub-directories
        tree_no = 1
        if (verbose):
            print "Found "+ str(len(s.xpath("source_tree"))) + " trees in this source"
        for t in s.xpath("source_tree"):
            tree_dir = os.path.join(source_dir,"Tree_"+str(tree_no))
            os.mkdir(tree_dir)
            # save the tree data
            handle = StringIO(t.xpath("tree_data/string_value")[0].text)
            tree = Phylo.parse(handle, 'newick')
            out_tree_file = open(os.path.join(tree_dir,name+"_tree_"+str(tree_no)+".tre"),"w")
            out_tree_file.write('#NEXUS\nBEGIN TREES;\nTree tree_1 = [&u] ')
            handler_out = StringIO()
            Phylo.NewickIO.write(tree, handler_out, plain=True)
            out_tree_file.write(handler_out.getvalue())
            out_tree_file.write("\nENDBLOCK;")
            out_tree_file.close()
            # create and save XML
            create_xml_metadata(etree.tostring(s), etree.tostring(t), os.path.join(tree_dir,name+"_tree_"+str(tree_no)))
            tree_no += 1

def create_xml_metadata(XML_string, this_source, filename):
    """ Converts a PHYML source block to the old style XML file"""

    XML = etree.fromstring(XML_string)
    source_XML = etree.fromstring(this_source)

    # from file name we can construct new tree object
    tree = Phylo.read(filename+'.tre','nexus')
    taxa_list = tree.get_terminals()
    
    # Then get all taxa:
    taxa_list = tree.get_terminals()
    new_xml = etree.Element("SourceTree")

    # The source publication info
    source = etree.SubElement(new_xml,"Source")
    author = etree.SubElement(source,"Author")
    find_authors = etree.XPath("//author/surname")
    surnames = find_authors(XML)
    authors_list = ''
    for s in surnames:
        if (authors_list != ''):
            authors_list = authors_list+" and "
        print s
        authors_list += s.xpath('string_value')[0].text
        
    author.text = authors_list
    year = etree.SubElement(source,"Year")
    year.text = XML.xpath("//year/integer_value")[0].text
    title = etree.SubElement(source,"Title")
    title.text = XML.xpath("//title/string_value")[0].text
    journal = etree.SubElement(source,"Journal")
    if (len(XML.xpath("//journal/string_value")) > 0):
        journal.text = XML.xpath("//journal/string_value")[0].text
    volume = etree.SubElement(source,"Volume")
    if (len(XML.xpath("//volume/string_value")) > 0):
        volume.text = XML.xpath("//volume/string_value")[0].text
    book = etree.SubElement(source,"Booktitle")
    if (len(XML.xpath("//booktitle/string_value")) > 0):
        book.text = XML.xpath("//booktitle/string_value")[0].text
    page = etree.SubElement(source,"Pages")
    if (len(XML.xpath("//pages/string_value")) > 0):
        page.text = XML.xpath("//pages/string_value")[0].text
    editor = etree.SubElement(source,"Editor")
    find_editors= etree.XPath("//editor/surname")
    surnames = find_editors(XML)
    authors_list = ''
    for s in surnames:
        if (authors_list != ''):
            authors_list = authors_list+" and "
        authors_list += s.xpath('string_value')[0].text
        
    editor.text = authors_list

    publisher = etree.SubElement(source, "Publisher")
    if (len(XML.xpath("//publisher/string_value")) > 0):
        publisher.text = XML.xpath("//publisher/string_value")[0].text


    # The taxa info
    taxa = etree.SubElement(new_xml,"Taxa")
    # add List for the number of taxa
    for t in taxa_list:
        l = etree.SubElement(taxa, "List")
        taxon = t.name
        taxon = taxon.replace('_',' ')
        l.text = taxon

    # if we find any taxa will fossil switched on, then add fossil attribute
    find_fossil = etree.XPath("//fossil")
    if (len(find_fossil(source_XML)) == 0):
        taxa.attrib['fossil'] = 'none'
    elif (len(find_fossil(source_XML)) == len(taxa_list)):
        taxa.attrib['fossil'] = 'all'
    else:
        taxa.attrib['fossil'] = 'some'
    taxa.attrib['number'] = str(len(taxa_list))

    # character data
    character = etree.SubElement(new_xml,"Characters")
    find_characters = etree.XPath("//character_data")
    characters_phyml = find_characters(source_XML)
    nMolecular = 0
    nMorpho = 0
    nBehaviour = 0
    nOther = 0
    molecular = etree.SubElement(character,"Molecular")
    morphological = etree.SubElement(character,"Morphological")
    behavioural = etree.SubElement(character,"Behavioural")
    other = etree.SubElement(character,"Other")
    for c in characters_phyml:
        if c.xpath("character")[0].attrib['type'] == 'molecular':
            l = etree.SubElement(molecular,"Type")
            l.text = c.xpath("character")[0].attrib['name']
            nMolecular += 1
        if c.xpath("character")[0].attrib['type'] == 'behavioural':
            l = etree.SubElement(behavioural,"Type")
            l.text = c.xpath("character")[0].attrib['name']
            nBehaviour += 1
        if c.xpath("character")[0].attrib['type'] == 'morphological':
            l = etree.SubElement(morphological,"Type")
            l.text = c.xpath("character")[0].attrib['name']
            nMorpho += 1
        if c.xpath("character")[0].attrib['type'] == 'other':
            l = etree.SubElement(other,"Type")
            l.text = c.xpath("character")[0].attrib['name']
            nOther += 0

    if (nMolecular > 0):
        molecular.attrib['number'] = str(nMolecular)
    if (nBehaviour > 0):
        behavioural.attrib['number'] = str(nBehaviour)
    if (nMorpho > 0):
        morphological.attrib['number'] = str(nMorpho)
    if (nOther > 0):
        other.attrib['number'] = str(nOther)

    # analysis data
    analysis = etree.SubElement(new_xml,"Analysis")
    find_analysis = etree.XPath("//analysis")
    analysis_phyml = find_analysis(source_XML)
    for a in analysis_phyml:
        l = etree.SubElement(analysis,"Type")
        l.text = a.attrib['name']

    # tree file - same directory :)
    tree_f = etree.SubElement(new_xml,"TreeFile")
    tree_file_only = os.path.basename(filename)
    tree_file_only += '.tre'
    tree_f.text = tree_file_only

    etree.SubElement(new_xml,'Notes')

    xml_string = etree.tostring(new_xml, encoding='iso-8859-1', pretty_print=True)

    f = open(filename+'.xml','w')
    f.write(xml_string)
    f.close()

if __name__ == "__main__":
    main()

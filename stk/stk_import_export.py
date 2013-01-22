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

from StringIO import StringIO
import os
import sys
import math
import re
import numpy 
from lxml import etree
import stk.nameparser.parser as np
import re
import supertree_toolkit
from copy import deepcopy
from supertree_toolkit import _parse_xml
from stk_exceptions import *
from stk_internals import *
import stk.p4
import unicodedata

def export_to_old(xml, output_dir, verbose=False):

    """ Create an old STK dataset from a PHYML file. Hopefuly not useful 
    in the long run as all functionality will be replicated, but may 
    be useful in the short term
    """

    # Parse the file and away we go:
    xml_root = _parse_xml(xml)

    # First get project name and create the directory
    find = etree.XPath("//project_name")
    project_name = find(xml_root)[0].xpath("string_value")[0].text
    project_name.replace(' ','_')
    project_dir = os.path.join(output_dir,project_name)
    try:
        os.mkdir(project_dir)
    except OSError:
        msg = "Directory already exists. "
        msg += "Please check you are trying to output into the correct directory. If so remove "+project_dir
        raise STKImportExportError(msg)
    except:
        msg = "Error making project directory: "+os.path.join(output_dir,project_name)
        raise STKImportExportError(msg)

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
            msg = "One of the sources does not have a valid name. Aborting."
            raise STKImportExportError(msg)

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
            tree = t.xpath("tree_data/string_value")[0].text
            stk.p4.var.warnReadNoFile = False
            stk.p4.var.trees = []
            stk.p4.read(tree)
            stk.p4.var.warnReadNoFile = True
            trees = stk.p4.var.trees
            stk.p4.var.trees = []
            tree = trees[0].writeNewick(fName=None,toString=True).strip()
            out_tree_file = open(os.path.join(tree_dir,name+"_tree_"+str(tree_no)+".tre"),"w")
            out_tree_file.write('#NEXUS\nBEGIN TREES;\nTree tree_1 = [&u] ')
            out_tree_file.write(tree)
            out_tree_file.write("\nENDBLOCK;")
            out_tree_file.close()
            # create and save XML
            create_xml_metadata(etree.tostring(s), etree.tostring(t), os.path.join(tree_dir,name+"_tree_"+str(tree_no)))
            tree_no += 1


def import_old_data(input_dir, verbose=False):
    """ Converts an old STK dataset (based on directories) to the new PHYML
    file format. Note: we need XML files to get the meta data and also that
    the data imported may not be complete. It's up to the calling program to save the resulting 
    xml string somewhere sensible.
    """

    # strip trailing path separator if one
    if (input_dir.endswith(os.path.sep)):
        t = input_dir[0:-1]
        input_dir = t

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
        if (verbose):
            print "Parsing: "+xml
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
            append_to_source.append(deepcopy(source_tree))
            

        nXML += 1

    if (nXML == 0):
        msg = "Didn't find any XML files in this directory"
        raise STKImportExportError(msg)

    # create all sourcenames
    phyml = supertree_toolkit.all_sourcenames(etree.tostring(xml_root))

    # run data check
    try:
        supertree_toolkit._check_data(phyml)
    except:
        msg = "Error with creating data"
        raise STKImportExportError(msg)

    return phyml


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
    if isinstance(a, unicode):
        a = unicodedata.normalize('NFKD', a).encode('ascii','ignore')
        print a
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
        
    if (len(author_list) == 0):
	author_list.append(input_author)
   
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
        o = np.HumanName(a)
        ae = etree.SubElement(authors,'author')
        surname = etree.SubElement(ae,'surname')
        string = etree.SubElement(surname,'string_value')
        string.attrib['lines'] = "1"
        string.text = o.last.capitalize()
        if (o.last.capitalize() == ''):
	    string.text = a
        first = etree.SubElement(ae,'other_names')
        string = etree.SubElement(first,'string_value')
        string.attrib['lines'] = "1"
        string.text = o.first.capitalize()
        # reset to empty if needed
        if (o.last == None):
            string.text = ''

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


def create_xml_metadata(XML_string, this_source, filename):
    """ Converts a PHYML source block to the old style XML file"""

    XML = etree.fromstring(XML_string)
    source_XML = etree.fromstring(this_source)

    # from file name we can construct new tree object
    try:
        stk.p4.var.warnReadNoFile = False
        stk.p4.var.trees = []
        stk.p4.read(filename+'.tre')
        stk.p4.var.warnReadNoFile = True
    except:
        raise TreeParseError("Error parsing " + filename)
    trees = stk.p4.var.trees
    stk.p4.var.trees = []
    tree = trees[0]
    taxa_list = tree.getAllLeafNames(0)
    
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
        t = t.replace('_',' ')
        l.text = t

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

#def _capitalise_source_name(name):
#    "Capiltalises a source name, taking into account etal
#    smith_jones_2003 -> Smith_Jones_2003
#    smith_etal_2003 -> Smith_etal_2003
#    etc
#    """


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
import yapbib.biblist as biblist
import string
from stk_exceptions import *
import traceback
from cStringIO import StringIO
from collections import defaultdict
import p4
import re
from indent import *

# supertree_toolkit is the backend for the STK. Loaded by both the GUI and
# CLI, this contains all the functions to actually *do* something
#
# All functions take XML and a list of other arguments, process the data and return
# it back to the user interface handler to save it somewhere

def create_name(authors, year, append=''):
    """ From a list of authors and a year construct a sensible
    source name.
    Input: authors - list of last (family, sur) names (string)
           year - the year (string)
    Output: source_name - (string)"""

    source_name = None
    if (len(authors) == 1):
        # single name: name_year
        source_name = authors[0] + "_" + year + append
    elif (len(authors) == 2):
        source_name = authors[0] + "_" + authors[1] + "_" + year + append
    else:
        source_name = authors[0] + "_etal_" + year + append

    return source_name


def single_sourcename(XML,append=''):
    """ Create a sensible source name based on the 
    bibliographic data.
    xml_root should contain the xml_root for the source that is to be
    altered only
    NOTE: It is the responsibility of the calling process of this 
          function to check for name uniqueness.
    """

    xml_root = _parse_xml(XML)

    find = etree.XPath("//authors")
    authors_ele = find(xml_root)[0]
    authors = []
    for ele in authors_ele.iter():
        if (ele.tag == "surname"):
            authors.append(ele.xpath('string_value')[0].text)
    
    find = etree.XPath("//year/integer_value")
    year = find(xml_root)[0].text
    source_name = create_name(authors, year,append)

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

    xml_root = _parse_xml(XML)

    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    for s in sources:
        xml_snippet = etree.tostring(s,pretty_print=True)
        xml_snippet = single_sourcename(xml_snippet)
        parent = s.getparent()
        ele_T = _parse_xml(xml_snippet)
        parent.replace(s,ele_T)

    XML = etree.tostring(xml_root,pretty_print=True)
    # gah: the replacement has got rid of line breaks for some reason
    XML = string.replace(XML,"</source><source ", "</source>\n    <source ")
    XML = string.replace(XML,"</source></sources", "</source>\n  </sources") 
    XML = set_unique_names(XML)
    return XML

def get_all_source_names(XML):
    """ From a full XML-PHYML string, extract all source names
    """

    xml_root = _parse_xml(XML)
    find = etree.XPath("//source")
    sources = find(xml_root)
    names = []
    for s in sources:
        attr = s.attrib
        name = attr['name']
        names.append(name)
    
    return names

def set_unique_names(XML):
    """ Ensures all sources have unique names
    """
    
    xml_root = _parse_xml(XML)

    # All source names
    source_names = get_all_source_names(XML)

    # The list is stored as a dict, with the key being the name
    # The value is the number of times this names occurs
    unique_source_names = defaultdict(int)
    for n in source_names:
        unique_source_names[n] += 1

    # if they are unique (i.e. == 1), then make it == 0
    for k in unique_source_names.iterkeys():
        if unique_source_names[k] == 1:
            unique_source_names[k] = 0
    
    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    last_name = ''
    for s in sources:
        current_name = s.attrib['name']
        if (unique_source_names[current_name] > 0):
            number = unique_source_names[current_name]
            # if there are two entries for this name, we should get 'a' and 'b'
            # 'a' + 1 == b
            # 'a' + 0 == a
            letter = chr(ord('a')+(number-1)) 
            xml_snippet = etree.tostring(s,pretty_print=True)
            xml_snippet = single_sourcename(xml_snippet,append=letter)
            parent = s.getparent()
            ele_T = _parse_xml(xml_snippet)
            parent.replace(s,ele_T)
            # decrement the value so our letter is not the
            # same as last time
            unique_source_names[current_name] -=1

    XML = etree.tostring(xml_root,pretty_print=True)

    return XML


def import_bibliography(XML, bibfile):    
    
    # Out bibliography parser
    b = biblist.BibList()

    xml_root = _parse_xml(XML)
    
    # Track back along xpath to find the sources where we're about to add a new source
    sources = xml_root.xpath('sources')[0]
    sources.tail="\n      "
    if (bibfile == None):
        raise BibImportError("Error importing bib file. There was an error with the file")

    try: 
        b.import_bibtex(bibfile)
    except UnboundLocalError:
        # This seems to be raised if the authors aren't formatted correctly
        raise BibImportError("Error importing bib file. Check all your authors for correct format")
    except AttributeError:
        # This seems to occur if the keys are not set for the entry
        raise BibImportError("Error importing bib file. Check all your entry keys")
    except: 
        raise BibImportError("Error importing bibliography") 

    items= b.sortedList[:]

    for entry in items:
        # for each bibliographic entry, create the XML stub and
        # add it to the main XML
        it= b.get_item(entry)
        xml_snippet = it.to_xml()
        if xml_snippet != None:
            # turn this into an etree
            publication = _parse_xml(xml_snippet)
            # create top of source
            source = etree.Element("source")
            # now attach our publication
            source.append(publication)
            new_source = single_sourcename(etree.tostring(source,pretty_print=True))
            source = _parse_xml(new_source)

            # now create tail of source
            s_tree = etree.SubElement(source, "source_tree")
            s_tree.tail="\n      "
           
            characters = etree.SubElement(s_tree,"character_data")
            c_data = etree.SubElement(characters,"character")
            analyses = etree.SubElement(s_tree,"analysis_used")
            a_data = etree.SubElement(analyses,"analysis")
            tree = etree.SubElement(s_tree,"tree_data")
            tree_string = etree.SubElement(tree,"string_value")

            source.tail="\n      "

            # append our new source to the main tree
            sources.append(source)
        else:
            raise BibImportError("Error with one of the entries in the bib file")

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

def import_tree(filename, gui=None, tree_no = -1):
    """Takes a NEXUS formatted file and returns a list containing the tree
    strings"""
  
# Need to add checks on the file. Problems include:
# TreeView (Page, 1996):
# TreeView create a tree with the following description:
#
#   UTREE * tree_1 = ((1,(2,(3,(4,5)))),(6,7));
# UTREE * is not a supported part of the NEXUS format (as far as BioPython).
# so we need to replace the above with:
#   tree_1 = [&u] ((1,(2,(3,(4,5)))),(6,7));
#
# BioPython doesn throw an exception or anything on these files,
# So for now glob the file, replace the text, and create a StringIO 
# object to pass BioPython - MESSY!!
    f = open(filename)
    content = f.read()                 # read entire file into memory
    f.close()
    # Treeview
    m = re.search(r'\UTREE\s?\*\s?(.+)\s?=\s', content)
    if (m != None):
        treedata = re.sub("\UTREE\s?\*\s?(.+)\s?=\s","tree "+m.group(1)+" = [&u] ", content)
        content = treedata
# Now check for Macclade. easy to spot, has MacClade in the text
# MacClade has a whole heap of other stuff, we just want the tree...
# Mesquite is similar, but need more processing - see later
    m = re.search(r'MacClade',content)
    if (m!=None):
        # Done on a Mac? Replace ^M with a newline
        content = string.replace( content, '\r', '\n' )
        h = StringIO(content)
        content  = "#NEXUS\n"
        add_to = False
        for line in h:
            if (line.startswith('BEGIN TREES')):
                add_to = True
            if (add_to):
                content += line
            if (line.startswith('END') and add_to):
                add_to = False
                break

# Mesquite is similar to MacClade, but need more processing
    m = re.search(r'Mesquite',content)
    if (m!=None):
        # Done on a Mac? Replace ^M with a newline
        content = string.replace( content, '\r', '\n' )
        h = StringIO(content)
        content  = "#NEXUS\n"
        add_to = False
        for line in h:
            if (line.startswith('BEGIN TREES')):
                add_to = True
            if (add_to):
                # do not add the LINK line
                mq = re.search(r'LINK',line)
                if (mq == None):
                    content += line
            if (line.startswith('END') and add_to):
                add_to = False
                break

# Dendroscope produces non-Nexus trees. but the tree is easy to pick out
#{TREE 'tree_1'
#((Taxon_c:1.0,(Taxon_a:1.0,Taxon_b:1.0):1.0):0.5,(Taxon_d:1.0,Taxon_e:1.0):0.5);
#}
    m = re.search(r'#DENDRO',content)
    if (m!=None):
        h = StringIO(content)
        content = "#NEXUS\n"
        content += "begin trees;\ntree tree_1 = [&U] "
        add_to = False
        for line in h:
            if (line.startswith('}') and add_to):
                add_to = False
            if (add_to):
                content += line+"\n"
            if (line.startswith('{TREE')):
                add_to = True
        content += "\nend;"
        #remove nodal branch lengths
        content = re.sub("\):\d.\d+","):0.0", content)

    treedata = content
    handle = StringIO(treedata)
    
    if (filename.endswith(".nex") or filename.endswith(".tre")):
        trees = list(Phylo.parse(handle, "nexus"))
    elif (filename.endswith("nwk")):
        trees = list(Phylo.parse(handle, "newick"))
    elif (filename.endswith("phyloxml")):
        trees = list(Phylo.parse(handle, "phyloxml"))

    if (len(trees) > 1 and tree_no == -1):
        message = "Found "+len(trees)+" trees. Which one do you want to load (1-"+len(trees)+"?"
        if (gui==None):
            tree_no = raw_input(message)
            # assume the user counts from 1 to n
            tree_no -= 1
        else:
            #base this on a message dialog
            dialog = gtk.MessageDialog(
		        None,
		        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
		        gtk.MESSAGE_QUESTION,
		        gtk.BUTTONS_OK,
		        None)
            dialog.set_markup(message)
            #create the text input field
            entry = gtk.Entry()
            #allow the user to press enter to do ok
            entry.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
            #create a horizontal box to pack the entry and a label
            hbox = gtk.HBox()
            hbox.pack_start(gtk.Label("Tree number:"), False, 5, 5)
            hbox.pack_end(entry)
            #add it and show it
            dialog.vbox.pack_end(hbox, True, True, 0)
            dialog.show_all()
            #go go go
            dialog.run()
            text = entry.get_text()
            dialog.destroy()
            tree_no = int(text) - 1
    else:
        tree_no = 0

    h = StringIO()
    Phylo.write(trees[tree_no], h, "newick")
    tree = h.getvalue()

    return tree

def draw_tree(tree_string):
    
    h = StringIO(tree_string)
    tree = Phylo.read(h, 'newick')
    tree.ladderize()   # Flip branches so deeper clades are displayed at top
    Phylo.draw(tree)

def get_all_characters(XML):
    """Returns a dictionary containing a list of characters within each 
    character type"""

    xml_root = _parse_xml(XML)
    find = etree.XPath("//character")
    characters = find(xml_root)

    # grab all character types first
    types = []
    for c in characters:
        types.append(c.attrib['type'])

    u_types = _uniquify(types)
    u_types.sort()

    char_dict = {}
    for t in u_types:
        char = []
        for c in characters:
            if (c.attrib['type'] == t):
                if (not c.attrib['name'] in char):
                    char.append(c.attrib['name'])
        char_dict[t] = char       

    return char_dict

def get_character_numbers(XML):
    """ Return the number of trees that use each character
    """

    xml_root = _parse_xml(XML)
    find = etree.XPath("//character")
    characters = find(xml_root)

    char_numbers = defaultdict(int)

    for c in characters:
        char_numbers[c.attrib['name']] += 1

    return char_numbers



def get_fossil_taxa(XML):
    """Return a list of fossil taxa
    """

    f_ = []

    xml_root = _parse_xml(XML)
    find = etree.XPath("//fossil")
    fossils = find(xml_root)

    for f in fossils:
        name = f.getparent().attrib['name']
        f_.append(name)

    fossil_taxa = _uniquify(f_) 
    
    return fossil_taxa


def get_analyses_used(XML):
    """ Return a sorted, unique array of all analyses types used
    in this dataset
    """

    a_ = []

    xml_root = _parse_xml(XML)
    find = etree.XPath("//analysis")
    analyses = find(xml_root)

    for a in analyses:
        name = a.attrib['name']
        a_.append(name)

    analyses = _uniquify(a_) 
    analyses.sort()

    return analyses



def get_publication_years(XML):
    """Return a dictionary of years and the number of publications
    within that year
    """

    year_dict = defaultdict(int)
    xml_root = _parse_xml(XML)
    find = etree.XPath("//year")
    years = find(xml_root)

    for y in years:
        year = int(y.xpath('integer_value')[0].text)
        year_dict[year] += 1

    return year_dict

def obtain_trees(XML):
    """ Parse the XML and obtain all tree strings
    Output: dictionary of tree strings, with key indicating treename (unique)
    """

    xml_root = _parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    # within that source and construct a unique name
    find = etree.XPath("//source")
    sources = find(xml_root)

    trees = {}

    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        # get trees
        tree_no = 1
        for t in s.xpath("source_tree/tree_data"):
            t_name = name+"_"+str(tree_no)
            # append to dictionary, with source_name_tree_no = tree_string
            trees[t_name] = t.xpath("string_value")[0].text
            tree_no += 1

    return trees

def get_all_taxa(XML, pretty=False):
    """ Produce a taxa list by scanning all trees within 
    a PHYML file. 

    The list is return sorted (alphabetically).

    Setting pretty=True means all underscores will be
    replaced by spaces"""

    trees = obtain_trees(XML)

    taxa_list = []

    for tname in trees.keys():
        t = trees[tname]
        handle = StringIO(t)
        t_obj = list(Phylo.parse(handle, "newick"))
        t_obj = t_obj[0]
        terminals = t_obj.get_terminals()
        for term in terminals:
            taxa_list.append(str(term))

    # now uniquify the list of taxa
    taxa_list = _uniquify(taxa_list)
    taxa_list.sort()

    if (pretty):
        unpretty_tl = taxa_list
        taxa_list = []
        for t in unpretty_tl:
            taxa_list.append(t.replace('_',' '))

    return taxa_list

def create_matrix(XML,format="hennig"):

    # get all trees
    trees = obtain_trees(XML)

    # and the taxa
    taxa = []
    taxa.append("MRPOutgroup")
    taxa.extend(get_all_taxa(XML))

    # our matrix, we'll then append the submatrix
    # to this to make a 2D matrix
    # Our matrix is of length nTaxa on the i dimension
    # and nCharacters in the j direction
    matrix = []
    charsets = []
    names = []
    current_char = 1
    for key in trees:
        names.append(key)
        handle = StringIO(trees[key])
        newick_trees = list(Phylo.parse(handle, "newick"))
        newick_tree = newick_trees[0]
        submatrix, tree_taxa = _assemble_tree_matrix(newick_tree)
        nChars = len(submatrix[0,:])
        # loop over characters in the submatrix
        for i in range(1,nChars):
            # loop over taxa. Add '?' for an "unknown" taxa, otherwise
            # get 0 or 1 from submatrix. May as well turn into a string whilst
            # we're at it
            current_row = []
            for taxon in taxa:
                if (taxon in tree_taxa):
                    # get taxon index
                    t_index = tree_taxa.index(taxon)
                    # then get correct matrix entry - note:
                    # submatrix transposed wrt main matrix
                    current_row.append(str(int(submatrix[t_index,i])))
                elif (taxon == "MRPOutgroup"):
                    current_row.append('0')
                else:
                    current_row.append('?')
            matrix.append(current_row)
        charsets.append(str(current_char) + "-" + str(current_char + nChars-2))
        current_char += nChars-1

    matrix = numpy.array(matrix)
    matrix = matrix.transpose()

    if (format == 'hennig'):
        matrix_string = "xread\n"
        matrix_string += str(len(taxa)) + " "+str(current_char-1)+"\n"
        matrix_string += "\tformat missing = ?"
        matrix_string += ";\n"
        matrix_string += "\n\tmatrix\n\n";

        i = 0
        for taxon in taxa:
            matrix_string += taxon + "\t"
            string = ""
            for t in matrix[i][:]:
                string += t
            matrix_string += string + "\n"
            i += 1
            
        matrix_string += "\t;\n"
        matrix_string += "procedure /;"
    elif (format == 'nexus'):
        matrix_string = "#nexus\n\nbegin data;\n"
        matrix_string += "\tdimensions ntax = "+str(len(taxa)) +" nchar = "+str(current_char-1)+";\n"
        matrix_string += "\tformat missing = ?"
        matrix_string += ";\n"
        matrix_string += "\n\tmatrix\n\n"

        i = 0
        for taxon in taxa:
            matrix_string += taxon + "\t"
            string = ""
            for t in matrix[i][:]:
                string += t
            matrix_string += string + "\n"
            i += 1
            
        matrix_string += "\t;\nend;\n\n"
        matrix_string += "begin sets;\n"
        i = 0
        for char in charsets:
            matrix_string += "\tcharset "+names[i] + " "
            matrix_string += char + "\n"
            i += 1
        matrix_string += "end;\n\n"
    else:
        raise MatrixError("Invalid matrix format")

    return matrix_string

def load_phyml(filename):
    """ Super simple function that returns XML
        string from PHYML file
    """
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.tostring(etree.parse(filename,parser),pretty_print=True)


def substitute_taxa(XML, old_taxa, new_taxa=None):
    """
    Swap the taxa in the old_taxa array for the ones in the
    new_taxa array
    
    If the new_taxa array is missing, simply delete the old_taxa

    Returns a new XML with the taxa swapped from each tree and any taxon
    elements for those taxa removed. It's up to the calling function to
    do something sensible with this infomation
    """

    # are the input values lists or simple strings?
    if (isinstance(old_taxa,str)):
        old_taxa = [old_taxa]
    if (new_taxa and isinstance(new_taxa,str)):
        new_taxa = [new_taxa]

    # check they are same lengths now
    if (new_taxa):
        if (len(old_taxa) != len(new_taxa)):
            print "Substitution failed. Old and new are different lengths"
            return # need to raise exception here

    # need to check for uniquessness of souce names - error is not unique
    _check_uniqueness(XML)

    # grab all trees and store as bio.phylo.tree objects
    trees = obtain_trees(XML)

    for name in trees.iterkeys():
        tree = trees[name]
        i = 0
        for taxon in old_taxa:
            # tree contains the old_taxon, do something with it
            if (tree.find(taxon) > 0):
                if (new_taxa == None or new_taxa[i] == None):
                    # we are deleting taxa
                    tree = _delete_taxon(taxon, tree)
                    XML = _swap_tree_in_XML(XML,tree,name)
                else:
                    # we are substituting
                    tree = _sub_taxon(taxon, new_taxa[i], tree)
                    XML = _swap_tree_in_XML(XML,tree,name)
            i += 1
 

    # now loop over all taxon elements in the XML, and 
    # remove/sub as necessary
    i = 0
    xml_root = _parse_xml(XML)
    xml_taxa = []
    # grab all taxon elements and store
    # We're going to delete and we can't do that whilst
    # iterating over the XML. There lies chaos.
    for ele in xml_root.iter():
        if (ele.tag == "taxon"):
            xml_taxa.append(ele)

   
    i = 0
    for taxon in old_taxa:
        if (new_taxa == None or new_taxa[i] == None):
            # need to search for elements that have the right name and delete them
            for ele in xml_taxa:
                if (ele.attrib['name'] == taxon):
                    # You remove the element by getting the 
                    # deleting it from the parent
                    ele.getparent().remove(ele)
        else:
            for ele in xml_taxa:
                if (ele.attrib['name'] == taxon):
                    ele.attrib['name'] = new_taxa[i]
        i = i+1

    return etree.tostring(xml_root,pretty_print=True)


def safe_taxonomic_reduction(XML, matrix=None, verbose=False):
    """ Perform STR on data to remove taxa that 
    provide no useful additional information
    """

    # Algorithm descibed by ******
    # modified for *supertrees*, which mainly involves cutting
    # out stuff to do with multiple state characters

    missing_char = "?"
    TotalInvalid = 0

    if (matrix):
        # a matrix was supplied, so strip out the info needed
        i = 0
    else:
        # create matrix, but keep the matrix as an array
        # and get the taxa - hence we replicate most
        # create matrix code
        # *******REFACTOR: Split create_matrix into multiple 
        # functions, so we can just call them here and in create_matrix
        # get all trees
        trees = obtain_trees(XML)
        # and the taxa
        taxa = []
        taxa.append("MRPOutgroup")
        taxa.extend(get_all_taxa(XML))
        # our matrix, we'll then append the submatrix
        # to this to make a 2D matrix
        # Our matrix is of length nTaxa on the i dimension
        # and nCharacters in the j direction
        matrix = []
        charsets = []
        current_char = 1
        for key in trees:
            handle = StringIO(trees[key])
            newick_trees = list(Phylo.parse(handle, "newick"))
            newick_tree = newick_trees[0]
            submatrix, tree_taxa = _assemble_tree_matrix(newick_tree)
            nChars = len(submatrix[0,:])
            # loop over characters in the submatrix
            for i in range(1,nChars):
                # loop over taxa. Add '?' for an "unknown" taxa, otherwise
                # get 0 or 1 from submatrix. May as well turn into a string whilst
                # we're at it
                current_row = []
                for taxon in taxa:
                    if (taxon in tree_taxa):
                        # get taxon index
                        t_index = tree_taxa.index(taxon)
                        # then get correct matrix entry - note:
                        # submatrix transposed wrt main matrix
                        current_row.append(str(int(submatrix[t_index,i])))
                    elif (taxon == "MRPOutgroup"):
                        current_row.append('0')
                    else:
                        current_row.append('?')
                matrix.append(current_row)
            charsets.append(str(current_char) + "-" + str(current_char + nChars-2))
            current_char += nChars-1
        matrix = numpy.array(matrix)
        matrix = matrix.transpose()

    new_matrix = matrix
    nChars = len(matrix[0][:])
    # this is the heavy loop
    t1 = 0
    equiv_matrix = []
    missing_chars = []
    # count missing chars for each taxon
    for taxon in taxa:
        chars_t1 = numpy.asarray(matrix[t1][:])
        missing = 0
        for c in chars_t1:
            if c == missing_char:
                missing+=1
        missing_chars.append(missing)
        t1+=1

    nTaxa = len(taxa)

    t1 = 0
    for taxon in taxa:
        t2 = 0
        equiv_matrix.append([taxon,missing_chars[t1]])
        equiv_taxa = []
        for taxon2 in taxa:
            if (taxon2 == taxon):
                t2 += 1
                continue
            NonEquiv = 0
            t2_missing = missing_chars[t2]
            yMissing = 0
            xMissing = 0
            Symmetric = 1
            xMiss_yCode = 0
            xCode_yMiss = 0
            for i in range(nChars):
                char1 = matrix[t1][i]
                char2 = matrix[t2][i]
                if ((char1 != missing_char) and (char2 != missing_char)) :
                    #print taxon, taxon2, char1, char2
                    if(char1 != char2):
                        NonEquiv = 1
                elif((char1 == missing_char) and (char2 != missing_char)):
                    TotalInvalid+=1
                    xMissing = 1
                    xMiss_yCode = 1
                    Symmetric = 0
                elif((char1 != missing_char) and (char2 == missing_char)):
                    TotalInvalid+=1
                    yMissing = 1
                    xCode_yMiss = 1
                    Symmetric = 0
                elif((char1 == missing_char) and (char2 == missing_char)):
                    TotalInvalid+=1
                    yMissing = 1
                    xMissing = 1
			
            t2 = t2+1

            if (NonEquiv == 1):
                continue
            else:
                if(Symmetric == 1):
                    if((xMissing == 0) and (yMissing == 0)):
                        equiv_taxa.append([taxon2,"A",t2_missing])
                        continue
                    else:
                        equiv_taxa.append([taxon2,"B",t2_missing])
                        continue
                elif(Symmetric == 0):
                    if((xMissing == 0) and (yMissing == 1)):
                        equiv_taxa.append([taxon2,"C",t2_missing])
                        continue
                    elif((xMissing == 1) and (yMissing == 0)):
                        equiv_taxa.append([taxon2,"E",t2_missing])
                        continue
                    elif((xMissing == 1) and (yMissing == 1)):
                        if((xCode_yMiss == 1) and (xMiss_yCode == 1)):
                            equiv_taxa.append([taxon2,"D",t2_missing])
                            continue
                        elif(xMiss_yCode == 0):
                            equiv_taxa.append([taxon2,"C",t2_missing])
                            continue
                        elif(xCode_yMiss == 0):
                            equiv_taxa.append([taxon2,"E",t2_missing])
                            continue
        if (len(equiv_taxa) > 0):
            equiv_matrix[t1].extend([equiv_taxa])
        else:
            equiv_matrix[t1].extend(["No equivalence"])
        t1 += 1
        if (verbose):
            print "Done taxa "+str(t1)+" of "+str(nTaxa)
            
    can_replace = []
    # need to work out which taxa to remove
    for i in range(len(taxa)):
        if equiv_matrix[i][2] == 'No equivalence':
            continue
        elif equiv_matrix[i][0] in can_replace:
            # this taxon is already in the deleted list
            continue
        else:
            nMissing_t1 = missing_chars[i]
            equivs = equiv_matrix[i][2]
            for e in equivs:
                if (e[1] == "A" or e[1] == "B" or e[1] == "C"):
                    # we can delete one of these taxa
                    # first check which has more missing characters
                    if nMissing_t1 > e[2]:
                        can_replace.append(equiv_matrix[i][0])
                        break # no point checking the rest, we've removed the parent taxon!
                    else:
                        if (not e[0] in can_replace):
                            can_replace.append(e[0])


    # create output
    can_replace.sort()
    output_string = "Equivalency Matrix\n"
    labels = ('Taxon', 'No Missing', 'Equivalents')
    output_data = []
    for i in range(len(taxa)):
        equivs = equiv_matrix[i][2]
        eq = ""
        if equivs == "No equivalence":
            eq == equivs
        else:
            for e in equivs:
                eq += e[0]+"("+e[1]+")  "
        output_data.append([equiv_matrix[i][0],str(missing_chars[i]),eq])

    output_string += indent([labels]+output_data, hasHeader=True, prefix='| ', postfix=' |')

    output_string += "\n\n"
    output_string += "Recommend you remove the following taxa:\n"
    if (len(can_replace) == 0):
        output_string += "No taxa can be removed\n"
    else:
        for c in can_replace:
            output_string += c+"\n"

    return output_string, can_replace

def data_summary(XML,detailed=False):
    """Creates a text string that summarises the current data set via a number of 
    statistics such as the number of character types, distribution of years of publication,
    etc.

    Up to the calling function to display string nicely
    """
    xml_root = _parse_xml(XML)
    proj_name = xml_root.xpath('/phylo_storage/project_name/string_value')[0].text

    output_string  = "======================\n"
    output_string += " Data summary of: " + proj_name + "\n" 
    output_string += "======================\n\n"

    trees = obtain_trees(XML)
    taxa = get_all_taxa(XML, pretty=True)
    characters = get_all_characters(XML)
    char_numbers = get_character_numbers(XML)
    fossils = get_fossil_taxa(XML)
    publication_years = get_publication_years(XML)
    analyses = get_analyses_used(XML)
    years = publication_years.keys()
    years.sort()
    chars = char_numbers.keys()
    chars.sort()

    output_string += "Number of taxa: "+str(len(taxa))+"\n"
    output_string += "Number of characters: "+str(len(chars))+"\n"
    output_string += "Number of character types: "+str(len(characters))+"\n"
    output_string += "Number of trees: "+str(len(trees))+"\n"
    output_string += "Number of fossil taxa: "+str(len(fossils))+"\n"
    output_string += "Number of analyses: "+str(len(analyses))+"\n"
    output_string += "Data spans: "+str(years[0])+" - "+str(years[-1])+"\n"


    if (detailed):
        # append additional info including full list of characters
        # full list of taxa and full list of fossil taxa
        output_string += "\nPublication years:\n"
        output_string += "----------------------\n"
        for i in range(years[0],years[-1]+1):
            output_string += "    "+str(i)+": "+str(publication_years[i])+"\n"
        output_string += "----------------------\n"

        output_string += "\n\nCharacter Type List:\n"
        output_string += "----------------------\n"
        for c in characters:
            output_string += "     "+c+"    " + "\n"
        output_string += "----------------------\n"

        output_string += "\n\nAnalyses Used:\n"
        output_string += "----------------------\n"
        for a in analyses:
            output_string += "     "+a+"\n"
        output_string += "----------------------\n"


        output_string += "\n\nCharacter List:\n"
        output_string += "----------------------\n"
        for c in chars:
            output_string += "     "+c+"    "+str(char_numbers[c])+"("+str(float(char_numbers[c])/float(len(trees))*100.)+"%)\n"
        output_string += "----------------------\n"
        
        output_string += "\n\nTaxa List:\n"
        output_string += "----------------------\n"
        for t in taxa:
            output_string += "     "+t+"\n"
        output_string += "----------------------\n"


    return output_string

################ PRIVATE FUNCTIONS ########################


def _uniquify(l):
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()


def _check_uniqueness(XML):
    """ This funciton is an error check for uniqueness in 
    the keys of the sources
    """

    xml_root = _parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    # within that source and construct a unique name
    find = etree.XPath("//source")
    sources = find(xml_root)

    names = []

    # loop through all sources
    for s in sources:
        # for each source, get source name
        names.append(s.attrib['name'])

    names.sort()
    last_name = "" # This will actually throw an non-unique error if a name is empty
    # not great, but still an error!
    for name in names:
        if name == last_name:
            # if non-unique throw exception
            raise NotUniqueError("The source names in the dataset are not unique." +
                    "Please run the auto-name function on these data. Name: "+name)
        last_name = name
    return


def _assemble_tree_matrix(tree):
    """ Assembles the MRP matrix for an individual tree

        returns: matrix (2D numpy array: taxa on i, nodes on j)
                 taxa list: in same order as in the matrix
    """

    all_nodes = list(tree.get_nonterminals())
    look_up = {}
    for i, elem in enumerate(all_nodes):
        look_up[elem] = i

    all_terms = list(tree.get_terminals())
    look_up_t = {}
    names = []
    for i, elem in enumerate(all_terms):
        look_up_t[elem] = i
        names.append(str(elem))

    adjmat = numpy.zeros((len(look_up_t), len(look_up)))

    for i, terminal in enumerate(all_terms):
        my_parents =  list(tree.get_path(terminal))
        for j, p in enumerate(my_parents):
            if (p == terminal):
                adjmat[look_up_t[terminal],0] = 1
            else:
                adjmat[look_up_t[terminal],look_up[p]] = 1

    return adjmat, names

def _delete_taxon(taxon, tree):
    """ Delete a taxon from a tree string
    """

    # check if taxa is in there first
    # Prevent error from Bio.Phylo
    if (tree.find(taxon) == -1):
        return tree #raise exception?

    handle = StringIO(tree)
    t_obj = list(Phylo.parse(handle, "newick"))
    t_obj = t_obj[0]
    clade = t_obj.prune(taxon)
    h = StringIO()
    Phylo.write(t_obj, h, "newick")
    tree = h.getvalue()

    return tree
       

def _sub_taxon(old_taxon, new_taxon, tree):
    """ Simple swap of taxa
    """

    # swap spaces for _, as we're dealing with Newick strings here
    new_taxon = new_taxon.replace(" ","_")

    # check if taxa is in there first
    if (tree.find(old_taxon) == -1):
        return tree #raise exception?

    # simple text swap
    new_tree = tree.replace(old_taxon,new_taxon)

    return new_tree

def _swap_tree_in_XML(XML, tree, name):
    """ Swap tree with name, 'name' with this new one
    """

    # tree name has the tree number attached to the source name
    # The calling function should make sure the names are unique
    # First thing is to do is find the source name that corresponds to this tree

    # Our input tree has name source_no, so find the source by stripping off the number
    source_name, number = name.rsplit("_",1)
    number = int(number.replace("_",""))
    xml_root = _parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    find = etree.XPath("//source")
    sources = find(xml_root)
    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        if source_name == name:
            # found the bugger!
            tree_no = 1
            for t in s.xpath("source_tree/tree_data"):
                if tree_no == number:
                   t.xpath("string_value")[0].text = tree
                   # We can return as we're only replacing one tree
                   return etree.tostring(xml_root,pretty_print=True)
                tree_no += 1

    return XML

def _parse_subs_file(filename):
    """ Reads in a subs file and returns two arrays:
        new_taxa and the corresponding old_taxa

        None is used to indicated deleted taxa
    """

    try:
        f = open(filename,'r')
    except:
        raise UnableToParseSubsFile("Unable to open subs file. Check your path")

    old_taxa = []
    new_taxa = []
    i = 0
    n_t = ""
    for line in f.readlines(): 
        if (re.search('\s+=\s+', line) != None): # new taxa description
            data = re.split('\s+=\s+', line) # note the spaces!
            old_taxa.append(data[0].strip())
            if (i != 0):
                # append the last lot of new_taxa onto array
                i += 1
                if (n_t == ""):
                    new_taxa.append(None)
                else:
                    # strip all spaces out around commas
                    n_t = n_t.replace(' ,', ',')
                    n_t = n_t.replace(', ', ',')
                    new_taxa.append(n_t)
            # now start parsing n_t
            n_t = ""
            if (len(data) > 1):
                # strip off any quotes - we must add them, but it's easier to strip then add than
                # check, then add
                data[1] = re.sub("'","",data[1])
                # might contain non-standard characters, quote these names
                data[1] = re.sub(r"(,|^)(?P<name>\w*[=\+]\w*)",r"\1'\g<name>'", data[1])
                n_t = n_t + data[1].strip()
                i = i+1
        else:
            if (line.strip() != "" and not n_t.endswith(',') and not line.strip().startswith(',')):
                n_t = n_t + ","
            n_t = n_t + line.strip()

    f.close()
    # Add the last new taxa
    if (n_t == ""):
        new_taxa.append(None)
    else:
        n_t = n_t.replace(' ,', ',')
        n_t = n_t.replace(', ', ',')
        new_taxa.append(n_t.strip())

    if (len(old_taxa) != len(new_taxa)):
        raise UnableToParseSubsFile("Output arrays are not same length. File incorrectly formatted")
    if (len(old_taxa) == 0):
        raise UnableToParseSubsFile("No substitutions found! File incorrectly formatted")
 

    return old_taxa, new_taxa

def _check_taxa(XML):
    """ Checks that taxa in the XML are in the tree for the source thay are added to
    """

    # grab all sources
    xml_root = _parse_xml(XML)
    find = etree.XPath("//source")
    sources = find(xml_root)

    # for each source
    for s in sources:
        # get a list of taxa in the XML
        this_source = _parse_xml(etree.tostring(s))
        find = etree.XPath("//taxon")
        taxa = find(this_source)
        trees = obtain_trees(etree.tostring(this_source))
        for name in trees.iterkeys():
            tree = trees[name]
            # are the XML taxa in the tree?
            for t in taxa:
                xml_taxon = t.attrib['name']
                if (tree.find(xml_taxon) == -1):
                    # no - raise an error!
                    raise InvalidSTKData("Taxon: "+xml_taxon+" is not in the tree "+name)

    return

def _check_data(XML):
    """ Function to check various aspects of the dataset, including:
         - checking taxa in the XML for a source are included in the tree for that source
         - checking all source names are unique
    """

    # check all names are unique - this is easy...
    _check_uniqueness(XML) # this will raise an error is the test is not passed

    # now the taxa
    _check_taxa(XML) # again will raise an error if test fails

    return


def _parse_xml(xml_string):
    """ Lxml cannot parse non-unicode characters 
    so we're wrapping this up so we can strip these characters
    beforehand. We can then send it to lxml.parser as normal
    """

    xml_string = _removeNonAscii(xml_string)
    XML = etree.fromstring(xml_string)
    return XML

def _removeNonAscii(s): return "".join(i for i in s if ord(i)<128)

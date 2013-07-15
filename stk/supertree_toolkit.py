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
sys.path.insert(0,"../../")
import stk.yapbib.biblist as biblist
import stk.yapbib.bibparse as bibparse
import stk.yapbib.bibitem as bibitem
import string
from stk_exceptions import *
import traceback
from cStringIO import StringIO
from collections import defaultdict
import stk.p4 as p4
import re
import operator
import stk.p4.MRP as MRP
import networkx as nx
import pylab as plt
from matplotlib.ticker import MaxNLocator
from matplotlib import backends
import datetime
import gtk

#plt.ion()

# GLOBAL VARIABLES
IDENTICAL = 0
SUBSET = 1


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
    if (authors[0] == None):
        # No authors yet!
        raise NoAuthors("No authors found to sort") 
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

    # sort new name
    xml_root = _sort_data(xml_root)

    XML = etree.tostring(xml_root,pretty_print=True)

    return XML


def import_bibliography(XML, bibfile):    
    
    # Our bibliography parser
    b = biblist.BibList()

    xml_root = _parse_xml(XML)
    
    # Track back along xpath to find the sources where we're about to add a new source
    sources = xml_root.xpath('sources')[0]
    sources.tail="\n      "
    if (bibfile == None):
        raise BibImportError("Error importing bib file. There was an error with the file")

    try: 
        b.import_bibtex(bibfile)
    except bibparse.BibAuthorError as e:
        # This seems to be raised if the authors aren't formatted correctly
        raise BibImportError("Error importing bib file. Check all your authors for correct format: " + e.msg)
    except bibparse.BibKeyError as e:
        raise BibImportError("Error importing bib file. " + e.msg)
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
            # Tree data
            tree = etree.SubElement(s_tree,"tree")
            tree.tail="\n      "
            tree_string = etree.SubElement(tree,"tree_string")
            tree_string.tail="\n      "
            tree_string_string = etree.SubElement(tree_string,"string_value")
            tree_string_string.tail="\n      "
            tree_string_string.attrib['lines'] = "1"
            # Figure and page number stuff
            figure_legend = etree.SubElement(tree,"figure_legend")
            figure_legend.tail="\n      "
            figure_legend_string = etree.SubElement(figure_legend,"string_value")
            figure_legend_string.tail="\n      "
            figure_legend_string.attrib['lines'] = "1"
            figure_number = etree.SubElement(tree,"figure_number")
            figure_number.tail="\n      "
            figure_number_string = etree.SubElement(figure_number,"string_value")
            figure_number_string.tail="\n      "
            figure_number_string.attrib['lines'] = "1"
            page_number = etree.SubElement(tree,"page_number")
            page_number.tail="\n      "
            page_number_string = etree.SubElement(page_number,"integer_value")
            page_number_string.tail="\n      "
            page_number_string.attrib['rank'] = "0"
            tree_inference = etree.SubElement(tree,"tree_inference")
            optimality_criterion = etree.SubElement(tree_inference,"optimality_criterion")
            # taxa data
            taxa = etree.SubElement(s_tree,"taxa_data")
            taxa.tail="\n      "
            mixed_fossil_and_extant = etree.SubElement(taxa,"mixed_fossil_and_extant")
            mixed_fossil_and_extant.tail="\n      "
            taxon = etree.SubElement(mixed_fossil_and_extant,"taxon")
            taxon.tail="\n      "
            fossil = etree.SubElement(taxon,"fossil")
            fossil.tail="\n   "
            # character data
            character_data = etree.SubElement(s_tree,"character_data")
            character_data.tail="\n      "
            character = etree.SubElement(character_data,"character")
            character.tail="\n      "

            # append our new source to the main tree
            # if sources has no valid source, overwrite,
            # else append
            valid = True
            i = 0
            for ele in sources:
                try:
                    ele.attrib['name']
                    i += 1
                    continue
                except:
                    valid = False
            if not valid:
                sources[i] = source
            else:
                sources.append(source)
            
        else:
            raise BibImportError("Error with one of the entries in the bib file")

    # sort sources in alphabetical order
    xml_root = _sort_data(xml_root)
    XML = etree.tostring(xml_root,pretty_print=True)
    
    return XML

## Note: this is different to all other STK functions as
## it saves the file, rather than passing back a string for the caller to save
## This is becuase yapbib saves the file and rather than re-write, I thought
## I'd go with it as in this case I would only ever save the file
def export_bibliography(XML,filename,format="bibtex"):
    """ Export all source papers as a bibliography in 
    either bibtex, xml, html, short or long formats
    """

    #check format
    if (not (format == "xml" or
             format == "html" or
             format == "bibtex" or
             format == "short" or
             format == "latex" or
             format == "long")):
        return 
        # raise error here

    # our bibliography
    bibliography = biblist.BibList()
   
    xml_root = _parse_xml(XML)    
    find = etree.XPath("//article")
    articles = find(xml_root)
    # loop through all articles
    for a in articles: 
        name = a.getparent().getparent().attrib['name']
        # get authors
        authors = []
        for auths in a.xpath("authors/author"):
            surname = auths.xpath("surname/string_value")[0].text
            first = auths.xpath("other_names/string_value")[0].text
            authors.append(["", surname,first,''])
        title   = a.xpath("title/string_value")[0].text
        year    = a.xpath("year/integer_value")[0].text
        bib_dict = {
                "_code"  : name,
                "_type"  : 'article',
                "author" : authors,
                "title"  : title,
                "year"   : year,
                }
        # these are optional in the schema
        if (a.xpath("journal/string_value")):
            journal = a.xpath("journal/string_value")[0].text
            bib_dict['journal']=journal
        if (a.xpath("volume/string_value")):
            volume  = a.xpath("volume/string_value")[0].text
            bib_dict['volume']=volume
        if (a.xpath("pages/string_value")):
            pages   = a.xpath("pages/string_value")[0].text
            bib_dict['pages']=pages 
        if (a.xpath("issue/string_value")):
            issue   = a.xpath("issue/string_value")[0].text
            bib_dict['issue']=issue
        if (a.xpath("doi/string_value")):
            doi     = a.xpath("doi/string_value")[0].text
            bib_dict['doi']=doi
        if (a.xpath("number/string_value")):
            number  = a.xpath("number/string_value")[0].text
            bib_dict['number']=number
        if (a.xpath("url/string_value")):
            url     = a.xpath("url/string_value")[0].text
            bib_dict['url']=url
        
        bib_it = bibitem.BibItem(bib_dict)
        bibliography.add_item(bib_it)

    find = etree.XPath("//book")
    books = find(xml_root)
    # loop through all books
    for b in books: 
        name = b.getparent().getparent().attrib['name']
        # get authors
        authors = []
        for auths in b.xpath("authors/author"):
            surname = auths.xpath("surname/string_value")[0].text
            first = auths.xpath("other_names/string_value")[0].text
            authors.append(["", surname,first,''])
        title   = b.xpath("title/string_value")[0].text
        year    = b.xpath("year/integer_value")[0].text
        bib_dict = {
                "_code"  : name,
                "_type"  : 'article',
                "author" : authors,
                "title"  : title,
                "year"   : year,
                }
        # these are optional in the schema
        if (b.xpath("editors")):
            editors = []
            for eds in b.xpath("editors/editor"):
                surname = eds.xpath("surname/string_value")[0].text
                first = eds.xpath("other_names/string_value")[0].text
                editors.append(["", surname,first,''])
            bib_dict["editor"]=editors
        if (b.xpath("series/string_value")):
            series = b.xpath("series/string_value")[0].text
            bib_dict['series']=series
        if (b.xpath("publisher/string_value")):
            publisher  = b.xpath("publisher/string_value")[0].text
            bib_dict['publisher']=publisher
        if (b.xpath("doi/string_value")):
            doi     = b.xpath("doi/string_value")[0].text
            bib_dict['doi']=doi
        if (b.xpath("url/string_value")):
            url     = b.xpath("url/string_value")[0].text
            bib_dict['url']=url
        
        bib_it = bibitem.BibItem(bib_dict)
        bibliography.add_item(bib_it)


    find = etree.XPath("//in_book")
    inbook = find(xml_root)
    # loop through all in book 
    for i in inbook: 
        name = i.getparent().getparent().attrib['name']
        # get authors
        authors = []
        for auths in i.xpath("authors/author"):
            surname = auths.xpath("surname/string_value")[0].text
            first = auths.xpath("other_names/string_value")[0].text
            authors.append(["", surname,first,''])
        title   = i.xpath("title/string_value")[0].text
        year    = i.xpath("year/integer_value")[0].text
        editors = []
        for eds in a.xpath("editors/editor"):
            surname = eds.xpath("surname/string_value")[0].text
            first = eds.xpath("other_names/string_value")[0].text
            editors.append(["", surname,first,''])
        bib_dict["editors"]=editors
        bib_dict = {
                "_code"  : name,
                "_type"  : 'article',
                "author" : authors,
                "title"  : title,
                "year"   : year,
                "editor" : editors
                }
        # these are optional in the schema
        if (i.xpath("series/string_value")):
            series = i.xpath("series/string_value")[0].text
            bib_dict['series']=series
        if (i.xpath("publisher/string_value")):
            publisher  = i.xpath("publisher/string_value")[0].text
            bib_dict['publisher']=publisher
        if (i.xpath("pages/string_value")):
            pages   = i.xpath("pages/string_value")[0].text
            bib_dict['pages']=pages 
        if (i.xpath("doi/string_value")):
            doi     = i.xpath("doi/string_value")[0].text
            bib_dict['doi']=doi

        bib_it = bibitem.BibItem(bib_dict)
        bibliography.add_item(bib_it)



    find = etree.XPath("//in_collection")
    incollections = find(xml_root)
    # loop through all in collections 
    for i in incollections: 
        name = i.getparent().getparent().attrib['name']
        # get authors
        authors = []
        for auths in i.xpath("authors/author"):
            surname = auths.xpath("surname/string_value")[0].text
            first = auths.xpath("other_names/string_value")[0].text
            authors.append(["", surname,first,''])
        title   = i.xpath("title/string_value")[0].text
        year    = i.xpath("year/integer_value")[0].text
        bib_dict = {
                "_code"  : name,
                "_type"  : 'article',
                "author" : authors,
                "title"  : title,
                "year"   : year,
                }
        # these are optional in the schema
        if (i.xpath("editors")):
            editors = []
            for eds in i.xpath("editors/editor"):
                surname = eds.xpath("surname/string_value")[0].text
                first = eds.xpath("other_names/string_value")[0].text
                editors.append(["", surname,first,''])
            bib_dict["editor"]=editors
        if (i.xpath("booktitle/string_value")):
            booktitle = i.xpath("booktitle/string_value")[0].text
            bib_dict['booktitle']=booktitle
        if (i.xpath("series/string_value")):
            series = i.xpath("series/string_value")[0].text
            bib_dict['series']=series
        if (i.xpath("publisher/string_value")):
            publisher  = i.xpath("publisher/string_value")[0].text
            bib_dict['publisher']=publisher
        if (i.xpath("pages/string_value")):
            pages   = i.xpath("pages/string_value")[0].text
            bib_dict['pages']=pages 
        if (i.xpath("doi/string_value")):
            doi     = i.xpath("doi/string_value")[0].text
            bib_dict['doi']=doi
        if (i.xpath("url/string_value")):
            url     = i.xpath("url/string_value")[0].text
            bib_dict['url']=url

        bib_it = bibitem.BibItem(bib_dict)
        bibliography.add_item(bib_it)

    bibliography.output(fout=filename,formato=format,verbose=False)
    
    return

def import_trees(filename):
    """ Return an array of all trees in a file. 
        All formats are supported that we've come across
        but submit a bug if a (common-ish) tree file shows up that can't be
        parsed.
    """
    f = open(filename)
    content = f.read()                 # read entire file into memory
    f.close()    
    # Need to add checks on the file. Problems include:
# TNT: outputs Phyllip format or something - basically a Newick
# string without commas, so add 'em back in
    m = re.search(r'proc-;', content)
    if (m != None):
        # TNT output tree
        # Done on a Mac? Replace ^M with a newline
        content = string.replace( content, '\r', '\n' )
        h = StringIO(content)
        counter = 1
        content  = "#NEXUS\n"
        content += "begin trees;\n"
        add_to = False
        for line in h:
            if (line.startswith('(')):
                add_to = True
            if (line.startswith('proc') and add_to):
                add_to = False
                break
            if (add_to):
                line = line.strip() + ";"
                if line == ";":
                    continue
                m = re.findall("([a-zA-Z0-9_\.]+)\s+([a-zA-Z0-9_\.]+)", line)
                treedata = line
                for i in range(0,len(m)):
                    treedata = re.sub(m[i][0]+"\s+"+m[i][1],m[i][0]+", "+m[i][1],treedata)
                m = re.findall("([a-zA-Z0-9_\.]+)\s+([a-zA-Z0-9_\.]+)", treedata)
                for i in range(0,len(m)):
                    treedata = re.sub(m[i][0]+"\s+"+m[i][1],m[i][0]+","+m[i][1],treedata)
                m = re.findall("(\))\s*(\()", treedata)
                if (m != None):
                    for i in range(0,len(m)):
                        treedata = re.sub("(\))\s*(\()",m[i][0]+", "+m[i][1],treedata,count=1)
                m = re.findall("([a-zA-Z0-9_\.]+)\s*(\()", treedata)
                if (m != None):
                    for i in range(0,len(m)):
                        treedata = re.sub("([a-zA-Z0-9_\.]+)\s*(\()",m[i][0]+", "+m[i][1],treedata,count=1)
                m = re.findall("(\))\s*([a-zA-Z0-9_\.]+)", treedata)
                if (m != None):
                    for i in range(0,len(m)):
                        treedata = re.sub("(\))\s*([a-zA-Z0-9_\.]+)",m[i][0]+", "+m[i][1],treedata,count=1)
                # last swap - no idea why, but some times the line ends in '*'; remove it
                treedata = treedata.replace('*;',';')
                treedata = treedata.replace(';;',';')
                treedata += "\n"
                treedata = "\ntree tree_"+str(counter)+" = [&U] " + treedata
                counter += 1
                content += treedata

        content += "\nend;\n"

# TreeView (Page, 1996):
# TreeView create a tree with the following description:
#
#   UTREE * tree_1 = ((1,(2,(3,(4,5)))),(6,7));
# UTREE * is not a supported part of the NEXUS format.
# so we need to replace the above with:
#   tree_1 = [&u] ((1,(2,(3,(4,5)))),(6,7));
#
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
        # tidy up and remove the *
        content = string.replace( content, '* ', '')

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

# Comments. This is p4's issue as it uses glob.glob to find out if
# the incoming "thing" is a file or string. Comments in nexus files are
# [ ], which in glob.glob means something, so we need to delete content
# that is between the [] before passing to p4. We're going to cheat and 
# just pull out the tree
    m = re.search(r'\[\!',content)
    if (m!=None):
        h = StringIO(content)
        content = "#NEXUS\n"
        content += "begin trees;\n"
        add_to = False
        for line in h:
            if (line.strip().lower().startswith('end')):
                add_to = False
            if (line.strip().lower().startswith('tree')):
                add_to = True
            if (line.strip().lower().startswith('translate')):
                add_to=True
            if (add_to):
                content += line+"\n"
        content += "\nend;"

    treedata = content
    
    try:
        p4.var.warnReadNoFile = False
        p4.var.nexus_warnSkipUnknownBlock = False
        p4.var.trees = []
        p4.read(treedata)
        p4.var.nexus_warnSkipUnknownBlock = True
        p4.var.warnReadNoFile = True
    except:
        raise TreeParseError("Error parsing " + filename)
    trees = p4.var.trees
    p4.var.trees = []
    
    r_trees = []
    for t in trees:
        r_trees.append(t.writeNewick(fName=None,toString=True).strip())

    return r_trees


def import_tree(filename, gui=None, tree_no = -1):
    """Takes a NEXUS formatted file and returns a list containing the tree
    strings"""
  
    trees = import_trees(filename)

    if (len(trees) == 1):
        tree_no = 0

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

    tree = trees[tree_no]
    return tree

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

def get_characters_from_tree(XML,name,sort=False):
    """Get the characters that were used in a particular tree
    """

    characters = []
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
            for t in s.xpath("source_tree/tree/tree_string"):
                if tree_no == number:
                    # and now we have the correct tree. 
                    # Now we can get the characters for this tree
                    chars = t.getparent().getparent().xpath("character_data/character")
                    for c in chars:
                        characters.append(c.attrib['name'])
                    if (sort):
                        characters.sort()
                    return characters
                tree_no += 1

    # should raise exception here
    return characters


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

def get_taxa_from_tree(XML, tree_name, sort=False):
    """Return taxa from a single tree based on name
    """

    trees = obtain_trees(XML)
    taxa_list = []
    for t in trees:
        if t == tree_name:
            tree = trees[t]
            try:
                p4.var.warnReadNoFile = False
                p4.var.nexus_warnSkipUnknownBlock = False
                p4.var.trees = []
                p4.read(tree)
                p4.var.nexus_warnSkipUnknownBlock = True
                p4.var.warnReadNoFile = True
            except:
                raise TreeParseError("Error parsing tree to get taxa")
            tree = p4.var.trees[0]
            p4.var.trees = []
            terminals = tree.getAllLeafNames(tree.root)
            for term in terminals:
                taxa_list.append(str(term))
            if (sort):
                taxa_list.sort()
            return taxa_list

    # actually need to raise exception here
    # and catch it in calling function
    return taxa_list


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
    find = etree.XPath("//optimality_criterion")
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
        for t in s.xpath("source_tree/tree/tree_string"):
            t_name = name+"_"+str(tree_no)
            # append to dictionary, with source_name_tree_no = tree_string
            trees[t_name] = t.xpath("string_value")[0].text
            tree_no += 1

    return trees

def amalgamate_trees(XML,format="Nexus",anonymous=False):
    """ Create a string containing all trees in the XML.
        String can be formatted to one of Nexus, Newick or TNT.
        Only Nexus formatting takes into account the anonymous
        flag - the other two are anonymous anyway
        Any errors and None is returned - check for this as this is the 
        callers responsibility
    """


    # Check format flag - let the caller handle
    if (not (format == "Nexus" or 
        format == "Newick" or
        format == "tnt")):
            return None

    trees = obtain_trees(XML)

    return _amalgamate_trees(trees,format,anonymous)
        

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
        taxa_list.extend(_getTaxaFromNewick(t))

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
    """ From all trees in the XML, create a matrix
    """

    # get all trees
    trees = obtain_trees(XML)

    # and the taxa
    taxa = []
    taxa.append("MRPOutgroup")
    taxa.extend(get_all_taxa(XML))

    return _create_matrix(trees, taxa, format=format)


def create_matrix_from_trees(trees,format="hennig"):
    """ Given a dictionary of trees, create a matrix
    """

    taxa = []
    for t in trees:
        tree = trees[t]
        try:
            p4.var.warnReadNoFile = False
            p4.var.nexus_warnSkipUnknownBlock = False
            p4.var.trees = []
            p4.read(tree)
            p4.var.nexus_warnSkipUnknownBlock = True
            p4.var.warnReadNoFile = True
        except:
            raise TreeParseError("Error parsing tree to get taxa")
        tree = p4.var.trees[0]
        p4.var.trees = []
        terminals = tree.getAllLeafNames(tree.root)
        for term in terminals:
            taxa_list.append(str(term))
    

    return _create_matrix(trees, taxa, format=format)


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


def permute_tree(tree,matrix="hennig",treefile=None):
    """ Permute a tree where there is uncertianty in taxa location.
    Output either a tree file or matrix file of all possible 
    permutations.

    Note this is a recursive algorithm.
    """

    # check format strings

    permuted_trees = {} # The output of the recursive permute algorithm
    output_string = "" # what we pass back

    # first thing is to get hold of the unique taxa names
    # i.e. without % on them
    all_taxa = _getTaxaFromNewick(tree)

    names_d = [] # our duplicated list of names
    names = [] # our unique names (without any %)
    for name in all_taxa:
        if ( not name.find('%') == -1 ):
            # strip number and %
            name = name[0:name.find('%')]
            names_d.append(name)
            names.append(name)
        else:
            names.append(name)
    # we now uniquify these arrays
    names_d_unique = _uniquify(names_d)
    names_unique = _uniquify(names)
    names = []
    names_d = []
    non_unique_numbers = []
    # count the number of each of the non-unique taxa
    for i in range(0,len(names_unique)):
        count = 0
        for name in all_taxa:
            if not name.find('%') == -1:
                name = name[0:name.find('%')]
                if name == names_unique[i]:
                    count += 1
        non_unique_numbers.append(count)

    trees_saved = []
    # I hate recursive functions, but it actually is the
    # best way to do this.
    # We permute until we have replaced all % taxa with one of the
    # possible choices, then we back ourselves out, swapping taxa
    # in and out until we hit all permutations and pop out
    # of the recursion
    # Note: scope of variables in nested functions here (another evil thing)
    # Someone more intelligent than me should rewrite this so it's
    # easier to follow.
    def _permute(n,temp):
    
        tempTree = temp

        if ( n < len(names_unique) and non_unique_numbers[n] == 0 ):
            _permute( ( n + 1 ), tempTree );
        else:
            if ( n < len(names_unique) ):
                for i in range(1,non_unique_numbers[n]+1):
                    tempTree = temp;
                    taxa = _getTaxaFromNewick(tree)
                    # iterate over nodes
                    for name in taxa:
                        index = name.find('%')
                        short_name = name[0:index]
                        current_unique_name = names_unique[n]
                        current_unique_name = current_unique_name.replace(' ','_')
                        if ( index > 0 and short_name == current_unique_name ):
                            if ( not name == current_unique_name + "%" + str(i) ):
                                tempTree = _delete_taxon(name, tempTree)
                    if ( n < len(names_unique) ):
                        _permute( ( n + 1 ), tempTree )
            else:
                tempTree = re.sub('%\d+','',tempTree)
                trees_saved.append(tempTree)

    if (len(trees_saved) == 0):
        # we now call the recursive function (above) to start the process
        _permute(0,tree)

    # check none are actually equal and store as dictionary
    count = 1
    for i in range(0,len(trees_saved)):
        equal = False
        for j in range(i+1,len(trees_saved)):
            if (_trees_equal(trees_saved[i],trees_saved[j])):
                equal = True
                break
        if (not equal):
            permuted_trees["tree_"+str(count)] = trees_saved[i]
            count += 1
            

    # out pops a dictionary of trees - either amalgamte in a single treefile (same taxa)
    # or create a matrix.
    if (treefile == None):
        # create matrix
        # taxa are all the same in each tree
        taxa = []
        taxa.append("MRPOutgroup")
        taxa.extend(names_unique)
        output_string = _create_matrix(permuted_trees,taxa,format=matrix)
    else:
        output_string = _amalgamate_trees(permuted_trees,format=treefile) 

    # Either way we output a string that the caller can save or display or pass to tnt, or burn;
    # it's up to them, really.
    return output_string


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

def data_overlap(XML, overlap_amount=2, filename=None, detailed=False, show=False, verbose=False):
    """ Calculate the amount of taxonomic overlap between source trees.
    The output is a True/False by default, but you can specify an 
    optional filename, which will save a nice graphic. For the GUI,
    the output can also be a PNG graphic to display (and then save).

    If filename is None, no graphic is generated. Otherwise a simple
    graphic is generated showing the number of cluster. If detailed is set to
    true, a graphic is generated showing *all* trees. For data containing >200
    source tres this could be very big and take along time. More likely, you'll run
    out of memory.
    """

    sufficient_overlap = False
    key_list = None
    # Create triangular matrix of connectivity
    # This can then be used to create the graph
    # We don't need to record which taxa overlap, just the total number

    if (verbose):
        print "\tObtaining trees from dataset"

    # First grab all trees
    try:
        trees = obtain_trees(XML)
    except:
        return

    # Get some basic stats about them (how many, etc)
    tree_keys = trees.keys()
    nTrees = len(tree_keys)
    
    # Allocate out numpy NxN matrix
    connectivity = numpy.zeros((nTrees,nTrees))

    # Out matrix indices
    i = 0; j = 0

    if (verbose):
        print "\tCalculating connectivity"
    # loop over trees (i=0, N)
    for i in range(0,nTrees):
        # Grab the taxa from tree i
        taxa_list_i = _getTaxaFromNewick(trees[tree_keys[i]])
        taxa_set = set(taxa_list_i)

        # loop over tree i+1 to end (j=i+1,N)
        for j in range(i+1,nTrees):
            matches = 0
            # grab the taxa from tree j
            taxa_list_j = _getTaxaFromNewick(trees[tree_keys[j]])

            # Inspired by: http://stackoverflow.com/questions/1388818/how-can-i-compare-two-lists-in-python-and-return-matches
            matches = len(taxa_set.intersection(taxa_list_j)) 

            connectivity[i][j] = matches
            
    # For each pair of trees we now have the number of connective taxa between them.
    # Now check for any trees that don't have sufficent matches to any other tree
    # We create an undirected graph, joining trees that have sufficient conenctivity
    if (verbose):
        print "\tCreating graph"
    G=nx.Graph()
    G.add_nodes_from(tree_keys)
    for i in range(0,nTrees):
        for j in range(i+1,nTrees):
            if (connectivity[i][j] >= overlap_amount):
                G.add_edge(tree_keys[i],tree_keys[j],label=tree_keys[i])

    # That's out graph set up. Dead easy to test all nodes are connected - we can even get the number of seperate connected parts
    connected_components = nx.connected_components(G)
    if len(connected_components) == 1:
        sufficient_overlap = True

    # The above list actually contains which components are seperate from each other

    if (not filename == None or show):
        if (verbose):
            print "\tCreating graphic:"
        # create a graphic and save the file there
        plt.ioff()
        if detailed:
            if (verbose):
                print "\t\tdetailed graphic in file: "+filename
            # set the key_list to the keys - see below as to why we do this
            key_list = tree_keys
            # we want a detailed graphic instead
            # Turn tree names into integers
            G_relabelled = nx.convert_node_labels_to_integers(G,discard_old_labels=False)
            # The integer labelling will match the order in which we set
            # up the nodes, which matches tree_keys
            degrees = G.degree() # we colour nodes by number of edges
            # However, this is a dict and the colour argument of draw need an array of floats
            colours = []
            for key in G_relabelled.nodes_iter():
                colours.append(len(G_relabelled.neighbors(key)))
            # Define our colourmap, such that unconnected nodes stand out in red, with
            # a smooth white to blue transition above this
            # We need to normalize the colours array from (0,1) and find out where
            # our minimum overlap value sits in there
            if max(colours) == 0:
                norm_cutoff = 0.999
            else:
                norm_cutoff = 0.999/max(colours)
            # Our cut off is at 1 - i.e. one connected edge. 
            from matplotlib.colors import LinearSegmentedColormap
            cdict = {'red':   ((0.0, 1.0, 1.0),
                               (norm_cutoff, 1.0, 1.0),
                               (1.0, 0.1, 0.1)),
                     'green': ((0.0, 0.0, 0.0),
                               (norm_cutoff, 0.0, 1.0),
                               (1.0, 0.1, 0.1)),
                     'blue':  ((0.0, 0.0, 0.0),
                               (norm_cutoff, 0.0, 1.0),
                               (1.0, 1.0, 1.0))}
            custom = LinearSegmentedColormap('custom', cdict)
            
            if show:
                fig = plt.figure(dpi=90)
            else:
                fig = plt.figure(dpi=270)
            ax = fig.add_subplot(111)
            cs = nx.draw_circular(G_relabelled,with_labels=True,ax=ax,node_color=colours,cmap=custom,edge_color='k',node_size=100,font_size=8)
            limits=plt.axis('off')
            vmin, vmax = plt.gci().get_clim()
            plt.clim(0,vmax)
            plt.axis('equal')
            ticks = MaxNLocator(integer=True,nbins=9)
            pp=plt.colorbar(cs, orientation='horizontal', format='%d', ticks=ticks)
            pp.set_label("No. connected edges")
            if (show):
                from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
                canvas = FigureCanvas(fig)  # a gtk.DrawingArea 
                return sufficient_overlap, key_list, canvas
            else:
                fig.savefig(filename)
    
        else:
            if (verbose):
                print "\t\tsummmary graphic in file: "+filename

            # Here, out key_list is our connectivity info
            key_list = connected_components
            # Summary graph - here we just graph the connected bits
            Hs = nx.connected_component_subgraphs(G)
            G_new = nx.Graph()
            # Add nodes (no edges this time)
            G_new.add_nodes_from(Hs)
            # Set the colour and size according to the number of trees in each cluster
            # Unless there's only one cluster...
            colours = []
            sizes = []
            for H in Hs:
                colours.append(H.number_of_nodes())
                sizes.append(300*H.number_of_nodes())
            G_relabelled = nx.convert_node_labels_to_integers(G_new)
            if (show):
                fig = plt.figure(dpi=90)
            else:
                fig = plt.figure(dpi=270)
            ax = fig.add_subplot(111)
            limits=plt.axis('off')
            plt.axis('equal')
            if (len(colours) > 1):
                cs = nx.draw_networkx(G_relabelled,with_labels=True,ax=ax,node_size=sizes,node_color=colours,cmap=plt.cm.Blues,edge_color='k')
                ticks = MaxNLocator(integer=True,nbins=9)
                pp=plt.colorbar(cs, orientation='horizontal', format='%d', ticks=ticks)
                pp.set_label("No. connected edges")
            else:
                cs = nx.draw_networkx(G_relabelled,with_labels=True,ax=ax,edge_color='k',node_color='w',node_size=2000)
            
                limits=plt.axis('off')
            if (show):
                from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
                canvas = FigureCanvas(fig)  # a gtk.DrawingArea 
                return sufficient_overlap, key_list,canvas
            else:
                fig.savefig(filename)

    return sufficient_overlap, key_list

def data_independence(XML,make_new_xml=False):
    """ Return a list of sources that are not independent.
    This is decided on the source data and the analysis
    """
    # data storage:
    #
    # tree_name, character string, taxa_list
    # tree_name, character string, taxa_list
    # 
    # smith_2009_1, cytb, a:b:c:d:e
    # jones_2008_1, cytb:mit, a:b:c:d:e:f
    # jones_2008_2, cytb:mit, a:b:c:d:e:f:g:h
    #
    # The two jones_2008 trees are not independent.  jones_2008_2 is retained
    data_ind = []

    trees = obtain_trees(XML)
    for tree_name in trees:
        taxa = get_taxa_from_tree(XML, tree_name, sort=True)
        characters = get_characters_from_tree(XML, tree_name, sort=True)
        data_ind.append([tree_name, characters, taxa])
    
    # Then sort based on the character string and taxa_list as secondary sort
    # Doing so means the tree_names that use the same characters
    # are next to each other
    data_ind.sort(key=operator.itemgetter(1,2))

    # The loop through this list, and if the character string is the same
    # as the previous one, check the taxa. If the taxa from the 1st
    # source is contained within (or is equal) the taxa list of the 2nd
    # grab the source data - these are not independent.
    # Because we've sorted the data, if the 2nd taxa list will be longer
    # than the previous entry if the first N taxa are the same
    prev_char = None
    prev_taxa = None
    prev_name = None
    non_ind = {}
    for data in data_ind:
        name = data[0]
        char = data[1]
        taxa = data[2]
        if (char == prev_char):
            # when sorted, the longer list comes first
            if set(taxa).issubset(set(prev_taxa)):
                if (taxa == prev_taxa):
                    non_ind[name] = [prev_name,IDENTICAL]
                else:
                    non_ind[name] = [prev_name,SUBSET]
        prev_char = char
        prev_taxa = taxa
        prev_name = name

    if (make_new_xml):
        new_xml = XML
        for name in non_ind:
            if (non_ind[name][1] == SUBSET):
                new_xml = _swap_tree_in_XML(new_xml,None,name) 
        return non_ind, new_xml
    else:
        return non_ind

def add_historical_event(XML, event_description):

    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    xml_root = _parse_xml(XML)

    find = etree.XPath("//history")
    history = find(xml_root)[0]
    event = etree.SubElement(history,"event") 
    date = etree.SubElement(event,"datetime")
    action = etree.SubElement(event,"action")
    string = etree.SubElement(date,'string_value')
    string.text = now
    string.attrib['lines'] = "1"
    string = etree.SubElement(action,'string_value')
    string.attrib['lines'] = "1"
    string.text = event_description

    XML = etree.tostring(xml_root,pretty_print=True)

    return XML
    
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


def _assemble_tree_matrix(tree_string):
    """ Assembles the MRP matrix for an individual tree

        returns: matrix (2D numpy array: taxa on i, nodes on j)
                 taxa list: in same order as in the matrix
    """

    p4.var.warnReadNoFile = False    
    p4.var.trees = []
    p4.read(tree_string)
    tree = p4.var.trees[0]    
    mrp = MRP.mrp([tree])
    adjmat = []
    names = []
    for i in range(0,mrp.nTax):
        seq = (mrp.sequences[i].sequence)
        names.append(mrp.taxNames[i])
        chars = []
        chars.append(1)
        for c in seq:
            chars.append(int(c))
        adjmat.append(chars)

    adjmat = numpy.array(adjmat)

    return adjmat, names

def _delete_taxon(taxon, tree):
    """ Delete a taxon from a tree string
    """

    # check if taxa is in there first
    if (tree.find(taxon) == -1):
        return tree #raise exception?
    p4.var.warnReadNoFile = False    
    p4.var.trees = []
    p4.read(tree)
    tree_obj = p4.var.trees[0]
    for node in tree_obj.iterNodes():
        if node.name == taxon:
            tree_obj.removeNode(node.nodeNum,alsoRemoveBiRoot=False)
            break
    p4.var.warnReadNoFile = True    


    return tree_obj.writeNewick(fName=None,toString=True).strip()
       

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
    """ Swap tree with name, 'name' with this new one.
        If tree is None, name is removed.
        If source no longer contains any trees, the source is removed
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
    if (tree == None):
        delete_me = []
    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        if source_name == name:
            # found the bugger!
            tree_no = 1
            for t in s.xpath("source_tree/tree/tree_string"):
                if tree_no == number:
                    if (not tree == None): 
                        t.xpath("string_value")[0].text = tree
                        # We can return as we're only replacing one tree
                        return etree.tostring(xml_root,pretty_print=True)
                    else:
                        s.remove(t.getparent().getparent())
                        # we now need to check the source to check if there are
                        # any trees in this source now, if not, remove
                        s.getparent().remove(s)
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

def _check_sources(XML):
    """ Check that all sources in the dataset have at least one tree_string associated
        with them
    """

    xml_root = _parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    # within that source and construct a unique name
    find = etree.XPath("//source")
    sources = find(xml_root)
    # for each source
    for s in sources:
        # get a list of taxa in the XML
        this_source = _parse_xml(etree.tostring(s))
        name = s.attrib['name']
        trees = obtain_trees(etree.tostring(this_source))
        if (len(trees) < 1):
            raise InvalidSTKData("Source "+name+" has no trees")



def _check_data(XML):
    """ Function to check various aspects of the dataset, including:
         - checking taxa in the XML for a source are included in the tree for that source
         - checking all source names are unique
    """

    # check all names are unique - this is easy...
    _check_uniqueness(XML) # this will raise an error is the test is not passed

    # now the taxa
    _check_taxa(XML) # again will raise an error if test fails

    # check sources
    _check_sources(XML)

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

def _getTaxaFromNewick(tree):
    """ Get the terminal nodes from a Newick string"""

    p4.var.warnReadNoFile = False    
    p4.var.trees = []
    p4.read(tree)
    t_obj = p4.var.trees[0]
    terminals = t_obj.getAllLeafNames(0)
    p4.var.warnReadNoFile = True    

    return terminals


def _sort_data(xml_root):
    """ Grab all source names and sort them alphabetically, 
    spitting out a new XML """

    container = xml_root.find("sources")

    data = []
    for elem in container:
        key = elem.attrib['name']
        data.append((key, elem))

    data.sort()

    # insert the last item from each tuple
    container[:] = [item[-1] for item in data]
    
    return xml_root


def _trees_equal(t1,t2):
    """ compare two trees using Robinson-Foulds metric
    """

    try:
        p4.var.warnReadNoFile = False
        p4.var.nexus_warnSkipUnknownBlock = False
        p4.var.trees = []
        p4.read(t1)
        p4.read(t2)
        p4.var.nexus_warnSkipUnknownBlock = True
        p4.var.warnReadNoFile = True
    except:
        raise TreeParseError("Error parsing " + filename)

    tree_1 = p4.var.trees[0]
    tree_2 = p4.var.trees[1]
    
    # add the taxanames
    # Sort, otherwose p4 things the txnames are different
    names = tree_1.getAllLeafNames(tree_1.root)
    names.sort()
    tree_1.taxNames = names
    names = tree_2.getAllLeafNames(tree_2.root)
    names.sort()
    tree_2.taxNames = names

    same = False
    try:
        if (tree_1.topologyDistance(tree_2) == 0):
            same = True # yep, the same
            # but also check the root
            if not tree_1.root.getNChildren() == tree_2.root.getNChildren():
                same = False
    except:
        same = False # different taxa, so can't be the same!

    return same

def _find_trees_for_permuting(XML):

    trees = obtain_trees(XML)
    permute_trees = {}
    for t in trees:
        if trees[t].find('%') > -1:
            # tree needs permuting - we store the 
            permute_trees[t] = trees[t]

    return permute_trees

def _create_matrix(trees, taxa, format="hennig"):

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
        submatrix, tree_taxa = _assemble_tree_matrix(trees[key])
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
    
def _amalgamate_trees(trees,format,anonymous=False):
        # all trees are in Newick string format already
    # For each format, Newick, Nexus and TNT this format
    # is adequate. 
    # Newick: Do nothing - write one tree per line
    # Nexus: Add header, write one tree per line, prepending tree info, taking into acount annonymous flag
    # TNT: strip commas, write one tree per line
    output_string = ""
    if format == "Nexus":
        output_string += "#NEXUS\n\nBEGIN TREES;\n\n"
    tree_count = 0
    for tree in trees:
        if format == "Nexus":
            if anonymous:
                output_string += "\tTREE tree_"+str(tree_count)+" = "+trees[tree]+"\n"
            else:
                output_string += "\tTREE "+tree+" = "+trees[tree]+"\n"
        elif format == "Newick":
            output_string += trees[tree]+"\n"
        elif format == "tnt":
            t = trees[tree];
            t = t.replace(",","");
            t = t.replace(";","");
            output_string += t+"\n"
        tree_count += 1
    # Footer
    if format == "Nexus":
        output_string += "\n\nEND;"
    elif format == "tnt":
        output_string += "\n\nproc-;"

    return output_string


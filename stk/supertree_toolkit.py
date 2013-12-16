#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2013, Jon Hill, Katie Davis
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
import datetime
from indent import *
import unicodedata
from stk_internals import *

#plt.ion()

# GLOBAL VARIABLES
IDENTICAL = 0
SUBSET = 1
PLATFORM = sys.platform

# supertree_toolkit is the backend for the STK. Loaded by both the GUI and
# CLI, this contains all the functions to actually *do* something
#
# All functions take XML and a list of other arguments, process the data and return
# it back to the user interface handler to save it somewhere

def create_name(authors, year, append=''):
    """ 
    Construct a sensible from a list of authors and a year for a 
    source name.
    Input: authors - list of last (family, sur) names (string).
           year - the year (string).
           append - append something onto the end of the name.
    Output: source_name - (string)
    """

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
    XML should contain the xml_root for the source that is to be
    altered only.
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
    dataset. This includes appending a, b, etc for duplicate names.
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
    """ From a full XML-PHYML string, extract all source names.
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
    """ Ensures all sources have unique names.
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


def import_bibliography(XML, bibfile, skip=False):
    """
    Create a bunch of sources from a bibtex file. This includes setting the sourcenames 
    for each source.
    """
    
    # Our bibliography parser
    b = biblist.BibList()

    xml_root = _parse_xml(XML)
    
    # Track back along xpath to find the sources where we're about to add a new source
    sources = xml_root.xpath('sources')[0]
    sources.tail="\n      "
    if (bibfile == None):
        raise BibImportError("Error importing bib file. There was an error with the file")

    try: 
        b.import_bibtex(bibfile,True,False)
    except bibparse.BibAuthorError as e:
        # This seems to be raised if the authors aren't formatted correctly
        raise BibImportError("Error importing bib file. Check all your authors for correct format: " + e.msg)
    except bibparse.BibKeyError as e:
        raise BibImportError("Error importing bib file. " + e.msg)
    except AttributeError as e:
        # This seems to occur if the keys are not set for the entry
        raise BibImportError("Error importing bib file. Check all your entry keys. "+e.msg)
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
            page_number_string = etree.SubElement(page_number,"string_value")
            page_number_string.tail="\n      "
            page_number_string.attrib['lines'] = "1"
            tree_inference = etree.SubElement(tree,"tree_inference")
            # taxa data
            taxa = etree.SubElement(s_tree,"taxa_data")
            taxa.tail="\n      "
            # Note: we do not add all elements as otherwise they get set to some option
            # rather than remaining blank (and hence blue int he interface)

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
            if (skip):
                continue

            msg = entry
            raise BibImportError("Error with one of the entries in the bib file."+
                                " Note the name is mangled to generate a unique ID "+
                                "(but should include the name and the year). Remove this and"+
                                " try again. You can add the offending entry manually.\n\n"+msg)

    # sort sources in alphabetical order
    xml_root = _sort_data(xml_root)
    XML = etree.tostring(xml_root,pretty_print=True)
    
    return XML

## Note: this is different to all other STK functions as
## it saves the file, rather than passing back a string for the caller to save
## This is becuase yapbib saves the file and rather than re-write, I thought
## I'd go with it as in this case I would only ever save the file
def export_bibliography(XML,filename,format="bibtex"):
    """ 
    Export all source papers as a bibliography in 
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
            if (not a.xpath("journal/string_value") == None):
                journal = a.xpath("journal/string_value")[0].text
                bib_dict['journal']=journal
        if (a.xpath("volume/string_value")):
            if (not a.xpath("volume/string_value") == None):
                volume  = a.xpath("volume/string_value")[0].text
                bib_dict['volume']=volume
        if (a.xpath("pages/string_value")):
            if (not a.xpath("pages/string_value")[0].text == None):
                firstpage, lastpage = bibparse.process_pages(a.xpath("pages/string_value")[0].text)
                bib_dict['firstpage']=firstpage
                bib_dict['lastpage']=lastpage
        if (a.xpath("issue/string_value")):
            if (not a.xpath("issue/string_value") == None):
                issue   = a.xpath("issue/string_value")[0].text
                bib_dict['issue']=issue
        if (a.xpath("doi/string_value")):
            if (not a.xpath("doi/string_value") == None):
                doi     = a.xpath("doi/string_value")[0].text
                bib_dict['doi']=doi
        if (a.xpath("number/string_value")):
            if (not a.xpath("number/string_value") == None):
                number  = a.xpath("number/string_value")[0].text
                bib_dict['number']=number
        if (a.xpath("url/string_value")):
            if (not a.xpath("url/string_value") == None):
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
                "_type"  : 'book',
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
        for eds in i.xpath("editors/editor"):
            surname = eds.xpath("surname/string_value")[0].text
            first = eds.xpath("other_names/string_value")[0].text
            editors.append(["", surname,first,''])
        bib_dict = {
                "_code"  : name,
                "_type"  : 'inbook',
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
            firstpage, lastpage = bibparse.process_pages(i.xpath("pages/string_value")[0].text)
            bib_dict['firstpage']=firstpage
            bib_dict['lastpage']=lastpage
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
                "_type"  : 'incollection',
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
            firstpage, lastpage = bibparse.process_pages(i.xpath("pages/string_value")[0].text)
            bib_dict['firstpage']=firstpage
            bib_dict['lastpage']=lastpage
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

def safe_taxonomic_reduction(XML, matrix=None, taxa=None, verbose=False, queue=None, ignoreWarnings=False):
    """ Perform STR on data to remove taxa that 
    provide no useful additional information. Based on PerEQ (Jeffery and Wilkson, unpublished).
    """

    if not ignoreWarnings and not XML == None:
        _check_data(XML)

    # Algorithm descibed by Jeffery and Wilkson, unpublshed. 
    # Obtained original from http://www.uni-oldenburg.de/en/biology/systematics-and-evolutionary-biology/programs/
    # and modified for *supertrees*, which mainly involves cutting
    # out stuff to do with multiple state characters as we only have binary characters.

    missing_char = "?"
    TotalInvalid = 0

    if (not matrix==None):
        if (taxa == None):
            raise InvalidSTKData("If you supply a matrix to STR, you also need to supply taxa")
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
        taxa.append("MRP_Outgroup")
        taxa.extend(get_all_taxa(XML))
        # our matrix, we'll then append the submatrix
        # to this to make a 2D matrix
        # Our matrix is of length nTaxa on the i dimension
        # and nCharacters in the j direction
        matrix = []
        charsets = []
        current_char = 1
        for key in trees:
            if (verbose):
                print "Reading tree: "+key
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
                    elif (taxon == "MRP_Outgroup"):
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

    if (queue == None):
        return output_string, can_replace
    else:
        queue.put([output_string, can_replace])
        return

def subs_file_from_str(str_output):
    """From the textual output from STR (safe_taxonomic_reduction), create
    the subs file to put the C category taxa back into
    the dataset. We work with the text out as it's the same as PerlEQ, 
    which means this might work from them also...
    """

    file = StringIO(str_output)
    i = 0
    replacements = []
    all_C_taxa = []
    to_remove = []
    for line in file:
        if (i < 3):
            i += 1
            continue
        else:
            line = line.strip()
            # remove the leading and trailing '|' so we get correct number
            # of columns
            line = line.strip('|')
            data = line.split('|')
            # data[0] = index taxa
            # data[1] = missing characters
            # data[2] = potential equivs
            # we might have done with the table
            if (not len(data) == 3):
                break
            index = data[0].strip()
            pot_equivs = data[2].strip().split()
            replace = ""
            for e in pot_equivs:
                if (e[-3:] == '(C)'):
                    if  (not e[:-3] in all_C_taxa):
                        replace += e[:-3]+","
                    else:
                        # add it to the need to remove list as it appear multiple times
                        to_remove.append(e[:-3])
            if (not replace == ""):
                all_C_taxa.extend(replace[:-1].split(','))
                replacements.append(index+" = "+replace+index)

    # now need to remove the list in the to_remove list from the RHS
    for i in range(len(replacements)):
        for t in to_remove:
            replacements[i] = replacements[i].replace(t+",","")

    
    return replacements


def import_trees(filename):
    """ Return an array of all trees in a file. 
        All formats are supported that we've come across
        but submit a bug if a (common-ish) tree file shows up that can't be
        parsed.
    """
    f = open(filename)
    content = f.read() # read entire file into memory
    f.close()    

    # translate to ascii
    content = str(replace_utf(content))
    
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
   
    trees = _parse_trees(treedata)
    r_trees = []
    for t in trees:
        tree = _correctly_quote_taxa(t.writeNewick(fName=None,toString=True).strip())
        r_trees.append(tree)

    return r_trees


def import_tree(filename, gui=None, tree_no = -1):
    """Takes a NEXUS formatted file and returns a list containing the tree
    strings"""
    
    import gtk
  
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

def get_all_characters(XML,ignoreErrors=False):
    """Returns a dictionary containing a list of characters within each 
    character type"""

    xml_root = _parse_xml(XML)
    find = etree.XPath("//character")
    characters = find(xml_root)

    # grab all character types first
    types = []
    for c in characters:
        try:
            types.append(c.attrib['type'])
        except KeyError:
            if (ignoreErrors):
                pass
            else:
                raise KeyError("Error getting character type. Incomplete data")

    u_types = _uniquify(types)
    u_types.sort()

    char_dict = {}
    for t in u_types:
        char = []
        for c in characters:
            try:
                if (c.attrib['type'] == t):
                    if (not c.attrib['name'] in char):
                        char.append(c.attrib['name'])
            except KeyError:
                if (ignoreErrors):
                    pass
                else:
                    raise KeyError("Error getting character type. Incomplete data")

        char_dict[t] = char       

    return char_dict

def get_publication_year_tree(XML,name):
    """Return a dictionary of years and the number of publications
    within that year
    """

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
                    # Now we can get the year for this tree
                    if not t.getparent().getparent().getparent().xpath("bibliographic_information/article") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/article/year/integer_value")[0].text)
                    elif not t.getparent().getparent().getparent().xpath("bibliographic_information/book") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/book/year/integer_value")[0].text)
                    elif not t.getparent().getparent().getparent().xpath("bibliographic_information/in_book") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/in_book/year/integer_value")[0].text)
                    elif not t.getparent().getparent().getparent().xpath("bibliographic_information/in_collection") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/in_collection/year/integer_value")[0].text)
                    return year
                tree_no += 1

    # should raise exception here
    return None

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

def get_character_types_from_tree(XML,name,sort=False):
    """Get the character types that were used in a particular tree
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
                        characters.append(c.attrib['type'])
                    if (sort):
                        characters.sort()
                    return characters
                tree_no += 1

    # should raise exception here
    return characters


def get_characters_used(XML):
    """ Return a sorted, unique array of all character names used
    in this dataset
    """
 
    c_ = []
 
    xml_root = _parse_xml(XML)
    find = etree.XPath("//character")
    chars = find(xml_root)

    for c in chars:
        name = c.attrib['name']
        ctype = c.attrib['type']
        c_.append((name,ctype))
 
    characters = _uniquify(c_) 
    characters.sort(key=lambda x: x[0].lower())
 
    return characters

def get_character_numbers(XML,ignoreErrors=False):
    """ Return the number of trees that use each character
    """

    xml_root = _parse_xml(XML)
    find = etree.XPath("//character")
    characters = find(xml_root)

    char_numbers = defaultdict(int)

    for c in characters:
        try:
            char_numbers[c.attrib['name']] += 1
        except KeyError:
            if (ignoreErrors):
                pass
            else:
                raise KeyError("Error getting character type. Incomplete data")

    return char_numbers

def get_taxa_from_tree(XML, tree_name, sort=False):
    """Return taxa from a single tree based on name
    """

    trees = obtain_trees(XML)
    taxa_list = []
    for t in trees:
        if t == tree_name:
            tree = _parse_tree(trees[t]) 
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
        try:
            name = f.getparent().attrib['name']
            f_.append(name)
        except KeyError:
            pass

    fossil_taxa = _uniquify(f_) 
    
    return fossil_taxa

def get_analyses_used(XML,ignoreErrors=False):
    """ Return a sorted, unique array of all analyses types used
    in this dataset
    """

    a_ = []

    xml_root = _parse_xml(XML)
    find = etree.XPath("//optimality_criterion")
    analyses = find(xml_root)

    for a in analyses:
        try:
            name = a.attrib['name']
            a_.append(name)
        except KeyError:
            if (ignoreErrors):
                pass
            else:
                raise KeyError("Error parsing analyses. Incomplete data")

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
        try:
            year = int(y.xpath('integer_value')[0].text)
            year_dict[year] += 1
        except TypeError:
            pass

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
            if (not t.xpath("string_value")[0].text == None):
                trees[t_name] = t.xpath("string_value")[0].text
                tree_no += 1

    return trees

def amalgamate_trees(XML,format="nexus",anonymous=False,ignoreWarnings=False):
    """ Create a string containing all trees in the XML.
        String can be formatted to one of Nexus, Newick or TNT.
        Only Nexus formatting takes into account the anonymous
        flag - the other two are anonymous anyway
        Any errors and None is returned - check for this as this is the 
        callers responsibility
    """

    if not ignoreWarnings:
        _check_data(XML)

    # Check format flag - let the caller handle
    if (not (format == "nexus" or 
        format == "newick" or
        format == "tnt")):
            return None

    trees = obtain_trees(XML)

    return _amalgamate_trees(trees,format,anonymous)
        

def get_all_taxa(XML, pretty=False, ignoreErrors=False):
    """ Produce a taxa list by scanning all trees within 
    a PHYML file. 

    The list is return sorted (alphabetically).

    Setting pretty=True means all underscores will be
    replaced by spaces"""

    trees = obtain_trees(XML)

    taxa_list = []

    for tname in trees.keys():
        t = trees[tname]
        try:
            taxa_list.extend(_getTaxaFromNewick(t))
        except TreeParseError as detail:
            if (ignoreErrors):
                pass
            else:
                raise TreeParseError( detail.msg )



    # now uniquify the list of taxa
    taxa_list = _uniquify(taxa_list)
    taxa_list.sort()

    if (pretty):
        unpretty_tl = taxa_list
        taxa_list = []
        for t in unpretty_tl:
            taxa_list.append(t.replace('_',' '))

    return taxa_list


def create_matrix(XML,format="hennig",quote=False,taxonomy=None,ignoreWarnings=False):
    """ From all trees in the XML, create a matrix
    """

    if not ignoreWarnings:
        _check_data(XML)

    # get all trees
    trees = obtain_trees(XML)
    if (not taxonomy == None):
        trees['taxonomy'] = taxonomy

    # and the taxa
    taxa = []
    taxa.extend(get_all_taxa(XML))
    if (not taxonomy == None):
        taxa.extend(_getTaxaFromNewick(taxonomy))
        taxa = _uniquify(taxa)
        taxa.sort()
    taxa.insert(0,"MRP_Outgroup")
        
    return _create_matrix(trees, taxa, format=format, quote=quote)


def create_matrix_from_trees(trees,format="hennig"):
    """ Given a dictionary of trees, create a matrix
    """

    taxa = []
    for t in trees:
        tree = _parse_tree(trees[t])
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


def substitute_taxa(XML, old_taxa, new_taxa=None, only_existing=False, ignoreWarnings=False, verbose=False, skip_existing=False):
    """
    Swap the taxa in the old_taxa array for the ones in the
    new_taxa array
    
    If the new_taxa array is missing, simply delete the old_taxa

    only_existing will ensure that the new_taxa are already in the dataset

    Returns a new XML with the taxa swapped from each tree and any taxon
    elements for those taxa removed. It's up to the calling function to
    do something sensible with this infomation
    """

    if not ignoreWarnings:
        _check_data(XML)


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

    # Sort incoming taxa
    if (only_existing):
        import csv
        
        existing_taxa = get_all_taxa(XML)
        corrected_taxa = []
        for t in new_taxa:
            if (not t == None):    
                # remove duplicates in the new taxa
                for row in csv.reader([t],delimiter=',', quotechar="'"):
                    current_new_taxa = row
                current_corrected_taxa = []
                for cnt in current_new_taxa:
                    if (cnt in existing_taxa):
                        current_corrected_taxa.append(t)
                if (len(current_corrected_taxa) == 0):
                    corrected_taxa.append(None)
                else:
                    corrected_taxa.append(",".join(current_corrected_taxa))
            else:
                corrected_taxa.append(None)
        new_taxa = corrected_taxa

    # need to check for uniquessness of souce names - error is not unique
    _check_uniqueness(XML)

    # grab all trees and store as bio.phylo.tree objects
    trees = obtain_trees(XML)

    for name in trees.iterkeys():
        tree = trees[name]
        new_tree = _sub_taxa_in_tree(tree,old_taxa,new_taxa,skip_existing=skip_existing)
        XML = _swap_tree_in_XML(XML,new_tree,name)
 

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


def substitute_taxa_in_trees(trees, old_taxa, new_taxa=None, only_existing = False, ignoreWarnings=False, verbose=False):
    """
    Swap the taxa in the old_taxa array for the ones in the
    new_taxa array
    
    If the new_taxa array is missing, simply delete the old_taxa

    only_existing will ensure only taxa in the dataset are subbed in.

    Returns a new list of trees with the taxa swapped from each tree 
    It's up to the calling function to
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
    

    # Sort incoming taxa
    if (only_existing):
        existing_taxa = []
        for tree in trees:
            existing_taxa.extend(_getTaxaFromNewick(tree))
        existing_taxa = _uniquify(existing_taxa)
        corrected_taxa = []
        for t in new_taxa:
            if (not t == None):
                current_new_taxa = t.split(",")
                current_corrected_taxa = []
                for cnt in current_new_taxa:
                    if (cnt in existing_taxa):
                        current_corrected_taxa.append(t)
                if (len(current_corrected_taxa) == 0):
                    corrected_taxa.append(None)
                else:
                    corrected_taxa.append(",".join(current_corrected_taxa))
            else:
                corrected_taxa.append(None)
        new_taxa = corrected_taxa
    
    new_trees = []
    for tree in trees:
        new_trees.append(_sub_taxa_in_tree(tree,old_taxa,new_taxa))
 
    return new_trees



def permute_tree(tree,matrix="hennig",treefile=None,verbose=False):
    """ Permute a tree where there is uncertianty in taxa location.
    Output either a tree file or matrix file of all possible 
    permutations.

    Note this is a recursive algorithm.
    """

    # check format strings

    permuted_trees = {} # The output of the recursive permute algorithm
    output_string = "" # what we pass back
    tree = _correctly_quote_taxa(tree)

    # first thing is to get hold of the unique taxa names
    # i.e. without % on them
    tree = re.sub(r"'(?P<taxon>[a-zA-Z0-9_\+\=\.\? ]*) (?P<taxon2>[a-zA-Z0-9_\+\=\.\? %]*)'","\g<taxon>_\g<taxon2>",tree)

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

    total = 1
    for n in non_unique_numbers:
        if (n > 0):
            total = total * n

    if (verbose):
        print "This tree requires a of "+str(total)+ " permutations"

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
        taxa.append("MRP_Outgroup")
        taxa.extend(names_unique)
        output_string = _create_matrix(permuted_trees,taxa,format=matrix)
    else:
        output_string = _amalgamate_trees(permuted_trees,format=treefile) 

    # Either way we output a string that the caller can save or display or pass to tnt, or burn;
    # it's up to them, really.
    return output_string


def data_summary(XML,detailed=False,ignoreWarnings=False):
    """Creates a text string that summarises the current data set via a number of 
    statistics such as the number of character types, distribution of years of publication,
    etc.

    Up to the calling function to display string nicely
    """

    if not ignoreWarnings:
        _check_data(XML)

    xml_root = _parse_xml(XML)
    proj_name = xml_root.xpath('/phylo_storage/project_name/string_value')[0].text

    output_string  = "======================\n"
    output_string += " Data summary of: " + proj_name + "\n" 
    output_string += "======================\n\n"

    trees = obtain_trees(XML)
    taxa = get_all_taxa(XML, pretty=False, ignoreErrors=True)
    characters = get_all_characters(XML,ignoreErrors=True)
    char_numbers = get_character_numbers(XML,ignoreErrors=True)
    fossils = get_fossil_taxa(XML)
    publication_years = get_publication_years(XML)
    analyses = get_analyses_used(XML,ignoreErrors=True)
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

def data_overlap(XML, overlap_amount=2, filename=None, detailed=False, show=False, verbose=False, ignoreWarnings=False):
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
    import matplotlib
    if (sys.platform == "darwin"):
        matplotlib.use('GTKAgg')
    import pylab as plt
    from matplotlib.ticker import MaxNLocator
    from matplotlib import backends
    
    if not ignoreWarnings:
        _check_data(XML)

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
                if (verbose):
                    print "Joining "+ tree_keys[i] +" " + tree_keys[j]
                G.add_edge(tree_keys[i],tree_keys[j],label=str(i))

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
            # The integer labelling will match the order in which we set
            # up the nodes, which matches tree_keys
            mapping = {}
            i = 0
            for key in tree_keys:
                mapping[key] = str(i)
                i += 1
            G_relabelled = nx.relabel_nodes(G,mapping)
            degrees = G_relabelled.degree() # we colour nodes by number of edges
            # However, this is a dict and the colour argument of draw need an array of floats
            colours = []
            for key in G_relabelled.nodes_iter():
                colours.append(float(len(G_relabelled.neighbors(key))))
            # Define our colourmap, such that unconnected nodes stand out in red, with
            # a smooth white to blue transition above this
            # We need to normalize the colours array from (0,1) and find out where
            # our minimum overlap value sits in there
            if max(colours) == 0:
                norm_cutoff = 0.5
            else:
                norm_cutoff = 0.5/(max(colours)+1)

            # Our cut off is at 1 - i.e. one connected edge. 
            from matplotlib.colors import LinearSegmentedColormap
            cdict = {'red':   ((0.0, 1.0, 1.0),
                               (norm_cutoff, 1.0, 1.0),
                               (1.0, 0., 0.)),
                     'green': ((0.0, 0.0, 0.0),
                               (norm_cutoff, 0.0, 1.0),
                               (1.0, 0.1, 0.1)),
                     'blue':  ((0.0, 0.0, 0.0),
                               (norm_cutoff, 0.0, 1.0),
                               (1.0, 1.0, 1.0))}
            custom = LinearSegmentedColormap('custom', cdict)
            
            # we now make a empty figure to generate a colourbar, then throw away
            Z = [[0,0],[0,0]]
            levels = numpy.arange(0,max(colours)+1,0.5)
            CS3 = plt.contourf(Z, levels, cmap=custom)
            plt.clf()
            if show:
                fig = plt.figure(dpi=90)
            else:
                fig = plt.figure(dpi=270)
            #Z = [[0,0],[0,0]]
            #levels = plt.frange(0,max(colours)+1,(max(colours)+1)/256.)
            #print levels
            #CS3 = plt.contourf(Z,levels,cmap=custom)
            #plt.clf()
            ax = fig.add_subplot(111)
            cs = nx.draw_networkx(G_relabelled,with_labels=True,ax=ax,node_color=colours,
                                  cmap=custom,edge_color='k',node_size=100,font_size=8,vmax=max(colours),vmin=0)
            limits=plt.axis('off')
            #plt.axis('equal')
            ticks = MaxNLocator(integer=True,nbins=9)
            pp=plt.colorbar(CS3, orientation='horizontal', format='%d', ticks=ticks)
            pp.set_label("No. of connected trees")
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
                sizes.append(100*H.number_of_nodes())
            G_relabelled = nx.convert_node_labels_to_integers(G_new)
            if (show):
                fig = plt.figure(dpi=90)
            else:
                fig = plt.figure(dpi=270)
            # make a throw-away plot to get a colourbar info
            Z = [[0,0],[0,0]]
            levels = plt.frange(0,max(colours)+0.01,(max(colours)+0.01)/256.)
            CS3 = plt.contourf(Z,levels,cmap=plt.cm.Blues)
            plt.clf()
            ax = fig.add_subplot(111)
            limits=plt.axis('off')
            plt.axis('equal')
            if (len(colours) > 1):
                cs = nx.draw_shell(G_relabelled,with_labels=True,ax=ax,node_size=sizes,node_color=colours,
                              vmax=max(colours),vmin=0,cmap=plt.cm.Blues,edge_color='k')
                ticks = MaxNLocator(integer=True,nbins=9)
                pp=plt.colorbar(CS3, orientation='horizontal', format='%d', ticks=ticks)
                pp.set_label("No. connected edges")
            else:
                cs = nx.draw_networkx(G_relabelled,with_labels=True,ax=ax,edge_color='k',node_color='w',node_size=500)
            
                limits=plt.axis('off')
            if (show):
                from matplotlib.backends.backend_gtkagg import FigureCanvasGTKAgg as FigureCanvas
                canvas = FigureCanvas(fig)  # a gtk.DrawingArea 
                return sufficient_overlap, key_list,canvas
            else:
                fig.savefig(filename)

    return sufficient_overlap, key_list

def data_independence(XML,make_new_xml=False,ignoreWarnings=False):
    """ Return a list of sources that are not independent.
    This is decided on the source data and the characters.
    """

    if not ignoreWarnings:
        _check_data(XML)

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
        new_xml = clean_data(new_xml)
        return non_ind, new_xml
    else:
        return non_ind

def add_historical_event(XML, event_description):
    """
    Add a historial_event element to the XML. 
    The element contains a description of the event and the the current
    date will ba added
    """

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

def read_matrix(filename):
    """
    Read a Nexus or Hennig formatted matrix file. Returns the matrix and taxa.
    """

    matrix = []
    taxa = []

    try:
        p4.var.alignments = []
        p4.var.doCheckForDuplicateSequences = False
        p4.read(filename)
        p4.var.doCheckForDuplicateSequences = True
        # get data out
        a = p4.var.alignments[0]
        a.setNexusSets()
        sequences = a.sequences
        matrix = []
        taxa = []
        p4.var.alignments = []
        # Also need to reset nexusSets...subtle! Only spotted after running all tests
        p4.var.nexusSets = None
        for s in sequences:
            char_row = []
            for i in range(0,len(s.sequence)):
                char_row.append(s.sequence[i])
            matrix.append(char_row)
            taxa.append(s.name)
    except:
        # Raises exception with STK-type nexus matrix and with Hennig
        # open file and find out type
        f = open(filename,"r")
        data = f.read()
        data = data.lower()
        f.close()
        if (data.find("#nexus") > -1):
            matrix,taxa = _read_nexus_matrix(filename)
        elif (data.find("xread") > -1):
            matrix,taxa = _read_hennig_matrix(filename)
        else:
            raise MatrixError("Invalid matrix format")

    return matrix,taxa


def clean_data(XML):
    """ Cleans up (i.e. deletes) non-informative trees and empty sources
        Same function as check data, but instead of raising message, simply fixes the problems.
    """

    # check all names are unique - this is easy...
    try:
        _check_uniqueness(XML) # this will raise an error is the test is not passed
    except NotUniqueError:
        XML = set_unique_names(XML)

    # now the taxa
    XML = _check_taxa(XML,delete=True) 

    # check trees are informative
    XML = _check_informative_trees(XML,delete=True)

    # check sources
    XML = _check_sources(XML,delete=True)

    # unpermutable trees
    permutable_trees = _find_trees_for_permuting(XML)
    all_trees = obtain_trees(XML)
    for t in permutable_trees:
        new_tree = permutable_trees[t]
        for i in range(10): # do at most 10 iterations
            new_tree = _collapse_nodes(new_tree)
        
        if (not _trees_equal(new_tree,permutable_trees[t])):
           XML = _swap_tree_in_XML(XML,new_tree,t) 

    XML = _check_informative_trees(XML,delete=True)

    return XML



def replace_genera(XML,dry_run=False,ignoreWarnings=False):
    """ Remove all generic taxa by replacing them with a polytomy of
        all species in the dataset belonging to that genera
    """
        
    if not ignoreWarnings:
        _check_data(XML)

    # get all the taxa
    taxa = get_all_taxa(XML)

    generic = []
    # find all the generic and build an internal subs file
    for t in taxa:
        t = t.replace(" ","_")
        if t.find("_") == -1:
            # no underscore, so just generic
            generic.append(t)

    subs = []
    generic_to_replace = []
    for t in generic:
        currentSub = []
        for taxon in taxa:
            if (not taxon == t) and taxon.find(t) > -1:
                m = re.search('[\(|\)|\.|\?|"|=|,|&|^|$|@|+]', taxon)
                if (not m == None):
                    if taxon.find("'") == -1:
                        taxon = "'"+taxon+"'" 
                currentSub.append(taxon)
        if (len(currentSub) > 0):
            subs.append(",".join(currentSub))
            generic_to_replace.append(t)
    
    if (dry_run):
        return None,generic_to_replace,subs

    XML = substitute_taxa(XML, generic_to_replace, subs, ignoreWarnings=ignoreWarnings, skip_existing=True)

    XML = clean_data(XML)

    return XML,generic_to_replace,subs

def subs_from_csv(filename):
    """Create taxonomic subs from a CSV file, where
       the first column is the old taxon and all other columns are the
       new taxa to be subbed in-place
    """

    import csv

    new_taxa = []
    old_taxa = []

    with open(filename, 'rU') as csvfile:
        subsreader = csv.reader(csvfile, delimiter=',')
        for row in subsreader:
            if (len(row) == 0):
                continue
            if (len(row) == 1):
                old_taxa.append(row[0].replace(" ","_"))
                new_taxa.append(None)
            else:
                replacement=""
                rep_taxa = row[1:]
                for rep in rep_taxa:
                    if not rep == "":
                        if (replacement == ""):
                            replacement = rep.replace(" ","_")
                        else:
                            replacement = replacement+","+rep.replace(" ","_")
                old_taxa.append(row[0].replace(" ","_"))
                if (replacement == ""):
                    new_taxa.append(None)
                else:
                    new_taxa.append(replacement)

    return old_taxa, new_taxa


def parse_subs_file(filename):
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
        if (re.search('\w+=\s+', line) != None or re.search('\s+=\w+', line) != None):
            # probable error
            raise UnableToParseSubsFile("You sub file contains '=' without spaces either side. If it's within a taxa, remove the spaces. If this is a sub, add spaces")
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
                    n_t = n_t.replace(" ","_")
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
        n_t = n_t.replace(" ","_")
        new_taxa.append(n_t.strip())

    if (len(old_taxa) != len(new_taxa)):
        raise UnableToParseSubsFile("Output arrays are not same length. File incorrectly formatted")
    if (len(old_taxa) == 0):
        raise UnableToParseSubsFile("No substitutions found! File incorrectly formatted")
 

    return old_taxa, new_taxa

def get_all_genera(XML):

    taxa = get_all_taxa(XML)

    generic = []
    for t in taxa:
        t = t.replace('"','')
        generic.append(t.split("_")[0])

    return generic
    

def check_subs(XML,new_taxa):
    """Check a subs file and issue a warning if any of the incoming taxa
       are not already in the dataset. This is often what is wanted, but sometimes
       it is not. We run this before we do the subs to alert the user of this
       but they may continue
    """

    dataset_taxa = get_all_taxa(XML)
    unknown_taxa = []
    generic = get_all_genera(XML)
    for taxon in new_taxa:
        if not taxon == None:
            all_taxa = taxon.split(",")
            for t in all_taxa:
                if t.find("_") == -1:
                    # just generic, so check against that
                    if not t in generic:
                        unknown_taxa.append(t)
                else:
                    if not t in dataset_taxa:
                        unknown_taxa.append(t)
    unknown_taxa = _uniquify(unknown_taxa)
    unknown_taxa.sort()

    if (len(unknown_taxa) > 0):
        taxa_list = '\n'.join(unknown_taxa)
        msg = "These taxa are not already in the dataset, are you sure you want to substitute them in?\n"
        msg += taxa_list
        raise AddingTaxaWarning(msg) 
    
    return

def create_subset(XML,search_terms,andSearch=True,includeMultiple=True,ignoreWarnings=False):
    """Create a new dataset which is a subset of the incoming one.
       searchTerms is a dict, with the following keys:
       years - list consisting of the years to include. An entry can contain two years seperated by -. A range will then
               be used.
       characters - list of charcters to include
       character_types - list of character types to include (Molecular, Morphological, Behavioural or Other)
       analyses - list of analyses to include (MRP, etc)
       taxa - list of taxa that must be in a source tree
       fossil - all_fossil or all_extant

       Multiple requests produce *and* matches (so between 2000-2010 *and* Molecular *and* contain Gallus gallus) unless 
       andSearch is false. If it is, an *or* search is used. So the example would be years 2000-2010 *or* Molecular
       *or* contain Gallus gallus

       includeMultiple means that a source can contain Molecular and Morophological characters and match
       Molecular (or, indeed, Morpholoigcal). Set to False to include if it's *only* Molecular you're
       after (i.e. trees with mixed character sets will be ignored). This applies to characters and character_types
       only (as the other terms don't make sense with this off).

       Note: this funtion is not (yet) taxonomically aware, so Galliformes will only return trees that actually have
       a leaf called Galliformes. Gallus gallus will not match. 

       Also note: The tree strings are searched for taxa, not the taxa elements (which are optional)

       A new PHYML file will be produced. The calling function must do something sensible with that
    """

    if len(search_terms) == 0:
        print "Warning: No search terms present, returning original XML"
        return XML

    if not ignoreWarnings:
        _check_data(XML)

    # We just need to preprocess the years
    final_years = []
    try:
        years = search_terms['years']
        for y in years:
            if str(y).find('-') == -1:
                final_years.append(int(y))
            else:
                yRange = y.split('-')
                for i in range(int(yRange[0]),int(yRange[1])+1):
                    final_years.append(i)
        final_years.sort()
        search_terms['years'] = final_years
    except KeyError:
        pass


    # Easiest way to do this is to remove all sources from the incoming XML (after taking a copy!)
    # and add them back if they match the request requirements. That way, we keep the history, etc, etc
    original_XML = XML
    xml_root = _parse_xml(XML)
    orig_xml_root = _parse_xml(original_XML)

    # remove sources
    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)
    for s in sources:
        s.getparent().remove(s)

    # edit name (append _subset)
    proj_name = xml_root.xpath('/phylo_storage/project_name/string_value')[0].text
    proj_name += "_subset"
    xml_root.xpath('/phylo_storage/project_name/string_value')[0].text = proj_name

    # this is the tricky part
    # Loop over sources in the original data and if a tree matches the search requirements, add the source
    # then add the matching tree
    sources = []
    for ele in orig_xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    matching_sources = []
    # Years are first. This is easy - the source only has one year. 
    # Note years is already [] is we get a key error
    try:
        years = search_terms['years']
        if len(years) > 0:
            for s in sources:
                yrs = s.find(".//year")
                y = int(yrs.xpath("integer_value")[0].text)
                if y in years:
                    matching_sources.append(s)
            if (andSearch):
                sources = matching_sources
                matching_sources = []
    except KeyError:
        pass

    # Now character types. Not easy - we need to check each source tree and add the source
    # and matching source trees only.
    try:
        charTypes = search_terms['character_types']
        if (len(charTypes) > 0):
            for s in sources:
                st = s.findall(".//source_tree")
                include_source = False
                for t in st:
                    ct = t.findall(".//character")
                    include = False
                    if (andSearch and includeMultiple): # and search but tree can contain other types too
                        # uniqify ct, sort and compare to sorted charTypes - charTypes is a subset 
                        # of ct, include
                        this_trees_chars = []
                        for c in ct:
                            this_trees_chars.append(c.attrib['type'])
                        if (set(charTypes).issubset(this_trees_chars)):
                            include = True
                            include_source = True
                        if (not include):    
                            t.getparent().remove(t)
                    elif (andSearch==False): # or search 
                        for c in ct:
                            if c.attrib['type'] in charTypes:
                                include = True
                                include_source = True
                        if (not include):    
                            t.getparent().remove(t)
                    else: # and search and tree must contain *only* the search terms
                        include = True
                        for c in ct:
                            if not c.attrib['type'] in charTypes:
                                include = False
                                break
                        if (include):
                            include_source = True                                
                        if (not include):    
                            t.getparent().remove(t)
                if include_source:
                    # This is the source with the non-matching source_tree elements removed
                    matching_sources.append(s)
            if (andSearch):
                sources = matching_sources
                matching_sources = []     
    except KeyError:
        charTypes = []


    # Now character
    try:
        chars = search_terms['characters']
        if (len(chars) > 0):
            for s in sources:
                st = s.findall(".//source_tree")
                include_source = False
                for t in st:
                    ct = t.findall(".//character")
                    include = False
                    if (andSearch and includeMultiple): # and search but tree can contain other types too
                        # uniqify ct, sort and compare to sorted charTypes - charTypes is a subset 
                        # of ct, include
                        this_trees_chars = []
                        for c in ct:
                            this_trees_chars.append(c.attrib['name'])
                        if (set(chars).issubset(this_trees_chars)):
                            include = True
                            include_source = True
                        if (not include):    
                            t.getparent().remove(t)
                    elif (andSearch==False): # or search 
                        for c in ct:
                            if c.attrib['name'] in chars:
                                include = True
                                include_source = True
                        if (not include):    
                            t.getparent().remove(t)
                    else: # and search and tree must contain *only* the search terms
                        include = True
                        for c in ct:
                            if not c.attrib['name'] in chars:
                                include = False
                                break
                        if (include):
                            include_source = True                                
                        if (not include):    
                            t.getparent().remove(t)
                if include_source:
                    # This is the source with the non-matching source_tree elements removed
                    matching_sources.append(s)
            if (andSearch):
                sources = matching_sources
                matching_sources = []  
    except KeyError:
        chars = []

    # Now analyses
    try:
        analyses = search_terms['analyses'] # assume one only analysis is searched for?
        if (len(analyses) > 0):
            for s in sources:
                oc = s.findall(".//optimality_criterion")
                include = False
                for o in oc:
                    if o.attrib['name'] in analyses:
                        include = True
                    else:
                        source_tree = o.getparent().getparent().getparent()
                        source_tree.getparent().remove(source_tree)
                if include:
                    # This is the source with the non-matching source_tree elements removed
                    matching_sources.append(s)
            if (andSearch):
                sources = matching_sources
                matching_sources = []
    except KeyError:
        analyses = [] 

    # Now taxa - if a tree contains any of the taxa listed, include it
    try:
        taxa = search_terms['taxa'] # assume one only analysis is searched for?
        if (len(taxa) > 0):
            for s in sources:
                st = s.findall(".//source_tree")
                include_source = False
                for t in st:
                    treestring = t.xpath("tree/tree_string/string_value")[0].text
                    include = False
                    for taxon in taxa:
                        if (_tree_contains(taxon,treestring)):
                            include = True
                            include_source = True
                            break
                    if (not include):    
                        t.getparent().remove(t)
                if include_source:
                    # This is the source with the non-matching source_tree elements removed
                    matching_sources.append(s)
            if (andSearch):
                sources = matching_sources
                matching_sources = []  
    except KeyError:
        taxa = [] 

    # Finally, fossils. Just seach for all or none
    try:
        fossil = search_terms['fossil'] # can be none or all
        if (fossil == "all_extant" or fossil == "all_fossil"):
            for s in sources:
                st = s.findall(".//source_tree")
                include_source = False
                for t in st:
                    all_extant = False
                    all_fossil = False
                    if (len(t.findall(".//all_extant")) > 0):
                        all_extant = True
                    elif (len(t.findall(".//all_fossil")) > 0):
                        all_fossil = True
                    include = False
                    if ((fossil == "all_extant" and all_extant) or
                        (fossil == "all_fossil" and all_fossil)):
                        include = True
                        include_source = True
                    if (not include):    
                        t.getparent().remove(t)
                if include_source:
                    # This is the source with the non-matching source_tree elements removed
                    matching_sources.append(s)
            if (andSearch):
                sources = matching_sources
                matching_sources = []  
    except KeyError:
        taxa = [] 

    # If we did an "and" search, the matching sources are in the sources list, otherwise
    # they're in the matching_sources list
    # So we can now append those sources to the stub of an XML we created at the begining
    if (not andSearch):
        sources = matching_sources

    srcs = xml_root.xpath("phylo_storage/sources")
    for s in sources:
        xml_root[1].append(s)
    
    XML = etree.tostring(xml_root,pretty_print=True)

    return XML

################ PRIVATE FUNCTIONS ########################

def _uniquify(l):
    """
    Make a list, l, contain only unique data
    """
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()


def _check_uniqueness(XML):
    """ This funciton is an error check for uniqueness in 
    the keys of the sources
    """

    try:
        xml_root = _parse_xml(XML)
        # By getting source, we can then loop over each source_tree
        # within that source and construct a unique name
        find = etree.XPath("//source")
        sources = find(xml_root)
    except:
        raise InvalidSTKData("Error parsing the data to check uniqueness")
    
    names = []
    message = ""
    # loop through all sources
    try:
        for s in sources:
            # for each source, get source name
            names.append(s.attrib['name'])
    except:
        raise InvalidSTKData("Error parsing the data to check uniqueness")

    names.sort()
    last_name = "" # This will actually throw an non-unique error if a name is empty
    # not great, but still an error!
    for name in names:
        if name == last_name:
            # if non-unique throw exception
            message = message + \
                    "The source names in the dataset are not unique. Please run the auto-name function on these data. Name: "+name+"\n"
        last_name = name

    if (not message == ""):
        raise NotUniqueError(message)

    return


def _assemble_tree_matrix(tree_string):
    """ Assembles the MRP matrix for an individual tree

        returns: matrix (2D numpy array: taxa on i, nodes on j)
                 taxa list: in same order as in the matrix
    """

    tree = _parse_tree(tree_string)
    try:
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
    except p4.Glitch:
        names = _getTaxaFromNewick(tree_string)
        adjmat = []
        for i in range(0,len(names)):
            adjmat.append([1])
        adjmat = numpy.array(adjmat)

        print "Warning: Found uninformative tree in data. Including it in the matrix anyway"

    return adjmat, names

def _sub_taxa_in_tree(tree,old_taxa,new_taxa=None,skip_existing=False):
    """Swap the taxa in the old_taxa array for the ones in the
    new_taxa array
    
    If the new_taxa array is missing, simply delete the old_taxa
    """
   
    tree = _correctly_quote_taxa(tree)
    # are the input values lists or simple strings?
    if (isinstance(old_taxa,str)):
        old_taxa = [old_taxa]
    if (new_taxa == None):
        new_taxa = len(old_taxa)*[None]
    elif (new_taxa and isinstance(new_taxa,str)):
        new_taxa = [new_taxa]

    # check they are same lengths now
    if (new_taxa):
        if (len(old_taxa) != len(new_taxa)):
            print "Substitution failed. Old and new are different lengths"
            return # need to raise exception here

    i = 0
    for taxon in old_taxa:
        # tree contains the old_taxon, do something with it
        taxon = taxon.replace(" ","_")
        if (_tree_contains(taxon,tree)):
            if (new_taxa == None or new_taxa[i] == None):
                p4tree = _parse_tree(tree) 
                terminals = p4tree.getAllLeafNames(p4tree.root) 
                count = 0
                taxon_temp = taxon.replace("'","")
                for t in terminals:
                    t = t.replace(" ","_")
                    if (t == taxon_temp):
                        count += 1
                    if (t.startswith(taxon_temp+"%")):
                        count += 1 
                # we are deleting taxa - we might need multiple iterations
                for t in range(0,count):
                    tree = _delete_taxon(taxon, tree)

            else:
                # we are substituting
                tree = _sub_taxon(taxon, new_taxa[i], tree, skip_existing=skip_existing)
        i += 1

    tree = _collapse_nodes(tree)
    tree = _remove_single_poly_taxa(tree)

    return tree 

def _tree_contains(taxon,tree):
    """ Returns if a taxon is contained in the tree
    """

    taxon = taxon.replace(" ","_")
    tree = _parse_tree(tree) 
    terminals = tree.getAllLeafNames(tree.root)
    # p4 strips off ', so we need to do so for the input taxon
    taxon = taxon.replace("'","")
    for t in terminals:
        t = t.replace(" ","_")
        if (t == taxon):
            return True
        if (t.startswith(taxon+"%")):
            return True # match potential non-monophyletic taxa

    return False


def _delete_taxon(taxon, tree):
    """ Delete a taxon from a tree string
    """

    taxon = taxon.replace(" ","_")
    taxon = taxon.replace("'","")
    # check if taxa is in there first
    if (tree.find(taxon) == -1): # should find, even if non-monophyletic
        return tree #raise exception?

    # Remove all the empty nodes we left laying around
    tree_obj = _parse_tree(tree)    
    tree_obj.getPreAndPostOrderAboveRoot()
    for n in tree_obj.iterPostOrder():
        if n.getNChildren() == 1 and n.isLeaf == 0:
            tree_obj.collapseNode(n)

    for node in tree_obj.iterNodes():
        if node.name == taxon or (not node.name == None and node.name.startswith(taxon+"%")):
            tree_obj.removeNode(node.nodeNum,alsoRemoveBiRoot=False)
            break

    return tree_obj.writeNewick(fName=None,toString=True).strip()


def _get_all_siblings(node):
    """ Get all siblings of a node
    """

    # p4 returns the rightmost sibling, so we need to get all the right siblings,
    # and the leftSiblings
    siblings = []
    siblings_left = True
    newNode = node
    while siblings_left:
        newNode = newNode.sibling
        if not newNode == None:
            if not newNode.name == None:
                siblings.append(newNode.name)
        else:
            siblings_left = False
    # now the left siblings
    siblings_left = True
    newNode = node
    while siblings_left:
        newNode = newNode.leftSibling()
        if not newNode == None:
            if not newNode.name == None:
                siblings.append(newNode.name)
        else:
            siblings_left = False
    
    siblings.sort()
    return siblings


def _sub_taxon(old_taxon, new_taxon, tree, skip_existing=False):
    """ Simple swap of taxa
    """

    import csv

    taxa_in_tree = _getTaxaFromNewick(tree)
    # we might have to add quotes back in
    for i in range(0,len(taxa_in_tree)):
        m = re.search('[\(|\)|\.|\?|"|=|,|&|^|$|@|+]', taxa_in_tree[i])
        if (not m == None):
            if taxa_in_tree[i].find("'") == -1:
                taxa_in_tree[i] = "'"+taxa_in_tree[i]+"'" 
    
    # swap spaces for _, as we're dealing with Newick strings here
    new_taxon = new_taxon.replace(" ","_")

    # remove duplicates in the new taxa
    for row in csv.reader([new_taxon],delimiter=',', quotechar="'"):
        taxa = row
    taxa = _uniquify(taxa)
 
    # we might have to add quotes back in
    for i in range(0,len(taxa)):
        m = re.search('[\(|\)|\.|\?|"|=|,|&|^|$|@|+]', taxa[i])
        if (not m == None):
            if taxa[i].find("'") == -1:
                taxa[i] = "'"+taxa[i]+"'" 

    new_taxa = []
    if skip_existing:
        # now remove new taxa that are already in the tree
        for t in taxa:
            if not t in taxa_in_tree:
                new_taxa.append(t)
    else:
        new_taxa = taxa

    # Here's the plan - strip the duplicated taxa marker, _\d from the
    # taxa. We can then just swap taxa in plan text.
    # When done, p4 can fix duplicated taxa by adding back on _\d
    # Then we collapse the nodes, taking into account duplicated taxa
    # This will need several iterations.

    modified_tree = re.sub(r"(?P<taxon>[a-zA-Z0-9_\+\= ]*)%[0-9]+",'\g<taxon>',tree)
    new_taxon = ",".join(new_taxa)

    if (len(new_taxon) == 0):
        # we need to delete instead
        return _delete_taxon(old_taxon,tree)

    old_taxon = re.escape(old_taxon)    
    # check old taxon isn't quoted
    m = re.search('[\(|\)|\.|\?|"|=|,|&|^|$|@|+]', old_taxon)
    match = re.search(r"(?P<pretaxon>\(|,|\)| )"+old_taxon+r"(?P<posttaxon>\(|,|\)| |:)",modified_tree)
    if (not m == None and match == None):
        old_taxon = "'"+old_taxon+"'" 
        # given we've just quoted it, the _ might be spaces after all
        # search for this (it is in the tree, we just don't know the form)
        match = re.search(r"(?P<pretaxon>\(|,|\)| )"+old_taxon+r"(?P<posttaxon>\(|,|\)| |:)",modified_tree)
        if (match == None):
            old_taxon = old_taxon.replace("_"," ")
            match = re.search(r"(?P<pretaxon>\(|,|\)| )"+old_taxon+r"(?P<posttaxon>\(|,|\)| |:)",modified_tree)
            if (match == None):
                raise InvalidSTKData("Tried to find "+old_taxon+" in "+modified_tree+" and failed")

    # simple text swap
    new_tree = re.sub(r"(?P<pretaxon>\(|,|\)| )"+old_taxon+r"(?P<posttaxon>\(|,|\)| |:)",'\g<pretaxon>'+new_taxon+'\g<posttaxon>', modified_tree)
    # we might now need a final collapse - e.g. we might get ...(taxon1,taxon2),... due
    # to replacements, but they didn't collapse, so let's do this
    for i in range(10): # do at most 10 iterations
        new_tree = _collapse_nodes(new_tree)

    return new_tree

def _correctly_quote_taxa(tree):
    """ In order for the subs to work, we need to only quote taxa that need it, as otherwise 
        we might have have the same taxon, e.g. 'Gallus gallus' and Gallus_gallus being
        considered as different
    """

    # get taxa from tree
    t_obj = _parse_tree(tree)
    taxa = t_obj.getAllLeafNames(0)

    new_taxa = {}
    # set the taxon name correctly, including in quotes, if needed...
    for t in taxa:
       m = re.search('[\(|\)|\?|"|=|,|&|^|$|@|+]', t)
       if (m == None):
          new_taxa[t] = t.replace(" ","_")
       else:
          new_taxa[t] = "'" + t + "'"

    # search for the taxa in the tree now, check if quoted already
    modified_tree = tree
    for t in taxa:
        new = new_taxa[t]
        look_for = re.escape(t)
        modified_tree = re.sub(r"(?P<pretaxon>\(|,|\)| )"+look_for+r"(?P<posttaxon>\(|,|\)| |:)",'\g<pretaxon>'+new+'\g<posttaxon>',modified_tree)
        # new try with quotes on original - they get stripped by p4
        t = "'" + t + "'"
        look_for = re.escape(t)
        modified_tree = re.sub(r"(?P<pretaxon>\(|,|\)| )"+look_for+r"(?P<posttaxon>\(|,|\)| |:)",'\g<pretaxon>'+new+'\g<posttaxon>',modified_tree)

    return modified_tree

def _collapse_nodes(in_tree):
    """ Collapses nodes where the siblings are actually the same
        taxon, denoted by taxon1, taxon2, etc
    """

    modified_tree = re.sub(r"(?P<taxon>[a-zA-Z0-9_\+\= ]*)%[0-9]+",'\g<taxon>',in_tree)   
    tree = _parse_tree(modified_tree,fixDuplicateTaxa=True)
    taxa = tree.getAllLeafNames(0)
    
    for t in taxa:
        # we might have removed the current taxon in a previous loop
        try:
            siblings = _get_all_siblings(tree.node(t))
        except p4.Glitch:
            continue
        m = re.match('([a-zA-Z0-9_\+\=\?\. ]*)%[0-9]+', t)
        if (not m == None):
            t = m.group(1)
        for s in siblings:
            orig_s = s
            m = re.match('([a-zA-Z0-9_\+\=\?\. ]*)%[0-9]+', s)
            if (not m == None):
                s = m.group(1)
            if t == s:
                # remove this
                tree.removeNode(tree.node(orig_s),alsoRemoveSingleChildParentNode=True,alsoRemoveBiRoot=False)

    # Remove all the empty nodes we left laying around
    tree.getPreAndPostOrderAboveRoot()
    for n in tree.iterPostOrder():
        if n.getNChildren() == 1 and n.isLeaf == 0:
            tree.collapseNode(n)

    return tree.writeNewick(fName=None,toString=True).strip()    

def _remove_single_poly_taxa(tree):
    """ Count the numbers after % in taxa names """

    taxa = _getTaxaFromNewick(tree)

    numbers = {}
    for t in taxa:
        m = re.match('([a-zA-Z0-9_\+\= ]*)%([0-9]+)', t)
        if (not m == None):
            if (m.group(1) in numbers):
                numbers[m.group(1)] = numbers[m.group(1)]+1
            else:
                numbers[m.group(1)] = 1
        else:
            numbers[t] = 1

    for t in taxa:
        m = re.match('([a-zA-Z0-9_\+\= ]*)%([0-9]+)', t)
        if (not m == None):
            if numbers[m.group(1)] == 1:
                tree = re.sub(t,m.group(1),tree) 
    
    return tree


def _swap_tree_in_XML(XML, tree, name, delete=False):
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
                        if (delete):
                            # we now need to check the source to check if there are
                            # any trees in this source now, if not, remove
                            if (len(s.xpath("source_tree/tree/tree_string")) == 0):
                                s.getparent().remove(s)
                        return etree.tostring(xml_root,pretty_print=True)
                tree_no += 1

    return XML


def _check_taxa(XML,delete=False):
    """ Checks that taxa in the XML are in the tree for the source thay are added to
    """

    try:
        # grab all sources
        xml_root = _parse_xml(XML)
        find = etree.XPath("//source")
        sources = find(xml_root)
    except:
        raise InvalidSTKData("Error parsing the data to check taxa")
    
    message = ""

    # for each source
    for s in sources:
        # get a list of taxa in the XML
        this_source = _parse_xml(etree.tostring(s))
        trees = obtain_trees(etree.tostring(this_source))
        s_name = s.attrib['name']
        for name in trees.iterkeys():
            tree_no = 1
            for t in s.xpath("source_tree/tree/tree_string"):
                t_name = s_name+"_"+str(tree_no)
                tree_no += 1
                if (t_name == name):
                    find = etree.XPath(".//taxon")
                    taxa_ele = find(t.getparent().getparent())

            tree = trees[name]
            # are the XML taxa in the tree?
            for t in taxa_ele:
                xml_taxon = t.attrib['name']
                if (tree.find(xml_taxon) == -1):
                    if (delete):
                        # remove
                        t.get_parent().remove(t)
                    else:
                        # no - raise an error!
                        message = message + "Taxon: "+xml_taxon+" is not in the tree "+name+"\n"
    if not delete:               
        if (not message==""):
            raise InvalidSTKData(message)
        else:
            return
    else:
        return etree.tostring(xml_root,pretty_print=True)        


def _check_sources(XML,delete=True):
    """ Check that all sources in the dataset have at least one tree_string associated
        with them
    """

    try:
        xml_root = _parse_xml(XML)
        # By getting source, we can then loop over each source_tree
        # within that source and construct a unique name
        find = etree.XPath("//source")
        sources = find(xml_root)
    except:
        raise InvalidSTKData("Error parsing the data to check source")
            
    message = ""
    # for each source
    for s in sources:
        # get a list of taxa in the XML
        this_source = _parse_xml(etree.tostring(s))
        name = s.attrib['name']
        trees = obtain_trees(etree.tostring(this_source))
        if (len(trees) < 1):
            if (not delete):
                message =+ "Source "+name+" has no trees\n"
            else:
                s.getparent().remove(s)

    if not delete:
        if (not message == ""):
            raise InvalidSTKData(message)
        else:
            return
    else:
        return etree.tostring(xml_root,pretty_print=True)        



def _check_data(XML):
    """ Function to check various aspects of the dataset, including:
         - checking taxa in the XML for a source are included in the tree for that source
         - checking all source names are unique
    """

    # check all names are unique - this is easy...
    _check_uniqueness(XML) # this will raise an error is the test is not passed

    # now the taxa
    _check_taxa(XML) # again will raise an error if test fails

    # check trees are informative
    _check_informative_trees(XML)

    # check sources
    _check_sources(XML,delete=False)

    return


def _parse_xml(xml_string):
    """ Lxml cannot parse non-unicode characters 
    so we're wrapping this up so we can strip these characters
    beforehand. We can then send it to lxml.parser as normal
    """

    xml_string = _removeNonAscii(xml_string)
    XML = etree.fromstring(xml_string)
    return XML

def _removeNonAscii(s): 
    """
    Removes any non-ascii characters from string, s.
    """
    return "".join(i for i in s if ord(i)<128)

def _getTaxaFromNewick(tree):
    """ Get the terminal nodes from a Newick string"""

    t_obj = _parse_tree(tree)
    terminals = t_obj.getAllLeafNames(0)
    taxa = []
    for t in terminals:
        taxa.append(t.replace(" ","_"))

    return taxa


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

    tree_1 = _parse_tree(t1)
    tree_2 = _parse_tree(t2)
    
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
    """
    Returns any trees that contain %, i.e. non-monophyly
    """

    trees = obtain_trees(XML)
    permute_trees = {}
    for t in trees:
        if trees[t].find('%') > -1:
            # tree needs permuting - we store the 
            permute_trees[t] = trees[t]

    return permute_trees

def _create_matrix(trees, taxa, quote=False,format="hennig"):
    """
    Does the hard work on creating a matrix
    """

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
                elif (taxon == "MRP_Outgroup"):
                    current_row.append('0')
                else:
                    current_row.append('?')
            matrix.append(current_row)
        charsets.append(str(current_char) + "-" + str(current_char + nChars-2))
        current_char += nChars-1

    matrix = numpy.array(matrix)
    matrix = matrix.transpose()

    return _create_matrix_string(matrix,taxa,charsets=charsets,names=names,format=format,quote=quote)


def _create_matrix_string(matrix,taxa,charsets=None,names=None,format='hennig',quote=False):
    """
    Turns a matrix into a string
    """

    last_char = len(matrix[0])    
    if (format == 'hennig'):
        matrix_string = "xread\n"
        matrix_string += str(last_char) + " "+str(len(taxa))+"\n"

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
        matrix_string += "\tdimensions ntax = "+str(len(taxa)) +" nchar = "+str(last_char)+";\n"
        matrix_string += "\tformat missing = ?"
        matrix_string += ";\n"
        matrix_string += "\n\tmatrix\n\n"

        i = 0
        for taxon in taxa:
            if (quote):
                matrix_string += "'" + taxon + "'\t"
            else:
                matrix_string += taxon + "\t"
            string = ""
            for t in matrix[i][:]:
                string += t
            matrix_string += string + "\n"
            i += 1
        if (not charsets == None):
            
            matrix_string += "\t;\nend;\n\n"
            matrix_string += "begin sets;\n"
            if (names == None):
                names = []
                i = 1
                for c in charset:
                    names.append("chars_"+str(i))
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
    """
    Does all the hard work of amalgamating trees
    """
    
    # all trees are in Newick string format already
    # For each format, Newick, Nexus and TNT this format
    # is adequate. 
    # Newick: Do nothing - write one tree per line
    # Nexus: Add header, write one tree per line, prepending tree info, taking into acount annonymous flag
    # TNT: strip commas, write one tree per line
    output_string = ""
    if format.lower() == "nexus":
        output_string += "#NEXUS\n\nBEGIN TREES;\n\n"
    if format.lower() == "tnt":
        output_string += "tread 'tree(s) from TNT, for data in Matrix.tnt'\n"
    tree_count = 0
    for tree in trees:
        if format.lower() == "nexus":
            if anonymous:
                output_string += "\tTREE tree_"+str(tree_count)+" = "+trees[tree]+"\n"
            else:
                output_string += "\tTREE "+tree+" = "+trees[tree]+"\n"
        elif format.lower() == "newick":
            output_string += trees[tree]+"\n"
        elif format.lower() == "tnt":
            t = trees[tree];
            t = t.replace(",","");
            t = t.replace(";","");
            if (tree_count < len(trees)-1):
                output_string += t+"*\n"
            else:
                output_string += t+";\n"
        tree_count += 1
    # Footer
    if format.lower() == "nexus":
        output_string += "\n\nEND;"
    elif format.lower() == "tnt":
        output_string += "\n\nproc-;"

    return output_string


def _read_nexus_matrix(filename):
    """ Read in essential info from a NEXUS matrix file
        This does not include the charset as we don't actually use it
        for anything and is not saved in TNT format anyway
    """

    taxa = []
    matrix = []
    f = open(filename,"r")
    inData = False
    for line in f:
        linel = line.lower()
        if linel.find(";") > -1:
            inData = False
        if (inData):
            linel = linel.strip()
            if len(linel) == 0:
                continue # empty line
            
            data = line.split()
            taxa.append(data[0])
            char_row = []
            for n in range(0,len(data[1])):
                char_row.append(data[1][n])
            matrix.append(char_row)
        if (linel.find('matrix') > -1):
            inData = True

    return matrix,taxa

def _read_hennig_matrix(filename):
    """ Read in essential info from a TNT matrix file
    """

    taxa = []
    matrix = []
    f = open(filename,"r")
    inData = False
    for line in f:
        linel = line.lower()
        if linel.find(";") > -1:
            inData = False
        if (inData):
            linel = linel.strip()
            if len(linel) == 0:
                continue # empty line
            
            data = line.split()
            taxa.append(data[0])
            char_row = []
            for n in range(0,len(data[1])):
                char_row.append(data[1][n])
            matrix.append(char_row)
        m = re.match('\d+ \d+', linel)
        if (not m == None):
            inData = True

    return matrix,taxa


def _check_informative_trees(XML,delete=False):
    """ Checks that all trees in the data set are informative and raises error if not
    """

    try:
        trees = obtain_trees(XML)
    except:
        raise InvalidSTKData("Error parsing the data to check trees")
    remove = []
    message=""
    for t in trees:
        tree = trees[t]
        tree = _parse_tree(tree)

        # check if tree contains more than two taxa
        terminals = tree.getAllLeafNames(tree.root)
        if (len(terminals) < 3):
            message = message+"\nTree "+t+" contains only 2 taxa and is not informative"
            remove.append(t)
        # if tree contains three or more taxa, check it's rooted somewhere
        elif (tree.getDegree(tree.root) == len(terminals)):
            message = message+"\nTree "+t+" doesn't contain any clades and is not informative"
            remove.append(t)

    if (not delete):
        if (not message == ""):
            raise UninformativeTreeError(message)
        else:
            return
    else:
        remove.sort(reverse=True)
        for t in remove:
            XML = _swap_tree_in_XML(XML,None,t,delete=True)

        return XML

def _parse_trees(tree_block):
    """ Parse a string containing multiple trees 
        to a list of p4 tree objects
    """
   
    try:
        p4.var.doRepairDupedTaxonNames = 2
        p4.var.warnReadNoFile = False
        p4.var.nexus_warnSkipUnknownBlock = False
        p4.var.trees = []
        p4.read(tree_block)
        p4.var.nexus_warnSkipUnknownBlock = True
        p4.var.warnReadNoFile = True
        p4.var.doRepairDupedTaxonNames = 0
    except p4.Glitch as detail:
        raise TreeParseError("Error parsing tree\n"+detail.msg+"\n"+tree_block )
    trees = p4.var.trees
    p4.var.trees = []
    return trees

def _parse_tree(tree,fixDuplicateTaxa=False):
    """ Parse a newick string to p4 tree object
    """

    try:
        if (fixDuplicateTaxa):
            p4.var.doRepairDupedTaxonNames = 2
        p4.var.warnReadNoFile = False
        p4.var.nexus_warnSkipUnknownBlock = False
        p4.var.trees = []
        p4.read(tree)
        p4.var.nexus_warnSkipUnknownBlock = True
        p4.var.warnReadNoFile = True
        if (fixDuplicateTaxa):
            p4.var.doRepairDupedTaxonNames = 0
    except p4.Glitch as detail:
        raise TreeParseError("Error parsing tree\n"+detail.msg+"\n"+tree )

    t = p4.var.trees[0]
    p4.var.trees = []
    return t


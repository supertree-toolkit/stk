#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2017, Jon Hill, Katie Davis
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
#    Jon Hill. jon.hill@york.ac.uk. 
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
import stk_exceptions as excp
from stk_taxonomy import *
import traceback
from cStringIO import StringIO
from collections import defaultdict
import stk.p4 as p4
import re
import operator
import networkx as nx
import datetime
import indent
import unicodedata
import stk_internals
from copy import deepcopy
import time
import types

#plt.ion()

sys.setrecursionlimit(50000)
# GLOBAL VARIABLES
IDENTICAL = 0
SUBSET = 1
PLATFORM = sys.platform
#Logging
import logging
logging.basicConfig(filename='supertreetoolkit.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

# taxonomy levels
# What we get from EOL
current_taxonomy_levels = ['species','genus','tribe','subfamily','family','superfamily','order','superorder','class','superclass','phylum','subkingdom','kingdom']
# And the extra ones from ITIS
extra_taxonomy_levels = ['superfamily','infraorder','suborder','superorder','subclass','subphylum','superphylum','infrakingdom','subkingdom']
# all of them in order
taxonomy_levels = ['species','subgenus','genus','tribe','subfamily','family','superfamily','subsection','section','parvorder','infraorder','suborder','order','superorder','subclass','class','superclass','subphylum','phylum','superphylum','infrakingdom','subkingdom','kingdom']


SPECIES = taxonomy_levels[0]
GENUS = taxonomy_levels[1]
FAMILY = taxonomy_levels[2]
SUPERFAMILY = taxonomy_levels[3]
INFRAORDER = taxonomy_levels[4]
SUBORDER = taxonomy_levels[5]
ORDER = taxonomy_levels[6]
SUPERORDER = taxonomy_levels[7]
SUBCLASS = taxonomy_levels[8]
CLASS = taxonomy_levels[9]
SUBPHYLUM = taxonomy_levels[10]
PHYLUM = taxonomy_levels[11]
SUPERPHYLUM = taxonomy_levels[12] 
INFRAKINGDOM = taxonomy_levels[13]
SUBKINGDOM = taxonomy_levels[14]
KINGDOM = taxonomy_levels[15]

# supertree_toolkit is the backend for the STK. Loaded by both the GUI and
# CLI, this contains all the functions to actually *do* something
#
# All functions take XML and a list of other arguments, process the data and return
# it back to the user interface handler to save it somewhere




def create_taxonomy(XML, existing_taxonomy=None, pref_db=None, verbose=False, ignoreWarnings=False):
    """Generates a taxonomy of the data from EoL data. This is stored as a
    dictionary of taxonomy for each taxon in the dataset. Missing data are
    encoded as '' (blank string). It's up to the calling function to store this
    data to file or display it."""
    
    if not ignoreWarnings:
        check_data(XML)

    if (existing_taxonomy is None):
        taxonomy = {}
    else:
        taxonomy = existing_taxonomy
    taxa = get_all_taxa(XML, pretty=True)
    create_taxonomy_from_taxa(taxa, taxonomy)
    return taxonomy


def safe_taxonomic_reduction(XML, matrix=None, taxa=None, verbose=False, queue=None, ignoreWarnings=False):
    """ Perform STR on data to remove taxa that 
    provide no useful additional information. Based on PerEQ (Jeffery and Wilkson, unpublished).
    """

    if not ignoreWarnings and not XML == None:
        check_data(XML)

    # Algorithm descibed by Jeffery and Wilkson, unpublshed. 
    # Obtained original from http://www.uni-oldenburg.de/en/biology/systematics-and-evolutionary-biology/programs/
    # and modified for *supertrees*, which mainly involves cutting
    # out stuff to do with multiple state characters as we only have binary characters.

    missing_char = "?"
    TotalInvalid = 0

    if (not matrix==None):
        if (taxa == None):
            raise excp.InvalidSTKData("If you supply a matrix to STR, you also need to supply taxa")
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
            submatrix, tree_taxa = stk_internals._assemble_tree_matrix(trees[key])
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

    output_string += indent.indent([labels]+output_data, hasHeader=True, prefix='| ', postfix=' |')

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


def amalgamate_trees(XML,format="nexus",anonymous=False,ignoreWarnings=False):
    """ Create a string containing all trees in the XML.
        String can be formatted to one of Nexus, Newick or TNT.
        Only Nexus formatting takes into account the anonymous
        flag - the other two are anonymous anyway
        Any errors and None is returned - check for this as this is the 
        callers responsibility
    """

    if not ignoreWarnings:
        check_data(XML)

    # Check format flag - let the caller handle
    if (not (format == "nexus" or 
        format == "newick" or
        format == "tnt")):
            return None

    trees = obtain_trees(XML)

    return stk_internals._amalgamate_trees(trees,format,anonymous)
        
def get_taxa_from_tree_for_taxonomy(tree, pretty=False, ignoreErrors=False):
    """Returns a list of all taxa available for the tree passed as argument.
    :param tree: string with the data for the tree in Newick format.
    :type tree: string
    :param pretty: defines if '_' in taxa names should be replaced with spaces. 
    :type pretty: boolean
    :param ignoreErrors: should execution continue on error?
    :type ignoreErrors: boolean
    :returns: list of strings with the taxa names, sorted alphabetically
    :rtype: list
    """
    taxa_list = []

    try:
        taxa_list.extend(stk_internals._getTaxaFromNewick(tree))
    except excp.TreeParseError as detail:
        if (ignoreErrors):
            logging.warning(detail.msg)
            pass
        else:
            raise TreeParseError( detail.msg )

    # now uniquify the list of taxa
    taxa_list = stk_internals._uniquify(taxa_list)
    taxa_list.sort()

    if (pretty):
        taxa_list = [x.replace('_', ' ') for x in taxa_list]

    return taxa_list



def create_matrix(XML,format="hennig",quote=False,taxonomy=None,outgroups=False,ignoreWarnings=False, verbose=False):
    """ From all trees in the XML, create a matrix
    """

    if not ignoreWarnings:
        check_data(XML)

    weights = None

    # get all trees
    trees = obtain_trees(XML)
    if (not taxonomy == None):
        trees['taxonomy'] = taxonomy


    # return weights for each tree
    weights = get_weights(XML)
    # if all weights are 1, then just set back to None, so we don't add to matrix file
    w = weights.values()
    w = stk_internals._uniquify(w)
    if w == [1]:
        weights = None

    if (outgroups):
        outgroup_data = get_outgroup(XML)
        for t in trees:
            try:
                current_og = outgroup_data[t]
                # we need to delete any outgroups
                for o in current_og:
                    trees[t] = stk_internals._delete_taxon(o, trees[t])
            except KeyError:
                pass

    # and the taxa
    taxa = []
    for t in trees:
        taxa.extend(stk_internals._getTaxaFromNewick(trees[t]))
    taxa = stk_internals._uniquify(taxa)
    if (not taxonomy == None):
        taxa.extend(stk_internals._getTaxaFromNewick(taxonomy))
        taxa = stk_internals._uniquify(taxa)
        taxa.sort()
    taxa.insert(0,"MRP_Outgroup")
        
    return stk_internals._create_matrix(trees, taxa, format=format, quote=quote, weights=weights,verbose=verbose)


def create_matrix_from_trees(trees,format="hennig"):
    """ Given a dictionary of trees, create a matrix
    """

    taxa = []
    for t in trees:
        tree = stk_internals._parse_tree(trees[t])
        terminals = tree.getAllLeafNames(tree.root)
        for term in terminals:
            taxa.append(str(term))
    
    taxa = stk_internals._uniquify(taxa)

    return stk_internals._create_matrix(trees, taxa, format=format)



def substitute_taxa(XML, old_taxa, new_taxa=None, only_existing=False, ignoreWarnings=False, verbose=False, skip_existing=False, generic_match=False):
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
        check_data(XML)

    
    old_taxa, new_taxa = _sort_sub_taxa(old_taxa,new_taxa)

    # Sort incoming taxa
    if (only_existing):
        existing_taxa = get_all_taxa(XML)
        new_taxa = _sub_deal_with_existing_only(existing_taxa,old_taxa, new_taxa, generic_match)

    # need to check for uniquessness of souce names - error is not unique
    check_uniqueness(XML)

    # grab all trees and store as bio.phylo.tree objects
    trees = obtain_trees(XML)

    for name in trees.iterkeys():
        tree = trees[name]
        new_tree = _sub_taxa_in_tree(tree,old_taxa,new_taxa,skip_existing=skip_existing)
        XML = stk_internals._swap_tree_in_XML(XML,new_tree,name)
 
    # now loop over all taxon elements in the XML, and 
    # remove/sub as necessary
    i = 0
    xml_root = stk_internals._parse_xml(XML)
    xml_taxa = []
    xml_outgroup = []
    # grab all taxon elements and store
    # We're going to delete and we can't do that whilst
    # iterating over the XML. There lies chaos.
    for ele in xml_root.iter():
        if (ele.tag == "taxon"):
            xml_taxa.append(ele)
        if (ele.tag == "outgroup"):
            xml_outgroup.append(ele)
   
    i = 0
    for taxon in old_taxa:
        if (new_taxa == None or new_taxa[i] == None):
            # need to search for elements that have the right name and delete them
            for ele in xml_taxa:
                if (ele.attrib['name'] == taxon):
                    # You remove the element by getting the 
                    # deleting it from the parent
                    ele.getparent().remove(ele)
            for ele in xml_outgroup:
                if (taxon in ele.xpath("string_value")[0].text):
                    outgroup = ele.xpath("string_value")[0].text
                    outgroup_lines = [s.strip() for s in outgroup.splitlines()]
                    outgroup_taxa = []
                    for line in outgroup_lines:
                        outgroup_taxa.extend(line.split(","))
                    new_outgroup_taxa = []
                    for t in outgroup_taxa:
                        if not t == taxon:
                            new_outgroup_taxa.append(t)
                    if (len(new_outgroup_taxa) == 0):
                        ele.getparent().remove(ele)
                    else:
                        ele.xpath("string_value")[0].text = ",".join(new_outgroup_taxa)
        else:
            for ele in xml_taxa:
                new_taxa_info = []
                if (ele.attrib['name'] == taxon):
                    nt = new_taxa[i].split(",") # incoming polytomy, maybe
                    new_taxa_info.extend(nt)
                    if (len(new_taxa_info) == 1):
                        # straight swap
                        ele.attrib['name'] = new_taxa_info[0]
                    else:
                        # we need to construct multiple taxa blocks!
                        taxa_parent = ele.getparent()
                        original_ele = deepcopy(ele)
                        ele.getparent().remove(ele)
                        for nt in new_taxa_info:
                            temp_ele = deepcopy(original_ele)
                            temp_ele.attrib['name'] = nt
                            # add comment re: this was originally
                            comment = etree.SubElement(temp_ele,"comment")
                            comment.text = "Was originally "+taxon+" and was subbed"
                            taxa_parent.append(temp_ele)

            for ele in xml_outgroup:
                if (taxon in ele.xpath("string_value")[0].text):
                    outgroup = ele.xpath("string_value")[0].text
                    outgroup_lines = [s.strip() for s in outgroup.splitlines()]
                    outgroup_taxa = []
                    for line in outgroup_lines:
                        outgroup_taxa.extend(line.split(","))
                    new_outgroup_taxa = []
                    for t in outgroup_taxa:
                        if t == taxon:
                            nt = new_taxa[i].split(",") # incoming polytomy, maybe
                            new_outgroup_taxa.extend(nt)
                        else:
                            new_outgroup_taxa.append(t)
                    ele.xpath("string_value")[0].text = ",".join(new_outgroup_taxa)

        i = i+1

    return etree.tostring(xml_root,pretty_print=True)


def substitute_taxa_in_trees(trees, old_taxa, new_taxa=None, only_existing = False, ignoreWarnings=False, verbose=False,generic_match=False):
    """
    Swap the taxa in the old_taxa array for the ones in the
    new_taxa array
    
    If the new_taxa array is missing, simply delete the old_taxa

    only_existing will ensure only taxa in the dataset are subbed in.

    Returns a new list of trees with the taxa swapped from each tree 
    It's up to the calling function to
    do something sensible with this infomation
    """

    old_taxa, new_taxa = _sort_sub_taxa(old_taxa,new_taxa)

    # Sort incoming taxa
    if (only_existing):
        existing_taxa = []
        for tree in trees:
            existing_taxa.extend(stk_internals._getTaxaFromNewick(tree))
        existing_taxa = stk_internals._uniquify(existing_taxa)
        new_taxa = _sub_deal_with_existing_only(existing_taxa,old_taxa, new_taxa, generic_match)
    
    new_trees = []
    for tree in trees:
        new_trees.append(_sub_taxa_in_tree(tree,old_taxa,new_taxa))
 
    return new_trees





def data_summary(XML,detailed=False,ignoreWarnings=False):
    """Creates a text string that summarises the current data set via a number of 
    statistics such as the number of character types, distribution of years of publication,
    etc.

    Up to the calling function to display string nicely
    """

    if not ignoreWarnings:
        check_data(XML)

    xml_root = stk_internals._parse_xml(XML)
    proj_name = get_project_name(XML)

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


def taxonomic_checker_tree(tree_file,existing_data=None,verbose=False):
    """ For each name in the database generate a database of the original name,
    possible synonyms and if the taxon is not know, signal that. We do this by
    using the EoL API to grab synonyms of each taxon.  """

    tree = import_tree(tree_file)
    p4tree = stk_internals._parse_tree(tree) 
    taxa = p4tree.getAllLeafNames(p4tree.root) 
    if existing_data == None:
        equivalents = {}
    else:
        equivalents = existing_data

    equivalents = taxonomic_checker_list(taxa,existing_data,verbose)
    return equivalents

def taxonomic_checker(XML,existing_data=None,verbose=False):
    """ For each name in the database generate a database of the original name,
    possible synonyms and if the taxon is not know, signal that. We do this by
    using the EoL API to grab synonyms of each taxon.  """

    # grab all taxa
    taxa = get_all_taxa(XML)

    if existing_data == None:
        equivalents = {}
    else:
        equivalents = existing_data

    equivalents = taxonomic_checker_list(taxa,existing_data,verbose)
    return equivalents


def load_equivalents(equiv_csv):
    """Load equivalents data from a csv and convert to a equivalents Dict.
        Structure is key, with a list that is array of synonyms, followed by status ('green',
        'yellow' or 'red').
    """

    import csv

    equivalents = {}

    with open(equiv_csv, 'rU') as csvfile:
        equiv_reader = csv.reader(csvfile, delimiter=',')
        equiv_reader.next() # skip header
        for row in equiv_reader:
            i = 1
            equivalents[row[0]] = [row[1].split(';'),row[2]]
    
    return equivalents

def generate_species_level_data(XML, taxonomy, ignoreWarnings=False, verbose=False):
    """ Based on a taxonomy data set, amend the data to be at species level as
    far as possible.  This function creates an internal 'subs file' and calls
    the standard substitution functions.  The internal subs are generated by
    looping over the taxa and if not at species-level, working out which level
    they are at and then adding species already in the dataset to replace it
    via a polytomy. This has to be done in one step to avoid adding spurious
    structure to the phylogenies """

    if not ignoreWarnings:
        check_data(XML)

    # if taxonomic checker not done, warn
    if (not taxonomy):
        raise NoneCompleteTaxonomy("Taxonomy is empty. Create a taxonomy first. You'll probably need to hand edit the file to complete")
        return

    # if missing data in taxonomy, warn
    taxa = get_all_taxa(XML)
    keys = taxonomy.keys()
    if (not ignoreWarnings):
        for t in taxa:
            t = t.replace("_"," ")
            if not t in keys:
                # This idea here is that the caller will catch this, then re-run with ignoreWarnings set to True
                raise NoneCompleteTaxonomy("Taxonomy is not complete. I will soldier on anyway, but this might not work as intended")

    # get all taxa - see above!
    # for each taxa, if not at species level
    new_taxa = []
    old_taxa = []
    for t in taxa:
        subs = []
        t = t.replace("_"," ")
        if (not SPECIES in taxonomy[t]): # the current taxon is not a species, but higher level taxon
            # work out which level - should we encode this in the data to start with?
            for tl in taxonomy_levels:
                try:
                    tax_data = taxonomy[t][tl]
                except KeyError:
                    continue
                if (t == taxonomy[t][tl]):
                    current_level = tl
                    # find all species in the taxonomy that match this level
                    for taxon in taxa:
                        taxon = taxon.replace("_"," ")
                        if (SPECIES in taxonomy[taxon]):
                            try:
                                if taxonomy[taxon][current_level] == t: # our current taxon
                                    subs.append(taxon.replace(" ","_"))
                            except KeyError:
                                continue

        # create the sub
        if len(subs) > 0:
            old_taxa.append(t.replace(" ","_"))
            new_taxa.append(','.join(subs))

    # call the sub
    new_XML = substitute_taxa(XML, old_taxa, new_taxa, verbose=verbose)
    new_XML = clean_data(new_XML)
    
    return new_XML

def data_overlap(XML, overlap_amount=2, filename=None, detailed=False, show=False, verbose=False, ignoreWarnings=False):
    """ Calculate the amount of taxonomic overlap between source trees.
    The output is a True/False by default, but you can specify an 
    optional filename, which will save a nice graphic. For the GUI,
    the output can also be a PNG graphic to display (and then save).

    If filename is None, no graphic is generated. Otherwise a simple
    graphic is generated showing the number of cluster. If detailed is set to
    true, a graphic is generated showing *all* trees. For data containing >200
    source trees this could be very big and take along time. More likely, you'll run
    out of memory.
    """
    import matplotlib
    if (sys.platform == "darwin"):
        matplotlib.use('GTKAgg')
    import pylab as plt
    from matplotlib.ticker import MaxNLocator
    from matplotlib import backends
    
    if not ignoreWarnings:
        check_data(XML)

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
        taxa_list_i = stk_internals._getTaxaFromNewick(trees[tree_keys[i]])
        taxa_set = set(taxa_list_i)

        # loop over tree i+1 to end (j=i+1,N)
        for j in range(i+1,nTrees):
            matches = 0
            # grab the taxa from tree j
            taxa_list_j = stk_internals._getTaxaFromNewick(trees[tree_keys[j]])

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
    if isinstance(connected_components, types.GeneratorType):
        connected_components = list(connected_components)
    if len(connected_components) == 1:
        sufficient_overlap = True

    # The above list actually contains which components are seperate from each other
    key_list = connected_components

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
            if isinstance(Hs, types.GeneratorType):
                Hs = list(Hs)
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

    return sufficient_overlap, list(key_list)

def data_independence(XML,make_new_xml=False,ignoreWarnings=False):
    """ Return a list of sources that are not independent.
    This is decided on the source data and the characters.
    """

    if not ignoreWarnings:
        check_data(XML)

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
    subsets = []
    identical = []
    is_identical = False
    for data in data_ind:
        name = data[0]
        char = data[1]
        taxa = data[2]
        if (char == prev_char):
            # when sorted, the longer list comes first
            if set(taxa).issubset(set(prev_taxa)):
                if (taxa == prev_taxa):
                    if (is_identical):
                        identical[-1].append(name)
                    else:
                        identical.append([name,prev_name])
                        is_identical = True

                else:
                    subsets.append([prev_name, name])
                    prev_name = name
                    is_identical = False
            else:
                prev_name = name
                is_identical = False
        else:
            prev_name = name
            is_identical = False
            
        prev_char = char
        prev_taxa = taxa
        
    if (make_new_xml):
        new_xml = XML
        # deal with subsets
        for s in subsets:
            new_xml = stk_internals._swap_tree_in_XML(new_xml,None,s[1]) 
        new_xml = clean_data(new_xml)
        # deal with identical - weight them, if there's 3, weights are 0.3, i.e. 
        # weights are 1/no of identical trees
        for i in identical:
            weight = 1.0 / float(len(i))
            new_xml = add_weights(new_xml, i, weight)

        return identical, subsets, new_xml
    else:
        return identical, subsets


def add_historical_event(XML, event_description):
    """
    Add a historial_event element to the XML. 
    The element contains a description of the event and the the current
    date will ba added
    """

    now  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    xml_root = stk_internals._parse_xml(XML)

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

def clean_data(XML):
    """ Cleans up (i.e. deletes) non-informative trees and empty sources
        Same function as check data, but instead of raising message, simply fixes the problems.
    """

    # check all names are unique - this is easy...
    try:
        check_uniqueness(XML) # this will raise an error is the test is not passed
    except excp.NotUniqueError:
        XML = set_unique_names(XML)

    # now the taxa
    XML = stk_internals._check_taxa(XML,delete=True) 

    # check trees are informative
    XML = stk_internals._check_informative_trees(XML,delete=True)

    
    # check sources
    XML = stk_internals._check_sources(XML,delete=True)
    XML = all_sourcenames(XML)
    
    # fix tree names
    XML = set_unique_names(XML)
    XML = set_all_tree_names(XML,overwrite=True)
    

    # unpermutable trees
    permutable_trees = stk_internals._find_trees_for_permuting(XML)
    all_trees = obtain_trees(XML)
    for t in permutable_trees:
        new_tree = permutable_trees[t]
        for i in range(10): # do at most 10 iterations
            new_tree = stk_internals._collapse_nodes(new_tree)
        
        if (not stk_internals._trees_equal(new_tree,permutable_trees[t])):
           XML = stk_internals._swap_tree_in_XML(XML,new_tree,t) 

    XML = stk_internals._check_informative_trees(XML,delete=True)

    return XML



def replace_genera(XML,dry_run=False,ignoreWarnings=False):
    """ Remove all generic taxa by replacing them with a polytomy of
        all species in the dataset belonging to that genera
    """
        
    if not ignoreWarnings:
        check_data(XML)

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
        check_data(XML)

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
    xml_root = stk_internals._parse_xml(XML)
    orig_xml_root = stk_internals._parse_xml(original_XML)

    # remove sources
    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)
    for s in sources:
        s.getparent().remove(s)

    # edit name (append _subset)
    proj_name = get_project_name(XML)
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
                        if (stk_internals._tree_contains(taxon,treestring)):
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


def tree_from_taxonomy(top_level, tree_taxonomy):
    """ Create a tree from a taxonomy hash. Supply the starting level (e.g. Order) and the taxonomy.
        Will only work if most of the taxonomic information is filled in, but will search 2 levels up to complete 
        the taxonomy if required
        Returns: tree string
    """
    from ete2 import Tree
    
    start_level = taxonomy_levels.index(top_level)
    new_taxa = tree_taxonomy.keys()

    tl_types = []
    for tt in tree_taxonomy:
        tl_types.append(tree_taxonomy[tt][top_level])

    tl_types = stk_internals._uniquify(tl_types)
    levels_to_worry_about = taxonomy_levels[0:taxonomy_levels.index(top_level)+1]
        
    t = Tree()
    nodes = {}
    nodes[top_level] = []
    for tl in tl_types:
        n = t.add_child(name=tl)
        nodes[top_level].append({tl:n})

    for l in levels_to_worry_about[-2::-1]:
        names = []
        nodes[l] = []
        ci = levels_to_worry_about.index(l)
        for tt in tree_taxonomy:
            try:
                names.append(tree_taxonomy[tt][l])
            except KeyError:
                pass
        names = stk_internals._uniquify(names)
        for n in names:
            # find my parent
            parent = None
            for tt in tree_taxonomy:
                try:
                    if tree_taxonomy[tt][l] == n:
                        for jj in range(1,len(taxonomy_levels)-ci+1): # rest of taxonomy levels available
                            try:
                                parent = tree_taxonomy[tt][levels_to_worry_about[ci+jj]]
                                level = ci+jj
                                break # break the loop and jj get fixed < len(taxonomy_levels)-ci+1
                            
                            except KeyError: # this will loop until we find something
                                pass
                       
                            if jj == len(taxonomy_levels)-ci+1: # we completed the loop and found nothing!
                                print "ERROR: tried to find some taxonomic info for "+tt+" from tree_taxonomy file/downloaded data."
                                print "I went a few levels up, but failed find any info."
                                print "This is the taxonomy info I have for "+tt
                                print tree_taxonomy[tt]
                                sys.exit(1)

                        k = []
                        for nd in nodes[levels_to_worry_about[level]]:
                            k.extend(nd.keys())
                        i = 0
                        for kk in k:
                            if kk == parent:
                                break
                            i += 1
                        parent_id = i
                        break
                except KeyError:
                    pass # no data at this level for this beastie
            # find out where to attach it
            node_id = nodes[levels_to_worry_about[level]][parent_id][parent]
            nd = node_id.add_child(name=n.replace(" ","_"))
            nodes[l].append({n:nd})

    tree = t.write(format=9)  
    tree = stk_internals._collapse_nodes(tree)
    tree = stk_internals._collapse_nodes(tree)
    tree = stk_internals._collapse_nodes(tree)
    

    
    return tree


def already_in_data(new_source,sources):
    """
    Is the new source already in the dataset?

    Determine this by searching for the paper title.

    Returns the source which matches the new one and True if a match is found
    or None, False if not.
    """

    find = etree.XPath('//title/string_value')
    new_source_title = find(new_source)[0].text
    current_sources = find(sources)
    for title in current_sources:
        t = title.text
        if t == new_source_title:
            return title.getparent().getparent().getparent().getparent(), True

    return None, False

def check_data(XML):
    """ Function to check various aspects of the dataset, including:
         - checking taxa in the XML for a source are included in the tree for that source
         - checking all source names are unique
    """

    # check all names are unique - this is easy...
    check_uniqueness(XML) # this will raise an error is the test is not passed

    # now the taxa
    _check_taxa(XML) # again will raise an error if test fails

    # check trees are informative
    _check_informative_trees(XML)

    # check sources
    _check_sources(XML,delete=False)

    return

def _create_matrix(trees, taxa, format="hennig", quote=False, weights=None, verbose=False):
    """
    Does the hard work on creating a matrix
    """

    # our matrix, we'll then append the submatrix
    # to this to make a 2D matrix
    # Our matrix is of length nTaxa on the i dimension
    # and nCharacters in the j direction
    matrix = []
    charsets = []
    if (weights == None):
        weights_per_char = None
    else:
        weights_per_char = []
    names = []
    current_char = 1
    for key in trees:
        if (not weights == None):
            weight = weights[key]
        names.append(key)
        submatrix, tree_taxa = _assemble_tree_matrix(trees[key], verbose=verbose)
        nChars = len(submatrix[0,:])
        # loop over characters in the submatrix
        for i in range(1,nChars):
            if (not weights == None):
                weights_per_char.append(weight)
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

    return _create_matrix_string(matrix,taxa,charsets=charsets,names=names,
                                 format=format,quote=quote,weights=weights_per_char)


def _create_matrix_string(matrix,taxa,charsets=None,names=None,
                          format='hennig',quote=False,weights=None):
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
            
        matrix_string += "\n"
        if (not weights == None):
            # get unique weights
            unique_weights = _uniquify(weights)
            for uw in unique_weights:
                # The float for the weight cannot start with 0, even if it's 0.5
                # so we strip of the 0 to make .5 instead (lstrip). TNT is weird with formats...
                # We also strip off trailing zeros for neatness (rstrip)
                matrix_string += "ccode +[/"+("%.3f"%uw).lstrip('0').rstrip('0')
                i = 0
                for w in weights:
                    if (w == uw):
                        matrix_string += " " + str(i)
                    i += 1
                matrix_string += ";\n"
        matrix_string += "proc /;"
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




def import_bibliography(XML, bibfile, skip=False):
    """
    Create a bunch of sources from a bibtex file. This includes setting the sourcenames 
    for each source.
    """
    
    # Our bibliography parser
    b = biblist.BibList()

    xml_root = stk_internals._parse_xml(XML)
    
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
            publication = stk_internals._parse_xml(xml_snippet)
            # create top of source
            source = etree.Element("source")
            # now attach our publication
            source.append(publication)
            new_source = single_sourcename(etree.tostring(source,pretty_print=True))
            source = stk_internals._parse_xml(new_source)
            
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
            # rather than remaining blank (and hence blue in the interface)

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
    xml_root = stk_internals._sort_data(xml_root)
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
   
    xml_root = stk_internals._parse_xml(XML)    
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


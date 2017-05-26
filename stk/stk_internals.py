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
from lxml import etree
import unicodedata
import stk.p4 as p4
import re

""" This file contains the internal functionality of the STK
"""

replacements =     {
    u"\u00C6": u"AE", # LATIN CAPITAL LETTER AE
    u"\u00D0": u"D",  # LATIN CAPITAL LETTER ETH
    u"\u00D8": u"OE", # LATIN CAPITAL LETTER O WITH STROKE
    u"\u00DE": u"Th", # LATIN CAPITAL LETTER THORN
    u"\u00DF": u"ss", # LATIN SMALL LETTER SHARP S
    u"\u00E6": u"ae", # LATIN SMALL LETTER AE
    u"\u00F0": u"d",  # LATIN SMALL LETTER ETH
    u"\u00F8": u"oe", # LATIN SMALL LETTER O WITH STROKE
    u"\u00FE": u"th", # LATIN SMALL LETTER THORN
    u"\u2010": "-",
    u"\u2011": "-",
    u"\u2012": "-",
    u"\u2013": "-",
    u"\u2014": "-",
    u"\u2015": "-",
    u"\u2212": "-",
    u"\u2018": "'", # single quotes
    u"\u2019": "'",
    u"\u201A": "'",
    u"\u201B": "'",
    u"\u201C": '"', # double quotes
    u"\u201D": '"',
    u"\u201E": '"',
    u"\u201F": '"',
    }

def replace_utf(content):

    for c in replacements:
        content = content.replace(c,replacements[c])

    return content

def internet_on(host="8.8.8.8", port=443, timeout=5):
    import socket

    """
      Host: 8.8.8.8 (google-public-dns-a.google.com)
      OpenPort: 53/tcp
      Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        print ex.message
        return False   

def _uniquify(l):
    """
    Make a list, l, contain only unique data
    """
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()


def _assemble_tree_matrix(tree_string, verbose=False):
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
    if verbose:
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
    try:
        tree = _parse_tree(tree) 
    except excp.TreeParseError:
        return False
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
    new_taxa = [s.strip() for s in new_taxon.split(",")]
    new_taxon = ",".join(new_taxa)
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
    if (len(new_taxa) > 1):
        new_taxon = "("+new_taxon+")"

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
                raise excp.InvalidSTKData("Tried to find "+old_taxon+" in "+modified_tree+" and failed")

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
    try:
        tree = _parse_tree(modified_tree,fixDuplicateTaxa=True)
    except excp.TreeParseError:
        tree = ""
        return tree
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

    try:
        taxa = _getTaxaFromNewick(tree)
    except excp.TreeParseError:
        return tree

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
    # loop through all sources
    for s in sources:
        # for each source, get source name
        s_name = s.attrib['name']
        if source_name == s_name:
            # found the bugger!
            for t in s.xpath("source_tree"):
                tree_name = t.attrib['name']
                if (tree_name == name):
                    if (not tree == None): 
                        t.xpath("tree/tree_string/string_value")[0].text = tree
                        # We can return as we're only replacing one tree
                        return etree.tostring(xml_root,pretty_print=True)
                    else:
                        s.remove(t)
                        if (delete):
                            # we now need to check the source to check if there are
                            # any trees in this source now, if not, remove
                            if (len(s.xpath("source_tree")) == 0):
                                s.getparent().remove(s)
                        return etree.tostring(xml_root,pretty_print=True)

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
        raise excp.InvalidSTKData("Error parsing the data to check taxa")
    
    message = ""

    # for each source
    for s in sources:
        # get a list of taxa in the XML
        this_source = _parse_xml(etree.tostring(s))
        trees = obtain_trees(etree.tostring(this_source))
        s_name = s.attrib['name']
        taxa_ele = []
        for name in trees.iterkeys():
            tree_no = 1
            for t in s.xpath("source_tree"):
                try:
                    t_name = t.attrib['name']
                except KeyError:
                    message = message + "Tree in "+s_name+" is not named. Run the name_trees function"+"\n"
                    continue
                if (t_name == name):
                    find = etree.XPath(".//taxon")
                    taxa_ele = find(t)

            tree = trees[name]
            # are the XML taxa in the tree?
            for t in taxa_ele:
                xml_taxon = t.attrib['name']
                if (tree.find(xml_taxon) == -1):
                    if (delete):
                        # remove
                        t.getparent().remove(t)
                    else:
                        # no - raise an error!
                        message = message + "Taxon: "+xml_taxon+" is not in the tree "+name+"\n"
    if not delete:               
        if (not message==""):
            raise excp.InvalidSTKData(message)
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
        raise excp.InvalidSTKData("Error parsing the data to check source")
            
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
            raise excp.InvalidSTKData(message)
        else:
            return
    else:
        return etree.tostring(xml_root,pretty_print=True)        



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
        raise excp.InvalidSTKData("Error parsing the data to check trees")
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
            raise excp.UninformativeTreeError(message)
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
        raise excp.TreeParseError("Error parsing tree\n"+detail.msg+"\n"+tree_block[0:128] )
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
        raise excp.TreeParseError("Error parsing tree\n"+detail.msg+"\n"+tree[0:128] )

    t = p4.var.trees[0]
    p4.var.trees = []
    return t


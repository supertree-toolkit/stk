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
#    Jon Hill. jon.hill@york.ac.uk
"""stk_trees

This module contains the tree-processing and altering functions in the STK.
Most of these are not user-facing unless they are writing their own scripts.
The functions are generally called by the main supertree_toolkit functions and
require a tree_string as input (this is a Newick string) as input, plus
whatever else. Some funcitons require a list of such objects.

Similar returns are typically a tree_string or list of these.

"""


import stk.p4 as p4
import re
import stk_exceptions as excp
import stk_internals
from cStringIO import StringIO
import string
import stk.p4.MRP as MRP
import numpy
import csv
import sys
sys.setrecursionlimit(50000)


def get_taxa(tree):
    """ Get the terminal nodes from a Newick string"""

    t_obj = parse_tree(tree)
    terminals = t_obj.getAllLeafNames(0)
    taxa = []
    for t in terminals:
        taxa.append(t.replace(" ","_"))

    return taxa


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
    content = str(stk_internals.replace_utf(content))
    
    # Need to add checks on the file. Problems include:
    # TNT: outputs Phyllip format or something - basically a Newick
    # string without commas, so add 'em back in
    m = re.search(r'proc.;', content)
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
    trees = parse_trees(treedata)
    r_trees = []
    for t in trees:
        tree = correctly_quote_taxa(t.writeNewick(fName=None,toString=True).strip())
        r_trees.append(tree)

    return r_trees


def import_tree(filename, gui=False, tree_no = -1):
    """Takes a NEXUS formatted file and returns a list containing the tree
    strings"""
    
  
    trees = import_trees(filename)
    if (len(trees) == 1):
        tree_no = 0

    if (len(trees) > 1 and tree_no == -1):
        message = "Found "+str(len(trees))+" trees. Which one do you want to load (1-"+str(len(trees))+")?"
        if (not gui):
            tree_no = int(raw_input(message))
            # assume the user counts from 1 to n
            tree_no -= 1
        else:
            # Not super keen on this approach, but hey, you do better :p
            import gtk
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
            #responseToDialog = 0
            #entry.connect("activate", responseToDialog, dialog, gtk.RESPONSE_OK)
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


def trees_equal(t1,t2):
    """ compare two trees using Robinson-Foulds metric
    """

    tree_1 = parse_tree(t1)
    tree_2 = parse_tree(t2)
    
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


def assemble_tree_matrix(tree_string, verbose=False):
    """ Assembles the MRP matrix for an individual tree

        returns: matrix (2D numpy array: taxa on i, nodes on j)
                 taxa list: in same order as in the matrix
    """

    tree = parse_tree(tree_string)
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
    except p4.Glitch as e:
        names = get_taxa(tree_string)
        adjmat = []
        for i in range(0,len(names)):
            adjmat.append([1])
        adjmat = numpy.array(adjmat)
    if verbose:
        #TODO: This need making an exception to allow the user of this function to warn appropriately
        print "Warning: Found uninformative tree in data. Including it in the matrix anyway"

    return adjmat, names


def permute_tree(tree,matrix="hennig",treefile=None,verbose=False):
    """ Permute a tree where there is uncertianty in taxa location.
    Output either a tree file or matrix file of all possible 
    permutations.

    Note this is a recursive algorithm.
    """

    # check format strings

    permuted_trees = {} # The output of the recursive permute algorithm
    output_string = "" # what we pass back
    tree = correctly_quote_taxa(tree)

    # first thing is to get hold of the unique taxa names
    # i.e. without % on them
    tree = re.sub(r"'(?P<taxon>[a-zA-Z0-9_\+\=\.\? ]*) (?P<taxon2>[a-zA-Z0-9_\+\=\.\? %]*)'","\g<taxon>_\g<taxon2>",tree)

    all_taxa = get_taxa(tree)

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
    names_d_unique = stk_internals.uniquify(names_d)
    names_unique = stk_internals.uniquify(names)
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
                    taxa = get_taxa(tree)
                    # iterate over nodes
                    for name in taxa:
                        index = name.find('%')
                        short_name = name[0:index]
                        current_unique_name = names_unique[n]
                        current_unique_name = current_unique_name.replace(' ','_')
                        if ( index > 0 and short_name == current_unique_name ):
                            if ( not name == current_unique_name + "%" + str(i) ):
                                tempTree = delete_taxon(name, tempTree)
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
            if (trees_equal(trees_saved[i],trees_saved[j])):
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
        output_string = create_matrix_from_trees(permuted_trees,taxa,format=matrix)
    else:
        output_string = amalgamate_trees(permuted_trees,format=treefile) 

    # Either way we output a string that the caller can save or display or pass to tnt, or burn;
    # it's up to them, really.
    return output_string


def delete_taxon(taxon, tree):
    """ Delete a taxon from a tree string
    """

    taxon = taxon.replace(" ","_")
    taxon = taxon.replace("'","")
    # check if taxa is in there first
    if (tree.find(taxon) == -1): # should find, even if non-monophyletic
        return tree #raise exception?

    # Remove all the empty nodes we left laying around
    tree_obj = parse_tree(tree)    
    tree_obj.getPreAndPostOrderAboveRoot()
    for n in tree_obj.iterPostOrder():
        if n.getNChildren() == 1 and n.isLeaf == 0:
            tree_obj.collapseNode(n)

    for node in tree_obj.iterNodes():
        if node.name == taxon or (not node.name == None and node.name.startswith(taxon+"%")):
            tree_obj.removeNode(node.nodeNum,alsoRemoveBiRoot=False)
            break

    return tree_obj.writeNewick(fName=None,toString=True).strip()


def sub_taxon(old_taxon, new_taxon, tree, skip_existing=False):
    """ Simple, sorry, that should be "simple", swap of taxa
    """

    taxa_in_tree = get_taxa(tree)
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
    taxa = stk_internals.uniquify(taxa)
 
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
    # taxa. We can then just swap taxa in plain text.
    # When done, p4 can fix duplicated taxa by adding back on _\d
    # Then we collapse the nodes, taking into account duplicated taxa
    # This will need several iterations.

    modified_tree = re.sub(r"(?P<taxon>[a-zA-Z0-9_\+\= ]*)%[0-9]+",'\g<taxon>',tree)
    new_taxon = ",".join(new_taxa)
    if (len(new_taxa) > 1):
        new_taxon = "("+new_taxon+")"

    if (len(new_taxon) == 0):
        # we need to delete instead
        return delete_taxon(old_taxon,tree)

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
        new_tree = collapse_nodes(new_tree)

    return new_tree


def tree_contains(taxon,tree):
    """ Returns if a taxon is contained in the tree
    """

    taxon = taxon.replace(" ","_")
    try:
        tree = parse_tree(tree) 
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

def collapse_nodes(in_tree):
    """ Collapses nodes where the siblings are actually the same
        taxon, denoted by taxon1, taxon2, etc
    """

    modified_tree = re.sub(r"(?P<taxon>[a-zA-Z0-9_\+\= ]*)%[0-9]+",'\g<taxon>',in_tree)  
    try:
        tree = parse_tree(modified_tree,fixDuplicateTaxa=True)
    except excp.TreeParseError:
        tree = ""
        return tree
    taxa = tree.getAllLeafNames(0)
    
    for t in taxa:
        # we might have removed the current taxon in a previous loop
        try:
            siblings = get_all_siblings(tree.node(t))
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


def get_all_siblings(node):
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

def read_matrix(filename):
    """
    Read a Nexus or Hennig formatted matrix file. Returns the matrix and taxa.
    """
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




def parse_trees(tree_block):
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



def parse_tree(tree,fixDuplicateTaxa=False):
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



def sub_taxa_in_tree(tree,old_taxa,new_taxa=None,skip_existing=False):
    """Swap the taxa in the old_taxa array for the ones in the
    new_taxa array
    
    If the new_taxa array is missing, simply delete the old_taxa
    """
  
    tree = correctly_quote_taxa(tree)
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
        if (tree_contains(taxon,tree)):
            if (new_taxa == None or new_taxa[i] == None):
                p4tree = parse_tree(tree) 
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
                    tree = delete_taxon(taxon, tree)

            else:
                # we are substituting
                tree = sub_taxon(taxon, new_taxa[i], tree, skip_existing=skip_existing)
        i += 1

    tree = collapse_nodes(tree)
    tree = remove_single_poly_taxa(tree)

    return tree 



def correctly_quote_taxa(tree):
    """ In order for the subs to work, we need to only quote taxa that need it, as otherwise 
        we might have have the same taxon, e.g. 'Gallus gallus' and Gallus_gallus being
        considered as different
    """

    # get taxa from tree
    t_obj = parse_tree(tree)
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

def remove_single_poly_taxa(tree):
    """ Count the numbers after % in taxa names """

    try:
        taxa = get_taxa(tree)
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

############################## NOT TESTED ##################


def create_taxonomy_from_tree(tree, existing_taxonomy=None, pref_db=None, verbose=False, ignoreWarnings=False, fill=False):
    """ Generates the taxonomy from a tree. Uses a similar method to the XML version but works directly on a string with the tree.
    :param tree: list of the taxa.
    :type tree : list 
    :param existing_taxonomy: list of the taxa.
    :type existing_taxonomy: list 
    :param pref_db: Gives priority to database. Seems it is unused.
    :type pref_db: string 
    :param verbose: Flag for verbosity.
    :type verbose: boolean
    :param ignoreWarnings: Flag for exception processing.
    :type ignoreWarnings: boolean
    :returns: the modified taxonomy
    :rtype: dictionary
    """
    starttime = time.time()

    if(existing_taxonomy is None) :
        taxonomy = {}
    else :
        taxonomy = existing_taxonomy

    taxa = get_taxa_from_tree_for_taxonomy(tree, pretty=True)
    
    taxonomy = create_taxonomy_from_taxa(taxa, taxonomy)
    if fill:
        taxonomy = create_extended_taxonomy(taxonomy, starttime, verbose, ignoreWarnings, pref_db)
    
    return taxonomy


def create_matrix_from_trees(trees, taxa, format="hennig", quote=False, weights=None, verbose=False):
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
        submatrix, tree_taxa = assemble_tree_matrix(trees[key], verbose=verbose)
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
            unique_weights = stk_internals.uniquify(weights_per_char)
            for uw in unique_weights:
                # The float for the weight cannot start with 0, even if it's 0.5
                # so we strip of the 0 to make .5 instead (lstrip). TNT is weird with formats...
                # We also strip off trailing zeros for neatness (rstrip)
                matrix_string += "ccode +[/"+("%.3f"%uw).lstrip('0').rstrip('0')
                i = 0
                for w in weights_per_char:
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


    
def amalgamate_trees(trees,format,anonymous=False):
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


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

import csv
import stk_exceptions as excp


def get_mrca(tree,taxa_list):
    """Return the node number for the MRCA of the list of given taxa
       This node number must be used in conjection with a p4 tree object, along
       the lines of:
       treeobj = _parse_tree(tree_string)
       treeobj.node(mrca).parent 
    """

    # find MRCA of all taxa within this clade, already in the tree
    node_ids = []
    # get the nodes of the taxa in question
    node_id_for_taxa = []
    treeobj = stk_internals._parse_tree(tree)
    for t in taxa_list:
        node_id_for_taxa.append(treeobj.node(t).nodeNum)
    # for each, get all parents to root
    for n in node_id_for_taxa:
        nodes = []
        nodes.append(treeobj.node(n).parent.nodeNum)
        while 1:
            nn = treeobj.node(nodes[-1]).parent
            if nn == None:
                break
            else:
                nodes.append(nn.nodeNum)
        node_ids.append(nodes)
    # in the shortest list, loop through the values, check they exist in all lists. If it does, 
    # that node is your MRCA
    big = sys.maxsize
    node_ids
    shortest = 0
    for n in node_ids:
        if len(n) < big:
            big = len(n)
            shortest = n
    mrca = -1
    for s in shortest:
        found = True
        for n in node_ids:
            if not s in n:
                found = False
                break # move to next s
        # if we get here, we have the MRCA
        if (found):
            mrca = s
            break
    if mrca == -1:
        # something went wrong!
        raise excp.InvalidSTKData("Error finding MRCA of: "+" ".join(taxa_list))

    return mrca

def load_subs_files(filename):
    """ Reads in a subs file and returns two arrays:
        new_taxa and the corresponding old_taxa

        None is used to indicated deleted taxa
    """

    try:
        f = open(filename,'r')
    except:
        raise excp.UnableToParseSubsFile("Unable to open subs file. Check your path")

    old_taxa = []
    new_taxa = []
    i = 0
    n_t = ""
    for line in f.readlines():
        if (re.search('\w+=\s+', line) != None or re.search('\s+=\w+', line) != None):
            # probable error
            raise excp.UnableToParseSubsFile("Your sub file contains '=' without spaces either side. If it's within a taxa, remove the spaces. If this is a sub, add spaces")
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
        raise excp.UnableToParseSubsFile("Output arrays are not same length. File incorrectly formatted")
    if (len(old_taxa) == 0):
        raise excp.UnableToParseSubsFile("No substitutions found! File incorrectly formatted")
 

    return old_taxa, new_taxa


def subs_from_csv(filename):
    """Create taxonomic subs from a CSV file, where
       the first column is the old taxon and all other columns are the
       new taxa to be subbed in-place
    """

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


def check_subs_additions(XML,new_taxa):
    """Check that if additional taxa are being added via a substitution and issues
       a warning if any of the incoming taxa
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
    unknown_taxa = stk_internals._uniquify(unknown_taxa)
    unknown_taxa.sort()

    if (len(unknown_taxa) > 0):
        taxa_list = '\n'.join(unknown_taxa)
        msg = "These taxa are not already in the dataset, are you sure you want to substitute them in?\n"
        msg += taxa_list
        raise excp.AddingTaxaWarning(msg) 
    
    return


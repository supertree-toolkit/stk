#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2015, Jon Hill, Katie Davis
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

import urllib2
from urllib import quote_plus
import simplejson as json
import argparse
import copy
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
import stk
import csv
from ete2 import Tree
import tempfile
import re

taxonomy_levels = stk.taxonomy_levels
tlevels = taxonomy_levels

def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="Fill tree in using taxonomy",
         description="Fills in the taxonomic gaps using polytomies within a tree to increase coverage",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            '-s', 
            '--skip', 
            action='store_true', 
            help="Skip online checking, just use taxonomy files",
            default=False
            )
    parser.add_argument(
            '--pref_db',
            help="Taxonomy database to use. Default is Species 2000/ITIS",
            choices=['itis', 'worms', 'ncbi', 'eol'],
            default = 'worms'
            )
    parser.add_argument(
            '--save_taxonomy',
            help="Save the taxonomy downloaded. Give a filename"
            )
    parser.add_argument(
            '--taxonomy_from_file',
            help='Use a downloaded taxonomy database from the chosen database, rather than online. Much quicker for large datasets. Give the filename',
            )
    parser.add_argument(
            '--tree_taxonomy',
            help="Supply a STK taxonomy file for taxa in the tree. If not, one will be created from the database being used here."
            )
    parser.add_argument(
            'top_level', 
            nargs=1,
            help="The top level group to look in, e.g. Arthropoda, Decapoda. Must match the database."
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your tree file"
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            nargs=1,
            help="Your new tree file"
            )

    args = parser.parse_args()
    verbose = args.verbose
    input_file = args.input_file[0]
    output_file = args.output_file[0]
    top_level = args.top_level[0]
    save_taxonomy_file = args.save_taxonomy
    tree_taxonomy = args.tree_taxonomy
    taxonomy = args.taxonomy_from_file
    pref_db = args.pref_db
    skip = args.skip
    if (save_taxonomy_file == None):
        save_taxonomy = False
    else:
        save_taxonomy = True
    load_tree_taxonomy = False
    if (not tree_taxonomy == None):
        tree_taxonomy_file = tree_taxonomy
        load_tree_taxonomy = True
    if skip:
        if taxonomy == None:
            print "Error: If you're skipping checking online, then you need to supply taxonomy files"
            return

    # grab taxa in tree
    tree = stk.import_tree(input_file)
    taxa_list = stk.get_taxa(tree)
    
    if verbose:
        print "Taxa count for input tree: ", len(taxa_list)

    # load in any taxonomy files - we still call the APIs as a) they may have updated data and
    # b) the user may have missed some first time round (i.e. expanded the tree and not redone 
    # the taxonomy
    if (taxonomy == None):
        taxonomy = {}
    else:
        taxonomy = stk.load_taxonomy(taxonomy)
        tree_taxonomy = {}    
        # this might also have tree_taxonomy in too - let's check this
        for t in taxa_list:
            if t in taxonomy:
                tree_taxonomy[t] = taxonomy[t]
            elif t.replace(" ","_") in taxonomy:
                tree_taxonomy[t] = taxonomy[t.replace(" ","_")]
       
    if (load_tree_taxonomy): # overwrite the good work above...
        tree_taxonomy = stk.load_taxonomy(tree_taxonomy_file)
    if (tree_taxonomy == None):
        tree_taxonomy = {}

    print "Taxa count in taxonomy: ", len(taxonomy)
    if verbose:
        print "Taxa in tree, but not in any taxonomy:"
    need_taxonomy = []
    for t in sorted(taxa_list):
        try:
            tree_taxonomy[t]
        except KeyError:
            need_taxonomy.append(t)
            if verbose:
                print "\t",t

    print "\tThat's",len(need_taxonomy),"missing"

    count = 0
    if verbose:
        print "\nTaxa in taxonomy but not in tree (i.e. will be added):"
    for t in sorted(taxonomy.keys()):
        if not t in taxa_list:
            if verbose:
                print "\t",t
            count += 1
    print "\tThat's",count,"to be added to tree. You should therefore have a total of:", count+len(taxa_list),"in your output tree"

    # we're going to add the taxa in the tree to the main taxonomy, to stop them
    # being fetched in first place. We delete them later
    # If you've loaded a taxonomy created by this script, this overwrites the tree taxa in the main taxonomy dict
    # Don't worry, we put them back in before saving again!
    for taxon in taxa_list:
        taxon = taxon.replace(' ','_')
        taxonomy[taxon] = {}

    # get taxonomy for species in tree we have no data for
    tree_taxonomy = stk.create_taxonomy_from_taxa(need_taxonomy,taxonomy=tree_taxonomy, pred_db=pref_db)
    if save_taxonomy:
        if (verbose):
            print "Saving tree taxonomy"
        # note -temporary save as we overwrite this file later.
        stk.save_taxonomy(tree_taxonomy,save_taxonomy_file+'_tree.csv')


    # Get all other taxa from the top_level down. THis can take a while and crash out
    # if the servers are slow, so use temp files to restart where we left off.
    if not skip:
        # create a temp file so we can checkpoint and continue
        if verbose:
            print "About to fetech all other taxa in",top_level,"- this might take a while..."
        tmpf, tmpfile = tempfile.mkstemp()
        if os.path.isfile('.fit_lock'):
            f = open('.fit_lock','r')
            tf = f.read()
            f.close()
            if os.path.isfile(tf.strip()):
                taxonomy = stk.load_taxonomy(tf.strip())
            os.remove('.fit_lock')
        # create lock file - if this is here, then we load from the file in the lock file (or try to) and continue
        # where we left off.
        with open(".fit_lock", 'w') as f:
            f.write(tmpfile)

        if (pref_db == 'itis'):
            if (verbose):
                print "Getting data from ITIS"
            # get taxonomy from itis
            # bit naughty with tmpfile - we're using the filename rather than handle to write to it. Have to for write_taxonomy function
            taxonomy, start_level = get_taxonomy_itis(taxonomy,top_level,verbose,tmpfile=tmpfile,skip=True) 
        elif (pref_db == 'worms'):
            if (verbose):
                print "Getting data from WoRMS"
            taxonomy, start_level = get_taxonomy_worms(taxonomy,top_level,verbose,tmpfile=tmpfile,skip=True)
        elif (pref_db == 'eol'):
            if (verbose):
                print "Getting data from EOL"
            taxonomy, start_level = get_taxonomy_eol(taxonomy,top_level,verbose,tmpfile=tmpfile,skip=True) # this skips ones already there
        elif (pref_db == 'ncbi'):
            # get taxonomy from ncbi
            print "Sorry, NCBI is not implemented yet"        
            pass
        else:
            print "ERROR: Didn't understand your database choice"
            sys.exit(-1)
        # clean up
        os.close(tmpf)
        os.remove('.fit_lock')
        try:
            os.remove('tmpfile')
        except OSError:
            pass

    # clean up taxonomy, deleting the ones already in the tree
    for taxon in taxa_list:
        taxon = taxon.replace(' ','_')
        try:
            del taxonomy[taxon]
        except KeyError:
            pass # if it's not there, so we care?

    # We now have 2 taxonomies:
    #  - for taxa in the tree
    #  - for all other taxa in the clade of interest

    if save_taxonomy:
        tot_taxonomy = taxonomy.copy()
        tot_taxonomy.update(tree_taxonomy)
        stk.save_taxonomy(tot_taxonomy,save_taxonomy_file)
    orig_taxa_list = taxa_list

    remove_higher_level = [] # for storing the higher level taxa in the original tree that need deleting
    generic = []
    # find all the generic and build an internal subs file
    for t in taxa_list:
        t = t.replace(" ","_")
        if t.find("_") == -1:
            # no underscore, so just generic
            generic.append(t)

    # step up the taxonomy levels from genus, adding taxa to the correct node
    # as a polytomy
    start_level = start_level.encode('utf-8').strip()
    if verbose:
        print "I think your start OTU is at: ", start_level
    for level in tlevels[1::]: # skip species....
        if verbose:
            print "Dealing with ",level
        new_taxa = []
        for t in taxonomy:
            # skip odd ones that should be in there
            if start_level in taxonomy[t] and taxonomy[t][start_level] == top_level:
                try:
                    new_taxa.append(taxonomy[t][level])
                except KeyError:
                    continue # don't have this info
        new_taxa = stk.uniquify(new_taxa)

        for nt in new_taxa:
            taxa_to_add = {}
            taxa_in_clade = []
            for t in taxonomy:
                if start_level in taxonomy[t] and taxonomy[t][start_level] == top_level:
                    try:
                        if taxonomy[t][level] == nt and not t in taxa_list:
                            taxa_to_add[t] = taxonomy[t]
                    except KeyError:
                        continue

            # add to tree
            for t in taxa_list:
                if level in tree_taxonomy[t] and tree_taxonomy[t][level] == nt:
                    taxa_in_clade.append(t)
                    if t in generic:
                        # we are appending taxa to this higher taxon, so we need to remove it
                        remove_higher_level.append(t)


            if len(taxa_in_clade) > 0 and len(taxa_to_add) > 0:
                tree = add_taxa(tree, taxa_to_add, taxa_in_clade,level)
                try:
                    taxa_list = stk.get_taxa(tree) 
                except stk.TreeParseError as e:
                    print taxa_to_add, taxa_in_clade, level, tree
                    print e.msg
                    return

                for t in taxa_to_add:
                    tree_taxonomy[t.replace(' ','_')] = taxa_to_add[t]
                    try:
                        del taxonomy[t.replace(' ','_')]
                    except KeyError:
                        # It might have _ or it might not...
                        del taxonomy[t]


    # remove singelton nodes
    tree = stk.collapse_nodes(tree) 
    tree = stk.collapse_nodes(tree) 
    tree = stk.collapse_nodes(tree) 
    
    #tree = stk.sub_taxa_in_tree(tree, remove_higher_level)
    trees = {}
    trees['tree_1'] = tree
    output = stk.amalgamate_trees(trees,format='nexus')
    f = open(output_file, "w")
    f.write(output)
    f.close()
    taxa_list = stk.get_taxa(tree)
    
    print "Final taxa count:", len(taxa_list)
 

def add_taxa(tree, new_taxa, taxa_in_clade, level):

    # create new tree of the new taxa
    additionalTaxa = stk.tree_from_taxonomy(level,new_taxa)

    # find mrca parent
    treeobj = stk.parse_tree(tree)
    mrca = stk.get_mrca(tree,taxa_in_clade)
    if (mrca == 0):
        # we need to make a new tree! The additional taxa are being placed at the root of the tree
        t = Tree()
        A = t.add_child()
        B = t.add_child()
        t1 = Tree(additionalTaxa)
        t2 = Tree(tree)
        A.add_child(t1)
        B.add_child(t2)
        return t.write(format=9)
    else:
        mrca = treeobj.nodes[mrca]
        additionalTaxa = stk.parse_tree(additionalTaxa)
        
        if len(taxa_in_clade) == 1:
            taxon = treeobj.node(taxa_in_clade[0])
            mrca = treeobj.addNodeBetweenNodes(taxon,mrca)


        # insert a node into the tree between the MRCA and it's parent (p4.addNodeBetweenNodes)
        # newNode = treeobj.addNodeBetweenNodes(mrca, mrca_parent)

        # add the new tree at the new node using p4.addSubTree(self, selfNode, theSubTree, subTreeTaxNames=None)
        treeobj.addSubTree(mrca, additionalTaxa, ignoreRootAssert=True)

    return treeobj.writeNewick(fName=None,toString=True).strip()



if __name__ == "__main__":
    main()




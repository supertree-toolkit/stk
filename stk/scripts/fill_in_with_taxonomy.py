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
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
import csv

# What we get from EOL
current_taxonomy_levels = ['species','genus','family','order','class','phylum','kingdom']
# And the extra ones from ITIS
extra_taxonomy_levels = ['superfamily','infraorder','suborder','superorder','subclass','subphylum','superphylum','infrakingdom','subkingdom']
# all of them in order
taxonomy_levels = ['species','subgenus','genus','subfamily','family','superfamily','subsection','section','infraorder','suborder','order','superorder','subclass','class','superclass','subphylum','phylum','superphylum','infrakingdom','subkingdom','kingdom']

def get_tree_taxa_taxonomy(taxon,wsdlObjectWoRMS):

    taxon_data = wsdlObjectWoRMS.getAphiaRecords(taxon.replace('_',' '))
    if taxon_data == None:
        return {}

    taxon_id = taxon_data[0]['valid_AphiaID'] # there might be records that aren't valid - they point to the valid one though
    # call it again via the ID this time to make sure we've got the right one.
    taxon_data = wsdlObjectWoRMS.getAphiaRecordByID(taxon_id)
    # add data to taxonomy dictionary
    # get the taxonomy of this species
    classification = wsdlObjectWoRMS.getAphiaClassificationByID(taxon_id)
    # construct array
    tax_array = {}
    # classification is a nested dictionary, so we need to iterate down it
    current_child = classification.child
    while True:
        tax_array[current_child.rank.lower()] = current_child.scientificname
        current_child = current_child.child
        if current_child == '': # empty one is a string for some reason
            break
    return tax_array



def get_taxonomy_worms(taxonomy, start_otu):
    """ Gets and processes a taxon from the queue to get its taxonomy."""
    from SOAPpy import WSDL    

    wsdlObjectWoRMS = WSDL.Proxy('http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')

    # this is the recursive function
    def get_children(taxonomy, ID):

        # get data
        this_item = wsdlObjectWoRMS.getAphiaRecordByID(ID)
        if this_item == None:
            return taxonomy
        if this_item['rank'].lower() == 'species':
            # add data to taxonomy dictionary
            # get the taxonomy of this species
            classification = wsdlObjectWoRMS.getAphiaClassificationByID(ID)
            taxon = this_item.scientificname
            if not taxon in taxonomy: # is a new taxon, not previously in the taxonomy
                # construct array
                tax_array = {}
                # classification is a nested dictionary, so we need to iterate down it
                current_child = classification.child
                while True:
                    if taxonomy_levels.index(current_child.rank.lower()) <= taxonomy_levels.index(start_taxonomy_level):
                        # we need this - we're closer to the tips of the tree than we started                    
                        tax_array[current_child.rank.lower()] = current_child.scientificname
                    current_child = current_child.child
                    if current_child == '': # empty one is a string for some reason
                        break
                print tax_array
                taxonomy[this_item.scientificname] = tax_array
                return taxonomy
            else:
                return taxonomy

        all_children = []
        start = 1
        while True:
            children = wsdlObjectWoRMS.getAphiaChildrenByID(ID, start, False)
            if (children == None):
                break
            if (len(children) < 50):
                all_children.extend(children)
                break
            all_children.extend(children)
            start += 50
        
        if (len(all_children) == 0):
            return taxonomy

        for child in all_children:
            taxonomy = get_children(taxonomy, child['valid_AphiaID'])

        return taxonomy
            

    # main bit of the get_taxonomy_worms function
    try:
        start_taxa = wsdlObjectWoRMS.getAphiaRecords(start_otu)
        start_id = start_taxa[0]['valid_AphiaID'] # there might be records that aren't valid - they point to the valid one though
        # call it again via the ID this time to make sure we've got the right one.
        start_taxa = wsdlObjectWoRMS.getAphiaRecordByID(start_id)
        start_taxonomy_level = start_taxa['rank'].lower()
    except HTTPError:
        print "Error"
        sys.exit(-1)

    taxonomy = get_children(taxonomy,start_id)

    return taxonomy, start_taxonomy_level
            

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
            '--pref_db',
            help="Taxonomy database to use. Default is Species 2000/ITIS",
            choices=['itis', 'worms', 'ncbi'],
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
    pref_db = args.pref_db
    if (save_taxonomy_file == None):
        save_taxonomy = False
    else:
        save_taxonomy = True

    # grab taxa in tree
    tree = stk.import_tree(input_file)
    taxa_list = stk._getTaxaFromNewick(tree)

    taxonomy = {}

    # we're going to add the taxa in the tree to the taxonomy, to stop them
    # being fetched in first place. We delete them later
    for taxon in taxa_list:
        taxon = taxon.replace('_',' ')
        taxonomy[taxon] = {}


    if (pref_db == 'itis'):
        # get taxonomy info from itis
        print "Sorry, ITIS is not implemented yet"
        pass
    elif (pref_db == 'worms'):
        if (verbose):
            print "Getting data from WoRMS"
        # get tree taxonomy from worms
        if (tree_taxonomy == None):
            tree_taxonomy = {}
            for t in taxa_list:
                from SOAPpy import WSDL    
                wsdlObjectWoRMS = WSDL.Proxy('http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')
                tree_taxonomy[t] = get_tree_taxa_taxonomy(t,wsdlObjectWoRMS)
        else:
            tree_taxonomy = stk.load_taxonomy(tree_taxonomy)
        # get taxonomy from worms
        taxonomy, start_level = get_taxonomy_worms(taxonomy,top_level)
        #start_level = 'family'
        #taxonomy = tree_taxonomy

    elif (pref_db == 'ncbi'):
        # get taxonomy from ncbi
        print "Sorry, NCBI is not implemented yet"        
        pass
    else:
        print "ERROR: Didn't understand you database choice"
        sys.exit(-1)


    # clean up taxonomy, deleting the ones already in the tree
    for taxon in taxa_list:
        taxon = taxon.replace('_',' ')        
        del taxonomy[taxon]

    orig_taxonomy = copy.deepcopy(taxonomy)
    print start_level
    print orig_taxonomy

    # step up the taxonomy levels from genus, adding taxa to the correct node
    # as a polytomy
    for level in taxonomy_levels[1::]: # skip species....
        print level
        new_taxa = []
        for t in taxonomy:
            # skip odd ones that should be in there
            if start_level in taxonomy[t] and taxonomy[t][start_level] == top_level:
                try:
                    new_taxa.append(taxonomy[t][level])
                except KeyError:
                    continue # don't have this info
        new_taxa = _uniquify(new_taxa)
        
        for nt in new_taxa:
            taxa_to_add = []
            taxa_in_clade = []
            for t in taxonomy:
                if start_level in taxonomy[t] and taxonomy[t][start_level] == top_level:
                    # need to add taxonomic information in here - there's a structure to be added
                    # loop over level to genus - insert nodes from level to genus
                    # insert species on appropriate genus
                    for l in reversed(taxonomy_levels[taxonomy_levels.index(level):1:-1]):
                        current_tax = []

                    try:
                        if taxonomy[t][level] == nt:
                            taxa_to_add.append(t.replace(' ','_'))
                    except KeyError:
                        continue
            # add to tree
            for t in taxa_list:
                if level in tree_taxonomy[t] and tree_taxonomy[t][level] == nt:
                    taxa_in_clade.append(t)
            if len(taxa_in_clade) > 0:
                tree = add_taxa(tree, taxa_to_add, taxa_in_clade)
                for t in taxa_to_add: # clean up taxonomy
                    del taxonomy[t.replace('_',' ')]


    trees = {}
    trees['tree_1'] = tree
    output = stk._amalgamate_trees(trees,format='nexus')
    f = open(output_file, "w")
    f.write(output)
    f.close()

    if not save_taxonomy_file == None:
        with open(save_taxonomy_file, 'w') as f:
            writer = csv.writer(f)
            headers = []
            headers.append("OTU")
            headers.extend(taxonomy_levels)
            headers.append("Data source")
            writer.writerow(headers)
            for t in orig_taxonomy:
                otu = t
                try:
                    species = orig_taxonomy[t]['species']
                except KeyError:
                    species = "-"
                try:
                    subgenus = orig_taxonomy[t]['subgenus']
                except KeyError:
                    subgenus = "-"
                try:
                    genus = orig_taxonomy[t]['genus']
                except KeyError:
                    genus = "-"
                try:
                    subfamily = orig_taxonomy[t]['subfamily']
                except KeyError:
                    subfamily = "-"
                try:
                    family = orig_taxonomy[t]['family']
                except KeyError:
                    family = "-"
                try:
                    superfamily = orig_taxonomy[t]['superfamily']
                except KeyError:
                    superfamily = "-"
                try:
                    subsection = orig_taxonomy[t]['subsection']
                except KeyError:
                    subsection = "-"
                try:
                    section = orig_taxonomy[t]['section']
                except KeyError:
                    section = "-"
                try:
                    infraorder = orig_taxonomy[t]['infraorder']
                except KeyError:
                    infraorder = "-"
                try:
                    suborder = orig_taxonomy[t]['suborder']
                except KeyError:
                    suborder = "-"
                try:
                    order = orig_taxonomy[t]['order']
                except KeyError:
                    order = "-"
                try:
                    superorder = orig_taxonomy[t]['superorder']
                except KeyError:
                    superorder = "-"
                try:
                    subclass = orig_taxonomy[t]['subclass']
                except KeyError:
                    subclass = "-"
                try:
                    tclass = orig_taxonomy[t]['class']
                except KeyError:
                    tclass = "-"
                try:
                    superclass = orig_taxonomy[t]['superclass']
                except KeyError:
                    superclass = "-"
                try:
                    subphylum = orig_taxonomy[t]['subphylum']
                except KeyError:
                    subphylum = "-"
                try:
                    phylum = orig_taxonomy[t]['phylum']
                except KeyError:
                    phylum = "-"
                try:
                    superphylum = orig_taxonomy[t]['superphylum']
                except KeyError:
                    superphylum = "-"
                try:
                    infrakingdom = orig_taxonomy[t]['infrakingdom']
                except:
                    infrakingdom = "-"
                try:
                    subkingdom = orig_taxonomy[t]['subkingdom']
                except:
                    subkingdom = "-"
                try:
                    kingdom = orig_taxonomy[t]['kingdom']
                except KeyError:
                    kingdom = "-"
                try:
                    provider = orig_taxonomy[t]['provider']
                except KeyError:
                    provider = "-"

                if (isinstance(species, list)):
                    species = " ".join(species)
                this_classification = [
                        otu.encode('utf-8'),
                        species.encode('utf-8'),
                        subgenus.encode('utf-8'),
                        genus.encode('utf-8'),
                        subfamily.encode('utf-8'),
                        family.encode('utf-8'),
                        superfamily.encode('utf-8'),
                        subsection.encode('utf-8'),
                        section.encode('utf-8'),
                        infraorder.encode('utf-8'),
                        suborder.encode('utf-8'),
                        order.encode('utf-8'),
                        superorder.encode('utf-8'),
                        subclass.encode('utf-8'),
                        tclass.encode('utf-8'),
                        superclass.encode('utf-8'),
                        subphylum.encode('utf-8'),
                        phylum.encode('utf-8'),
                        superphylum.encode('utf-8'),
                        infrakingdom.encode('utf-8'),
                        subkingdom.encode('utf-8'),
                        kingdom.encode('utf-8'),
                        provider.encode('utf-8')]
                writer.writerow(this_classification)


def _uniquify(l):
    """
    Make a list, l, contain only unique data
    """
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()

def add_taxa(tree, new_taxa, taxa_in_clade):

    # create new tree of the new taxa
    tree_string = "(" + ",".join(new_taxa) + ");"
    additionalTaxa = stk._parse_tree(tree_string) 

    # find mrca parent
    treeobj = stk._parse_tree(tree)
    mrca = stk.get_mrca(tree,taxa_in_clade)
    mrca = treeobj.nodes[mrca]
    #mrca_parent = treeobj.node(mrca).parent

    # insert a node into the tree between the MRCA and it's parent (p4.addNodeBetweenNodes)
    # newNode = treeobj.addNodeBetweenNodes(mrca, mrca_parent)

    # add the new tree at the new node using p4.addSubTree(self, selfNode, theSubTree, subTreeTaxNames=None)
    treeobj.addSubTree(mrca, additionalTaxa, ignoreRootAssert=True)
    #for t in new_taxa:
    #    t.replace('(','')
    #    t.replace(')','')
    #    treeobj.addSibLeaf(mrca,t)

    # return new tree
    return treeobj.writeNewick(fName=None,toString=True).strip()

if __name__ == "__main__":
    main()




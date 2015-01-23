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
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
import csv

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
            default = 'itis'
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
            'top_level', 
            nargs=1,
            help="The top level group to look in, e.g. Arthropoda, Decapoda. Must match the EOL database."
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
    if (save_taxonomy_file == None):
        save_taxonomy = False
    else:
        save_taxonomy = True

    # grab taxa in tree
    tree = stk.import_tree(input_file)
    taxa_list = stk._getTaxaFromNewick(tree)


    taxonomy = {}
    # What we get from EOL
    current_taxonomy_levels = ['species','genus','family','order','class','phylum','kingdom']
    # And the extra ones from ITIS
    extra_taxonomy_levels = ['superfamily','infraorder','suborder','superorder','subclass','subphylum','superphylum','infrakingdom','subkingdom']
    # all of them in order
    taxonomy_levels = ['species','genus','subfamily','family','superfamily','infraorder','suborder','order','superorder','subclass','class','subphylum','phylum','superphylum','infrakingdom','subkingdom','kingdom']


    for taxon in taxa:
        taxon = taxon.replace("_"," ")
        if (verbose):
            print "Looking up ", taxon
        # get the data from EOL on taxon
        # What about synonyms?
        taxonq = quote_plus(taxon)
        URL = "http://eol.org/api/search/1.0.json?q="+taxonq
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = json.load(f)
        # check if there's some data
        if len(data['results']) == 0:
            taxonomy[taxon] = {}
            continue
        ID = str(data['results'][0]['id']) # take first hit
        # Now look for taxonomies
        URL = "http://eol.org/api/pages/1.0/"+ID+".json"
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = json.load(f)
        if len(data['taxonConcepts']) == 0:
            taxonomy[taxon] = {}
            continue
        TID = str(data['taxonConcepts'][0]['identifier']) # take first hit
        currentdb = str(data['taxonConcepts'][0]['nameAccordingTo'])
        # loop through and get preferred one if specified
        # now get taxonomy
        if (not pref_db == None):
            for db in data['taxonConcepts']:
                currentdb = db['nameAccordingTo'].lower()
                if (pref_db.lower() in currentdb):
                    TID = str(db['identifier'])
                    break
        URL="http://eol.org/api/hierarchy_entries/1.0/"+TID+".json"
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = json.load(f)
        this_taxonomy = {}
        this_taxonomy['provider'] = currentdb
        for a in data['ancestors']:
            try:
                this_taxonomy[a['taxonRank']] = a['scientificName']
            except KeyError:
                continue
        try:
            if (not data['taxonRank'].lower() == 'species'):
                # higher taxa, add it in to the taxonomy!
                this_taxonomy[data['taxonRank'].lower()] = taxon
        except KeyError:
            continue
        taxonomy[taxon] = this_taxonomy
    
    if (verbose):
        print "Done basic taxonomy, getting more info from ITIS"
    
    # fill in the rest of the taxonomy
    # get all genera
    genera = []
    for t in taxonomy:
        try:
            genera.append(taxonomy[t]['genus'])
        except KeyError:
            continue
    
    genera = _uniquify(genera)
    for g in genera:
        if (verbose):
            print "Looking up ", g
        try:
            URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(g.strip())
        except:
            continue
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        string = unicode(f.read(),"ISO-8859-1")
        data = json.loads(string)
        if data['scientificNames'][0] == None:
            continue
        tsn = data["scientificNames"][0]["tsn"]
        URL="http://www.itis.gov/ITISWebService/jsonservice/getFullHierarchyFromTSN?tsn="+str(tsn)
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        try:
            string = unicode(f.read(),"ISO-8859-1")
        except:
            continue
        data = json.loads(string)
        this_taxonomy = {}
        for level in data['hierarchyList']:
            if not level['rankName'].lower() in current_taxonomy_levels:
                this_taxonomy[level['rankName'].lower()] = level['taxonName']

        for t in taxonomy:
            try:
                if taxonomy[t]['genus'] == g:
                    taxonomy[t].update(this_taxonomy)
            except KeyError:
                continue
        

    # Now create the CSV output
    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(taxonomy_levels)
        for t in taxonomy:
            species = t
            try:
                genus = taxonomy[t]['genus']
            except KeyError:
                genus = "-"
            try:
                family = taxonomy[t]['family']
            except KeyError:
                family = "-"
            try:
                superfamily = taxonomy[t]['superfamily']
            except KeyError:
                superfamily = "-"
            try:
                infraorder = taxonomy[t]['infraorder']
            except KeyError:
                infraorder = "-"
            try:
                suborder = taxonomy[t]['suborder']
            except KeyError:
                suborder = "-"
            try:
                order = taxonomy[t]['order']
            except KeyError:
                order = "-"
            try:
                superorder = taxonomy[t]['superorder']
            except KeyError:
                superorder = "-"
            try:
                subclass = taxonomy[t]['subclass']
            except KeyError:
                subclass = "-"
            try:
                tclass = taxonomy[t]['class']
            except KeyError:
                tclass = "-"
            try:
                subphylum = taxonomy[t]['subphylum']
            except KeyError:
                subphylum = "-"
            try:
                phylum = taxonomy[t]['phylum']
            except KeyError:
                phylum = "-"
            try:
                superphylum = taxonomy[t]['superphylum']
            except KeyError:
                superphylum = "-"
            try:
                infrakingdom = taxonomy[t]['infrakingdom']
            except:
                infrakingdom = "-"
            try:
                subkingdom = taxonomy[t]['subkingdom']
            except:
                subkingdom = "-"
            try:
                kingdom = taxonomy[t]['kingdom']
            except KeyError:
                kingdom = "-"
            try:
                provider = taxonomy[t]['provider']
            except KeyError:
                provider = "-"


            this_classification = [
                    species.encode('utf-8'),
                    genus.encode('utf-8'),
                    family.encode('utf-8'),
                    superfamily.encode('utf-8'),
                    infraorder.encode('utf-8'),
                    suborder.encode('utf-8'),
                    order.encode('utf-8'),
                    superorder.encode('utf-8'),
                    subclass.encode('utf-8'),
                    tclass.encode('utf-8'),
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

    # find MRCA of all taxa within this clade, already in the tree
    node_ids = []
    # get the nodes of the taxa in question
    node_id_for_taxa = []
    for t in taxa:
        node_id_for_taxa.append(tree.node(t))
    # for each, get all parents to root
    for n in node_id_for_taxa:
        nodes = []
        nodes.append(tree.node(n)).parent
        while:
            nn = tree.node(nodes[-1]).parent
            if nn == None:
                break
            else:
                nodes.append(nn)
        node_ids.append(nodes)
    # in the shortest list, loop through the values, check they exist in all lists. If it does, 
    # that node is your MRCA
    big = sys.maxsize
    for n in node_ids:
        if len(n) < big:
            big = len(n)
            shortest = n
    mrca = -1
    for s in shortest:
        for n in node_ids:
            if not s in n:
                break # move to next s
        # if we get here, we have the MRCA
        mrca = s
        break
    if mrca == -1:
        # something went wrong!
        print "Error finding MRCA"
    mrca_parent = tree.node(mrca).parent

    # insert a node into the tree between the MRCA and it's parent (p4.addNodeBetweenNodes)
    newNode = tree.addNodeBetweenNodes(mrca, mrca_paraent)

    # add the new tree at the new node using p4.addSubTree(self, selfNode, theSubTree, subTreeTaxNames=None)
    tree,addSubTree(newNode, additionalTaxa)

    # return new tree
    return

if __name__ == "__main__":
    main()




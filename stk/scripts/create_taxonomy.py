#!/usr/bin/env python
#
#
# Generate a number of colours, that are different enough and evenly distributed
# for tree display
#

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
         prog="Create a taxonomy",
         description="Generate a taxonomy from Phyml. Fills in most taxonomic levels. Uses EOL and ITIS",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your tree"
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            nargs=1,
            help="The output file. A CSV-based taxonomy"
            )

    args = parser.parse_args()
    verbose = args.verbose
    input_file = args.input_file[0]
    output_file = args.output_file[0]

    # grab taxa in dataset
    XML = stk.load_phyml(input_file)
    taxa = stk.get_all_taxa(XML)

    taxonomy = {}
    # What we get from EOL
    current_taxonomy_levels = ['species','genus','family','order','class','phylum','kingdom']
    # And the extra ones from ITIS
    extra_taxonomy_levels = ['superfamily','infraorder','suborder','superorder','subclass','subphylum','superphylum','infrakingdom','subkingdom']
    # all of them in order
    taxonomy_levels = ['species','genus','family','superfamily','infraorder','suborder','order','superorder','subclass','class','subphylum','phylum','superphylum','infrakingdom','subkingdom','kingdom']


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
        TID = str(data['taxonConcepts'][0]['identifier']) # take first hit
        # now get taxonomy
        URL="http://eol.org/api/hierarchy_entries/1.0/"+TID+".json"
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = json.load(f)
        this_taxonomy = {}
        for a in data['ancestors']:
            try:
                this_taxonomy[a['taxonRank']] = a['scientificName']
            except KeyError:
                continue
        if (not data['taxonRank'].lower() == 'species'):
            # higher taxa, add it in to the taxonomy!
            this_taxonomy[data['taxonRank'].lower()] = taxon
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
        URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(g.strip())
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
        string = unicode(f.read(),"ISO-8859-1")
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

            this_classification = [
                    species,
                    genus,
                    family,
                    superfamily,
                    infraorder,
                    suborder,
                    order,
                    superorder,
                    subclass,
                    tclass,
                    subphylum,
                    phylum,
                    superphylum,
                    infrakingdom,
                    subkingdom,
                    kingdom]
            writer.writerow(this_classification)
            
    
def _uniquify(l):
    """
    Make a list, l, contain only unique data
    """
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()

if __name__ == "__main__":
    main()



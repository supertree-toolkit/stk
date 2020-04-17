#!/usr/bin/env python
#
#
# Generate a number of colours, that are different enough and evenly distributed
# for tree display
#

import urllib.request, urllib.error, urllib.parse
from urllib.parse import quote_plus
import simplejson as json
import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
import csv

taxonomy_levels = stk.taxonomy_levels

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
            '--pref_db',
            help="Preferred database. Need to be able to list avialable databases?"
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your input taxa list or phyml"
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
    pref_db = args.pref_db

    # grab taxa in dataset
    fileName, fileExtension = os.path.splitext(input_file)
    if (fileExtension == '.phyml'):
        XML = stk.load_phyml(input_file)
        taxa = stk.get_all_taxa(XML)
    else:
        f = open(input_file,"r")
        taxa = []
        for line in f:
            taxa.append(line.strip())
        f.close()

    taxonomy = {}

    for taxon in taxa:
        taxon = taxon.replace("_"," ")
        if (verbose):
            print("Looking up ", taxon)
        # get the data from EOL on taxon
        # What about synonyms?
        taxonq = quote_plus(taxon)
        URL = "http://eol.org/api/search/1.0.json?q="+taxonq
        req = urllib.request.Request(URL)
        opener = urllib.request.build_opener()
        f = opener.open(req)
        data = json.load(f)
        # check if there's some data
        if len(data['results']) == 0:
            taxonomy[taxon] = {}
            continue
        ID = str(data['results'][0]['id']) # take first hit
        # Now look for taxonomies
        URL = "http://eol.org/api/pages/1.0/"+ID+".json"
        req = urllib.request.Request(URL)
        opener = urllib.request.build_opener()
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
        req = urllib.request.Request(URL)
        opener = urllib.request.build_opener()
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
        print("Done basic taxonomy, getting more info from ITIS")
    
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
            print("Looking up ", g)
        try:
            URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(g.strip())
        except:
            continue
        req = urllib.request.Request(URL)
        opener = urllib.request.build_opener()
        f = opener.open(req)
        string = str(f.read(),"ISO-8859-1")
        data = json.loads(string)
        if data['scientificNames'][0] == None:
            continue
        tsn = data["scientificNames"][0]["tsn"]
        URL="http://www.itis.gov/ITISWebService/jsonservice/getFullHierarchyFromTSN?tsn="+str(tsn)
        req = urllib.request.Request(URL)
        opener = urllib.request.build_opener()
        f = opener.open(req)
        try:
            string = str(f.read(),"ISO-8859-1")
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
        

    stk.save_taxonomy(taxonomy, output_file)
     
def _uniquify(l):
    """
    Make a list, l, contain only unique data
    """
    keys = {}
    for e in l:
        keys[e] = 1

    return list(keys.keys())

if __name__ == "__main__":
    main()




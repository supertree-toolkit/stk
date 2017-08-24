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
#tlevels = ['species','genus','family','superfamily','suborder','order','class','phylum','kingdom']
tlevels = ['species','genus', 'subfamily', 'family','superfamily','infraorder','suborder','order','class','phylum','kingdom']

def get_tree_taxa_taxonomy_eol(taxon):

    taxonq = quote_plus(taxon)
    URL = "http://eol.org/api/search/1.0.json?q="+taxonq
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    data = json.load(f)
    
    if data['results'] == []:
        return {}
    ID = str(data['results'][0]['id']) # take first hit
    # Now look for taxonomies
    URL = "http://eol.org/api/pages/1.0/"+ID+".json"
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    data = json.load(f)
    if len(data['taxonConcepts']) == 0:
        return {}
    TID = str(data['taxonConcepts'][0]['identifier']) # take first hit
    currentdb = str(data['taxonConcepts'][0]['nameAccordingTo'])
    # loop through and get preferred one if specified
    # now get taxonomy        
    for db in data['taxonConcepts']:
        currentdb = db['nameAccordingTo'].lower()
        TID = str(db['identifier'])
        break
    URL="http://eol.org/api/hierarchy_entries/1.0/"+TID+".json"
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    data = json.load(f)
    tax_array = {}
    tax_array['provider'] = currentdb
    for a in data['ancestors']:
        try:
            if a.has_key('taxonRank') :
                temp_level = a['taxonRank'].encode("ascii","ignore")
                if (temp_level in taxonomy_levels):
                    # note the dump into ASCII
                    temp_name = a['scientificName'].encode("ascii","ignore")
                    temp_name = temp_name.split(" ")
                    if (temp_level == 'species'):
                        tax_array[temp_level] = "_".join(temp_name[0:2])
                        
                    else:
                        tax_array[temp_level] = temp_name[0]  
        except KeyError as e:
            logging.exception("Key not found: taxonRank")
            continue
    try:
        # add taxonomy in to the taxonomy!
        # some issues here, so let's make sure it's OK
        temp_name = taxon.split(" ")            
        if data.has_key('taxonRank') :
            if not data['taxonRank'].lower() == 'species':
                tax_array[data['taxonRank'].lower()] = temp_name[0]
            else:
                tax_array[data['taxonRank'].lower()] = ' '.join(temp_name[0:2])
    except KeyError as e:
       return tax_array 

    return tax_array

def get_tree_taxa_taxonomy_worms(taxon):

    from SOAPpy import WSDL    
    wsdlObjectWoRMS = WSDL.Proxy('http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')

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
    if (classification == ""):
        return {}
    # classification is a nested dictionary, so we need to iterate down it
    current_child = classification.child
    while True:
        tax_array[current_child.rank.lower()] = current_child.scientificname
        current_child = current_child.child
        if current_child == '': # empty one is a string for some reason
            break
    return tax_array

def get_tree_taxa_taxonomy_itis(taxon):

    URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(taxon.replace('_',' ').strip())
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)    
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    if this_item['scientificNames'] == [None]: # not found
        return {}
    tsn = this_item['scientificNames'][0]['tsn'] # there might be records that aren't valid - they point to the valid one though
    # so call another function to get any valid names
    URL="http://www.itis.gov/ITISWebService/jsonservice/getAcceptedNamesFromTSN?tsn="+tsn
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    if not this_item['acceptedNames'] == [None]:
        tsn = this_item['acceptedNames'][0]['acceptedTsn']

    URL="http://www.itis.gov/ITISWebService/jsonservice/getFullHierarchyFromTSN?tsn="+str(tsn)
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    string = unicode(f.read(),"ISO-8859-1")
    data = json.loads(string)
    # construct array
    this_taxonomy = {}
    for level in data['hierarchyList']:
        if level['rankName'].lower() in taxonomy_levels:
            # note the dump into ASCII            
            this_taxonomy[level['rankName'].lower().encode("ascii","ignore")] = level['taxonName'].encode("ascii","ignore")

    return this_taxonomy



def get_taxonomy_eol(taxonomy, start_otu, verbose,tmpfile=None,skip=False):
        
    # this is the recursive function
    def get_children(taxonomy, ID, aphiaIDsDone):

        # get data
        URL="http://eol.org/api/hierarchy_entries/1.0/"+str(ID)+".json?common_names=false&synonyms=false&cache_ttl="
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        string = unicode(f.read(),"ISO-8859-1")
        this_item = json.loads(string)
        if this_item == None:
            return taxonomy  
        if this_item['taxonRank'].lower().strip() == 'species':
            # add data to taxonomy dictionary
            taxon = this_item['scientificName'].split()[0:2] # just the first two words
            taxon = " ".join(taxon[0:2])
            # NOTE following line means existing items are *not* updated
            if not taxon in taxonomy: # is a new taxon, not previously in the taxonomy
                this_taxonomy = {}
                for level in this_item['ancestors']:
                    if level['taxonRank'].lower() in taxonomy_levels:
                        # note the dump into ASCII            
                        this_taxonomy[level['taxonRank'].lower().encode("ascii","ignore")] = level['scientificName'].encode("ascii","ignore")
                # add species:
                this_taxonomy['species'] = taxon.replace(" ","_")
                if verbose:
                    print "\tAdding "+taxon
                taxonomy[taxon] = this_taxonomy
                if not tmpfile == None:
                    stk.save_taxonomy(taxonomy,tmpfile)
                return taxonomy
            else:
                return taxonomy
        all_children = []
        for level in this_item['children']:
            if not level == None:
                all_children.append(level['taxonID'])
        
        if (len(all_children) == 0):
            return taxonomy

        for child in all_children:
            if child in aphiaIDsDone: # we get stuck sometime
                continue
            aphiaIDsDone.append(child)
            taxonomy = get_children(taxonomy, child, aphiaIDsDone)
        return taxonomy
            

    # main bit of the get_taxonomy_eol function
    taxonq = quote_plus(start_otu)
    URL = "http://eol.org/api/search/1.0.json?q="+taxonq
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    data = json.load(f)
    start_id = str(data['results'][0]['id']) # this is the page ID. We get the species ID next
    URL = "http://eol.org/api/pages/1.0/"+start_id+".json"
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    data = json.load(f)
    if len(data['taxonConcepts']) == 0:
        print "Error finding you start taxa. Spelling?"
        return None  
    start_id = data['taxonConcepts'][0]['identifier']
    start_taxonomy_level = data['taxonConcepts'][0]['taxonRank'].lower()

    aphiaIDsDone = []
    if not skip:
        taxonomy = get_children(taxonomy,start_id,aphiaIDsDone)

    return taxonomy, start_taxonomy_level



def get_taxonomy_itis(taxonomy, start_otu, verbose,tmpfile=None,skip=False):
    import simplejson as json
        
    # this is the recursive function
    def get_children(taxonomy, ID, aphiaIDsDone):

        # get data
        URL="http://www.itis.gov/ITISWebService/jsonservice/getFullRecordFromTSN?tsn="+ID
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        string = unicode(f.read(),"ISO-8859-1")
        this_item = json.loads(string)
        if this_item == None:
            return taxonomy
        if not this_item['usage']['taxonUsageRating'].lower() == 'valid':
            print "rejecting " , this_item['scientificName']['combinedName']
            return taxonomy        
        if this_item['taxRank']['rankName'].lower().strip() == 'species':
            # add data to taxonomy dictionary
            taxon = this_item['scientificName']['combinedName']
            # NOTE following line means existing items are *not* updated
            if not taxon in taxonomy: # is a new taxon, not previously in the taxonomy
                # get the taxonomy of this species
                tsn = this_item["scientificName"]["tsn"]
                URL="http://www.itis.gov/ITISWebService/jsonservice/getFullHierarchyFromTSN?tsn="+tsn
                req = urllib2.Request(URL)
                opener = urllib2.build_opener()
                f = opener.open(req)
                string = unicode(f.read(),"ISO-8859-1")
                data = json.loads(string)
                this_taxonomy = {}
                for level in data['hierarchyList']:
                    if level['rankName'].lower() in taxonomy_levels:
                        # note the dump into ASCII            
                        this_taxonomy[level['rankName'].lower().encode("ascii","ignore")] = level['taxonName'].encode("ascii","ignore")
                if verbose:
                    print "\tAdding "+taxon
                taxonomy[taxon] = this_taxonomy
                if not tmpfile == None:
                    stk.save_taxonomy(taxonomy,tmpfile)
                return taxonomy
            else:
                return taxonomy

        all_children = []
        URL="http://www.itis.gov/ITISWebService/jsonservice/getHierarchyDownFromTSN?tsn="+ID
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        string = unicode(f.read(),"ISO-8859-1")
        this_item = json.loads(string)
        if this_item == None:
            return taxonomy

        for level in this_item['hierarchyList']:
            if not level == None:
                all_children.append(level['tsn'])
        
        if (len(all_children) == 0):
            return taxonomy

        for child in all_children:
            if child in aphiaIDsDone: # we get stuck sometime
                continue
            aphiaIDsDone.append(child)
            taxonomy = get_children(taxonomy, child, aphiaIDsDone)
            
        return taxonomy
            

    # main bit of the get_taxonomy_worms function
    URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(start_otu.strip())
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    start_id = this_item['scientificNames'][0]['tsn'] # there might be records that aren't valid - they point to the valid one though
    # call it again via the ID this time to make sure we've got the right one.
    # so call another function to get any valid names
    URL="http://www.itis.gov/ITISWebService/jsonservice/getAcceptedNamesFromTSN?tsn="+start_id
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    if not this_item['acceptedNames'] == [None]:
        start_id = this_item['acceptedNames'][0]['acceptedTsn']

    URL="http://www.itis.gov/ITISWebService/jsonservice/getFullRecordFromTSN?tsn="+start_id
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    start_taxonomy_level = this_item['taxRank']['rankName'].lower()

    aphiaIDsDone = []
    if not skip:
        taxonomy = get_children(taxonomy,start_id,aphiaIDsDone)

    return taxonomy, start_taxonomy_level




def get_taxonomy_worms(taxonomy, start_otu, verbose,tmpfile=None,skip=False):
    """ Gets and processes a taxon from the queue to get its taxonomy."""
    from SOAPpy import WSDL    

    wsdlObjectWoRMS = WSDL.Proxy('http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')

    # this is the recursive function
    def get_children(taxonomy, ID, aphiaIDsDone):

        # get data
        this_item = wsdlObjectWoRMS.getAphiaRecordByID(ID)
        if this_item == None:
            return taxonomy
        if not this_item['status'].lower() == 'accepted':
            print "rejecting " , this_item.valid_name
            return taxonomy        
        if this_item['rank'].lower() == 'species':
            # add data to taxonomy dictionary
            taxon = this_item.valid_name
            # NOTE following line means existing items are *not* updated
            if not taxon in taxonomy: # is a new taxon, not previously in the taxonomy
                # get the taxonomy of this species
                classification = wsdlObjectWoRMS.getAphiaClassificationByID(ID)
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
                if verbose:
                    print "\tAdding "+this_item.scientificname
                taxonomy[this_item.valid_name] = tax_array
                if not tmpfile == None:
                    stk.save_taxonomy(taxonomy,tmpfile)
                return taxonomy
            else:
                return taxonomy

        all_children = []
        start = 1
        while True:
            children = wsdlObjectWoRMS.getAphiaChildrenByID(ID, start, False)
            if (children is None or children == None):
                break
            if (len(children) < 50):
                all_children.extend(children)
                break
            all_children.extend(children)
            start += 50

        if (len(all_children) == 0):
            return taxonomy

        for child in all_children:
            if child['valid_AphiaID'] in aphiaIDsDone: # we get stuck sometime
                continue
            aphiaIDsDone.append(child['valid_AphiaID'])
            taxonomy = get_children(taxonomy, child['valid_AphiaID'], aphiaIDsDone)
            
        return taxonomy
            

    # main bit of the get_taxonomy_worms function
    try:
        start_taxa = wsdlObjectWoRMS.getAphiaRecords(start_otu)
        start_id = start_taxa[0]['valid_AphiaID'] # there might be records that aren't valid - they point to the valid one though
        # call it again via the ID this time to make sure we've got the right one.
        start_taxa = wsdlObjectWoRMS.getAphiaRecordByID(start_id)
        if start_taxa == None:
            start_taxonomy_level = 'infraorder'
        else:
            start_taxonomy_level = start_taxa['rank'].lower()
    except urllib2.HTTPError:
        print "Error finding start_otu taxonomic level. Do you have an internet connection?"
        sys.exit(-1)

    aphiaIDsDone = []
    if not skip:
        taxonomy = get_children(taxonomy,start_id,aphiaIDsDone)

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
            elif t.replace("_"," ") in taxonomy:
                tree_taxonomy[t] = taxonomy[t.replace("_"," ")]
       
    if (load_tree_taxonomy): # overwrite the good work above...
        tree_taxonomy = stk.load_taxonomy(tree_taxonomy_file)
    if (tree_taxonomy == None):
        tree_taxonomy = {}

    # we're going to add the taxa in the tree to the main WORMS taxonomy, to stop them
    # being fetched in first place. We delete them later
    # If you've loaded a taxonomy created by this script, this overwrites the tree taxa in the main taxonomy dict
    # Don't worry, we put them back in before saving again!
    for taxon in taxa_list:
        taxon = taxon.replace('_',' ')
        taxonomy[taxon] = {}

    if (pref_db == 'itis'):
        # get taxonomy info from itis
        if (verbose):
            print "Getting data from ITIS"
        if (verbose):
            print "Dealing with taxa in tree"
        for t in taxa_list:
            if verbose:
                print "\t"+t
            if not(t in tree_taxonomy or t.replace("_"," ") in tree_taxonomy):
                # we don't have data - NOTE we assume things are *not* updated here if we do
                tree_taxonomy[t] = get_tree_taxa_taxonomy_itis(t)
       
        if save_taxonomy:
            if (verbose):
                print "Saving tree taxonomy"
            # note -temporary save as we overwrite this file later.
            stk.save_taxonomy(tree_taxonomy,save_taxonomy_file+'_tree.csv')

        # get taxonomy from worms
        if verbose:
            print "Now dealing with all other taxa - this might take a while..."
        # create a temp file so we can checkpoint and continue
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
        # bit naughty with tmpfile - we're using the filename rather than handle to write to it. Have to for write_taxonomy function
        taxonomy, start_level = get_taxonomy_itis(taxonomy,top_level,verbose,tmpfile=tmpfile,skip=skip) # this skips ones already there

        # clean up
        os.close(tmpf)
        os.remove('.fit_lock')
        try:
            os.remove('tmpfile')
        except OSError:
            pass
    elif (pref_db == 'worms'):
        if (verbose):
            print "Getting data from WoRMS"
        # get tree taxonomy from worms
        if (verbose):
            print "Dealing with taxa in tree"
        
        for t in taxa_list:
            if verbose:
                print "\t"+t
            if not(t in tree_taxonomy or t.replace("_"," ") in tree_taxonomy):
                # we don't have data - NOTE we assume things are *not* updated here if we do
                tree_taxonomy[t] = get_tree_taxa_taxonomy_worms(t)

        if save_taxonomy:
            if (verbose):
                print "Saving tree taxonomy"
            # note -temporary save as we overwrite this file later.
            stk.save_taxonomy(tree_taxonomy,save_taxonomy_file+'_tree.csv')

        # get taxonomy from worms
        if verbose:
            print "Now dealing with all other taxa - this might take a while..."
        # create a temp file so we can checkpoint and continue
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
        # bit naughty with tmpfile - we're using the filename rather than handle to write to it. Have to for write_taxonomy function
        taxonomy, start_level = get_taxonomy_worms(taxonomy,top_level,verbose,tmpfile=tmpfile,skip=skip) # this skips ones already there

        # clean up
        os.close(tmpf)
        os.remove('.fit_lock')
        try:
            os.remove('tmpfile')
        except OSError:
            pass

    elif (pref_db == 'ncbi'):
        # get taxonomy from ncbi
        print "Sorry, NCBI is not implemented yet"        
        pass
    elif (pref_db == 'eol'):
        if (verbose):
            print "Getting data from EOL"
        # get tree taxonomy from worms
        if (verbose):
            print "Dealing with taxa in tree"
        for t in taxa_list:
            if verbose:
                print "\t"+t
            try:
                tree_taxonomy[t]
                pass # we have data - NOTE we assume things are *not* updated here...
            except KeyError:
                try:
                    tree_taxonomy[t.replace('_',' ')]
                except KeyError:
                    tree_taxonomy[t] = get_tree_taxa_taxonomy_eol(t)
       
        if save_taxonomy:
            if (verbose):
                print "Saving tree taxonomy"
            # note -temporary save as we overwrite this file later.
            stk.save_taxonomy(tree_taxonomy,save_taxonomy_file+'_tree.csv')

        # get taxonomy from worms
        if verbose:
            print "Now dealing with all other taxa - this might take a while..."
        # create a temp file so we can checkpoint and continue
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
        # bit naughty with tmpfile - we're using the filename rather than handle to write to it. Have to for write_taxonomy function
        taxonomy, start_level = get_taxonomy_eol(taxonomy,top_level,verbose,tmpfile=tmpfile,skip=skip) # this skips ones already there

        # clean up
        os.close(tmpf)
        os.remove('.fit_lock')
        try:
            os.remove('tmpfile')
        except OSError:
            pass
    else:
        print "ERROR: Didn't understand your database choice"
        sys.exit(-1)

    # clean up taxonomy, deleting the ones already in the tree
    for taxon in taxa_list:
        taxon = taxon.replace('_',' ')
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
        new_taxa = _uniquify(new_taxa)

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
                        del taxonomy[t.replace('_',' ')]
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
 

def _uniquify(l):
    """
    Make a list, l, contain only unique data
    """
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()

def add_taxa(tree, new_taxa, taxa_in_clade, level):

    # create new tree of the new taxa
    additionalTaxa = tree_from_taxonomy(level,new_taxa)

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



def tree_from_taxonomy(top_level, tree_taxonomy):

    start_level = taxonomy_levels.index(top_level)
    new_taxa = tree_taxonomy.keys()

    tl_types = []
    for tt in tree_taxonomy:
        tl_types.append(tree_taxonomy[tt][top_level])

    tl_types = _uniquify(tl_types)
    levels_to_worry_about = tlevels[0:tlevels.index(top_level)+1]
        
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
        names = _uniquify(names)
        for n in names:
            # find my parent
            parent = None
            for tt in tree_taxonomy:
                try:
                    if tree_taxonomy[tt][l] == n:
                        try:
                            parent = tree_taxonomy[tt][levels_to_worry_about[ci+1]]
                            level = ci+1
                        except KeyError:
                            try:
                                parent = tree_taxonomy[tt][levels_to_worry_about[ci+2]]
                                level = ci+2
                            except KeyError:
                                try:
                                    parent = tree_taxonomy[tt][levels_to_worry_about[ci+3]]
                                    level = ci+3
                                except KeyError:
                                    print "ERROR: tried to find some taxonomic info for "+tt+" from tree_taxonomy file/downloaded data and I went two levels up, but failed find any. Looked at:\n"
                                    print "\t"+levels_to_worry_about[ci+1]
                                    print "\t"+levels_to_worry_about[ci+2]
                                    print "\t"+levels_to_worry_about[ci+3]
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
    
    return tree

if __name__ == "__main__":
    main()




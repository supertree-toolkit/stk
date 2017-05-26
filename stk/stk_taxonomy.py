#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2013, Jon Hill, Katie Davis
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
from StringIO import StringIO
import os
import sys
import math
import re
import numpy 
from lxml import etree
sys.path.insert(0,"../../")
import string
import stk_exceptions as excp
from collections import defaultdict
import stk.p4 as p4
import re
import stk.p4.MRP as MRP
import stk_internals
import Queue
import threading
import urllib2
from urllib import quote_plus
import simplejson as json



def taxonomic_checker_list(name_list,existing_data=None,verbose=False):
    """ For each name in the database generate a database of the original name,
    possible synonyms and if the taxon is not know, signal that. We do this by
    using the EoL API to grab synonyms of each taxon.  """

    import urllib2
    from urllib import quote_plus
    import simplejson as json

    if existing_data == None:
        equivalents = {}
    else:
        equivalents = existing_data

    # for each taxon, check the name on EoL - what if it's a synonym? Does EoL still return a result?
    # if not, is there another API function to do this?
    # search for the taxon and grab the name - if you search for a recognised synonym on EoL then
    # you get the original ('correct') name - shorten this to two words and you're done.
    for t in name_list:
        if t in equivalents:
            continue
        taxon = t.replace("_"," ")
        if (verbose):
            print "Looking up ", taxon
        # get the data from EOL on taxon
        taxonq = quote_plus(taxon)
        URL = "http://eol.org/api/search/1.0.json?q="+taxonq
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = opener.open(req)
        data = json.load(f)
        # check if there's some data
        if len(data['results']) == 0:
            equivalents[t] = [[t],'red']
            continue
        amber = False
        if len(data['results']) > 1:
            # this is not great - we have multiple hits for this taxon - needs the user to go back and warn about this
            # for automatic processing we'll just take the first one though
            # colour is amber in this case
            amber = True
        ID = str(data['results'][0]['id']) # take first hit
        URL = "http://eol.org/api/pages/1.0/"+ID+".json?images=0&videos=0&sounds=0&maps=0&text=0&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0"       
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        
        try:
            f = opener.open(req)
        except urllib2.HTTPError:
            equivalents[t] = [[t],'red'] 
            continue
        data = json.load(f)
        if len(data['scientificName']) == 0:
            # not found a scientific name, so set as red
            equivalents[t] = [[t],'red']            
            continue
        correct_name = data['scientificName'].encode("ascii","ignore")
        # we only want the first two bits of the name, not the original author and year if any
        temp_name = correct_name.split(' ')
        if (len(temp_name) > 2):
            correct_name = ' '.join(temp_name[0:2])
        correct_name = correct_name.replace(' ','_')

        # build up the output dictionary - original name is key, synonyms/missing is value
        if (correct_name == t):
            # if the original matches the 'correct', then it's green
            equivalents[t] = [[t], 'green']
        else:
            # if we managed to get something anyway, then it's yellow and create a list of possible synonyms with the 
            # 'correct' taxon at the top
            eol_synonyms = data['synonyms']
            synonyms = []
            for s in eol_synonyms:
                ts = s['synonym'].encode("ascii","ignore")
                temp_syn = ts.split(' ')
                if (len(temp_syn) > 2):
                    temp_syn = ' '.join(temp_syn[0:2])
                    ts = temp_syn
                if (s['relationship'] == "synonym"):
                    ts = ts.replace(" ","_")
                    synonyms.append(ts)
            synonyms = _uniquify(synonyms)
            # we need to put the correct name at the top of the list now
            if (correct_name in synonyms):
                synonyms.insert(0, synonyms.pop(synonyms.index(correct_name)))
            elif len(synonyms) == 0:
                synonyms.append(correct_name)
            else:
                synonyms.insert(0,correct_name)

            if (amber):
                equivalents[t] = [synonyms,'amber']
            else:
                equivalents[t] = [synonyms,'yellow']
        # if our search was empty, then it's red - see above

    # up to the calling funciton to do something sensible with this
    # we build a dictionary of names and then a list of synonyms or the original name, then a tag if it's green, yellow, red.
    # Amber means we found synonyms and multilpe hits. User def needs to sort these!

    return equivalents



def save_taxonomy(taxonomy, output_file):

    import csv

    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        row = ['OTU']
        row.extend(taxonomy_levels)
        row.append('Provider')
        writer.writerow(row)
        for t in taxonomy:
            species = t
            row = []
            row.append(t.encode('utf-8'))
            for l in taxonomy_levels:
                try:
                    g = taxonomy[t][l]
                except KeyError:
                    g = '-'
                row.append(g.encode('utf-8'))
            try:
                provider = taxonomy[t]['provider']
            except KeyError:
                provider = "-"
            row.append(provider)

            writer.writerow(row)


def load_taxonomy(taxonomy_csv):
    """Load in a taxonomy CSV file and convert to taxonomy Dict"""
    
    import csv

    taxonomy = {}

    with open(taxonomy_csv, 'rU') as csvfile:
        tax_reader = csv.reader(csvfile, delimiter=',')
        try:
            j = 0
            for row in tax_reader:
                if j == 0:
                    tax_levels = row[1:-1]
                    j += 1
                    continue
                i = 1
                current_taxonomy = {}
                for t in tax_levels:
                    if not row[i] == '-':
                        current_taxonomy[t] = row[i]
                    i = i+ 1
                current_taxonomy['provider'] = row[-1] # data source
                taxonomy[row[0].replace(" ","_")] = current_taxonomy
                j += 1
        except:
            pass
    
    return taxonomy


class TaxonomyFetcher(threading.Thread):
    """ Class to provide the taxonomy fetching functionality as a threaded function to be used individually or working with a pool.
    """

    def __init__(self, taxonomy, lock, queue, id=0, pref_db=None, verbose=False, ignoreWarnings=False):
        """ Constructor for the threaded model.
        :param taxonomy: previous taxonomy available (if available) or an empty dictionary to store the results .
        :type taxonomy: dictionary
        :param lock: lock to keep the taxonomy threadsafe.
        :type lock: Lock
        :param queue: queue where the taxa are kept to be processed.
        :type queue: Queue of strings
        :param id: id for the thread to use if messages need to be printed.
        :type id: int 
        :param pref_db: Gives priority to database. Seems it is unused.
        :type pref_db: string 
        :param verbose: Show verbose messages during execution, will also define level of logging. True will set logging level to INFO.
        :type verbose: boolean
        :param ignoreWarnings: Ignore warnings and errors during execution? Errors will be logged with ERROR level on the logging output.
        :type ignoreWarnings: boolean 
        """

        threading.Thread.__init__(self)
        self.taxonomy = taxonomy
        self.lock = lock
        self.queue = queue
        self.id = id
        self.verbose = verbose
        self.pref_db = pref_db
        self.ignoreWarnings = ignoreWarnings

    def run(self):
        """ Gets and processes a taxon from the queue to get its taxonomy."""
        while True :
            if self.verbose :
                logging.getLogger().setLevel(logging.INFO)
            #get taxon from queue
            taxon = self.queue.get()

            logging.debug("Starting {} with thread #{} remaining ~{}".format(taxon,str(self.id),str(self.queue.qsize())))
             
            #Lock access to the taxonomy
            self.lock.acquire()
            if not taxon in self.taxonomy: # is a new taxon, not previously in the taxonomy
                #Release access to the taxonomy
                self.lock.release()
                if (self.verbose):
                    print "Looking up ", taxon
                    logging.info("Loolking up taxon: {}".format(str(taxon)))
                try:
                    # get the data from EOL on taxon
                    taxonq = quote_plus(taxon)
                    URL = "http://eol.org/api/search/1.0.json?q="+taxonq
                    req = urllib2.Request(URL)
                    opener = urllib2.build_opener()
                    f = opener.open(req)
                    data = json.load(f)
                    # check if there's some data
                    if len(data['results']) == 0:
                        # try PBDB as it might be a fossil
                        URL = "http://paleobiodb.org/data1.1/taxa/single.json?name="+taxonq+"&show=phylo&vocab=pbdb"
                        req = urllib2.Request(URL)
                        opener = urllib2.build_opener()
                        f = opener.open(req)
                        datapbdb = json.load(f)
                        if (len(datapbdb['records']) == 0):
                            # no idea!
                            with self.lock:
                                self.taxonomy[taxon] = {}
                            self.queue.task_done()
                            continue
                        # otherwise, let's fill in info here - only if extinct!
                        if datapbdb['records'][0]['is_extant'] == 0:
                            this_taxonomy = {}
                            this_taxonomy['provider'] = 'PBDB'
                            for level in taxonomy_levels:
                                try:
                                    if datapbdb.has_key('records'):
                                        pbdb_lev = datapbdb['records'][0][level]
                                        temp_lev = pbdb_lev.split(" ")
                                        # they might have the author on the end, so strip it off
                                        if (level == 'species'):
                                            this_taxonomy[level] = ' '.join(temp_lev[0:2])
                                        else:
                                            this_taxonomy[level] = temp_lev[0]       
                                except KeyError as e:
                                    logging.exception("Key not found records")
                                    continue
                            # add the taxon at right level too
                            try:
                                if datapbdb.has_key('records'):
                                    current_level = datapbdb['records'][0]['rank']
                                    this_taxonomy[current_level] = datapbdb['records'][0]['taxon_name']
                            except KeyError as e:
                                self.queue.task_done()
                                logging.exception("Key not found records")
                                continue
                            with self.lock:
                                self.taxonomy[taxon] = this_taxonomy
                            self.queue.task_done()
                            continue
                        else:
                            # extant, but not in EoL - leave the user to sort this one out
                            with self.lock:
                                self.taxonomy[taxon] = {}
                            self.queue.task_done()
                            continue

                                
                    ID = str(data['results'][0]['id']) # take first hit
                    # Now look for taxonomies
                    URL = "http://eol.org/api/pages/1.0/"+ID+".json"
                    req = urllib2.Request(URL)
                    opener = urllib2.build_opener()
                    f = opener.open(req)
                    data = json.load(f)
                    if len(data['taxonConcepts']) == 0:
                        with self.lock:
                            self.taxonomy[taxon] = {}
                        self.queue.task_done()
                        continue
                    TID = str(data['taxonConcepts'][0]['identifier']) # take first hit
                    currentdb = str(data['taxonConcepts'][0]['nameAccordingTo'])
                    # loop through and get preferred one if specified
                    # now get taxonomy
                    if (not self.pref_db is None):
                        for db in data['taxonConcepts']:
                            currentdb = db['nameAccordingTo'].lower()
                            if (self.pref_db.lower() in currentdb):
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
                            if a.has_key('taxonRank') :
                                temp_level = a['taxonRank'].encode("ascii","ignore")
                                if (temp_level in taxonomy_levels):
                                    # note the dump into ASCII
                                    temp_name = a['scientificName'].encode("ascii","ignore")
                                    temp_name = temp_name.split(" ")
                                    if (temp_level == 'species'):
                                        this_taxonomy[temp_level] = temp_name[0:2]
                                        
                                    else:
                                        this_taxonomy[temp_level] = temp_name[0]  
                        except KeyError as e:
                            logging.exception("Key not found: taxonRank")
                            continue
                    try:
                        # add taxonomy in to the taxonomy!
                        # some issues here, so let's make sure it's OK
                        temp_name = taxon.split(" ")            
                        if data.has_key('taxonRank') :
                            if not data['taxonRank'].lower() == 'species':
                                this_taxonomy[data['taxonRank'].lower()] = temp_name[0]
                            else:
                                this_taxonomy[data['taxonRank'].lower()] = ' '.join(temp_name[0:2])
                    except KeyError as e:
                        self.queue.task_done()
                        logging.exception("Key not found: taxonRank")
                        continue
                    with self.lock:
                        #Send result to dictionary
                        self.taxonomy[taxon] = this_taxonomy
                except urllib2.HTTPError:
                    print("Network error when processing {} ".format(taxon,))
                    logging.info("Network error when processing {} ".format(taxon,))
                    self.queue.task_done()
                    continue
                except urllib2.URLError:
                    print("Network error when processing {} ".format(taxon,))
                    logging.info("Network error when processing {} ".format(taxon,))
                    self.queue.task_done()
                    continue
            else :
                #Nothing to do release the lock on taxonomy
                self.lock.release()
            #Mark task as done
            self.queue.task_done()

def create_taxonomy_from_taxa(taxa, taxonomy=None, pref_db=None, verbose=False, ignoreWarnings=False, threadNumber=5):
    """Uses the taxa provided to generate a taxonomy for all the taxon available. 
    :param taxa: list of the taxa.
    :type taxa : list 
    :param taxonomy: previous taxonomy available (if available) or an empty 
    dictionary to store the results. If None will be init to an empty dictionary
    :type taxonomy: dictionary
    :param pref_db: Gives priority to database. Seems it is unused.
    :type pref_db: string 
    :param verbose: Show verbose messages during execution, will also define 
    level of logging. True will set logging level to INFO.
    :type verbose: boolean
    :param ignoreWarnings: Ignore warnings and errors during execution? Errors 
    will be logged with ERROR level on the logging output.
    :type ignoreWarnings: boolean 
    :param threadNumber: Maximum number of threads to use for taxonomy processing.
    :type threadNumber: int
    :returns: dictionary with resulting taxonomy for each taxon (keys) 
    :rtype: dictionary 
    """
    if verbose :
        logging.getLogger().setLevel(logging.INFO)
    if taxonomy is None:
        taxonomy = {}

    lock = threading.Lock()
    queue = Queue.Queue()

    #Starting a few threads as daemons checking the queue
    for i in range(threadNumber) :
        t = TaxonomyFetcher(taxonomy, lock, queue, i, pref_db, verbose, ignoreWarnings)
        t.setDaemon(True)
        t.start()
    
    #Popoluate the queue with the taxa.
    for taxon in taxa :
        queue.put(taxon)
    
    #Wait till everyone finishes
    queue.join()
    logging.getLogger().setLevel(logging.WARNING)

def create_taxonomy_from_tree(tree, existing_taxonomy=None, pref_db=None, verbose=False, ignoreWarnings=False):
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
    
    create_taxonomy_from_taxa(taxa, taxonomy)
    
    taxonomy = create_extended_taxonomy(taxonomy, starttime, verbose, ignoreWarnings)
    
    return taxonomy

def create_taxonomy(XML, existing_taxonomy=None, pref_db=None, verbose=False, ignoreWarnings=False):
    """Generates a taxonomy of the data from EoL data. This is stored as a
    dictionary of taxonomy for each taxon in the dataset. Missing data are
    encoded as '' (blank string). It's up to the calling function to store this
    data to file or display it."""
    
    starttime = time.time()

    if not ignoreWarnings:
        _check_data(XML)

    if (existing_taxonomy is None):
        taxonomy = {}
    else:
        taxonomy = existing_taxonomy
    taxa = get_all_taxa(XML, pretty=True)
    create_taxonomy_from_taxa(taxa, taxonomy)
    #taxonomy = create_extended_taxonomy(taxonomy, starttime, verbose, ignoreWarnings)
    return taxonomy

def create_extended_taxonomy(taxonomy, starttime, verbose=False, ignoreWarnings=False):
    """Bring extra taxonomy terms from other databases, shared method for completing the taxonomy
    both for trees comming from XML or directly from trees.
    :param taxonomy: Dictionary with the relationship for taxa and taxonomy terms.
    :type taxonomy: dictionary
    :param starttime: time to keep track of processing time.
    :type starttime: long
    :param verbose: Flag for verbosity.
    :type verbose: boolean
    :param ignoreWarnings: Flag for exception processing.
    :type ignoreWarnings: boolean
    :returns: the modified taxonomy
    :rtype: dictionary
    """
    
    if (verbose):
        logging.info('Done basic taxonomy, getting more info from ITIS')
        print("Time elapsed {}".format(str(time.time() - starttime)))
        print "Done basic taxonomy, getting more info from ITIS"
    # fill in the rest of the taxonomy
    # get all genera
    genera = []
    for t in taxonomy:
        if t in taxonomy:
            if GENUS in taxonomy[t]:
                genera.append(taxonomy[t][GENUS])
    genera = _uniquify(genera)
    # We then use ITIS to fill in missing info based on the genera only - that saves us a species level search
    # and we can fill in most of the EoL missing data
    for g in genera:
        if (verbose):
            print "Looking up ", g
            logging.info("Looking up {}".format(str(g)))
        try:
            URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(g.strip())
        except:
            continue
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        try:
            f = opener.open(req)
        except urllib2.HTTPError:
            continue
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
                # note the dump into ASCII            
                if level['rankName'].lower() == 'species':
                    this_taxonomy[level['rankName'].lower().encode("ascii","ignore")] = ' '.join.level['taxonName'][0:2].encode("ascii","ignore")
                else:
                    this_taxonomy[level['rankName'].lower().encode("ascii","ignore")] = level['taxonName'].encode("ascii","ignore")

        for t in taxonomy:
            if t in taxonomy:
                if GENUS in taxonomy[t]:
                    if taxonomy[t][GENUS] == g:
                        taxonomy[t].update(this_taxonomy)

    return taxonomy


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
"""stk_taxonomy

This module contains the taxonomy-processing and getting functions in the STK.
Most of these are not user-facing unless they are writing their own scripts.
The functions are generally called by the main supertree_toolkit functions and
require a taxonomy of some kind. 

Taxonomy is stored as a dictionary. I/O is done in a CSV file.

Most functions return the taxonomy dictionary.

"""
import os
import sys
from lxml import etree
sys.path.insert(0,"../../")
import string
import stk_exceptions as excp
from collections import defaultdict
import p4
import p4.MRP as MRP
import stk_internals
import stk_trees
import Queue
import threading
import urllib2
from urllib import quote_plus
import simplejson as json
from fuzzywuzzy import process
import backoff
import re

tag_re = re.compile(r'(<!--.*?-->|<[^>]*>)')

taxonomy_levels = ['species','subgenus','genus','tribe','subfamily','family','subsuperfamily','superfamily','subsection','section','parvorder','infraorder','suborder','order','superorder','subclass','infraclass', 'superinfraclass','class','superclass','subphylum','phylum','superphylum','infrakingdom','subkingdom','kingdom']

def taxonomic_checker_list(name_list,existing_data=None,pref_db="eol",verbose=False):
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
        #if t contains % strip off after that
        t = t.split('%')[0]
        if t in equivalents:
            continue
        taxon = t.replace("_"," ")
        if (verbose):
            print "Looking up ", taxon

        # each of these funcitons return a tuple of the correct name|synonyms and the status (red|green|yellow|amber)
        if (pref_db == "eol"):
            status = _check_taxa_eol(t,verbose)
        elif pref_db == 'worms':
            status = _check_taxa_worms(t,verbose)
        else:
            # raise something
            continue
            
        # put the data in the database
        equivalents[t] = status

    # now do some fuzzy pattern matching to sort out extra taxa
    taxa = equivalents.keys()
    for t in taxa:
        if equivalents[t][1] == "red":
            result = process.extract(t, taxa, limit=2)
            if len(result) == 1:
                continue
            # returns something like
            # [('Thyanoessa_macrura', 100), ('Thysanoessa_macrura', 97)]
            # first hit is the taxon in question
            # second hit is the next closest. Above 90, we assume a typo or two and pick that as a yellow instead of red
            if result[1][1] > 90: # % fuzzy match
                # only if results[1][0] is green! No point if red or yellow or amber. If yellow or amber sub in with the proper thing
                if equivalents[result[1][0]][1] == 'green':
                    equivalents[t] = [[result[1][0]], "yellow"]
                elif equivalents[result[1][0]][1] == 'yellow':
                    # this is horrible, sorry
                    # result[1][0] - name on second hit on fuzzy name search, is X in...
                    # equivalents[X][0] - name hit on the equivalents dictioanry
                    equivalents[t] = [equivalents[result[1][0]][0],'yellow']
                elif  equivalents[result[1][0]][1] == 'amber':
                    equivalents[t] = [equivalents[result[1][0]][0],'amber']
                else:
                    # red, no nothing 
                    pass

    # up to the calling funciton to do something sensible with this
    # we build a dictionary of names and then a list of synonyms or the original name, then a tag if it's green, yellow, red.
    # Amber means we found synonyms and multilpe hits. User def needs to sort these!

    return equivalents


def _check_taxa_eol(taxon,verbose=False):

    @backoff.on_exception(backoff.expo,
                      urllib2.ssl.SSLError,
                      max_tries=4)
    @backoff.on_exception(backoff.expo,
                      urllib2.HTTPError,
                      max_tries=4)
    def url_open(req):
        return opener.open(req)
    
    status = ''
    correct_name = []

    # get the data from EOL on taxon
    taxonq = quote_plus(taxon.replace("_"," "))
    URL = "http://eol.org/api/search/1.0.json?q="+taxonq
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    try:
        f = url_open(req)
    except (urllib2.HTTPError, urllib2.ssl.SSLError):
        correct_name = [taxon]
        status = 'red'
        return (correct_name, status)
    data = json.load(f)
    if data == None or len(data['results']) == 0:
        correct_name = [taxon]
        status = 'red'
        return (correct_name, status)

    if int(data['totalResults'] == 1):
        # one hit. Might be the same, might be the only synonym...we change to green later if we can
        status = "yellow"
    elif int(data['totalResults']) < 50:
        # this is not great - we have multiple hits for this taxon - but there's a limited nuber
        # so it may be ok - we'll take the first hit in ths case and swap
        status = 'amber'    
    elif int(data['totalResults']) >= 50:
        # lots of hits. Bad. Consider this red, but we record the hits
        status = 'red'
 
    ID = str(data['results'][0]['id']) # take first hit

    URL = "http://eol.org/api/pages/1.0/"+ID+".json?common_names=true&synonyms=true"       
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    try:
        f = url_open(req)
    except (urllib2.HTTPError, urllib2.ssl.SSLError) :
        correct_name = [taxon]
        status = 'red'
        return (correct_name, status)
    tdata = json.load(f)
    # some sources are basically rubbish, so try using EOL's data first
    for i in range(0,len(tdata['taxonConcept']['taxonConcepts'])):
        if "EOL" in tdata['taxonConcept']['taxonConcepts'][i]['nameAccordingTo']:
            break
    if i == len(tdata['taxonConcept']['taxonConcepts'])-1:
        i = 0

    if len(tdata['taxonConcept']['taxonConcepts'][i]['scientificName']) == 0:
        # not found a scientific name, so set as red
        correct_name = [taxon]
        status = 'red'
        return (correct_name, status)

    correct_name = tdata['taxonConcept']['taxonConcepts'][i]['scientificName'].encode("ascii","ignore")
    # we only want the first two bits of the name, not the original author and year if any
    correct_name = re.sub(r'\([^)]*\)', '', correct_name) # remove ()
    correct_name = ' '.join(correct_name.split()) # remove extra whitespace
    temp_name = correct_name.split()

    if (len(temp_name) >= 2 and len(tdata['taxonConcept']['taxonConcepts']) > 0 and 'taxonRank' in tdata['taxonConcept']['taxonConcepts'][i] and
            (tdata['taxonConcept']['taxonConcepts'][i]['taxonRank'].lower() == 'species' or 
             tdata['taxonConcept']['taxonConcepts'][i]['taxonRank'].lower() == 'infraspecies' or
             tdata['taxonConcept']['taxonConcepts'][i]['taxonRank'].lower() == 'subspecies')):
        correct_name = ' '.join(temp_name[0:2])
    elif len(temp_name) >= 2 and len(tdata['taxonConcept']['taxonConcepts']) == 0:
        # crap. We have a long name with extra stuff, but no idea if this is 
        # a species, genus or what. # loop through hits until we hit one with some knowledge
        # of the taxonRank (only first page of hits - 30 by default)
        for i in range(0,len(data['results'])):
            ID = str(data['results'][i]['id'])
            URL = "http://eol.org/api/pages/1.0/"+ID+".json?images=0&videos=0&sounds=0&maps=0&text=0&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0"       
            req = urllib2.Request(URL)
            opener = urllib2.build_opener()
            try:
                f = url_open(req)
            except urllib2.HTTPError:
                continue
            tdata = json.load(f)
            if len(tdata['scientificName']) == 0:
                continue
            try:
                # ha! found one!
                correct_name = tdata['scientificName'].encode("ascii","ignore")
                # we only want the first two bits of the name, not the original author and year if any
                correct_name = re.sub(r'\([^)]*\)', '', correct_name) # remove ()
                correct_name = ' '.join(correct_name.split()) # remove extra whitespace
                temp_name = correct_name.split()
                if (len(temp_name) >= 2 and len(tdata['taxonConcepts']) > 0 and 'taxonRank' in tdata['taxonConcepts'][0] and
                        (tdata['taxonConcept']['taxonConcepts'][0]['taxonRank'].lower() == 'species' or 
                         tdata['taxonConcept']['taxonConcepts'][0]['taxonRank'].lower() == 'infraspecies' or
                         tdata['taxonConcept']['taxonConcepts'][0]['taxonRank'].lower() == 'subspecies')):
                    correct_name = ' '.join(temp_name[0:2])
                else:
                    correct_name = temp_name[0]   
                break
            except:
                pass
    else:
        correct_name = temp_name[0] 
    correct_name = correct_name.replace(' ','_')

    # build up the output dictionary - original name is key, synonyms/missing is value
    if (correct_name == taxon):
         # if the original matches the 'correct', then it's green
         return ([taxon], 'green')
    else:
         # if we managed to get something anyway, then it's yellow or amber and create a list of possible synonyms with the 
         # 'correct' taxon at the top
         eol_synonyms = tdata['taxonConcept']['synonyms']
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
         synonyms = stk_internals.uniquify(synonyms)
         # we need to put the correct name at the top of the list now
         if (correct_name in synonyms):
             synonyms.pop(synonyms.index(correct_name))
             synonyms.insert(0, correct_name)
         elif len(synonyms) == 0:
             synonyms.append(correct_name)
         else:
             synonyms.insert(0,correct_name)

         if len(synonyms) == 1:
             status = "yellow" # the multilpe hits were probably all synonyms and different sources

         if status == 'amber':
             return (synonyms,'amber')
         elif status == "yellow":
             return (synonyms,'yellow')
         elif status == "red":
             return (synonyms,'red')
    # if our search was empty, then it's red - see above
    correct_name = [taxon]
    status = 'red'
    return (correct_name, status)


def _check_taxa_worms(taxon,verbose=False):

    import zeep

    wsdlObjectWoRMS = zeep.Client(wsdl='http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')
    
    status = 'red'
    correct_name = []

    # get the data from EOL on taxon
    taxon_data = wsdlObjectWoRMS.service.getAphiaRecords(taxon.replace('_',' '), like='false', fuzzy='true', marine_only='false', offset=0)
    if len(taxon_data) == 0:
        # try vernacular names
        taxon_data = wsdlObjectWoRMS.service.getAphiaRecordsByVernacular(taxon.replace('_',' '), like='false', offset=0)
        if len(taxon_data) == 0:
            correct_name = [taxon]
            status = 'red'
            return (correct_name, status)

    amber = False
    if len(taxon_data) > 1:
        # this is not great - we have multiple hits for this taxon - needs the user to go back and warn about this
        # for automatic processing we'll just take the first one though
        # colour is amber in this case
        amber = True

    taxon_id = taxon_data[0]['valid_AphiaID'] # there might be records that aren't valid - they point to the valid one though
    # call it again via the ID this time to make sure we've got the right one.
    taxon_data = wsdlObjectWoRMS.service.getAphiaRecordByID(taxon_id)

    if len(taxon_data['scientificname']) == 0:
        # not found a scientific name, so set as red
        correct_name = [taxon]
        status = 'red'
        return (correct_name, status)

    correct_name = taxon_data['scientificname']
    # we only want the first two bits of the name, not the original author and year if any
    temp_name = correct_name.split(' ')
    if (len(temp_name) > 2):
        correct_name = ' '.join(temp_name[0:2])
    correct_name = correct_name.replace(' ','_')

    # build up the output dictionary - original name is key, synonyms/missing is value
    if (taxon_data['status'] == 'accepted' and correct_name == taxon):
        # if the original matches the 'correct', then it's green
        return ([correct_name], 'green')
    elif (taxon_data['status'] == 'accepted' and not correct_name == taxon):
        if (amber):
            return ([correct_name], 'amber')
        else:
            return ([correct_name], 'yellow')

    # if our search was empty, then it's red - see above
    correct_name = [taxon]
    status = 'red'
    return (correct_name, status)



def save_taxonomy(taxonomy, output_file):

    import csv

    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        row = ['OTU']
        row.extend(taxonomy_levels)
        row.append('Provider')
        writer.writerow(row)
        taxa_list = taxonomy.keys()
        taxa_list.sort()
        for t in taxa_list:
            species = t
            row = []
            row.append(t.encode('utf-8'))
            for l in taxonomy_levels:
                try:
                    g = taxonomy[t][l]
                    if taxonomy[t][l] == None:
                        g = "-"
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
                        if not row[i] == "":
                            current_taxonomy[t] = row[i].replace(" ","_")
                    i = i+ 1
                current_taxonomy['provider'] = row[-1] # data source
                taxonomy[row[0].replace(" ","_")] = current_taxonomy
                j += 1
        except:
            pass
    
    return taxonomy


def get_taxonomy(taxonomy, lock, queue, id=0, pref_db='eol', check_fossil=True, verbose=False, ignoreWarnings=False):
        """
        :param taxonomy: previous taxonomy available (if available) or an empty dictionary to store the results .
        :type taxonomy: dictionary
        :param lock: lock to keep the taxonomy threadsafe.
        :type lock: Lock
        :param queue: queue where the taxa are kept to be processed.
        :type queue: Queue of strings
        :param id: id for the thread to use if messages need to be printed.
        :type id: int 
        :param pref_db: Gives preferred DB. Can be backfilled with "create_extended_taxonomy"
        :type pref_db: string 
        :param check_fossil: If a taxon can't be found in the preferred database, check PBDB in case it's a fossil
        :type pref_db: boolean
        :param verbose: Show verbose messages during execution, will also define level of logging. True will set logging level to INFO.
        :type verbose: boolean
        :param ignoreWarnings: Ignore warnings and errors during execution? Errors will be logged with ERROR level on the logging output.
        :type ignoreWarnings: boolean 
        """

        while True :
            # get taxon from queue
            taxon = queue.get()
            # Lock access to the taxonomy
            lock.acquire()
            if not taxon in taxonomy: # is a new taxon, not previously in the taxonomy
                # Release access to the taxonomy
                lock.release()
                if (verbose):
                    print "Looking up "+taxon
                try:
                    if pref_db == 'eol':
                        this_taxonomy = get_taxonomy_for_taxon_eol(taxon)
                    elif pref_db == 'worms':
                        this_taxonomy = get_taxonomy_for_taxon_worms(taxon)
                    elif pref_db == 'itis':
                        this_taxonomy = get_taxonomy_for_taxon_itis(taxon)
                    elif pref_db == 'pbdb':
                        this_taxonomy = get_taxonomy_for_taxon_pbdb(taxon)
                    else:
                        # raise something?
                        queue.task_done()
                        break
                finally:
                    queue.task_done()
                    break
                if (check_fossil and this_taxonomy == {} and pref_db != 'pbdb'):
                    this_taxonomy = get_taxonomy_for_taxon_pbdb(taxon)

                if this_taxonomy == None:
                    queue.task_done()
                    continue
                
                with lock:
                    #Send result to dictionary
                    taxonomy[taxon.replace(" ","_")] = this_taxonomy
            else :
                if verbose:
                    print "Skipping: "+taxon+"\n",
                # Nothing to do release the lock on taxonomy
                lock.release()
            
            # Mark task as done
            queue.task_done()


def create_taxonomy_from_taxa(taxa, taxonomy=None, pref_db=None, check_fossil=False, verbose=False, ignoreWarnings=False, threadNumber=10):
    """Uses the taxa provided to generate a taxonomy for all the taxon available. 
    :param taxa: list of the taxa.
    :type taxa: list 
    :param taxonomy: previous taxonomy available (if available) or an empty 
    dictionary to store the results. If None will be init to an empty dictionary
    :type taxonomy: dictionary
    :param pref_db: Gives priority to database.
    :type pref_db: string 
    :param verbose: Show verbose messages during execution
    :type verbose: boolean
    :param ignoreWarnings: Ignore warnings and errors during execution?
    :type ignoreWarnings: boolean 
    :param threadNumber: Maximum number of threads to use for taxonomy processing.
    :type threadNumber: int
    :returns: dictionary with resulting taxonomy for each taxon (keys) 
    :rtype: dictionary 
    """
    if taxonomy is None:
        taxonomy = {}

    lock = threading.Lock()
    queue = Queue.Queue()

    # Starting a few threads as daemons checking the queue
    #for i in range(threadNumber) :
    #    t = threading.Thread(target=get_taxonomy, args=(taxonomy, lock, queue, i, pref_db, check_fossil, verbose, ignoreWarnings))
    #    t.setDaemon(True)
    #    t.start()
    
    ## Populate the queue with the taxa.
    for taxon in taxa:
        #if t contains % strip off after that
        taxon = taxon.split('%')[0]
        taxon = taxon.replace(" ","_")
        taxon.strip()
        if (verbose):
            print "Looking up "+taxon
        if pref_db == 'eol':
            this_taxonomy = get_taxonomy_for_taxon_eol(taxon)
        elif pref_db == 'worms':
            this_taxonomy = get_taxonomy_for_taxon_worms(taxon)
        elif pref_db == 'itis':
            this_taxonomy = get_taxonomy_for_taxon_itis(taxon)
        elif pref_db == 'pbdb':
            this_taxonomy = get_taxonomy_for_taxon_pbdb(taxon)
        else:
            # raise something?
            break
        if (check_fossil and this_taxonomy == {} and pref_db != 'pbdb'):
            this_taxonomy = get_taxonomy_for_taxon_pbdb(taxon)
        taxonomy[taxon.replace(" ","_")] = this_taxonomy
        #queue.put(taxon)
    
    # Wait till everyone finishes
    #queue.join()

    return taxonomy


def create_extended_taxonomy(taxonomy, pref_db='eol', verbose=False, ignoreWarnings=False, threadNumber=5):
    """Bring extra taxonomy terms from other databases, but pref_db is maintained
    :param taxonomy: Dictionary with the relationship for taxa and taxonomy terms.
    :type taxonomy: dictionary
    :param verbose: Flag for verbosity.
    :type verbose: boolean
    :param ignoreWarnings: Flag for exception processing.
    :type ignoreWarnings: boolean
    :param threadNumber: Maximum number of threads to use for taxonomy processing.
    :type threadNumber: int
    :returns: the modified taxonomy
    :rtype: dictionary
    """

    def update_taxonomy(taxonomy,additions):

        uber_taxonomy = {}
        for t in taxonomy:
            if t in additions:
                additions[t].update(taxonomy[t])
                uber_taxonomy[t] = additions[t]
            else:
                uber_taxonomy[t] = taxonomy[t]

        return uber_taxonomy
    
    # get taxa from existing taxonomy
    taxa = taxonomy.keys()

    if pref_db == 'eol':
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'itis')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'worms')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)        
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'pbdb')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)
    if pref_db == 'itis':
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'eol')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'worms')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)        
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'pbdb')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy) 
    if pref_db == 'worms':
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'itis')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'eol')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)        
        temp_taxonomy = create_taxonomy_from_taxa(taxa, pref_db = 'pbdb')
        taxonomy = update_taxonomy(taxonomy,temp_taxonomy)

    return taxonomy


def tree_from_taxonomy(top_level, tree_taxonomy):
    """ Create a tree from a taxonomy hash. Supply the starting level (e.g. Order) and the taxonomy.
        Returns: tree string
    """
    from ete2 import Tree
    
    start_level = taxonomy_levels.index(top_level)

    tl_types = []
    for tt in tree_taxonomy.keys():
        try:
            tl_types.append(tree_taxonomy[tt][top_level])
        except KeyError:
            # no info, remove
            del tree_taxonomy[tt]

    new_taxa = tree_taxonomy.keys()

    tl_types = stk_internals.uniquify(tl_types)
    levels_to_worry_about = taxonomy_levels[0:taxonomy_levels.index(top_level)+1]
        
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
        names = stk_internals.uniquify(names)
        for n in names:
            # find my parent
            parent = None
            for tt in tree_taxonomy:
                try:
                    if tree_taxonomy[tt][l] == n:
                        for jj in range(1,len(taxonomy_levels)-ci+1): # rest of taxonomy levels available
                            try:
                                parent = tree_taxonomy[tt][levels_to_worry_about[ci+jj]]
                                level = ci+jj
                                break # break the loop and jj get fixed < len(taxonomy_levels)-ci+1
                            
                            except KeyError: # this will loop until we find something
                                pass
                       
                            if jj == len(taxonomy_levels)-ci+1: # we completed the loop and found nothing!
                                print "ERROR: tried to find some taxonomic info for "+tt+" from tree_taxonomy file/downloaded data."
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
            #print n#, parent, node_id
            nodes[l].append({n:nd})

    tree = t.write(format=9)  
    try:
        pass
        #tree = stk_trees.collapse_nodes(tree)
        #tree = stk_trees.collapse_nodes(tree)
        #tree = stk_trees.collapse_nodes(tree)
        #tree = stk_trees.collapse_nodes(tree)
    except excp.TreeParseError:
        print e.msg
        return None

    return tree

def get_taxonomy_for_taxon_otl(taxon):
    """Fetches taxonomic info a single taxon from the OpenTree of Life taxonomy database
     Return: dictionary of taxonomic levels ready to put in a taxonomy dictionary
     """
    @backoff.on_exception(backoff.expo,
                      urllib2.HTTPError,
                      max_tries=4)
    def url_open(req):
        return opener.open(req)

    


# these function need to add genus from the taxon name
# as that's alway available
# also check it's a species coming in!

def get_taxonomy_for_taxon_pbdb(taxon):
    """Fetches taxonomic info a single taxon from the PBDB database (if extinct only)
     Return: dictionary of taxonomic levels ready to put in a taxonomy dictionary
     """

    @backoff.on_exception(backoff.expo,
                      urllib2.ssl.SSLError,
                      max_tries=4)
    @backoff.on_exception(backoff.expo,
                      urllib2.HTTPError,
                      max_tries=4)
    def url_open(req):
        # PBDB is seriously slow....
        return opener.open(req,timeout=60)

    taxonomy = {'species': taxon}
    taxonq = quote_plus(taxon) 
    URL = "http://paleobiodb.org/data1.2/taxa/single.json?name="+taxonq+"&show=phylo&vocab=pbdb"
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    try:
        f = url_open(req)
    except urllib2.HTTPError:
        return taxonomy
    datapbdb = json.load(f)
    if (len(datapbdb['records']) == 0):
        return taxonomy   
    # otherwise, let's fill in info here - only if extinct!
    if datapbdb['records'][0]['is_extant'] == 'extinct':
        taxonomy['provider'] = 'PBDB'
        for level in taxonomy_levels:
            try:
                if datapbdb.has_key('records'):
                    pbdb_lev = datapbdb['records'][0][level]
                    temp_lev = pbdb_lev.split(" ")
                    # they might have the author on the end, so strip it off
                    if (level == 'species'):
                        taxonomy[level] = ' '.join(temp_lev[0:2])
                    else:
                        taxonomy[level] = temp_lev[0]       
            except KeyError as e:
                pass
        # add the taxon at right level too
        try:
            if datapbdb.has_key('records'):
                current_level = datapbdb['records'][0]['taxon_rank']
                taxonomy[current_level] = datapbdb['records'][0]['accepted_name']
        except KeyError as e:
            pass

    return taxonomy

def get_taxonomy_for_taxon_eol(taxon):

    """Fetches taxonomic info for a single taxon from the EOL database
     Return: dictionary of taxonomic levels ready to put in a taxonomy dictionary
     """
    @backoff.on_exception(backoff.expo,
                      urllib2.ssl.SSLError,
                      max_tries=4)
    @backoff.on_exception(backoff.expo,
                      urllib2.HTTPError,
                      max_tries=4)
    def url_open(req):
        return opener.open(req)

    taxonomy = {}
    taxon = taxon.replace("_"," ")
    taxonq = quote_plus(taxon)
    URL = "http://eol.org/api/search/1.0.json?q="+taxonq
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    try:
        f = url_open(req)
    except (urllib2.HTTPError, urllib2.ssl.SSLError) :
        return taxonomy

    data = json.load(f)
    
    if data['results'] == []:
        return taxonomy
    # take first hit - TODO: add more finese here
    ID = str(data['results'][0]['id'])
    # Now look for taxonomies
    URL = "http://eol.org/api/pages/1.0/"+ID+".json"
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    try:
        f = url_open(req)
    except (urllib2.HTTPError, urllib2.ssl.SSLError) :
        return taxonomy
    data = json.load(f)
    if len(data['taxonConcept']['taxonConcepts']) == 0:
        return taxonomy
    # some sources are basically rubbish, so try using EOL's data first
    TID = None
    for i in range(0,len(data['taxonConcept']['taxonConcepts'])):
        if "EOL Dynamic Hierarchy 1.1" in data['taxonConcept']['taxonConcepts'][i]['nameAccordingTo']:
            TID = str(data['taxonConcept']['taxonConcepts'][i]['identifier'])
            currentdb = data['taxonConcept']['taxonConcepts'][i]['nameAccordingTo'].encode("ascii","ignore")
            break
    if TID == None:
        # take first one and hope for the best
        TID = str(data['taxonConcept']['taxonConcepts'][0]['identifier']) # take first hit
        currentdb = data['taxonConcept']['taxonConcepts'][0]['nameAccordingTo'].encode("ascii","ignore")


    # now get taxonomy        
    URL="http://eol.org/api/hierarchy_entries/1.0/"+TID+".json"
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    try:
        f = url_open(req)
    except (urllib2.HTTPError, urllib2.ssl.SSLError) :
        return taxonomy
    data = json.load(f)
    taxonomy = taxonomy
    taxonomy['provider'] = currentdb
    for a in data['ancestors']:
        try:
            if a.has_key('taxonRank') and not a['taxonRank'] == None:
                temp_level = a['taxonRank'].encode("ascii","ignore")
                if (temp_level in taxonomy_levels):
                    # note the dump into ASCII
                    no_tags = tag_re.sub('', a['scientificName'])
                    temp_name = no_tags.encode("ascii","ignore")
                    temp_name = temp_name.split(" ")
                    if (temp_level == 'species'):
                        taxonomy[temp_level] = " ".join(temp_name[0:2])
                        
                    else:
                        taxonomy[temp_level] = temp_name[0]  
        except KeyError as e:
            logging.exception("Key not found: taxonRank")
            continue

    try:
        # add taxonomy in to the taxonomy!
        # This adds the actuall taxon being searched for to the taxonomy
        # sub-species will be ignored here, giving two entries for the same species, but under different OTUs
        temp_name = taxon.split(" ")
        if data.has_key('taxonRank')  and not data['taxonRank'] == None:
            if (data['taxonRank'].lower() != 'species' and 
               data['taxonRank'].lower() in taxonomy_levels):
                taxonomy[data['taxonRank'].lower()] = temp_name[0]
            elif data['taxonRank'].lower() in taxonomy_levels:
                taxonomy[data['taxonRank'].lower()] = ' '.join(temp_name[0:2])
    except KeyError as e:
       return taxonomy 

    return taxonomy

def get_taxonomy_for_taxon_worms(taxon):

    import zeep

    taxonomy = {'species': taxon}

    wsdlObjectWoRMS = zeep.Client(wsdl='http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')

    taxon_data = wsdlObjectWoRMS.service.getAphiaRecords(taxon.replace('_',' '), like='false', fuzzy='false', marine_only='false', offset=0)
    if len(taxon_data) == 0:
        return taxonomy

    taxon_id = taxon_data[0]['valid_AphiaID'] # there might be records that aren't valid - they point to the valid one though
    # call it again via the ID this time to make sure we've got the right one.
    taxon_data = wsdlObjectWoRMS.service.getAphiaRecordByID(taxon_id)
    # add data to taxonomy dictionary
    # get the taxonomy of this species
    classification = wsdlObjectWoRMS.service.getAphiaClassificationByID(taxon_id)
    # construct array
    if (classification == ""):
        return taxonomy
    # classification is a nested dictionary, so we need to iterate down it
    current_child = classification["child"]
    taxonomy['provider'] = 'WoRMS'
    while True:
        if current_child['rank'].lower() in taxonomy_levels:
            taxonomy[current_child['rank'].lower()] = current_child['scientificname']
        current_child = current_child['child']
        if current_child['rank'] == None: 
            break
    return taxonomy


def get_taxonomy_for_taxon_itis(taxon):

    taxonomy = {'species': taxon}
    URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(taxon.replace('_',' ').strip())
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = opener.open(req)    
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    if this_item['scientificNames'] == [None]: # not found
        return taxonomy
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
    taxonomy['provider'] = 'ITIS'    
    for level in data['hierarchyList']:
        if level['rankName'].lower() in taxonomy_levels:
            # note the dump into ASCII            
            taxonomy[level['rankName'].lower().encode("ascii","ignore")] = level['taxonName'].encode("ascii","ignore")

    return taxonomy


# retuns any fossil taxa too. Can't turn this off.
def get_taxonomy_eol(taxonomy, start_otu, verbose=False, tmpfile=None, skip=False):

    @backoff.on_exception(backoff.expo,
                      urllib2.HTTPError,
                      max_tries=1)
    def url_open(req):
        return opener.open(req)

        
    # this is the recursive function
    def get_children(taxonomy, ID, aphiaIDsDone):

        # get data
        URL="http://eol.org/api/hierarchy_entries/1.0/"+str(ID)+".json?common_names=false&synonyms=false&cache_ttl="
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = url_open(req)
        string = unicode(f.read(),"ISO-8859-1")
        this_item = json.loads(string)
        if this_item == None:
            return taxonomy 
        try:
            if this_item['taxonRank'].lower().strip() == 'species':
                # add data to taxonomy dictionary
                # EOL have helpfully added <i> tags. Strip 'em
                no_tags = tag_re.sub('', this_item['scientificName'])
                taxon = no_tags.split()[0:2] # just the first two words
                taxon = " ".join(taxon[0:2])
                # NOTE following line means existing items are *not* updated
                if not taxon in taxonomy: # is a new taxon, not previously in the taxonomy
                    this_taxonomy = {}
                    for level in this_item['ancestors']:
                        if level['taxonRank'].lower() in taxonomy_levels:
                            # note the dump into ASCII            
                            temp_name = level['scientificName'].encode("ascii","ignore").split(" ")
                            temp_name = temp_name[0]
                            this_taxonomy[level['taxonRank'].lower().encode("ascii","ignore")] = temp_name
                    # add species:
                    this_taxonomy['species'] = taxon.encode("ascii","ignore").replace("_"," ")
                    this_taxonomy['provider'] = 'EOL'
                    if verbose:
                        print "\tAdding "+taxon
                    taxonomy[taxon.encode("ascii","ignore")] = this_taxonomy
                    if not tmpfile == None:
                        stk.save_taxonomy(taxonomy,tmpfile)
                    return taxonomy
                else:
                    return taxonomy
        except KeyError:
            pass

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
    f = url_open(req)
    data = json.load(f)
    highest_rank = taxonomy_levels.index('species')
    high_level_start_id = 0000000
    print data
    # ignores pages. FIXME
    for ids in range(0,data['totalResults']):
        start_id = str(data['results'][ids]['id']) # this is the page ID. We get the OTU ID next
        URL = "http://eol.org/api/pages/1.0/"+start_id+".json"
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = url_open(req)
        data2 = json.load(f)
        if len(data2['taxonConcept']['taxonConcepts']) == 0:
            continue
        start_id = data2['taxonConcept']['taxonConcepts'][0]['identifier']
        start_taxonomy_level = data2['taxonConcept']['taxonConcepts'][0]['taxonRank'].lower()
        if taxonomy_levels.index(start_taxonomy_level) > highest_rank:
            high_level_start_id = start_id

    start_id = high_level_start_id
    aphiaIDsDone = []
    if not skip:
        taxonomy = get_children(taxonomy,start_id,aphiaIDsDone)

    return taxonomy, start_taxonomy_level



def get_taxonomy_itis(taxonomy, start_otu, verbose,tmpfile=None,skip=False):
    @backoff.on_exception(backoff.expo,
                      urllib2.HTTPError,
                      max_tries=4)
    def url_open(req):
        return opener.open(req)

    # this is the recursive function
    def get_children(taxonomy, ID, aphiaIDsDone):

        # get data
        URL="http://www.itis.gov/ITISWebService/jsonservice/getFullRecordFromTSN?tsn="+ID
        req = urllib2.Request(URL)
        opener = urllib2.build_opener()
        f = url_open(req)
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
                f = url_open(req)
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
        f = url_open(req)
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
            

    # main bit
    URL="http://www.itis.gov/ITISWebService/jsonservice/searchByScientificName?srchKey="+quote_plus(start_otu.strip())
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = url_open(req)
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    start_id = this_item['scientificNames'][0]['tsn'] # there might be records that aren't valid - they point to the valid one though
    # call it again via the ID this time to make sure we've got the right one.
    # so call another function to get any valid names
    URL="http://www.itis.gov/ITISWebService/jsonservice/getAcceptedNamesFromTSN?tsn="+start_id
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = url_open(req)
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    if not this_item['acceptedNames'] == [None]:
        start_id = this_item['acceptedNames'][0]['acceptedTsn']

    URL="http://www.itis.gov/ITISWebService/jsonservice/getFullRecordFromTSN?tsn="+start_id
    req = urllib2.Request(URL)
    opener = urllib2.build_opener()
    f = url_open(req)
    string = unicode(f.read(),"ISO-8859-1")
    this_item = json.loads(string)
    start_taxonomy_level = this_item['taxRank']['rankName'].lower().strip()

    aphiaIDsDone = []
    if not skip:
        taxonomy = get_children(taxonomy,start_id,aphiaIDsDone)

    return taxonomy, start_taxonomy_level




def get_taxonomy_worms(taxonomy, start_otu, verbose,tmpfile=None,skip=False):
    """ Gets and processes a taxon from the queue to get its taxonomy."""
    import zeep 

    wsdlObjectWoRMS = zeep.Client('http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')

    # this is the recursive function
    def get_children(taxonomy, ID, aphiaIDsDone):

        # get data
        this_item = wsdlObjectWoRMS.service.getAphiaRecordByID(ID)
        if this_item == None:
            return taxonomy
        if not this_item['status'].lower() == 'accepted':
            if verbose:
                print "rejecting " , this_item['scientificname']
            return taxonomy        
        if this_item['rank'].lower() == 'species':
            # add data to taxonomy dictionary
            taxon = this_item['valid_name']
            # NOTE following line means existing items are *not* updated
            if not taxon in taxonomy: # is a new taxon, not previously in the taxonomy
                # get the taxonomy of this species
                classification = wsdlObjectWoRMS.service.getAphiaClassificationByID(ID)
                # construct array
                tax_array = {}
                # classification is a nested dictionary, so we need to iterate down it
                current_child = classification['child']
                while True:
                    if taxonomy_levels.index(current_child['rank'].lower()) <= taxonomy_levels.index(start_taxonomy_level):
                        # we need this - we're closer to the tips of the tree than we started
                        tax_array[current_child['rank'].lower()] = current_child['scientificname']
                    current_child = current_child['child']
                    if current_child['rank'] == None: 
                        break
                if verbose:
                    print "\tAdding "+this_item.scientificname
                taxonomy[this_item['valid_name']] = tax_array
                if not tmpfile == None:
                    stk.save_taxonomy(taxonomy,tmpfile)
                return taxonomy
            else:
                return taxonomy

        all_children = []
        start = 1
        while True:
            children = wsdlObjectWoRMS.service.getAphiaChildrenByID(ID, start, False)
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
            if child['valid_AphiaID'] == None:
                continue
            if child['valid_AphiaID'] in aphiaIDsDone: # we get stuck sometime
                continue
            aphiaIDsDone.append(child['valid_AphiaID'])
            taxonomy = get_children(taxonomy, child['valid_AphiaID'], aphiaIDsDone)
        return taxonomy
            

    # main bit of the get_taxonomy_worms function
    try:
        start_taxa = wsdlObjectWoRMS.service.getAphiaRecords(start_otu.replace('_',' ') , like='false', fuzzy='false', marine_only='false', offset=0)
        if len(start_taxa) == 0:
            return {}

        start_id = start_taxa[0]['valid_AphiaID'] # there might be records that aren't valid - they point to the valid one though
        # call it again via the ID this time to make sure we've got the right one.
        start_taxa = wsdlObjectWoRMS.service.getAphiaRecordByID(start_id)
        start_taxonomy_level = start_taxa['rank'].lower()
    except urllib2.HTTPError:
        print "Error finding start_otu taxonomic level. Do you have an internet connection?"
        sys.exit(-1)

    aphiaIDsDone = []
    if not skip:
        taxonomy = get_children(taxonomy,start_id,aphiaIDsDone)

    return taxonomy, start_taxonomy_level


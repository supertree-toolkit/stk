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
from SOAPpy import WSDL

class TaxonomyFetcherWorms(threading.Thread):            
    """ Class to provide the taxonomy fetching from WORMS
    """

    def __init__(self, taxonomy, lock, queue, id=0, verbose=False, ignoreWarnings=False):
        """ Constructor for the threaded model.
        :param taxonomy: previous taxonomy available (if available) or an empty dictionary to store the results .
        :type taxonomy: dictionary
        :param lock: lock to keep the taxonomy threadsafe.
        :type lock: Lock
        :param queue: queue where the taxa are kept to be processed.
        :type queue: Queue of strings
        :param id: id for the thread to use if messages need to be printed.
        :type id: int 
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
             
            if not taxon in self.taxonomy: # is a new taxon, not previously in the taxonomy
                #Release access to the taxonomy
                self.lock.release()
                if (self.verbose):
                    print "Looking up ", taxon
                    logging.info("Looking up taxon: {}".format(str(taxon)))
                try:
                    wsdlObjectWoRMS = WSDL.Proxy('http://www.marinespecies.org/aphia.php?p=soap&wsdl=1')
                    a = wsdlObjectWoRMS.getAphiaRecords('Lopholithodes foraminatus', like='true', fuzzy='false', marine_only='false')

                    t = wsdlObjectWoRMS.getAphiaClassificationByID(378125)

"""
In [4]: a = wsdlObjectWoRMS.getAphiaRecords('Lopholithodes foraminatus', like='true', fuzzy='false', marine_only='false')

In [5]: a
Out[5]: [<SOAPpy.Types.structType item at 140452007880896>: {'kingdom': 'Animalia', 'match_type': 'exact', 'isFreshwater': None, 'family': 'Lithodidae', 'citation': 'Ahyong, S. (2014). Lopholithodes foraminatus (Stimpson, 1859). Accessed through:  World Register of Marine Species at http://www.marinespecies.org/aphia.php?p=taxdetails&id=378125 on 2015-01-26', 'rank': 'Species', 'unacceptreason': None, 'phylum': 'Arthropoda', 'valid_name': 'Lopholithodes foraminatus', 'isExtinct': None, 'AphiaID': 378125, 'isMarine': 1, 'status': 'accepted', 'valid_authority': '(Stimpson, 1859)', 'lsid': 'urn:lsid:marinespecies.org:taxname:378125', 'isBrackish': None, 'scientificname': 'Lopholithodes foraminatus', 'authority': '(Stimpson, 1859)', 'class': 'Malacostraca', 'url': 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=378125', 'valid_AphiaID': 378125, 'modified': '2013-04-12T09:17:18Z', 'isTerrestrial': None, 'genus': 'Lopholithodes', 'order': 'Decapoda'}]

In [6]: t = wsdlObjectWoRMS.getAphiaClassificationByID(378125)

In [7]: t
Out[7]: <SOAPpy.Types.structType return at 140452007879744>: {'child': <SOAPpy.Types.structType child at 140452007881616>: {'child': <SOAPpy.Types.structType child at 140452007880248>: {'child': <SOAPpy.Types.structType child at 140452007881544>: {'child': <SOAPpy.Types.structType child at 140452007882048>: {'child': <SOAPpy.Types.structType child at 140452007882120>: {'child': <SOAPpy.Types.structType child at 140451929051720>: {'child': <SOAPpy.Types.structType child at 140451929052152>: {'child': <SOAPpy.Types.structType child at 140451929052440>: {'child': <SOAPpy.Types.structType child at 140451929052728>: {'child': <SOAPpy.Types.structType child at 140451929053016>: {'child': <SOAPpy.Types.structType child at 140452007882408>: {'child': <SOAPpy.Types.structType child at 140452007882192>: {'child': <SOAPpy.Types.structType child at 140452007882480>: {'child': '', 'scientificname': 'Lopholithodes foraminatus', 'rank': 'Species', 'AphiaID': 378125}, 'scientificname': 'Lopholithodes', 'rank': 'Genus', 'AphiaID': 378124}, 'scientificname': 'Lithodidae', 'rank': 'Family', 'AphiaID': 106737}, 'scientificname': 'Lithodoidea', 'rank': 'Superfamily', 'AphiaID': 366102}, 'scientificname': 'Anomura', 'rank': 'Infraorder', 'AphiaID': 106671}, 'scientificname': 'Pleocyemata', 'rank': 'Suborder', 'AphiaID': 106670}, 'scientificname': 'Decapoda', 'rank': 'Order', 'AphiaID': 1130}, 'scientificname': 'Eucarida', 'rank': 'Superorder', 'AphiaID': 1089}, 'scientificname': 'Eumalacostraca', 'rank': 'Subclass', 'AphiaID': 1086}, 'scientificname': 'Malacostraca', 'rank': 'Class', 'AphiaID': 1071}, 'scientificname': 'Crustacea', 'rank': 'Subphylum', 'AphiaID': 1066}, 'scientificname': 'Arthropoda', 'rank': 'Phylum', 'AphiaID': 1065}, 'scientificname': 'Animalia', 'rank': 'Kingdom', 'AphiaID': 2}, 'scientificname': 'Biota', 'rank': 'Superdomain', 'AphiaID': 1}

In [9]: a
Out[9]: [<SOAPpy.Types.structType item at 140451929054744>: {'kingdom': 'Animalia', 'match_type': 'exact', 'isFreshwater': None, 'family': None, 'citation': 'WoRMS (2014). Decapoda. Accessed through:  World Register of Marine Species at http://www.marinespecies.org/aphia.php?p=taxdetails&id=1130 on 2015-01-26', 'rank': 'Order', 'unacceptreason': None, 'phylum': 'Arthropoda', 'valid_name': 'Decapoda', 'isExtinct': None, 'AphiaID': 1130, 'isMarine': 1, 'status': 'accepted', 'valid_authority': 'Latreille, 1803', 'lsid': 'urn:lsid:marinespecies.org:taxname:1130', 'isBrackish': None, 'scientificname': 'Decapoda', 'authority': 'Latreille, 1803', 'class': 'Malacostraca', 'url': 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=1130', 'valid_AphiaID': 1130, 'modified': '2004-12-21T16:54:05Z', 'isTerrestrial': None, 'genus': None, 'order': 'Decapoda'}]

In [10]: t = wsdlObjectWoRMS.getAphiaChildrenByID(1130)

In [11]: t
Out[11]: [<SOAPpy.Types.structType item at 140451929054960>: {'kingdom': 'Animalia', 'match_type': 'exact', 'isFreshwater': None, 'family': None, 'citation': 'Fransen, C.; De Grave, S. (2014). Dendrobranchiata. Accessed through:  World Register of Marine Species at http://www.marinespecies.org/aphia.php?p=taxdetails&id=106669 on 2015-01-26', 'rank': 'Suborder', 'unacceptreason': None, 'phylum': 'Arthropoda', 'valid_name': 'Dendrobranchiata', 'isExtinct': None, 'AphiaID': 106669, 'isMarine': 1, 'status': 'accepted', 'valid_authority': 'Spence Bate, 1888', 'lsid': 'urn:lsid:marinespecies.org:taxname:106669', 'isBrackish': None, 'scientificname': 'Dendrobranchiata', 'authority': 'Spence Bate, 1888', 'class': 'Malacostraca', 'url': 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=106669', 'valid_AphiaID': 106669, 'modified': '2011-10-27T14:38:38Z', 'isTerrestrial': None, 'genus': None, 'order': 'Decapoda'}, <SOAPpy.Types.structType item at 140451929055032>: {'kingdom': 'Animalia', 'match_type': 'exact', 'isFreshwater': None, 'family': None, 'citation': 'WoRMS (2014). Macrura Reptantia. Accessed through:  World Register of Marine Species at http://www.marinespecies.org/aphia.php?p=taxdetails&id=536657 on 2015-01-26', 'rank': 'Suborder', 'unacceptreason': None, 'phylum': 'Arthropoda', 'valid_name': 'Macrura Reptantia', 'isExtinct': None, 'AphiaID': 536657, 'isMarine': None, 'status': 'accepted', 'valid_authority': 'Bouvier, 1917', 'lsid': 'urn:lsid:marinespecies.org:taxname:536657', 'isBrackish': None, 'scientificname': 'Macrura Reptantia', 'authority': 'Bouvier, 1917', 'class': 'Malacostraca', 'url': 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=536657', 'valid_AphiaID': 536657, 'modified': '2010-11-03T12:25:36Z', 'isTerrestrial': None, 'genus': None, 'order': 'Decapoda'}, <SOAPpy.Types.structType item at 140451929055104>: {'kingdom': 'Animalia', 'match_type': 'exact', 'isFreshwater': None, 'family': None, 'citation': 'WoRMS (2014). Natantia. Accessed through:  World Register of Marine Species at http://www.marinespecies.org/aphia.php?p=taxdetails&id=181484 on 2015-01-26', 'rank': 'Suborder', 'unacceptreason': None, 'phylum': 'Arthropoda', 'valid_name': None, 'isExtinct': None, 'AphiaID': 181484, 'isMarine': None, 'status': 'unaccepted', 'valid_authority': None, 'lsid': 'urn:lsid:marinespecies.org:taxname:181484', 'isBrackish': None, 'scientificname': 'Natantia', 'authority': 'Boas, 1880', 'class': 'Malacostraca', 'url': 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=181484', 'valid_AphiaID': 0, 'modified': '2009-02-24T11:52:11Z', 'isTerrestrial': None, 'genus': None, 'order': 'Decapoda'}, <SOAPpy.Types.structType item at 140451929055176>: {'kingdom': 'Animalia', 'match_type': 'exact', 'isFreshwater': None, 'family': None, 'citation': 'WoRMS (2014). Pleocyemata. Accessed through:  World Register of Marine Species at http://www.marinespecies.org/aphia.php?p=taxdetails&id=106670 on 2015-01-26', 'rank': 'Suborder', 'unacceptreason': None, 'phylum': 'Arthropoda', 'valid_name': 'Pleocyemata', 'isExtinct': None, 'AphiaID': 106670, 'isMarine': 1, 'status': 'accepted', 'valid_authority': 'Burkenroad, 1963', 'lsid': 'urn:lsid:marinespecies.org:taxname:106670', 'isBrackish': None, 'scientificname': 'Pleocyemata', 'authority': 'Burkenroad, 1963', 'class': 'Malacostraca', 'url': 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=106670', 'valid_AphiaID': 106670, 'modified': '2005-05-02T14:40:44Z', 'isTerrestrial': None, 'genus': None, 'order': 'Decapoda'}, <SOAPpy.Types.structType item at 140451929053880>: {'kingdom': 'Animalia', 'match_type': 'exact', 'isFreshwater': None, 'family': None, 'citation': 'WoRMS (2014). Reptantia. Accessed through:  World Register of Marine Species at http://www.marinespecies.org/aphia.php?p=taxdetails&id=148412 on 2015-01-26', 'rank': 'Suborder', 'unacceptreason': None, 'phylum': 'Arthropoda', 'valid_name': 'Macrura Reptantia', 'isExtinct': None, 'AphiaID': 148412, 'isMarine': None, 'status': 'unaccepted', 'valid_authority': 'Bouvier, 1917', 'lsid': 'urn:lsid:marinespecies.org:taxname:148412', 'isBrackish': None, 'scientificname': 'Reptantia', 'authority': 'Boas, 1880', 'class': 'Malacostraca', 'url': 'http://www.marinespecies.org/aphia.php?p=taxdetails&id=148412', 'valid_AphiaID': 536657, 'modified': '2010-11-04T11:16:19Z', 'isTerrestrial': None, 'genus': None, 'order': 'Decapoda'}]


"""

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
    pref_db = args.pref_db
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


    if (pref_db == 'itis'):
        # get taxonomy info from itis
        print "Sorry, ITIS is not implemented yet"
        pass
    elif (pref_db == 'worms'):
        # get taxonomy from worms
        lock = threading.Lock()
        queue = Queue.Queue()

        #Starting a few threads as daemons checking the queue
        for i in range(threadNumber) :
            t = TaxonomyFetcherWorms(taxonomy, lock, queue, i, pref_db, verbose, ignoreWarnings)
            t.setDaemon(True)
            t.start()
        
        #Popoluate the queue with the taxa.
        for taxon in taxa :
            queue.put(taxon)
        
        #Wait till everyone finishes
        queue.join()
        logging.getLogger().setLevel(logging.WARNING)

    elif (pref_db == 'ncbi'):
        # get taxonomy from ncbi
        print "Sorry, NCBI is not implemented yet"        
        pass
    else:
        print "ERROR: Didn't understand you database choice"
        sys.exit(-1)





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
    mrca = stk.get_mrca(taxa_in_clade)
    mrca_parent = treeobj.node(mrca).parent

    # insert a node into the tree between the MRCA and it's parent (p4.addNodeBetweenNodes)
    newNode = tree.addNodeBetweenNodes(mrca, mrca_paraent)

    # add the new tree at the new node using p4.addSubTree(self, selfNode, theSubTree, subTreeTaxNames=None)
    treeobj.addSubTree(newNode, additionalTaxa)

    # return new tree
    return treeobj.writeNewick(fName=None,toString=True).strip()

if __name__ == "__main__":
    main()




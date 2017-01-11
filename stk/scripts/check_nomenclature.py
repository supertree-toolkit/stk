#!/usr/bin/env python
#
#    Derived from the Supertree Toolkit. Software for managing and manipulating sources
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
#    Jon Hill. jon.hill@york.ac.uk. 
#
#
# This is an enitrely self-contained script that does not require the STK to be installed.

import urllib2
from urllib import quote_plus
import simplejson as json
import argparse
import os
import sys
import csv

def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="Check nomenclature",
         description="Check nomenclature from a tree file or list against valid names derived from EOL",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            '--existing', 
            help="An existing output file to update further, e.g. with a new set of taxa. Supply the file name."
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your input taxa list"
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            nargs=1,
            help="The output file. A CSV-based output, listing name checked, valid name, synonyms and status (red, amber, yellow, green)."
            )

    args = parser.parse_args()
    verbose = args.verbose
    input_file = args.input_file[0]
    output_file = args.output_file[0]
    existing_data  = args.existing

    if (not existing_data == None):
        exiting_data = load_equivalents(existing_data)
    else:
        existing_data = None

    with open(input_file,'r') as f:
        lines = f.read().splitlines()        
    equivs = taxonomic_checker_list(lines, existing_data, verbose=verbose)

   
    f = open(output_file,"w")
    for taxon in sorted(equivs.keys()):
        f.write(taxon+","+";".join(equivs[taxon][0])+","+equivs[taxon][1]+"\n")
    f.close()

    return


def taxonomic_checker_list(name_list,existing_data=None,verbose=False):
    """ For each name in the database generate a database of the original name,
    possible synonyms and if the taxon is not know, signal that. We do this by
    using the EoL API to grab synonyms of each taxon.  """


    if existing_data == None:
        equivalents = {}
    else:
        equivalents = existing_data

    # for each taxon, check the name on EoL - what if it's a synonym? Does EoL still return a result?
    # if not, is there another API function to do this?
    # search for the taxon and grab the name - if you search for a recognised synonym on EoL then
    # you get the original ('correct') name - shorten this to two words and you're done.
    for t in name_list:
        # make sure t has no spaces.
        t = t.replace(" ","_")
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
        URL = "http://eol.org/api/pages/1.0/"+ID+".json?images=2&videos=0&sounds=0&maps=0&text=2&iucn=false&subjects=overview&licenses=all&details=true&common_names=true&synonyms=true&references=true&vetted=0"       
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
        print correct_name, t

        # build up the output dictionary - original name is key, synonyms/missing is value
        if (correct_name == t or correct_name == taxon):
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

def load_equivalents(equiv_csv):
    """Load equivalents data from a csv and convert to a equivalents Dict.
        Structure is key, with a list that is array of synonyms, followed by status ('green',
        'yellow', 'amber', or 'red').

    """

    import csv

    equivalents = {}

    with open(equiv_csv, 'rU') as csvfile:
        equiv_reader = csv.reader(csvfile, delimiter=',')
        equiv_reader.next() # skip header
        for row in equiv_reader:
            i = 1
            equivalents[row[0]] = [row[1].split(';'),row[2]]
    
    return equivalents

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




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
from ete2 import Tree


# What we get from EOL
current_taxonomy_levels = ['species','genus','family','order','class','phylum','kingdom']
# And the extra ones from ITIS
extra_taxonomy_levels = ['superfamily','infraorder','suborder','superorder','subclass','subphylum','superphylum','infrakingdom','subkingdom']
# all of them in order
taxonomy_levels = ['species','subgenus','genus','subfamily','family','superfamily','subsection','section','infraorder','suborder','order','superorder','subclass','class','superclass','subphylum','phylum','superphylum','infrakingdom','subkingdom','kingdom']


def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="create a tree from a taxonomy file",
         description="Create a taxonomic tree",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'top_level', 
            nargs=1,
            help="The top level group to start with, e.g. family"
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your taxonomy file"
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

    start_level = taxonomy_levels.index(top_level)

    tree_taxonomy = stk.load_taxonomy(input_file)

    new_taxa = tree_taxonomy.keys()

    #print new_taxa

    taxa_tree = Tree()
    taxonomy_markers = []
    i = 0

    for l in range[start_level:0:-1]:
        current_level_names = {}
        for t in tree_taxonomy:
            current_level_names[taxonomy_levels[t][l]] = [t for taxonomy_levels[t][l:start_level+1:1]]

        nodes = []

        # empty dictionaries evaulate to False
        if bool(taxonomy_markers):
            for c in current_level_names:
                nodes.append([t.add_child(name=c),c])
        else:
            # need to ID which node to attach to - step back up the taoxnomy until a non-"-" is found
            for c in current_level_names:
                for tm in taxonomy_markers[i-1]:
                    if tm[1] == 
                node_to_append_to = taxonomy_markers[i-1]
                nodes.append([t.add_child(name=c),c])

        i += 1



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




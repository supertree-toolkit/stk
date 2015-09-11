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

import argparse
import copy
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
import csv
from ete2 import Tree

taxonomy_levels = ['species','subgenus','genus','subfamily','family','superfamily','subsection','section','infraorder','suborder','order','superorder','subclass','class','superclass','subphylum','phylum','superphylum','infrakingdom','subkingdom','kingdom']
tlevels = ['species','genus','family','order','class','phylum','kingdom']


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

    tl_types = []
    for tt in tree_taxonomy:
        tl_types.append(tree_taxonomy[tt][top_level])

    tl_types = _uniquify(tl_types)
    levels_to_worry_about = tlevels[0:tlevels.index(top_level)+1]
        
    #print levels_to_worry_about[-2::-1]
    
    t = Tree()
    nodes = {}
    nodes[top_level] = []
    for tl in tl_types:
        n = t.add_child(name=tl)
        nodes[top_level].append({tl:n})

    for l in levels_to_worry_about[-2::-1]:
        #print t
        names = []
        nodes[l] = []
        ci = levels_to_worry_about.index(l)
        for tt in tree_taxonomy:
            names.append(tree_taxonomy[tt][l])
        names = _uniquify(names)
        for n in names:
            #print n
            # find my parent
            parent = None
            for tt in tree_taxonomy:
                if tree_taxonomy[tt][l] == n:
                    parent = tree_taxonomy[tt][levels_to_worry_about[ci+1]]
                    k = []
                    for nd in nodes[levels_to_worry_about[ci+1]]:
                        k.extend(nd.keys())
                    i = 0
                    for kk in k:
                        print kk
                        if kk == parent:
                            break
                        i += 1
                    parent_id = i
                    break
            # find out where to attach it
            node_id = nodes[levels_to_worry_about[ci+1]][parent_id][parent]
            nd = node_id.add_child(name=n.replace(" ","_"))
            nodes[l].append({n:nd})

    tree = t.write(format=9)  
    tree = stk._collapse_nodes(tree) 
    tree = stk._collapse_nodes(tree) 
    print tree


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




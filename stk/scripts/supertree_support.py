#!/usr/bin/env python
#
#
# Perform p4's supertree support measure. V+, V-, etc.
#

import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import stk.supertree_toolkit as stk
from stk.p4.SuperTreeSupport import SuperTreeSupport
from stk.stk_exceptions import *

def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="supertree_support",
         description="Add supertree support measures to your supertree.",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            '--measure',
            choices=['v','v+','v-','wv','wv+','wv-'],
            default='v+',
            help="Choose measure to add to the supertree output. The w version weight against the length of the source tree."
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your Phyml"
            )
    parser.add_argument(
            'input_supertree', 
            metavar='input_supertree',
            nargs=1,
            help="Your supertree"
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            nargs=1,
            help="The output stub for all the various output files"
            )
    args = parser.parse_args()
    verbose = args.verbose
    measure = args.measure
    input_file = args.input_file[0]
    input_supertree = args.input_supertree[0]
    output_stub = args.output_file[0]

    if measure == 'wv+':
        measure = 10
    elif measure == 'wv':
        measure = 9
    elif measure == 'wv-':
        measure = 11
    elif measure == 'v+':
        measure = 7
    elif measure == 'v':
        measure = 6
    elif measure == 'v-':
        measure = 8
    else:
        print "Unknown metric"
        sys.exit(-1)
# see p4.SuperTreeSupport for indices.
#        if non stadard decoration, what metric to use
#        [S,  P,  R,  Q,  WS, WP, V,  V+, V-, wV, wV+,wV-]
#         0   1   2   3   4   5   6   7   8   9   10  11


    # grab taxa in dataset
    if (verbose):
        print "Parsing PHYML"            
    XML = stk.load_phyml(input_file)
    taxa = stk.get_all_taxa(XML)

    # load supertree
    supertree_data = stk.import_tree(input_supertree)
    supertree = stk._parse_tree(supertree_data) 
    terminals = supertree.getAllLeafNames(supertree.root)   

    if (not len(taxa) == len(terminals)):
        # this happens if the supertree has been pruned to remove dodgy taxa
        if (verbose):
            print "Warning: supertree contains different number of taxa to your input data. Pruning input data"
        taxa.sort()
        terminals.sort()
        delete_me = []
        # create subs file
        for t in taxa:
            if not t in terminals:
                delete_me.append(t)
        # strip from phyml
        if (verbose):
            print "Deleting: " + str(len(delete_me)) + " from original "+str(len(taxa))
        try:
            XML = stk.substitute_taxa(XML, delete_me,ignoreWarnings=True)
            # do we need a clean data to check for non-informative trees here?
        except TreeParseError as detail:
            msg = "***Error: failed to parse a tree in your data set.\n"+detail.msg
            print msg
            return 

    # get all trees from phyml
    input_trees = stk.obtain_trees(XML)
    source_trees = []
    for t in input_trees:
        source_trees.append(stk._parse_tree(input_trees[t]))
    sts = SuperTreeSupport(input_supertree, source_trees)

    sts.doSaveDecoratedTree = True
    sts.doStandardDecoration=False
    sts.decorationMetric = measure
    sts.decoratedFilename=output_stub+'dec_st.nex'
    sts.doSaveIndexTree=True
    sts.indexFilename=output_stub+'_index.nex'
    sts.csvFilename=output_stub+'_index.csv'
    sts.doDrawTree=False
    sts.verbose=1

    sts.superTreeSupport()
    
if __name__ == "__main__":
    main()




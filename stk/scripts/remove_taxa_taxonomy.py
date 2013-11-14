#!/usr/bin/env python
import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
from lxml import etree


def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="Remove taxa taxonomy",
         description="""Removes taxa from a taxonomy (or indeed any) tree that aren't in a dataset""",
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
            help="Your input Phyml"
            )
    parser.add_argument(
            'input_tree', 
            metavar='input_tree',
            nargs=1,
            help="Your input tree files"
    )
    parser.add_argument(
            'new_file', 
            metavar='new_file',
            nargs=1,
            help="The new tree file"
            )


    args = parser.parse_args()
    verbose = args.verbose
    input_file = args.input_file[0]
    input_tree = args.input_tree[0]
    new_file = args.new_file[0]

    # load tree
    tree = stk.import_tree(input_tree)
    tree_taxa = stk._getTaxaFromNewick(tree)

    # grab taxa in dataset
    XML = stk.load_phyml(input_file)
    taxa = stk.get_all_taxa(XML)

    # build our subs up
    deleteme = []
    for taxon in tree_taxa:
        if not taxon in taxa:
            deleteme.append(taxon)

    new_tree = stk._sub_taxa_in_tree(tree,deleteme)

    t = stk._parse_tree(new_tree)
    t.writeNexus(fName=new_file)

    tree_taxa = stk._getTaxaFromNewick(new_tree)
    tree_taxa.sort()
    for t in tree_taxa:
        print t



if __name__ == "__main__":
    main()

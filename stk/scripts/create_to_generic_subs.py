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
         prog="convert tree from specific to generic",
         description="""Converts a tree at specific level to generic level""",
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
            help="Your tree"
            )
    parser.add_argument(
            'subs_file', 
            metavar='subs_file',
            nargs=1,
            help="The subs file"
            )


    args = parser.parse_args()
    verbose = args.verbose
    input_file = args.input_file[0]
    subs_file = args.subs_file[0]

    # load tree
    tree = stk.import_tree(input_file)

    # grab taxa
    taxa = stk._getTaxaFromNewick(tree)

    # loop through species assigning correct sub to genus
    subs = []
    for t in taxa:
        genus = t.split("_")[0]
        if (len(t.split("_")) > 1):
            subs.append(t+" = "+genus)

    # write file
    f = open(subs_file,"w")
    for s in subs:
        f.write(s+"\n")
    f.close()

if __name__ == "__main__":
    main()

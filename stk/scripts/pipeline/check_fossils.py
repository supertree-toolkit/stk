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

import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir, os.pardir )
sys.path.insert(0, stk_path)
import stk

taxonomy_levels = stk.taxonomy_levels
taxonomy_levels.insert(0,"subspecies")
tlevels = taxonomy_levels


def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="Check fossils",
         description="Given taxonomy file where fossil names are in ALL CAPS; check those names are CAPS in tree",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'taxonomy_file', 
            metavar='taxonomy_file',
            nargs=1,
            help="Taxonomy file"
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
    taxonomy_file = args.taxonomy_file[0]


    taxonomy = stk.load_taxonomy(taxonomy_file)

    tree = stk.import_tree(input_file)
    taxa_list = stk.get_taxa(tree)

    # build list of ALL CAPS taxa in taxonomy
    fossil_taxa = []
    for t in taxonomy.keys():
        if t.isupper():
            fossil_taxa.append(t)

    # now check if any are in the tree as not CAPS
    fossil_new = []
    fossil_old = []
    for f in fossil_taxa:
        if f.capitalize() in taxa_list:
            fossil_new.append(f)
            fossil_old.append(f.capitalize())

    # now do a sub
    new_tree = stk.sub_taxa_in_tree(tree, fossil_old, fossil_new)

    # save tree:
    f = open(output_file, "w")
    f.write(new_tree)
    f.close()


if __name__ == "__main__":
    main()


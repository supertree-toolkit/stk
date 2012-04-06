#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2011, Jon Hill, Katie Davis
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

import os
import sys
from lxml import etree
import argparse
from copy import deepcopy


# Generate a subs file from STR output whereby the C taxa can be added back in
# You can then run sub_taxa on the tree file to add them back.
#
# Note - the sub taxa requires a PHYML. Umm...
#

def main():

    parser = argparse.ArgumentParser(
         prog="str_reinsert_taxa",
         description="""Create a sub_taxa file to reinsert STR C taxa back into a tree"""
                     )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'str_file',
            help="The str file"
            )
    parser.add_argument(
            'subs_file',
            help="The subs_taxa file"
            )
   
    args = parser.parse_args()
    verbose = args.verbose
    str_file = args.str_file
    subs_file = args.subs_file

    # parse output file
    # skip first three lines (header)
    file = open(str_file)
    i = 0
    replacements = []
    all_C_taxa = []
    to_remove = []
    for line in file:
        if (i < 3):
            i += 1
            continue
        else:
            line = line.strip()
            # remove the leading and trailing '|' so we get correct number
            # of columns
            line = line.strip('|')
            data = line.split('|')
            # data[0] = index taxa
            # data[1] = missing characters
            # data[2] = potential equivs
            # we might have done with the table
            if (not len(data) == 3):
                break
            index = data[0].strip()
            pot_equivs = data[2].strip().split()
            replace = ""
            for e in pot_equivs:
                if (e[-3:] == '(C)'):
                    if  (not e[:-3] in all_C_taxa):
                        replace += e[:-3]+","
                    else:
                        # add it to the need to remove list as it appear multiple times
                        to_remove.append(e[:-3])
            if (not replace == ""):
                all_C_taxa.extend(replace[:-1].split(','))
                replacements.append(index+" = "+replace+index)

    # now need to remove the list in the to_remove list from the RHS
    for i in range(len(replacements)):
        for t in to_remove:
            replacements[i] = replacements[i].replace(t+",","")

    
    # save file
    f = open(subs_file,'w')
    for r in replacements:
        f.write(r+"\n")
    f.close()           


if __name__ == "__main__":
    main()

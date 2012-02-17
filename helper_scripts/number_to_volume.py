#!/usr/bin/env python
#
#    Supertree Toolkit. SOftware for managing and manipulating sources
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


# Older schema had no volume for journal articles, for some
# reason. Steve used number to record the volume. This script
# swaps number to volume

def main():

    parser = argparse.ArgumentParser(
         prog="stk",
         description="""Replace number to volume"""
                     )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'old_file',
            help="The old PHYML file"
            )
    parser.add_argument(
            'new_file',
            help="The new, improved PHYML file"
            )
   
    args = parser.parse_args()
    verbose = args.verbose
    old_file = args.old_file
    new_file = args.new_file

    # parse old file
    old_phyml = etree.parse(old_file)

    # easiest way is to serialise the XML, then do a text replace
    text = etree.tostring(old_phyml)
    text = text.replace('number','volume')

    # save file
    f = open(new_file,'w')
    f.write(text)
    f.close()           


if __name__ == "__main__":
    main()

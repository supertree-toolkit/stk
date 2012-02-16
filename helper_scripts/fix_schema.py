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


# Move the characters from multiple character_data to a single character_data
# and multiple characters
#
# Old schema was:
#        <character_data>
#          <character type="morphological" name="Appendage"/>
#        </character_data>
#        <character_data>
#          <character type="morphological" name="Leg_length"/>
#        </character_data>
#
# New is:
#        <character_data>
#          <character type="morphological" name="Appendage"/>
#          <character type="morphological" name="Leg_length"/>
#        </character_data>

def main():

    parser = argparse.ArgumentParser(
         prog="stk",
         description="""Fix the schema from rev to rev"""
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

    # loop over source_trees
    find = etree.XPath("//source")
    find_trees = etree.XPath("//source_tree")
    sources = find(old_phyml)
    for s in sources:
        # Make directory
        name = s.attrib['name']
        if (verbose):
            print "---\nWorking on: " +name
        if (name == '' or name == None):
            print "One of the sources does not have a valid name. Aborting. Sorry about the mess"
            sys.exit(-1)

        # for each source_tree, loop over characters
        for t in s.xpath("source_tree"):
            chars = []
            for cd in t.xpath('character_data'):
                # grab the characters and then remove the character_data
                chars.append(cd.xpath('character')[0])
                t.remove(cd) 

            # add a new character data
            character_data = etree.SubElement(t,"character_data")
            for c in chars:
                character_data.append(deepcopy(c))



    # save file
    f = open(new_file,'w')
    f.write(etree.tostring(old_phyml))
    f.close()           


if __name__ == "__main__":
    main()

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
import math
import numpy 
import argparse

# STK is the main command line program for the supertree toolkit
# Using the XML files created by the GUI it can processes the data, without
# launching the GUI - useful for batch processing or tasks that might take a while.
def main():

    parser = argparse.ArgumentParser(
         description="""stk is the command line interface to the supertree toolkit. """+
                     """It can access all the functionality of the STK that is available in """+
                     """the GUI. """
                     )
    parser.add_argument(
            '-c', 
            '--command', 
            help="Which STK command do you want to use",
            choices=["", "rename_sources", "import_bib"]
            )

    parse.add_argument(
            '-o',
            '--output',
            help="Output file"
            )

    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports",
            default=False
            )

    # All of the rest may or may not apply to the command chosen
    # The rest of this function is effectively checking all of the arguments
    # against the command specified

if __name__ == "__main__":
    main()

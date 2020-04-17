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

import unicodedata

""" This file contains the internal functionality of the STK
"""

replacements =     {
    "\u00C6": "AE", # LATIN CAPITAL LETTER AE
    "\u00D0": "D",  # LATIN CAPITAL LETTER ETH
    "\u00D8": "OE", # LATIN CAPITAL LETTER O WITH STROKE
    "\u00DE": "Th", # LATIN CAPITAL LETTER THORN
    "\u00DF": "ss", # LATIN SMALL LETTER SHARP S
    "\u00E6": "ae", # LATIN SMALL LETTER AE
    "\u00F0": "d",  # LATIN SMALL LETTER ETH
    "\u00F8": "oe", # LATIN SMALL LETTER O WITH STROKE
    "\u00FE": "th", # LATIN SMALL LETTER THORN
    "\u2010": "-",
    "\u2011": "-",
    "\u2012": "-",
    "\u2013": "-",
    "\u2014": "-",
    "\u2015": "-",
    "\u2212": "-",
    "\u2018": "'", # single quotes
    "\u2019": "'",
    "\u201A": "'",
    "\u201B": "'",
    "\u201C": '"', # double quotes
    "\u201D": '"',
    "\u201E": '"',
    "\u201F": '"',
    }

def replace_utf(content):

    for c in replacements:
        content = content.replace(c,replacements[c])

    return content


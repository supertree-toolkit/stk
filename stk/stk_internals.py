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

from StringIO import StringIO
import os
import sys
import math
import re
import numpy 
from lxml import etree
import parser
import re
import supertree_toolkit
from copy import deepcopy
import unicodedata


""" This file contains the internal functionality of the STK
"""




replacements =     {
    u"\u00C6": u"AE", # LATIN CAPITAL LETTER AE
    u"\u00D0": u"D",  # LATIN CAPITAL LETTER ETH
    u"\u00D8": u"OE", # LATIN CAPITAL LETTER O WITH STROKE
    u"\u00DE": u"Th", # LATIN CAPITAL LETTER THORN
    u"\u00DF": u"ss", # LATIN SMALL LETTER SHARP S
    u"\u00E6": u"ae", # LATIN SMALL LETTER AE
    u"\u00F0": u"d",  # LATIN SMALL LETTER ETH
    u"\u00F8": u"oe", # LATIN SMALL LETTER O WITH STROKE
    u"\u00FE": u"th", # LATIN SMALL LETTER THORN
    u"\u2010": "-",
    u"\u2011": "-",
    u"\u2012": "-",
    u"\u2013": "-",
    u"\u2014": "-",
    u"\u2015": "-",
    u"\u2212": "-",
    u"\u2018": "'", # single quotes
    u"\u2019": "'",
    u"\u201A": "'",
    u"\u201B": "'",
    u"\u201C": '"', # double quotes
    u"\u201D": '"',
    u"\u201E": '"',
    u"\u201F": '"',
    }

def replace_utf(content):

    for c in replacements:
        content = content.replace(c,replacements[c])

    return content


def already_in_data(new_source,sources):
    """
    Is the new source already in the dataset?

    Determine this by searching for the paper title.

    Returns the source which matches the new one and True if a match is found
    or None, False if not.
    """

    find = etree.XPath('//title/string_value')
    new_source_title = find(new_source)[0].text
    current_sources = find(sources)
    for title in current_sources:
        t = title.text
        if t == new_source_title:
            return title.getparent().getparent().getparent().getparent(), True

    return None, False



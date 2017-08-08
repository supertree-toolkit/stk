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
from lxml import etree
import unicodedata
import os
import stk_exceptions as excp

"""stk_internals

This file contains some useful internal functionality of the STK

They might be useful for other things, but not necessarily!
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

    try:
        # not a unicode string passed in
        content = unicode(content, 'utf-8')
    except TypeError:
        pass # already a unicode string
    for c in replacements:
        content = content.replace(c,replacements[c])

    return content


def internet_on(host="8.8.8.8", port=443, timeout=3):
    import socket

    """
      Host: 8.8.8.8 (google-public-dns-a.google.com)
      OpenPort: 53/tcp
      Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except Exception as ex:
        #print ex.message
        return False   


def uniquify(l):
    """
    Make a list, l, contain only unique data
    """
    keys = {}
    for e in l:
        keys[e] = 1

    return keys.keys()



def sort_sub_taxa(old_taxa, new_taxa):
    """
    Sort out what the new and old taxa vars are and sort them out 
    into the expected format
    """

    # are the input values lists or simple strings?
    if (isinstance(old_taxa,str)):
        old_taxa = [old_taxa]
    if (new_taxa and isinstance(new_taxa,str)):
        new_taxa = [new_taxa]

    # check they are same lengths now
    if (new_taxa):
        if (len(old_taxa) != len(new_taxa)):
            raise excp.UnableToParseSubsFile("Substitution failed. Old and new are different lengths")

    return old_taxa, new_taxa


def sub_deal_with_existing_only(existing_taxa, old_taxa, new_taxa, generic_match=False):
   
    import csv

    corrected_taxa = []
    if (generic_match):
        generic = []
        for t in existing_taxa:
            gen = t.split("_")
            if len(gen) == 2:
                generic.append(gen[0])
        generic = uniquify(generic)
    i = 0
    for t in new_taxa:
        if (not t == None):    
            current_corrected_taxa = []
            # remove duplicates in the new taxa
            for row in csv.reader([t],delimiter=',', quotechar="'"):
                current_new_taxa = row
                for cnt in current_new_taxa:
                    cnt = cnt.strip()
                    cnt = cnt.strip('_')
                    if (generic_match):
                        if (cnt.split('_')[0] in generic):
                            current_corrected_taxa.append(cnt)
                    else:
                        if (cnt in existing_taxa):
                            current_corrected_taxa.append(cnt)
           
                if (len(current_corrected_taxa) == 0):
                    # None of the incoming taxa are in the data already - we need to leave in the old taxa instead
                    removed = old_taxa.pop(i)
                    i = i-1
                else:
                    temp = ", ".join(current_corrected_taxa)
                    corrected_taxa.append(temp)
        else:
            corrected_taxa.append(None)
        i += 1
    new_taxa = corrected_taxa
    return new_taxa


def locate(pattern, root=os.curdir):
    """Locate all files matching the pattern with the root dir and
    all subdirectories
    """
    import fnmatch
    for path, dirs, files in os.walk(os.path.abspath(root)):
        for filename in fnmatch.filter(files,pattern):
            yield os.path.join(path, filename)


def removeNonAscii(s): 
    """
    Removes any non-ascii characters from string, s.
    """
    return "".join(i for i in s if ord(i)<128)


def already_in_data(new_source, sources):
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



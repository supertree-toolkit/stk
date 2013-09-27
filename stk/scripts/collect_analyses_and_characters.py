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
         prog="collect analyses and characters",
         description="""Grab all the characters and optimality_ctiterions from a list of Phyml files and create
                        the correct RNC files""",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'input_files', 
            metavar='input_files',
            nargs='+',
            help="""List of phyml files. Output will be analyses.rnc and characters.rnc"""
            )

    args = parser.parse_args()
    verbose = args.verbose
    input_files = args.input_files

    characters = []
    analyses = []
    for phyml in input_files:
        xml = stk.load_phyml(phyml)
        char = stk.get_characters_used(xml)
        characters.extend(char)
        an = stk.get_analyses_used(xml)
        analyses.extend(an)

    # uniquify them - this is technically a private function...
    analyses = stk._uniquify(analyses)
    characters = stk._uniquify(characters)
    analyses.sort()
    characters.sort(key=lambda x: x[0].lower())

    header = """
characters =
    (
    element character {
    attribute name { string },
    attribute type { "morphological"|"molecular"|"behavioural"|"other" },
    char_info 
    }|"""
    i = 0
    for c in characters:
        new_char = '\n    element character {\n    attribute name { "'+c[0]+'" },'
        new_char += '\n    attribute type { "'+c[1]+'" },'
        if (i < len(characters)-1):
            new_char += '\n    char_info\n    }|'
        else:
            new_char += '\n    char_info\n    }+\n)'
        header += new_char
        i+=1

    characters_rnc = header

    header = """
analysis =
(
    element optimality_criterion {
        attribute name {string}
    }|"""
    i = 0
    for a in analyses:
        new_analysis = '\n    element character {\n\tattribute name { "'+a+'" },'
        if (i < len(analyses)-1):
            new_analysis += '\n    }|'
        else:
            new_analysis += '\n    }\n)'
        header += new_analysis
        i+=1

    analyses_rnc = header

    f = open("analyses.rnc","w")
    f.write(analyses_rnc)
    f.close()
    f = open("characters.rnc","w")
    f.write(characters_rnc)
    f.close()

    f = open("analyses.txt","w")
    for a in analyses:
        f.write(a+"\n")
    f.close()
    f = open("characters.txt","w")
    for c in characters:
        f.write(c[0]+" ("+c[1]+")\n")
    f.close()


if __name__ == "__main__":
    main()

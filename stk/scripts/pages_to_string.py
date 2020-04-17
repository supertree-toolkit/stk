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
         prog="pages to string",
         description="""Make page numbers string not integers in PHYML files""",
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
            help="""List of phyml files. These files will be overwritten - make a backup first"""
            )

    args = parser.parse_args()
    verbose = args.verbose
    input_files = args.input_files
    print(input_files)

    for phyml in input_files:
        xml_root = stk._parse_xml(stk.load_phyml(phyml))

        pages = xml_root.findall(".//page_number")
        for page in pages:
            string = etree.Element("string_value")
            string.text = page[0].text
            string.tail = "\n      "
            page.replace(page[0], string)
            string.attrib['lines'] = "1"

        f = open(phyml,"w")
        f.write("<?xml version='1.0' encoding='utf-8'?>\n")
        XML = etree.tostring(xml_root,pretty_print=True)
        f.write(XML)
        f.close()
        


if __name__ == "__main__":
    main()

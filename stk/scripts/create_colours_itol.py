#!/usr/bin/env python
#
#
# Generate a number of colours, that are different enough and evenly distributed
# for tree display
# From: http://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
#

import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir, os.pardir )
sys.path.insert(0, stk_path)
import stk
import csv
import colorsys
import random

def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="Create colours for iTOL",
         description="Generate a asthetically pleasing colour scheme for iToL based"+
                     " on a Phyml and a taxonomy csv file",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            '--scheme',
            choices=['pastel','bright','dark','faded'],
            default='pastel',
            help="Choose a colour scheme"
            )
    parser.add_argument(
            '--level',
            choices=['Genus','Subfamily','Family','Superfamily','Infraorder','Suborder','Order'],
            default='Family',
            help="Which taxonomic level to colour at. Note that not all will return data. Family and Order will always work."
            )
    parser.add_argument(
            '--tree',
            help = "Give a tree to colour and the colour will go around the tree, rather than be sorted alphabetically",
            action='store_true', 
            default=False,
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your Phyml *or* a taxa lis *or* a tree file (use --tree in this case)t"
            )
    parser.add_argument(
            'input_taxonomy', 
            metavar='input_taxonomy',
            nargs=1,
            help="Your taxonomy"
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            nargs=1,
            help="The output file for iToL"
            )
    args = parser.parse_args()
    verbose = args.verbose
    level = args.level
    scheme = args.scheme
    input_file = args.input_file[0]
    input_taxonomy = args.input_taxonomy[0]
    output_file = args.output_file[0]
    tree = args.tree

    saturation=0.5
    value=0.95
    if (scheme == 'bright'):
        saturation=0.99
        value=0.99
    elif (scheme == 'dark'):
        saturation=0.6
        value=0.8
    elif (scheme == 'faded'):
        saturation=0.25
        value=0.8

    if (tree):
        tree_data = stk.import_tree(input_file)
        # rather than simply grabbing taxa, just go through in "tree order"
        tree_data = tree_data.replace("(","")
        tree_data = tree_data.replace(")","")
        tree_data = tree_data.replace(";","")
        taxa = tree_data.split(",")
        for i in range(0,len(taxa)):
            taxa[i] = taxa[i].split(":")[0].strip()
    else:
        # grab taxa in dataset - ignore if tree
        fileName, fileExtension = os.path.splitext(input_file)
        if (fileExtension == '.phyml'):
            print "Parsing PHYML"            
            XML = stk.load_phyml(input_file)
            taxa = stk.get_all_taxa(XML)
        else:
            f = open(input_file,"r")
            taxa = []
            for line in f:
                taxa.append(line.strip())
            f.close()

    print len(taxa)
    taxonomy = {}
    index = 0
    with open(input_taxonomy, 'r') as f:
        reader = csv.reader(f)
        i = 0
        for row in reader:
            if i == 0:
                # find index of the level required
                j = 0
                for r in row:
                    if r.lower() == level.lower():
                        index = j
                        i = 1
                        break
                    j = j+ 1
                if j == len(row):
                    print "Error finding the desired level in your taxonomy file."
                    print "You asked for: "+level.lower()
                    print "Your taxonomy contains: "+" ".join(row)
                    sys.exit()
            else:
               taxonomy[row[0].replace(" ","_")] = row[index] # the replace is to make sure we're consistant across PHYML, tree and taxonomy
    print taxonomy
    values = taxonomy.values()
    values = stk.uniquify(values)
    n = len(values)
    colours = get_colours(n,format="HEX",saturation=saturation,value=value)
    output_colours = {}
    i = 0
    for v in values:
        output_colours[v] = colours[i]
        i += 1
    
    f = open(output_file,"w")
    # write header
    f.write(
"""DATASET_COLORSTRIP
#=================================================================#
#                    MANDATORY SETTINGS                           #
#=================================================================#
SEPARATOR COMMA

#label is used in the legend table (can be changed later)
DATASET_LABEL,""")
    f.write(level+"\n")
    f.write(
"""
#dataset color (can be changed later)
COLOR,#000000

#=================================================================#
#                    OPTIONAL SETTINGS                            #
#=================================================================#
COLOR_BRANCHES,1

#=================================================================#
#       Actual data follows after the "DATA" keyword              #
#=================================================================#
DATA

""")
    for t in taxa:
        tt = t.replace(" ","_")
        try:
            if (taxonomy[tt] == "-"):
                f.write(t+",#000000\n")
            else:
                f.write(t+",#"+output_colours[taxonomy[tt]]+","+taxonomy[tt]+"\n")
        except KeyError:
            #print "Couldn't find "+tt
            f.write(t+",#000000\n")

    f.close()


def get_colours(num_colours,saturation=0.5,value=0.95,format="RGB"):
    colours=[]
    golden_ratio_conjugate = 0.618033988749895
    h = random.random()
    for i in range(0,num_colours):
        h += golden_ratio_conjugate
        h = h%1
        if format=="RGB":
            colours.append(colorsys.hsv_to_rgb(h, saturation, value))
        elif format=="HEX":
            c = list(colorsys.hsv_to_rgb(h, saturation, value))
            for i in range(0,len(c)):
                c[i] = int(256*c[i])
            hexc = int_to_hex_colour(c)
            colours.append(hexc)
    return colours

def int_to_hex_colour(rgb):
  return "".join(map(chr, rgb)).encode('hex')

if __name__ == "__main__":
    main()




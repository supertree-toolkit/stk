#!/usr/bin/env python
import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
from lxml import etree
import matplotlib
if (sys.platform == "darwin"):
    matplotlib.use('GTKAgg')
from pylab import *

params = {
          'legend.fontsize': 25,
          'xtick.labelsize': 25,
          'ytick.labelsize': 25,
          'font.size' : 28,
          'axes.labelsize' : 32,
          'font.size' : 25,
          'text.fontsize' : 25,
	  # need to do these to make room for labels
          # no labels, then comment these out
          'figure.subplot.top' : 0.75,
          'figure.subplot.right' : 0.75,
}
rcParams.update(params)


def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="plot chracter taxa matrix",
         description="""Plot a matrix of character availability against taxa""",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            'input_file', 
            metavar='input_file',
            nargs=1,
            help="Your pyhml"
            )
    parser.add_argument(
            'output_file', 
            metavar='output_file',
            nargs=1,
            help="The output graphics. .png, .pdf, or .svg"
            )


    args = parser.parse_args()
    verbose = args.verbose
    input_file = args.input_file[0]
    output_file = args.output_file[0]

    XML = stk.load_phyml(input_file)
    all_taxa = stk.get_all_taxa(XML)
    all_chars_d = stk.get_all_characters(XML)
    all_chars = []
    for c in all_chars_d:
        all_chars.extend(all_chars_d[c])

    taxa_character_matrix = {}
    for t in all_taxa:
        taxa_character_matrix[t] = []

    trees = stk.obtain_trees(XML)
    for t in trees:
        chars = stk.get_characters_from_tree(XML,t,sort=True)
        taxa = stk.get_taxa_from_tree(XML,t, sort=True)
        for taxon in taxa:
            taxon = taxon.replace(" ","_")
            taxa_character_matrix[taxon].extend(chars)
    
    for t in taxa_character_matrix:
        array = taxa_character_matrix[t]
        taxa_character_matrix[t] = list(set(array))

    # create a map
    x = []
    y = []
    for i in range(0,len(all_taxa)):
        for j in range(0,len(all_chars)):
            if (all_chars[j] in taxa_character_matrix[all_taxa[i]]):
                x.append(i)
                y.append(j)

    fig=figure(figsize=(22,17),dpi=90)
    fig.subplots_adjust(left=0.3)
    ax = fig.add_subplot(1,1,1)
    ax.scatter(x,y,50,marker='o',c='r',lw=0)
    yticks(range(0,len(all_chars)), all_chars)    
    ax.set_xlim(0,len(all_taxa))
    ax.set_ylim(0,len(all_chars))
    xlabel('Taxa')
    ylabel('Characters')
    savefig(output_file, dpi=90)

if __name__ == "__main__":
    main()

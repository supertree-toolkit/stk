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
          'legend.fontsize': 16,
          'xtick.labelsize': 20,
          'ytick.labelsize': 20,
          'font.size' : 22,
          'axes.labelsize' : 24,
	  # need to do these to make room for labels
          # no labels, then comment these out
          'figure.subplot.top' : 0.75,
          'figure.subplot.right' : 0.75,
}
rcParams.update(params)


def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="plot character data",
         description="""Plot a line plot of character data from Phyml""",
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

    # grab taxa in dataset
    fileName, fileExtension = os.path.splitext(input_file)
    XML = stk.load_phyml(input_file)
    trees = stk.obtain_trees(XML)
    years = stk.get_publication_years(XML).keys()
    years.sort()
    min_year = min(years)
    max_year = max(years)

    mol = {}
    morph = {}
    other = {}
    for y in range(min_year,max_year+1,1):
        mol[y] = 0
        morph[y] = 0
        other[y] = 0

    for t in trees:
        current_chars = stk.get_character_types_from_tree(XML,t)
        current_year = stk.get_publication_year_tree(XML,t)
        for c in current_chars:
            if c == "molecular":
                mol[current_year] += 1
            elif c == "morphological":
                morph[current_year] += 1
            else:
                other[current_year] += 1

    mol_data = []
    morph_data = []
    other_data = []
    for y in years:
        try:
            mol_data.append(mol[y])
        except KeyError:
            mol_data.append(0)
        try:
            morph_data.append(morph[y])
        except KeyError:
            morph_data.append(0)
        try:
            other_data.append(other[y])
        except KeyError:
            other_data.append(0)


    fig=figure(figsize=(11.7,8.3),dpi=90) #A4 landscape
    fig.subplots_adjust(left=0.3)
    ax = fig.add_subplot(1,1,1)
    plot(years,mol_data,'b-',lw=3,label="Molecular ("+str(sum(mol_data))+")")
    plot(years,morph_data,'r-',lw=3,label="Morphological ("+str(sum(morph_data))+")")
    if (sum(other_data) > 0):
        plot(years,other_data,'g-',lw=3,label="Other ("+str(sum(other_data))+")")
    legend(loc=2)
    ax.set_xlim([min_year,max_year])
    xlabel('Year')
    ylabel('Number trees')
    savefig(output_file, dpi=90)

if __name__ == "__main__":
    main()

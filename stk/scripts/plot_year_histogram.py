#!/usr/bin/env python
import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
from lxml import etree
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
         prog="plot year histogram",
         description="""Plot a histogram of data years from Phyml""",
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
            help="Your pyhml or data file"
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
    if (fileExtension == '.phyml'):
        XML = stk.load_phyml(input_file)
        years = stk.get_publication_years(XML)
    else:
        f = open(input_file,"r")
        years = {}
        for line in f:
            data = line.strip().split()
            years[int(data[0][0:-2])] = float(data[1])
        f.close()

    year_dist = years.keys()
    year_data = years.values()

    fig=figure(figsize=(11.7,8.3),dpi=90) #A4 landscape
    fig.subplots_adjust(bottom=0.2)
    ax = fig.add_subplot(1,1,1)
    plt.xticks(rotation=70)
    rects1 = plt.bar(year_dist, year_data, 1,
                 color='b')
    xlabel('Year')
    ylabel('Number of publications')
    savefig(output_file, dpi=90)

if __name__ == "__main__":
    main()

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
from collections import Counter

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
         prog="plot tree-taxa matrix",
         description="""Plot a matrix of trees against taxa""",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            '-t', 
            '--taxonomy', 
            help="Use taxonomy to sort the taxa on the axis. Supply a STK taxonomy file",
            )
    parser.add_argument(
            '--level',
            choices=['family','superfamily','infraorder','suborder','order'],
            default='family',
            help="""What level to group the taxonomy at. Default is family. 
                    Note data for a particular levelmay be missing in taxonomy."""
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
    taxonomy = args.taxonomy
    level = args.level

    XML = stk.load_phyml(input_file)
    if not taxonomy == None:
        taxonomy = stk.load_taxonomy(taxonomy)

    all_taxa = stk.get_all_taxa(XML)

    taxa_tree_matrix = {}
    for t in all_taxa:
        taxa_tree_matrix[t] = []
        
    if not taxonomy == None:
        tax_data = {}
        new_all_taxa = []
        for t in all_taxa:
            taxon = t.replace("_"," ")
            try:
                if taxonomy[taxon][level] == "":
                    # skip this
                    continue
                tax_data[t] = taxonomy[taxon][level]
            except KeyError:
                print "Couldn't find "+t+" in taxonomy. Adding as null data"
                tax_data[t] = 'zzzzz' # it's at the end...

        from sets import Set
        unique = set(tax_data.values())
        unique = list(unique)
        unique.sort()
        print "Groups are:"
        print unique
        counts = []
        for u in unique:
            count = 0
            for t in tax_data:
                if tax_data[t] == u:
                    count += 1
                    new_all_taxa.append(t)
            counts.append(count)

        all_taxa = new_all_taxa
        # cumulate counts
        count_cumulate = []
        count_cumulate.append(counts[0])
        for c in counts[1::]:
            count_cumulate.append(c+count_cumulate[-1])

        print count_cumulate


    trees = stk.obtain_trees(XML)
    i = 0
    for t in trees:
        taxa = stk.get_taxa_from_tree(XML,t, sort=True)
        for taxon in taxa:
            taxon = taxon.replace(" ","_")
            taxa_tree_matrix[taxon].append(i)
        i+=1
    
    # create a map
    y = []
    for i in range(0,len(all_taxa)):
        for j in range(0,len(trees)):
            if (j in taxa_tree_matrix[all_taxa[i]]):
                y.append(j)

    tree_count = Counter(y)
    tree_dict = dict(tree_count)
    tree_order = sorted(tree_dict.items(), key=lambda x: x[1], reverse=True)
    
    new_x = []
    new_y = []
    for i in range(0,len(all_taxa)):
        counter = 0
        for t in tree_order:
            j = t[0]
            if (j in taxa_tree_matrix[all_taxa[i]]):
                new_x.append(i)
                new_y.append(counter)
            counter += 1

    fig=figure(figsize=(22,17),dpi=90)
    fig.subplots_adjust(left=0.3)
    ax = fig.add_subplot(1,1,1)
    ax.scatter(new_x,new_y,50,marker='o',c='k',lw=0)
    ax.set_xlim(0,len(all_taxa))
    ax.set_ylim(0,len(trees))
    xlabel('Taxa')
    ylabel('Tree Number')
    savefig(output_file, dpi=90)

if __name__ == "__main__":
    main()

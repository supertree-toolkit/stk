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
    all_chars_d = stk.get_all_characters(XML)
    all_chars = []
    for c in all_chars_d:
        all_chars.extend(all_chars_d[c])

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
                print("Couldn't find "+t+" in taxonomy. Adding as null data")
                tax_data[t] = 'zzzzz' # it's at the end...

        from sets import Set
        unique = set(tax_data.values())
        unique = list(unique)
        unique.sort()
        print("Groups are:")
        print(unique)
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

        print(count_cumulate)
            

    taxa_character_matrix = {}
    for t in all_taxa:
        taxa_character_matrix[t] = []

    trees = stk.obtain_trees(XML)
    for t in trees:
        chars = stk.get_characters_from_tree(XML,t,sort=True)
        taxa = stk.get_taxa_from_tree(XML,t, sort=True)
        for taxon in taxa:
            taxon = taxon.replace(" ","_")
            if taxon in all_taxa:
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


    i = 0
    for j in all_chars:
        # do a substitution of character names to tidy things up
        if j.lower().startswith('mitochondrial carrier; adenine nucleotide translocator'):
            j = "ANT"
        if j.lower().startswith('mitochondrially encoded 12s'):
            j = '12S'
        if j.lower().startswith('complete mitochondrial genome'):
            j = 'Mitogenome'
        if j.lower().startswith('mtdna'):
            j = "mtDNA restriction sites"
        if j.lower().startswith('h3 histone'):
            j = 'H3'
        if j.lower().startswith('mitochondrially encoded cytochrome'):
            j = 'COI'
        if j.lower().startswith('rna, 28s'):
            j = '28S'
        if j.lower().startswith('rna, 18s'):
            j = '18S'
        if j.lower().startswith('mitochondrially encoded 16s'):
            j = '16S'
        all_chars[i] = j
        i += 1

    fig=figure(figsize=(22,17),dpi=90)
    fig.subplots_adjust(left=0.3)
    ax = fig.add_subplot(1,1,1)
    ax.scatter(x,y,50,marker='o',c='r',lw=0)
    yticks(list(range(0,len(all_chars))), all_chars)    
    ax.set_xlim(0,len(all_taxa))
    ax.set_ylim(0,len(all_chars))
    xlabel('Taxa')
    ylabel('Characters')
    savefig(output_file, dpi=90)

if __name__ == "__main__":
    main()

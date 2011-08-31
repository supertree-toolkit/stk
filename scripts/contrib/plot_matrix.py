#!/usr/bin/env python

import os
import sys
import math
from pylab import *
import numpy

####################
#                  #
# CONFIGURE SCRIPT #
#                  #
####################

# plot params, such as font!

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
          'text.usetex': True
}
rcParams.update(params)

# input file
matrix_file = "data_availability_matrix.txt";
# output graphic name
output = "data_availability_matrix.png"
# For each taxa you want labelled, add the name, with the label text
# Note that names do not contain _, and the \emph is latex for italicize
labelled_taxa = {"Gallus gallus":"\emph{Gallus gallus}"}
# Same for the trees - these are in the format of short_name:tree_file
labelled_trees = {"sibley_1990:Sibley_Ahlquist_1990_corr.tre":"Sibley and Ahlquist (1990)"}
#..except for the data_availability.txt file, where it's the full file name
labelled_trees = {"../../../../FullDataset_02_01_10_Subs/Forster_etal_1998/Tree 1/Forster_etal_1998_corr.tre":"Forster \emph{et al.} (1998)"}

###########################################
# SCRIPT PROPER - SHOULD NOT NEED TO EDIT #
###########################################
print "Reading data..."
f = open(matrix_file,'r')
nLines = 0
matrix = []
filename = []
key_taxa = {}
key_trees = {}
for line in f:
    line = line.strip()
    if (nLines == 0):
        taxa = line.split(",")
        # remove header
        taxa.pop(0)
        i = 0
        for taxon in taxa:
            if (labelled_taxa.has_key(taxon)):
                 key_taxa[labelled_taxa[taxon]] = i+1
            i += 1
    else:
        temp = line.split(",")
        filename.append(temp[0])
        if (labelled_trees.has_key(temp[0])):
            key_trees[labelled_trees[temp[0]]] = nLines-1
        nPoints = len(temp)
        #print nPoints
        present = []
        for i in range(1,nPoints):
            present.append(int(temp[i]))

        matrix.append(present)
    nLines +=1

matrix = array(matrix)
x = []
y = []
nTrees, nTaxa = shape(matrix)
nTaxa = nTaxa-1
nTrees = nTrees-1
for i in range(0,nTaxa):
    for j in range(0,nTrees):
        if (matrix[j][i] == 1):
            x.append(i)
            y.append(j)

print "plotting..."
fig=figure(figsize=(25,10),dpi=90)
ax = fig.add_subplot(1,1,1)
ax.scatter(x,y,1,marker='o', c='r')
ax.set_xlim(0,nTaxa)
ax.set_ylim(0,nTrees)
for x in key_taxa.keys():
    ax.annotate(x, xy=(key_taxa[x], nTrees-0.1), xycoords="data", xytext=(key_taxa[x], nTrees+200),
                  va="bottom", ha="center", bbox=dict(boxstyle="round", fc="w"),
                  arrowprops=dict(arrowstyle="->"), fontstyle="italic")
for x in key_trees.keys():
    ax.annotate(x, xy=(nTaxa-0.1,key_trees[x]), xycoords="data", xytext=(nTaxa+200,key_trees[x]),
                  va="center", ha="left", bbox=dict(boxstyle="round", fc="w"),
                  arrowprops=dict(arrowstyle="->"))
xlabel('Taxa')
ylabel('Source Trees')
savefig(output, dpi=90,format='png')

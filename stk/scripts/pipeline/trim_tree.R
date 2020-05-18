#!/usr/bin/env Rscript

library(phytools)
library(adephylo)

tree <- read.tree("dated_tree_randres.tre")
lengths <- distRoot(tree, tree$tip.label)
root <- max(lengths)
trim <- root - 0.13
chopped tt<-treeSlice(tree, trim, trivial=FALSE, orientation="rootwards")
write.tree(chopped,"temp_chopped.tre")

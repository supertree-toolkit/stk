#!/usr/bin/env Rscript

library(TreeSim)

tree <- read.tree("dated_tree_randres.tre")
chopped <- cuttree(tree,0.13)
write.tree(chopped,"temp_chopped.tre")

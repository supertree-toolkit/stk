#!/usr/bin/env Rscript

library(paleotree)

tree <- read.tree("dated_tree_randres.tre")
trim <- 0.13
chopped<-timeSliceTree(tree, trim, tipLabels="allDesc")

write.tree(chopped,"temp_chopped.tre")

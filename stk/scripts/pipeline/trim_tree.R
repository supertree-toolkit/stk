#!/usr/bin/env Rscript

library(paleotree)

tree <- read.tree("dated_tree_randres.tre")
trim <- 0.13
chopped<-timeSliceTree(tree, trim, tipLabels="allDesc")
# replace - with _ in labels
chopped$tip.label <- gsub(';', '_', chopped$tip.label)

write.tree(chopped,"temp_chopped.tre")

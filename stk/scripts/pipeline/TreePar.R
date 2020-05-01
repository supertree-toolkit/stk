#!/usr/bin/env Rscript

library(TreePar)
tree <-read.tree('final_tree.tre')
x<-sort(getx(tree),decreasing=TRUE)
start <- 0
end <- 15
grid <- 1
sampling <- rep(1,11)
sampling[1] <- 0.99
res <- bd.shifts.optim(x,sampling,grid,start,end)
save(list = ls(all.names = TRUE), file = "TreePar_Mammals.RData", envir = .GlobalEnv)



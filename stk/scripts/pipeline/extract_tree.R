#!/usr/bin/env Rscript

require(ape)

args<-commandArgs(trailingOnly=TRUE)
input_file <- args[1]
i <- as.numeric(args[2])

trees<-read.tree(input_file)
write.tree(trees[[i]],"temp.tre")


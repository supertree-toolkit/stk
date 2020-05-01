#!/usr/bin/env Rscript

library(paleotree)
library(adephylo)
library(caper)
library(phangorn)
library(phytools)

orig_tree <- read.tree("input_tree.tre")
tree<-read.tree('filled_tree.tre')

# read in csv data
date_data = read.csv("FossilMammalAges_statusChecked_210420.csv",header=TRUE,sep=",",stringsAsFactors=FALSE)
orig_tree<-di2multi(orig_tree, tol = 1e-08)
lengths = distRoot(orig_tree, orig_tree$tip.label)
desired_root = max(lengths)

# get dates for all nodes - we want to keep these the same
node_dates = dateNodes(orig_tree,rootAge=desired_root)

# make a list of nodes all NA
dates <- rep(NA, tree$Nnode)
for (i in 1:length(node_dates)) {
    cm = clade.members(i, orig_tree, tip.labels=TRUE, include.nodes = FALSE)
    if (length(cm) < 2) {
        next
    }
    # get MRCA on new tree and set the date
    mrca = getMRCA(tree, cm)
    if (is.null(mrca)) {
        next # not in new tree
    }
    dates[mrca-Ntip(tree)] = node_dates[i]
}
 
# get all taxa from the tree and set as 0,0 for FAD and LAD
all_otus = tree$tip.label
all_otudates = matrix(0, nrow = length(all_otus), ncol=2)
all_otudates = data.frame(all_otudates)
row.names(all_otudates) <- all_otus

# now go through data data and reset and FAD dates for known fossils
# we want to control the extinction date with a bit more finesse
# so we make LAD = 0 for now.
for (i in 1:length(date_data$accepted_name)) {
    name <- sub(" ","_",toupper(date_data[i,]$accepted_name)) # assuming fossils are being added and their names are in all CAPS
    # random dates code
    #FAD <- runif(1,date_data[i,]$FAD2, date_data[i,]$FAD1)
    #LAD <- runif(1,date_data[i,]$LAD2, date_data[i,]$LAD1)
    # FAD in spreadsheet means origination
    # LAD in spreadsheet is extinction.
    FAD <- date_data[i,]$FAD2 + (date_data[i,]$FAD1 - date_data[i,]$FAD2) / 2.0
    LAD <- 0

    # leaving this here in case we need it in future.
    # if the random number has generated the other way, swap
    # can happen in FAD and LAD are same interval
    #if (LAD > FAD) {
    #    temp <- LAD
    #    LAD <- FAD
    #    FAD <- temp
    #}
    # only add names in the tree
    if (any(row.names(all_otudates) == name)) {
        all_otudates[name,]$X1 <- FAD
        all_otudates[name,]$X2 <- LAD
    } else if (any(row.names(all_otudates) == tools::toTitleCase(tolower(name)))) {
        name <- tools::toTitleCase(tolower(name))
        all_otudates[name,]$X1 <- FAD
        all_otudates[name,]$X2 <- LAD
    } else {
        print(paste0(name," not found"))
    }
}

#now date the new tree
ttree <-timePaleoPhy(tree,all_otudates,type="equal",vartime=0.001,plot=FALSE,randres=TRUE,node.mins=dates)

# we now have to adjust the tips of a few species - first those that were in the original tree but are actually fossils.
adjust_these = read.csv("adjust_these.csv",header=TRUE,sep=",",stringsAsFactors=FALSE)
lengths = distRoot(ttree, ttree$tip.label)
desired_root = max(lengths)
terms <- ttree$edge[, 2] <= Ntip(ttree)
index_name <- ttree$tip.label[ttree$edge[terms, 2]]
terminal.edges <- ttree$edge.length[terms]
end_dates <- desired_root - lengths
names(terminal.edges) <- ttree$tip.label[ttree$edge[terms, 2]]
for (i in 1:length(adjust_these$accepted_name)) {
    name <- sub(" ","_",toupper(adjust_these[i,]$accepted_name)) # assuming fossils are being added and their names are in all CAPS
    LAD <- adjust_these[i,]$LAD2# + (adjust_these[i,]$LAD1 - adjust_these[i,]$LAD2) / 2.0
    adjustment <- end_dates[name] - LAD
    if (terminal.edges[name] < -1*adjustment) {
        # we're adjusting too much - make the edge.lengths 0.01
        edge.length <- 0.01
    } else {
        edge.length <- terminal.edges[name] + adjustment
    }
    index <- which(index_name == name)
    terminal.edges[index] <- edge.length
}

# now the fossils we dealt with earlier, but we didn't put in the extinction data (LAD in timePaleoPhy lingo).
for (i in 1:length(date_data$accepted_name)) {
    name <- sub(" ","_",toupper(date_data[i,]$accepted_name)) # assuming fossils are being added and their names are in all CAPS
    LAD <- date_data[i,]$LAD2# + (date_data[i,]$LAD1 - date_data[i,]$LAD2) / 2.0
    adjustment <- end_dates[name] - LAD
    if (terminal.edges[name] < -1*adjustment) {
        # we're adjusting too much - make the edge.lengths 0.01
        edge.length <- 0.01
    } else {
        edge.length <- terminal.edges[name] + adjustment
    }
    index <- which(index_name == name)
    terminal.edges[index] <- edge.length
}
ttree$edge.length[terms] = terminal.edges

# and save!
write.tree(ttree,"dated_tree_randres_LAD2termination.tre")



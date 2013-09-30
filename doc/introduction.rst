Introduction
============

What is the STK?
----------------

The Supertree Tool Kit (STK) is software for collecting, curating, storing and
processing data ready for inclusion in supertree analysis. It does include any
methods for creating supertrees. However, it does include a number of functions
to get the data ready for running a supertree analysis. This includes
standardising taxonomy, ensuring adequate taxonomic overlap and creating a
matrix.

What does it do?
----------------

* Import bibliographic files to create a dataset
* Import trees created in most software packages 
* Export your data to common formats (Nexus, Newick, Hennig)
* Allow you to summerise your data
* Swap and delete taxa easily
* Create a matrix from your data
* Manage your data graphically
* Ensure data independence
* Ensure adequate taxonomic overlap
* Replace non-monophyletic taxa correctly
* Perform Safe Taxonomic Reduction
* Some post-processing of supertrees (e.g. pruning taxa)

What does it not do?
--------------------

* Make supertrees

About this document
-------------------

This document is the main manual for the software. Included in the software is
context-relevant help embedded in the GUI, which in complimentary to this
manual. This manual will help you install and use the software, but it will
still take experience to know which functions are appropriate for your dataset. 

The processing pipeline
-----------------------

The idea behind the STK is to create a processing pipeline that is robust,
error-free, repeatable and easy. You create a dataset by importing bibliographic
data and trees, then use the STK functions to process this data. Each stage in
the pipeline creates a new file, with a history of the previous steps embedded.
This way it is easy to undo steps and come back to your data later and
understand how it was derived.

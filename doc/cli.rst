.. index:: CLI
The STK Command Line Interface
==============================

The STK CLI contains a number of functions for initialising and processing data.

The basics
----------

The CLI is intialised using:

.. code-block:: bash

    stk

This will produce:

.. code-block:: bash

    usage: stk [-h] [-v] [-i]
           
            {create_matrix,sub_taxa,import_data,export_data,export_trees,export_bib,
             data_summary,safe_taxonomic_reduction,data_ind,data_overlap,permute_trees,
             clean_data,replace_genera,convert_files,create_subset}
            ...
    stk: error: too few arguments

The STK has a number of commands relating to data input and export, or processing, along with a some miscellaneous functions. These are detailed below.

Data input/export
-----------------

.. index:: export_bib
export_bib
**********

Exports a bibliographic file containing the references for all your sources. This output is a standard bibtex file.


.. index:: export_data
export_data
***********

Exports the data to the old STK format. This is directory based, with each source in a seperate directory. The
sources are split into two files per tree: an XML data file containing the meta-data and a tree file.


.. index:: export_trees
export_trees
***********

Export all the trees in the dataset into a single tree file.


.. index:: import_data
import_data
***********

Import data from the old STK format into a Phyml. Note there may be issues with author names which should be in the 
format of "Jon Hill and Katie Davis". 


Data processing
---------------

.. index:: clean_data
clean_data
**********


.. index:: create_subset
create_subset
*************


.. index:: create_matrix
create_matrix
*************

Create a Hennig or Nexus matrix using Baum and Ragen coding of all trees in the dataset.

.. code:: bash
  
  usage: stk create_matrix [-h] [-f {hennig,nexus}] [--overwrite] input output

-h --help
  Display the help message

-f --format
  Select format for the output matrix. Either hennig or nexus. Default is hennig

\-\-overwrite
  Overwrite the output file is it already exists. Otherwise you will be asked if you want to overwrite.

input
  The input Phyml

output
  The output filename

.. index:: create_subset
create_subset
*************


.. index:: data_ind
data_ind
********


.. index:: data_overlap
data_overlap
************


.. index:: data_summary
data_summary
************


.. index:: permute_trees
permute_trees
*************


.. index:: replace_genera
replace_genera
**************


.. index:: safe_taxonomic_reduction
safe_taxonomic_reduction
************************


.. index:: sub_taxa
sub_taxa
********


Miscellaneous functions
-----------------------

.. index:: convert_files
convert_files
*************

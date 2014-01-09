.. index:: CLI

The STK Command Line Interface
==============================

The STK CLI contains a number of functions for initialising and processing data.

The basics
----------

The CLI is initialised using:

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

The STK has a number of commands relating to data input and export,
processing, and some miscellaneous functions. These are detailed below.

To run a command, e.g. the create matrix function, the command is:

.. code-block:: bash

    stk create_matrix

This will produce the help for the create matrix function:

.. code-block:: bash 

    usage: stk create_matrix [-h] [-f {hennig,nexus}] [--overwrite] input output
    stk create_matrix: error: too few arguments

More detailed help can be obtained using the '''-h''' flag.

.. code-block:: bash

    >$ stk create_matrix -h
    usage: stk create_matrix [-h] [-f {hennig,nexus}] [--overwrite] input output

    positional arguments:
        input                 The input phyml file
        output                The output matrix file

    optional arguments:
        -h, --help          show this help message and exit
        -f {hennig,nexus},  --format {hennig,nexus}
                            The format of the matrix. hennig or nexus. Default is
                            hennig
        --overwrite         Overwrite the existing file without asking for
                            confirmation

The options can be given with either the long format (--help) or (-h). Not all
arguments have both (e.g. --overwrite).

Note the stk itself has three options:
 
 * -h -- help
 * -v -- verbose
 * -i -- ignore warnings

Note that these *must* come before the function you want to use. For example
this is valid:

.. code-block:: bash

    stk -v create_matrix

This is not.

.. code-block:: bash

    stk create_matrix -v

The functions are divided into input/output and processing, with one additional
miscellaneous function used for converting data files. Below is a brief
description of each function. Use the '''-h''' flag for information on options
and further details of input/output for the function.

Data input/export
-----------------

.. index:: export_bib

export_bib
**********

Exports a bibliographic file containing the references for all your sources. This output is a standard bibtex file.


.. index:: export_data

export_data
***********

Exports the data to the old STK format. This is directory based, with each source in a separate directory. The
sources are split into two files per tree: an XML data file containing the meta-data and a tree file.


.. index:: export_trees

export_trees
************

Export all the trees in the dataset into a single tree file.


.. index:: import_data

import_data
***********

Import data from the old STK format into a Phyml. Note there may be issues with author names which should be in the 
format of "FirstName1 LastName1 and FirstName2 LastName2". 


Data processing
---------------

.. index:: clean_data

clean_data
**********

Remove all non-informative trees and sources from the dataset. These are trees
that contain only three or fewer taxa.

.. index:: create_matrix

create_matrix
*************

Create a Hennig or Nexus matrix using Baum and Ragan coding of all trees in the dataset.

.. index:: create_subset

create_subset
*************

Create a subset from your data, specifying various criteria, including year
published, characters contained and taxa included.

.. index:: data_ind

data_ind
********

Check your data for adequate data independence. The output is a CSV file that
can be opened in a standard spreadsheet package and contains identical and
subset categories. It can also give you a new Phyml with non-independent data
removed.

.. index:: data_overlap

data_overlap
************

Check your data for adequate taxonomic overlap. Optional extras are graphical
outputs.

.. index:: data_summary

data_summary
************

Produce a text summary of the data, containing a taxa list, character list and
other useful things.

.. index:: permute_trees

permute_trees
*************

Permute individual trees or all trees containing non-monophyletic taxa (indicated by
a '%' symbol). Output is tree file or matrix for analysis.

.. index:: replace_genera

replace_genera
**************

Replace all generic level taxa with a polytomy of all species of that genus
already in the dataset.

.. index:: safe_taxonomic_reduction

safe_taxonomic_reduction
************************

Perform safe taxonomic reduction on the dataset. Output is the equivalency
matrix, plus the option to give subs files to safely delete and re-insert taxa

.. index:: sub_taxa

sub_taxa
********

Substitute or delete taxa from the dataset. Returns a new Phyml.


Miscellaneous functions
-----------------------

.. index:: convert_files

convert_files
*************

Convert a tree file or matrix into Nexus, Newick (tree only) or Hennig (matrix
only) formats.



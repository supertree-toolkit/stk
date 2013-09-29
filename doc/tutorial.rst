A STK Tutorial
==============

Introduction
------------

Entering data
-------------

Processing example
------------------

Examining the data
------------------


.. note:: old_data

The following is an example of how the scripts were used in creating a species-level supertree of birds.

The whole procedure can be divided into 5 stages:
# Collect data
# Standardise taxa
# Remove unnecessary data and taxa
# Check data
# Create matrix

Collecting Data
---------------

*STK tools used*
.. code:: bash
 stk_fix_treeview
 stk_check_data
 STK_XML

Data is collected as NEXUS tree files, with an accompanying XML file. TreeView is good for creating the NEXUS files. STK_XML can be used to create the accompanying XML file. Data is transcribed *exactly* as it is in the original source paper.

We stored data in directories named after the author, e.g. SmithAndJones_1990, JonesEtAl_1989, Smith_2007, etc, etc. Each author directory contains the tree and XML files as necessary.

If you are using TreeView, run the stk_fix_treeview script to ensure the NEXUS files are actually NEXUS compatible.
<code>
 stk_fix_treeview.pl --dir /home/jon/data/
</code>

Once data are collected (and indeed during collection), run the stk_check_data script, which will pick up missing XML files and malformed data files.
<code>
 stk_check_data.pl --dir /home/jon/data
</code>

Note that if errors occur, it is often helpful to run the check data script on the subdirectory that gave errors in verbose mode.
<code>
 stk_check_data.pl --dir /home/jon/data/bad_data --verbose
</code>

== Standardising Taxa ==

'''STK tools used'''
<code>
 stk_replace_taxa
 stk_check_data
 stk_tree_permutation
 stk_create_matrix
</code>

The next stage is to standardise the taxa - removing synonyms, polyphyletic taxa and sub-species.

Removing synonyms requires that a "standard" taxonomy is used. It does not matter what this is, but it does matter that two taxa that are actually the same taxa have the same name. The [http://darwin.zoology.gla.ac.uk/~rpage/MyToL/www/index.php Glasgow Taxonomic Name Server], [http://www.itis.gov/ ITIS] and other online databases are useful. In future this functionality is planned to be included in STK. Once a standardised taxa has been decided, the names can be replaced. For example:
<code>
 stk_replace_taxa.pl --dir /home/jon/data --old Incorrect_taxa --new Correct_taxa
</code>
will replace Incorrect_taxa with Correct_taxa throughout the dataset. In addition, this can be automated somewhat using a taxa substitution file:
<code>
 Incorrect_taxa = Correct_taxa
 Other_taxa = new_taxa
</code>
which allows you to do the '''all''' substitutions in one command and allows a record to be kept of what changes were made. In addition, this can then be used when the tree is updated.

To remove polyphyletic taxa and sub-species, the stk_tree_permutation script is used. This creates a number of trees per source tree, each with a different combination of the paraphyletic taxa (which sub-species can be). Note that this produces unique trees only.
<code>
 stk_tree_permutation.pl --file /home/jon/data/para_tree/para_tree.tre
</code>

These trees can then be combined into a single tree using PAUP or similar. First generate the matrix:
<code>
 stk_create_matrix.pl --dir /home/jon/data/para_tree
</code>
then load in PAUP and get the tree required with a branch-and-bound search or heuristic search for larger trees.

As always, run stk_check_data regularly:
<code>
 stk_check_data.pl --dir /home/jon/data
</code>

This is the "standard" data - '''''keep this''''' as this is what gets updated when new trees are added to the dataset.

'''The next few steps need doing each time you need to generate a tree.'''

== Remove unnecessary data and taxa ==

'''STK tools used'''
<code>
 stk_replace_taxa
 stk_check_data
 stk_check_substitutions
 stk_replace_genera
</code>

This is the first step that is needed each time a tree is generated. We need to check for data dependence, remove vernacular and higher names and finally, make all taxa specific.

To check for data dependence you '''must''' have created XML files to store the meta-data. Simply run the stk_data_dependence script on your data:
<code>
 stk_data_dependence.pl --dir /home/jon/data
</code>
This will produce a tab-delimited file in your data directory called duplication.dat. Load this into Excel or Open Office and it will list any other tree files that potentially overlap with that study.

Any data sources that overlap should be removed by combining the trees into a single tree, or removing the study with fewest taxa, as per the protocol of Davis (2008).

As it stands, the dataset still contains vernacular names and higher-order (e.g. family) names. This have to be removed by hand and replaced with polytomies of taxa that are part of that name. As this must happen each time a tree is produced, it is best done with a taxa substitution file. For example:

<code>
 Aegialornithidae = Aegialornis gallicus,Aegialornis leenhardti
 Ciconiidae = Mycteria,Anastomus,Ciconia,Ephippiorhynchus,Jabiru,Leptoptilos 
</code>

Note we can replace using generic or specific names. This file should be made to cover as many taxa as possible (even if you know they are not currently in your tree). We can then modify it to ensure that only taxa that are part of your dataset are included in the substitutions using the stk_check_subs script
<code>
 stk_check_subs.pl --file subs.txt --dir /home/jon/data
</code>

This will tell you about any taxa that are to be subbed into the dataset, but aren't currently part of the dataset. These should be removed from the substitution file (after a copy of the original has been saved of course!).

You can then carry out the substitutions using the stk_replace_taxa script.
<code>
 stk_repalce_taxa.pl --dir /home/jon/data --taxa subs.txt
</code>

For very large datasets it is probably best to split up your subs files into stages. In addition, due to memory considerations large datasets may cause a typical desktop to run out of memory. There is a [[Hints and Tips#Memory usage|wrapper script]] which carries out the substitutions one file-at-a-time which reduces memory consumption, but takes a lot longer to complete.

Finally, to guard against errors and bugs, back-up your data '''before''' carrying out substitutions. If you come across something that went wrong, report a bug here.

The final part of this process is to replace all generic taxa with specific taxa, e.g. ''Gallus'' is replace with a polytomy of all species belonging to ''Gallus''. This is done with the stk_replace_genera script.
<code>
 stk_replace_genera.pl --dir /home/jon/data
</code>

As with the stk_replace_taxa script, memory may be an issue, so use the stk_replace_genera script to produce a taxa substitution file for you, and use that with the [[Hints and Tips#Memory usage|wrapper script]].
<code>
 stk_replace_genera.pl --dir /home/jon/data --higher /home/jon/data/generic_subs.txt
 perl replace_genera_wrapper.pl --dir /home/jon/data/ --taxa /home/jon/data/generic_subs.txt
</code>

== Check data ==

'''STK tools used'''
<code>
 stk_check_data
 stk_check_overlap
 stk_data_summary
</code>

This stage makes sure that the data is ready for inclusion in the final tree. First step is to run stk_check_data (you have been running it all the time, right?). Then produce a data summary. Although this is not necessary, it allows manual checking of the data: were all the generic names removed where specific taxa are also in the data? are there any odd names that I forgot to substitute?
<code>
 stk_data_summary.pl --dir /home/jon/data --output /home/jon/data/Data_Summary.txt
</code>

Have a look in the file output and check everything is OK. If not, go back and fix things. Note that some of the statistics in the file might be useful when writing up your papers - how many trees, over what years the data is from, etc, etc.

Next, we need to check that all the trees are connected by at least two taxa with another tree. Use stk_check_overlap.
<code>
 stk_check_overlap.pl --dir /home/jon/data
</code>

This produces a tree2.dot file, which can be run through [http://www.graphviz.org/ GraphViz] to produce an image.
<code>
 neato -Tpng -O tree2.dot
</code>

This produces something like the following image.
[[File:Tree2.dot.png]]

== Create matrix ==

'''STK tools used'''
<code>
 stk_check_data
 stk_create_matrix
</code>

Finally, create your matrix ready for use in PAUP, etc.
<code>
 stk_create_matrix.pl --dir /home/jon/data
</code>

Your matrix will be in /home/jon/data/MRPmatrix.nex

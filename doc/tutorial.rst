A STK Tutorial
==============

Introduction
------------

.. note:: old_tutorial

The following is an example of how the scripts were used in creating a species-level supertree of birds.

The whole procedure can be divided into 5 stages:
 # Collect data
 # Standardise taxa
 # Remove unnecessary data and taxa
 # Check data
 # Create matrix

Collecting Data
---------------

Data is collected from literature as Nexus tree files and bibliographic (bibtex)
files. The easiest way to start is to create a bibtex file of your source data.
You can then import this to create your sources.

For each source you then create each tree you want to include in the analysis.
For each tree, you should also record the page and figure number, the characters
used, the analysis used and any other relavant information .Data is transcribed
*exactly* as it is in the original source paper. We deal with incorrect taxa
later. 

.. note:: Once done, this is your original file before any processing. Keep this safe. When you extend the data later, you should begin with this file.
 

One of the time consuming tasks is to digitise trees from the papers. Authors
rarely give digital trees, so you must use programs such as TreeView or Mequite
to turn the graphic in the paper into a digital tree file. This is normally a
Nexus file, though the STK can parse the trees from most of the popular tree
creation software packages. Note that paraphyletic taxa are encoded differently.
For example consider a tree as in figure .


Rather than include subspecies (we assume you want a species level tree), which
would then involve adding subspecies everywhere, you can tell the STK that these
taxa should be considered as one. We then remove these in the next step. We
would therefore encode this tree as shown in figure .

.. todo:: Video of entering data (link to this) and screenshots of the process (from video?)

Standardising Taxa
------------------

The next stage is to standardise the taxa - removing synonyms, polyphyletic taxa
and sub-species.

To remove polyphyletic taxa and sub-species, the tree permutation function is
used. This creates a number of trees per source tree, each with a different
combination of the paraphyletic taxa (which sub-species can be). Note that this
produces unique trees only. These can then be used to create a matrix or
output in a single tree file. You take this and create a 'mini-supertree' which
becomes your single source tree. For example load into PAUP and get the tree
required with a branch-and-bound search or heuristic search for larger trees.

.. note:: This is the "standard" data - *keep this* as this is what gets updated when new trees are added to the dataset.


Removing synonyms requires that a "standard" taxonomy is used. It does not
matter what this is, but it does matter that two taxa that are actually the same
taxa have the same name. Services such as `ITIS <http://www.itis.gov/>`_ and
other online databases are useful. In future this functionality is planned to
be included in STK. Once a standardised taxa has been decided, the names can be
replaced. 

Use your taxonomy to create a *subs file*. This can be done manually in a
standard text editor or using the STK GUI.

Once you have a *subs file* you can replace the taxa. Using either the GUI or
the command line, run the sub taxa function on your Phyml. This replaces and
deletes the taxa defined in your *subs file* in all trees in your dataset.

'''The next few steps need doing each time you need to generate a tree.'''

Remove unnecessary data and taxa
--------------------------------

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

Check data
----------

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

Create matrix
-------------

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

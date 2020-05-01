#!/bin/bash


# edit anything below
NTREES=2
TREE_FILE="Consensus_fixed.tre" # should contain NTREES trees
BAMMCONTROL="divcontrol.txt"
TAXONOMY="Taxonomy_220420_A_added.csv"

# Note all intermediate files are hardcoded in the scripts.

for i in $(seq 1 $NTREES);
do
    # extract tree from TREE_FILE
    Rscript extract_tree.R ${TREE_FILE} ${i}
    # this is saved to temp.tre in current dir

    # correct fossil names
    python2 check_fossils.py $TAXONOMY temp.tre temp_corrected.tre

    # fill in fossil taxa
    python2 fill_in_with_taxonomy.py --taxonomy_from_file ${TAXONOMY} --tree_taxonomy ${TAXONOMY} -s temp_corrected.tre temp_filled.tre

    # date tree
    Rscript date_nodes.R temp_filled.tre temp_corrected.tre

    # chop tree
    Rscript trim_tree.R

    # remove RED taxa
    python2 ../../stk sub_taxa -s RedTaxaToRemove.txt temp_chopped.tre final_tree.tre

    # create bamm folder and save everything
    mkdir mammal_tree_${i}
    mv final_tree.tre mammal_tree_${i}
    cp divcontrol.txt mammal_tree_${i}
    cp TreePar.R mammal_tree_{$i}

    # tidy up
    rm temp_filled.tre temp.tre temp_corrected.tre temp_chopped.tre
    rm dated_tree_randres.tre 
    # temp_final is mv'd hence no rm

done

# create job script for viking
sed 's/NCORES/${NTREES}/g' bamm_array_template.job > bamm_array.job


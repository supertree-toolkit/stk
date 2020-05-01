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
    Rscript extract_tree.R ${TREE_FILE} ${i} 2>&1 >/dev/null
    # this is saved to temp.tre in current dir
    if [ $? -eq 0 ]
    then
        echo "Extracted tree ${i}"
    else
        echo "Extract tree failed" >&2
        exit 1
    fi
    # correct fossil names
    python2 check_fossils.py $TAXONOMY temp.tre temp_corrected.tre
    if [ $? -eq 0 ]
    then
        echo "Made fossils CAPS"
    else
        echo "Fossil check failed" >&2
        exit 1
    fi

    # fill in fossil taxa
    python2 fill_in_with_taxonomy.py --taxonomy_from_file ${TAXONOMY} --tree_taxonomy ${TAXONOMY} -s Mammalia temp_corrected.tre temp_filled.tre 2>&1 >/dev/null
    if [ $? -eq 0 ]
    then
        echo "Tree filled"
    else
        echo "Tree filled failed" >&2
        exit 1
    fi

    # date tree
    Rscript date_nodes.R temp_filled.tre temp_corrected.tre 2>&1 >/dev/null
    if [ $? -eq 0 ]
    then
        echo "Dated tree"
    else
        echo "Dating tree failed" >&2
        exit 1
    fi

    # chop tree
    Rscript trim_tree.R 2>&1 >/dev/null

    # remove RED taxa
    python2 ../../stk sub_taxa -s RedTaxaToRemove.txt temp_chopped.tre final_tree.tre 2>&1 >/dev/null
    if [ $? -eq 0 ]
    then
        echo "Tree ready ${i}"
    else
        echo "Last step failed" >&2
        exit 1
    fi
    
    # create bamm folder and save everything
    mkdir mammal_tree_${i}
    mv final_tree.tre mammal_tree_${i}/
    cp divcontrol.txt mammal_tree_${i}/
    cp TreePar.R mammal_tree_${i}/

    # tidy up
    rm temp_filled.tre temp.tre temp_corrected.tre temp_chopped.tre
    rm dated_tree_randres.tre 
    # temp_final is mv'd hence no rm

done

# create job script for viking
sed "s/NCORES/${NTREES}/g" bamm_array_template.txt > bamm_array.txt
sed "s/NCORES/${NTREES}/g" treepar_array_template.txt > treepar_array.txt


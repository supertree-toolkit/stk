#
#  Makefile
#
#  Run our tests, either quietly or with verbose output

SRC = \
    stk_amalgamate_trees.t \
    stk_check_data.t \
    stk_check_overlap.t \
    stk_check_substitutions.t \
    stk_create_matrix.t \
    stk_data_independence.t \
    stk_data_summary.t \
    stk_fix_treefiles.t \
    stk_replace_genera.t \
    stk_replace_taxa.t \
	stk_search_data.t \
    stk_tree_permutation.t 
    
all: $(SRC)
	perl -MTest::Harness -e "runtests @ARGV;" $(SRC)

verbose: $(SRC)
	perl .run_verbose.pl $(SRC)

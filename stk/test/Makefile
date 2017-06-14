# Unit tests
# Add your unit test file here - make sure it contains
# if __name__ == '__main__':
#    unittest.main()
# so that the tests get run
#
UNIT_TESTS = \
_stk_taxonomy.py \
_stk_util.py \
_stk_trees.py \
_stk_internals.py \
_stk_phyml.py \
_supertree_toolkit.py \
_stk_import_export.py \
_schema_validation.py

# default case (and test). Loop through all
# tests listed above and run them
test: ${UNIT_TESTS}
	@for file in $(UNIT_TESTS); do \
	echo "----"; \
	echo "Running: $${file}"; \
	python $${file}; \
	done ;

# schema only test
# Incorrect schema are usually the fault of this
test-schema: _schema_validation.py
	python _schema_validation.py

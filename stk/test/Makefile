# Unit tests
# Add your unit test file here - make sure it contains
# if __name__ == '__main__':
#    unittest.main()
# so that the tests get run
#
UNIT_TESTS = \
_set_source_name.py 

# default case (and test). Loop through all
# tests listed above and run them
test: ${UNIT_TESTS}
	@for file in $(UNIT_TESTS); do \
	echo "----"; \
	echo "Running: $${file}"; \
	python $${file}; \
	done ;

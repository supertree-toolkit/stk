# Unit tests
# Add your unit test file here - make sure it contains
# if __name__ == '__main__':
#    unittest.main()
# so that the tests get run
#

# default case (and test). Loop through all
# tests listed above and run them
test:
	python -m unittest discover -p '_*.py'
# schema only test
# Incorrect schema are usually the fault of this
test-schema: _schema_validation.py
	python _schema_validation.py

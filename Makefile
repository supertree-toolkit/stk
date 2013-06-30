default:
	python setup.py build

test:
	cd stk/test/; make

install:
	python setup.py install

uninstall:
	rm -rf /usr/local/lib/python2.7/dist-packages/supertree_toolkit-0.1.1.egg-info/
	rm -rf /usr/local/lib/python2.7/dist-packages/stk*
	rm -rf /usr/local/lib/python2.7/dist-packages/p4
	rm -rf /usr/local/lib/python2.7/dist-packages/dxdiff/
	rm -rf /usr/local/lib/python2.7/dist-packages/yapbib/
	rm -rf /usr/local/bin/stk*
	rm -rf /usr/local/share/stk
	rm -rf /usr/local/share/phyml

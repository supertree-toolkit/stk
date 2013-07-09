VERSION=0.1.1

default:
	python setup.py build

test:
	cd stk/test/; make

install:
	python setup.py install --prefix=$(DESTDIR)/usr/local

uninstall:
	rm -rf /usr/local/lib/python2.7/dist-packages/supertree_toolkit-0.1.1.egg-info/
	rm -rf /usr/local/lib/python2.7/dist-packages/stk*
	rm -rf /usr/local/lib/python2.7/dist-packages/p4
	rm -rf /usr/local/lib/python2.7/dist-packages/dxdiff/
	rm -rf /usr/local/lib/python2.7/dist-packages/yapbib/
	rm -rf /usr/local/bin/stk*
	rm -rf /usr/local/share/stk
	rm -rf /usr/local/share/phyml

#builddeb:
#	python setup.py --command-packages=stdeb.command sdist_dsc --prefix=$(DESTDIR)/usr/local
#	cd deb_dist/supertree-toolkit-${VERSION}
#	dpkg-buildpackage -rsudo -uc -us


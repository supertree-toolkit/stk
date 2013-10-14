curl -O -L http://sourceforge.net/projects/macpkg/files/PyGTK/2.24.0/PyGTK.pkg/download
mv download PyGTK.pkg
open PyGTK.pkg
read -p "Press any key to continue when PyGTK is finished installing..." -n1 -s
curl -O https://pypi.python.org/packages/source/s/setuptools/setuptools-1.1.6.tar.gz
tar zxvf setuptools-1.1.6.tar.gz
cd setuptools-1.1.6
python setup.py install
cd ../

# Let's get lxml installed
easy_install --allow-hosts=lxml.de,*.python.org lxml
# dateutil (for matplotlib) 
easy_install python-dateutil
# Numpy
easy_install numpy
# matplotlib
easy_install matplotlib
# networkx
easy_install networkx
# dxdiff
cd dxdiff/
python setup.py install
cd ../../
# Now install the STK
python setup.py install

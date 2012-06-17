import unittest
import math
import sys
sys.path.append("../../")
from stk.supertree_toolkit import import_bibliography 
import os
from lxml import etree
from util import *
from stk.stk_exceptions import *

parser = etree.XMLParser(remove_blank_text=True)
xml_start = etree.parse("data/input/start_up.phyml")

class TestBibliography(unittest.TestCase):

    def test_import_single_article(self):
        xml_article_c = etree.tostring(etree.parse("data/output/bib_import_single_article.phyml",parser),pretty_print=True)
        bib_article = "data/input/article.bib"
        # import basic xml file
        xml = etree.tostring(xml_start)
        # call import_bib function
        new_xml = import_bibliography(xml, bib_article)
        # test resulting xml
        self.assert_(isEqualXML(new_xml, xml_article_c))

    def test_import_single_article_doi(self):
        xml_article_c = etree.tostring(etree.parse("data/output/bib_import_single_article_doi.phyml",parser),pretty_print=True)
        bib_article = "data/input/article_doi.bib"
        # import basic xml file
        xml = etree.tostring(xml_start)
        # call import_bib function
        new_xml = import_bibliography(xml, bib_article)
        # test resulting xml
        self.assert_(isEqualXML(new_xml, xml_article_c))

    def test_import_single_book(self):
        xml_book_c = etree.tostring(etree.parse("data/output/bib_import_single_book.phyml",parser),pretty_print=True)
        bib_book = "data/input/book.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_book)
        self.assert_(isEqualXML(new_xml, xml_book_c))

    def test_katie_article(self):
        bib_book = "data/input/test.bib"
        xml = etree.tostring(xml_start)
        try:
            new_xml = import_bibliography(xml, bib_book)
        except BibImportError as details:
           self.assert_(details.msg == "Error importing bib file. Check all your authors for correct format")
        except:
           return False

    def test_katie_article2(self):
        bib_book = "data/input/test2.bib"
        xml = etree.tostring(xml_start)
        try:
            new_xml = import_bibliography(xml, bib_book)
        except BibImportError as details:
           self.assert_(details.msg == "Error importing bib file. Check all your entry keys")
        except:
           return False
#    def test_import_single_incollection(self):
#
#    def test_import_single_inbook(self):
#
#    def test_import_allitems(self):
#
#    def test_import_allitems_existing_tree(self):

if __name__ == '__main__':
    unittest.main()
 

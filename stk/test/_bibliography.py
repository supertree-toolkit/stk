import unittest
import math
import sys
# so we import local stk before any other
sys.path.insert(0,"../")
from supertree_toolkit import import_bibliography, export_bibliography
import os
from lxml import etree
from util import *
from stk.stk_exceptions import *
import tempfile
import stk.yapbib.biblist as biblist
import stk.yapbib.bibparse as bibparse
import stk.yapbib.bibitem as bibitem

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

    def test_ut8_article(self):
        bib_import_utf8_answer = etree.tostring(etree.parse("data/output/bib_import_utf8.phyml",parser),pretty_print=True)
        bib_utf8 = "data/input/utf8_input.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_utf8)
        self.assert_(isEqualXML(new_xml, bib_import_utf8_answer))


    def test_katie_article(self):
        bib_book = "data/input/test.bib"
        xml = etree.tostring(xml_start)
        try:
            new_xml = import_bibliography(xml, bib_book)
        except BibImportError as details:
           # Check that an entry with dodgy author entry reports the correct key to help the user find it
           self.assert_(details.msg == "Error importing bib file. Check all your authors for correct format: Porter2005")
        except:
           return False

    def test_katie_article2(self):
        bib_book = "data/input/test2.bib"
        xml = etree.tostring(xml_start)
        try:
            new_xml = import_bibliography(xml, bib_book)
        except BibImportError as details:
           self.assert_(details.msg == "Error importing bib file. Error parsing:  author = {Ahyong, S. T. and O'Meally, D.}, title = {Phylogeny of the Decapoda reptantia: Resolutio...\nMissing Bibtex Key")
        except:
           return False

    def test_export_bib_article(self):
        xml_article_c = etree.tostring(etree.parse("data/output/bib_import_single_article.phyml",parser),pretty_print=True)
        bib_article = "data/input/article.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_article)
        # Now export it back and compare the data
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".bib")
        export_bibliography(new_xml,temp_file)        
        # parse both files in yapbib and compare
        b_orig = biblist.BibList()
        b_exported = biblist.BibList()
        b_orig.import_bibtex(bib_article)
        b_exported.import_bibtex(temp_file)
        items= b_exported.List() # yapbib helpfully renames the item key, so grab the first one
        exp = b_exported.get_item(items[0])
        items= b_orig.List() # yapbib helpfully renames the item key, so grab the first one
        orig = b_orig.get_item(items[0])
        os.remove(temp_file)        
        self.assert_(orig.get('title') == exp.get('title'))
        self.assert_(orig.get('journal') == exp.get('journal'))
        self.assert_(orig.get('volume') == exp.get('volume'))
        self.assert_(orig.get('doi') == exp.get('doi'))
        self.assert_(orig.get('pages') == exp.get('pages'))
        self.assert_(orig.get('author') == exp.get('author'))


    def test_export_bib_book(self):
        xml_article_c = etree.tostring(etree.parse("data/output/bib_import_single_book.phyml",parser),pretty_print=True)
        bib_article = "data/input/book.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_article)
        # Now export it back and compare the data
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".bib")
        export_bibliography(new_xml,temp_file)        
        # parse both files in yapbib and compare
        b_orig = biblist.BibList()
        b_exported = biblist.BibList()
        b_orig.import_bibtex(bib_article)
        b_exported.import_bibtex(temp_file)
        items= b_exported.List() # yapbib helpfully renames the item key, so grab the first one
        exp = b_exported.get_item(items[0])
        items= b_orig.List() # yapbib helpfully renames the item key, so grab the first one
        orig = b_orig.get_item(items[0])
        os.remove(temp_file)        
        self.assert_(orig.get('title') == exp.get('title'))
        self.assert_(orig.get('series') == exp.get('series'))
        self.assert_(orig.get('doi') == exp.get('doi'))
        self.assert_(orig.get('pages') == exp.get('pages'))
        self.assert_(orig.get('author') == exp.get('author'))
        self.assert_(orig.get('editor') == exp.get('editor'))
        self.assert_(orig.get('publisher') == exp.get('publisher'))


    def test_export_html(self):
        bib_article = "data/input/article.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_article)
        # Now export it back and compare the data
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".html")
        export_bibliography(new_xml,temp_file,format="html")        
        f = open(temp_file,"r")
        output = f.readlines()
        output = '\n'.join(output)
        os.remove(temp_file)              
        # just asserts something useful has been written out
        self.assert_(output.find('html') > -1)
        self.assert_(output.find('Davis') > -1)
        self.assert_(output.find('Hill') > -1)
        self.assert_(output.find('book .series') > -1)

    def test_export_latex(self):
        bib_article = "data/input/article.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_article)
        # Now export it back and compare the data
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tex")
        export_bibliography(new_xml,temp_file,format="latex")        
        f = open(temp_file,"r")
        output = f.readlines()
        output = '\n'.join(output)
        os.remove(temp_file)              
        # just asserts something useful has been written out
        self.assert_(output.find('documentclass') > -1)
        self.assert_(output.find('Davis') > -1)
        self.assert_(output.find('Hill') > -1)
    
    def test_export_long(self):
        bib_article = "data/input/article.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_article)
        # Now export it back and compare the data
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tex")
        export_bibliography(new_xml,temp_file,format="long")        
        f = open(temp_file,"r")
        output = f.readlines()
        output = '\n'.join(output)
        os.remove(temp_file)  
        # just asserts something useful has been written out
        self.assert_(output.find('article') > -1)
        self.assert_(output.find('Davis') > -1)
        self.assert_(output.find('Hill') > -1)

    def test_export_short(self):
        bib_article = "data/input/article.bib"
        xml = etree.tostring(xml_start)
        new_xml = import_bibliography(xml, bib_article)
        # Now export it back and compare the data
        temp_file_handle, temp_file = tempfile.mkstemp(suffix=".tex")
        export_bibliography(new_xml,temp_file,format="short")        
        f = open(temp_file,"r")
        output = f.readlines()
        output = '\n'.join(output)
        os.remove(temp_file) 
        # just asserts something useful has been written out
        self.assert_(output.find('Davis') > -1)
        self.assert_(output.find('Hill') > -1)


#    def test_import_single_incollection(self):
#
#    def test_import_single_inbook(self):
#
#    def test_import_allitems(self):
#
#    def test_import_allitems_existing_tree(self):

if __name__ == '__main__':
    unittest.main()
 

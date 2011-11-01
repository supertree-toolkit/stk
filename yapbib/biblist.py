#!/usr/bin/env python
'''
Class storing a bibliography

A Class that to store a list of references (list of papers, books, manuals, ...)
It is based in dictionaries, with a unique self-generated key

Example of use:
  
import yapbib.biblist as biblist
b=biblist.BibList()
b.import_bibtex("mybib.bib")
items= b.List() # Shows the keys of all entries
it= b.get_item(items[0]) # Get first item 
# (Alternatively, to get the first item you can use 
it= b.get_items()[0] 
it.get_fields() # Show all fields for item
it.preview()    # Show a preview (brief info)
bib= it.to_bibtex() # get item in BibTeX form
tex= it.to_latex() # get item in LaTeX form
html= it.to_html() # get item in html form
print it  # print full information on the item
print unicode(it) # Use this if it has non-ascii characters

'''
import sys
import os

import textwrap

import bibitem
import helper
import latex
latex.register()

import cPickle as pickle

# Index used for internally for each part of a name
# (A_VON, A_LAST, A_JR, A_FIRST)= range(4)

class BibList(dict):
  '''Class storing a bibliography  (list of papers, books, manuals, ...)'''
  def __init__(self):
    self.ListItems= []
    self.abbrevDict= dict(helper.standard_abbrev)
    self.sortorder=['_type','key'] # Fields used to sort the list
    self.sortedList=[]   # Sorted version of ListItems
    self.issorted=False # Keeps tracks whether the List is sorted
    self.reverse=False
    self.keepAbbrevs=True
    self.encoding='utf-8'
    self.bib={}

  def update(self,blist):
    try:
      self.bib.update(blist.bib)  # blist es un objeto del tipo BibList
      self.set_properties_from(blist)
    except:
      try: self.bib.update(blist)  # blist es solo un diccionario
      except:  raise TypeError, 'Argument incorrect type, must be BibList object'

  def set_properties_from(self,blist):
    """
    Try to get properties from other biblist object
    """
    try:
      self.ListItems += blist.ListItems
      self.ListItems= list(set(self.ListItems))
#       for k in blist.ListItems:
#         if k not in self.ListItems:  self.ListItems.append(k)
    except:  pass
    try:     self.abbrevDict.update(blist.abbrevDict)
    except:  pass
    if self.issorted: self.sort()
    else: self.sortedList = self.ListItems[:]

  def __str__(self):
    s=''
    if not self.issorted:      self.sortedList= self.sort()
    for l in self.sortedList:
      s+= '%s\n' %(self.get_item(l).__str__())
    return s.encode(self.encoding,'ignore')

  def __repr__(self):
    s= u'bib= %s\n'%(str(self.bib).decode(self.encoding,'ignore'))
    s+= u'abbrevDict= %s\n' %(self.abbrevDict)
    s+= u'ListItems= %s\n' %(self.ListItems)
    s+= u'sortedList= %s\n' %(self.sortedList)
    s+= u'issorted= %s\n' %(self.issorted)
    s+= u'encoding= %s\n'%(self.encoding)
    return s.decode(self.encoding,'ignore')

  def preview(self,n=None):
    """
    Show a preview of the publications (sorted).
    Optionally, only show the first n of them. If n is None, show all publications.
    """
    s=''
    nn= len(self.ListItems)
    if n != None:
      nn= min(n,nn)
    if not self.issorted:
      self.sort()
    for l in self.sortedList[:nn]:
      s+= '%s\n' %(self.get_item(l).preview())

    s=unicode(s,self.encoding,'ignore')
    return s

  def add_item(self, bib, key=None):
    be= bibitem.BibItem(bib,key)
    key= be.get_key()
    if key == None:
      sys.stderr.write('%s\nENTRY FAILED TO IMPORT: %s\n%s%s\n'%(80*'*',bib.get_field('_code',''),bib,80*'*'))
      return False

    if key in self.ListItems:
      if key == self.get_item(key).get_field('_code'): 
        sys.stderr.write('W: ENTRY ALREADY PRESENT: %s (%s)\n'%(key,bib['_code']))
        return False
      else:
        key = be.get_field('_code')

    self.bib[key]= be
    self.ListItems.append(key)
    self.sortedList.append(key)
    self.issorted=False
    return True

  def remove_item(self, key):
    if key in self.ListItems[:]:
      self.ListItems.remove(key)
      self.sortedList.remove(key)
      del(self.bib[key])
      return True
    else:
      return False

  def get_items(self):
    return self.bib.values()

  def get_item(self,key):
    return self.bib.get(key)

  def set_item(self,key,value):
    "Set the value of a given item (that already exists)"
    if key in self.ListItems:
      self.bib[key].update(value)
      return True
    else:
      return False

  def insertAbbrev(self, abbrev, value):
    if abbrev in self.abbrevDict:
      return False
    self.abbrevDict[abbrev] = value
    return True

  # resolve all abbreviations found in the value fields of all entries
  def resolve_abbrevs(self):
    self.keepAbbrevs=False
    for k in self.ListItems:
      self.get_item(k).resolve_abbrevs(self.abbrevDict)

  def List(self):
    return self.ListItems
  
  def sort(self, order=[], reverse=None):
    """
    Sort the entries according to the specified order
    """
    if order == []:
      order= self.sortorder
    else:
      self.sortorder= order
    if reverse == None:
      reverse= self.reverse
    else:
      self.reverse= reverse

    numericfields= ['year','volume','number','firstpage','lastpage']
    sortorder=order
    sortorder.append('key')
    s=[]
    for k in self.ListItems:
      oo=[]
      for o in sortorder:
        if o in numericfields : # For Numerical values we complete to the left with zeros
          oo.append(self.get_item(k).get(o,'').zfill(10))
        elif o == 'author':
          oo.append(self.get_item(k).get_authors_last())
        elif o == 'date': # Shorthand for ['year','month']
          oo.append(self.get_item(k).get_field('year','').zfill(10))
          oo.append(self.get_item(k).get_field('month',''))
        else:
          oo.append(self.get_item(k).get_field(o,'ZZZZ'))  # At the end if they have not field o
      s.append(oo)

    s.sort(reverse=reverse)
    self.issorted=True
    self.sortedList=[x[-1] for x in s]
    return self.sortedList


  def search(self, findstr, fields=[], caseSens=False, types='all'):
    """
    Search on the bibliography for findstr
    The result is a list with the keys of the items that match the search
    keys are the keys that we look
    types are on what kind of publication do we search (article, book,...)
    """
    result = []
    for f in self.sortedList:
      if types=='all' or self.get_item(f).get('_type') in types:
        if findstr == '*': found= True
        else:     found= self.get_item(f).search(findstr,fields,caseSens)
        if found:
          result.append(f)
    return result

#   def recreate_keys(self):
#     for b in self.sortedList[:]:
#       b1= self.get_item(b)
#       if b1 != None:
#         self.ListItems.remove(b)
#         key= b1.recreate_key()
#     self.sortedList= self.ListItems[:]
#     self.sort()

  def normalize(self):
    '''Make bibtex key tha same that internal key'''
    for b in self.sortedList:
      self.get_item(b).normalize()
    
	#############################################################3
	# import methods
	#############################################################3
  def load(self, fname):
    '''
    Load a biblist from file "fname" using the standard cPickle module.
    It can be used uncompressed or compressed with gzip or bzip
    '''
    try:
      fi= helper.openfile(fname,'rb');  c= pickle.load(fi);  helper.closefile(fi)
    except: 
      raise ValueError, 'Error loading data'
    try:    self.update(c)
    except: raise ValueError, 'Error updating data'
      
  def dump(self, fname, protocol=pickle.HIGHEST_PROTOCOL):
    '''
    Store the biblist in file "fname" using the standard cPickle module.
    It can be used uncompressed or compressed with gzip or bzip
    '''
    # if not '.dmp' in fname: fname='%s.dmp' %(fname)
    try:
      fo=helper.openfile(fname,'wb');  pickle.dump(self,fo,protocol=pickle.HIGHEST_PROTOCOL);
      helper.closefile(fo)
    except:
      raise ValueError, 'Error loading data'

  def import_bibtex(self, fname=None, normalize=True, ReplaceAbbrevs=True):
    """
    Import a bibliography (set of items) from a file
    If normalize the code (citekey) is overwritten with a standard key following our criteria
    """
    ncount=0
    st,db= bibitem.bibparse.parsefile(fname)

    if st != []:
      for k,v in st.iteritems():
        self.insertAbbrev(k, v)

    self.keepAbbrevs = not ReplaceAbbrevs
    if db != None:
      for k,v in db.iteritems():
        b1= bibitem.BibItem(bibitem.bibparse.replace_abbrevs(self.abbrevDict,dict(v)), normalize = normalize)
        key= b1.get_key()               # The key is generated
        if self.keepAbbrevs:  status= self.add_item(v, key)
        else:                 status= self.add_item(b1,key)
        if status:
          ncount+= 1
          if normalize:   self.get_item(key).normalize() # _code is put equal to key
    self.sort()
    return ncount

  def import_ads(self, fname, normalize=True):
    """
    Import a bibliography (set of items) from a file
    If normalize the code (citekey) is overwritten with a standard key following our criteria
    """
    ncount=0
    db= bibitem.adsparse.parsefile(fname)
    if db != None:
      for k,v in db.iteritems():
        status= self.add_item(v)
        if status:
          ncount+= 1
          if normalize:
            self.get_item(self.ListItems[-1]).normalize()
    self.sort()
    return ncount

##########################################################################################
                                     # export methods
##########################################################################################
  def set_default_styles(self):
    for item in self.get_items():
      item.set_default_styles()
      
  def output(self, fout=None, formato='short', verbose=True):
    """
    Export all entries to a fout file with default options. All strings are resolved.
    following formats are defined:
    short (default)
    long
    bibtex
    latex
    html
    xml
    """

    if verbose:
      print '# %d items to output' %(len(self.ListItems))

    if formato == 'bibtex':  self.export_bibtex(fout)
    elif formato == 'latex' :  self.export_latex(fout)
    elif formato == 'html'  :  self.export_html(fout)
    elif formato == 'xml'   :  self.export_xml(fout)
    else:
      fi= helper.openfile(fout,'w')
      if formato   == 'full'  :   fi.write(str(self))
      else:  fi.write(self.preview().encode(self.encoding))
      helper.closefile(fi)


  def to_bibtex(self, indent=2, width=80):
    """
    Export all entries to a bibtex file. All strings are resolved.
    """
    if not self.issorted:      self.sort()

    s=''
    if self.keepAbbrevs:
      # Abbreviations with no standard abbreviations
      abbrevs={}
      std_abb= [x[0] for x in helper.standard_abbrev]
      for k in self.abbrevDict.keys()[:]:
        if k not in std_abb:
          abbrevs[k]= self.abbrevDict[k]

      for k in sorted(abbrevs):
        s+='@STRING{%s = "%s"}\n'%(k,self.abbrevDict[k])
      s+='\n\n'

    for l in self.sortedList:
      s+= '%s\n' %(self.get_item(l).to_bibtex(width= width))
      
    if not self.keepAbbrevs:      return s 
    else:      return helper.reg_defstrng.sub(r'\1\2',s)


  def export_bibtex(self, fname=None,indent=2, width=80):
    """
    Export a bibliography (set of items) to a file in bibtex format:
    """
    fi= helper.openfile(fname,'w');  fi.write(self.to_bibtex(width));  helper.closefile(fi)

  ##############################
  def to_latex(self,style={}):
    if not self.issorted:
      self.sort()

    s=''
    for l in self.sortedList:
      if self.keepAbbrevs:
        bib=bibitem.BibItem(self.get_item(l)) # copy the item to resolve_abbrevs
        bib.resolve_abbrevs(self.abbrevDict)
        ss= bib.to_latex(style)
      else:
        ss= self.get_item(l).to_latex(style)
      s+= '%s %s\n' %(r'\item',ss)
    return s

      
  def export_latex(self, fname=None, style={}, head=None,tail=None):
    """
    Export a bibliography (set of items) to a file in latex format:
    """
    if head == None:
      head= r'''\documentclass[12pt]{article}
\newcommand{\authors}[1]{#1}
\usepackage{hyperref}
\begin{document}
\begin{enumerate}
'''
    if tail== None:
      tail= r'\end{enumerate} \end{document}'
    s= '%s\n%s\n%s\n'%(head, self.to_latex(style=style).encode('latex'), tail)
    fi= helper.openfile(fname,'w');  fi.write(s);  helper.closefile(fi)

  ##############################
  def to_html(self,style={}):
    if not self.issorted:
      self.sort()

    s=''
    for l in self.sortedList:
      tipo= self.get_item(l).get_field('_type','article')

      if self.keepAbbrevs:
        bib= bibitem.BibItem(self.get_item(l)) # copy the item to resolve_abbrevs
        bib.resolve_abbrevs(self.abbrevDict)
        ss= bib.to_html(style)
      else:
        ss= self.get_item(l).to_html(style)
      s+= '<li class="%s"> %s </li>\n' %(tipo, ss)
    return s

  def export_html(self, fname=None, style={}, head='',tail='', separate_css='biblio.css',encoding='utf-8'):
    """
    Export a bibliography (set of items) to a file in bibtex format: style is a dictionary
    (like in bibitem objects) where the values is a pair (open,close) to insert around the
    data.
    head and tail are html code to insert before and after the list of publications
    separate_css may have the
    """
    # default style
    css_style="""
.title a,
.title {font-weight: bold;	color :    #416DFF; }
ol.bibliography li{	margin-bottom:0.5em;}
.journal {  font-style: italic;}
.book .series {  font-style: italic;}
.journal:after {content:" ";}
.series:after {content:" ";}
li.article .publisher {display:none;}
.publisher:before {content:" (";}
.publisher:after {content:") ";}
.year:before {content:" (";}
.year:after {content:").";}
.authors {font-weight:bol; display:list;}
.authors:after {content:". ";}
.volume { font-weight: bold;}
.book .volume: before { content: "Vol. ";}
.number:before {content:":";}
.button {display:inline; border: 3px ridge;line-height:2.2em;margin: 0pt 10pt 0pt 0pt;padding:1pt;}
.masterthesis{content:"Master Thesis"}
.phdthesis{content:"Phd Thesis"}
div.abstracts {display: inline; font-weight: bold; text-decoration : none;  border: 3px ridge;}
div.abstract {display: none;padding: 0em 1% 0em 1%; border: 3px double rgb(130,100,110); text-align: justify;} 
    """

    if helper.is_string_like(separate_css):
      fi=helper.openfile(separate_css,'w');  fi.write(css_style);  helper.closefile(fi)
      name= os.path.commonprefix([os.path.dirname(fname),os.path.dirname(separate_css)])
      print os.path.basename(separate_css)
      name= os.path.join(name,separate_css[len(name):])
      css='  <link title="new" rel="stylesheet" href="' + name + '" type="text/css">'
    else:
      css= '<style type="text/css">' +css_style + '</style>'

    if head=='':
      head='''
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset='''+encoding.upper()+'''">
    ''' +  css + '''
    <title>Publicaciones</title>
    <script language="JavaScript" type="text/javascript">
    //<![CDATA[
    function toggle(thisid) {
    var thislayer=document.getElementById(thisid);
    if (thislayer.style.display == 'block') {
    thislayer.style.display='none';
    } else {
    thislayer.style.display='block';}
    }
    //]]>
    </script>
    </head>
    <body>
    <h2>Publicaciones</h2>
    <ol class="bibliography">
    '''
    if tail == '':
      tail="""
      </ol>
      </body>
      </html>
      """
      
    s= head + self.to_html(style=style) + tail
    fi= helper.openfile(fname,'w');  fi.write(s.encode(encoding,'xmlcharrefreplace'))
    helper.closefile(fi)

  ##############################
  def to_xml(self, prefix='', indent=2):
    if not self.issorted:      self.sort()

    s=''
    for l in self.sortedList:
      if self.keepAbbrevs:
        bib=bibitem.BibItem(self.get_item(l)) # copy the item to resolve_abbrevs
        bib.resolve_abbrevs(self.abbrevDict)
        ss= bib.to_xml(p=prefix,indent=indent)
      else:
        ss= self.get_item(l).to_xml(p=prefix,indent=indent)
      
      s+= '%s' %(ss)
    return s
      
  def export_xml(self, fname=None, prefix='', head='', tail='', indent=2):
    """
    Export a bibliography (set of items) to a file in xml format:
    A prefix may be added to account for a namespace. But if added both head and tail
    should take it into account to make it a valid xml document
    """
    if head == '':
      head='''<?xml version="1.0" encoding="utf-8"?>
  <''' + prefix +'''bibliography>
'''
    if tail == '':
      tail="\n</"+prefix+"bibliography>"
      
    s= head + self.to_xml(prefix=prefix) + tail
    fi= helper.openfile(fname,'w');  fi.write(s.encode('utf-8','xmlcharrefreplace'))
    helper.closefile(fi)
##########################################################################################
##########################################################################################
    
def test():
  if sys.argv[1:]:
    filepath= sys.argv[1]
  else:
    print "No input file"
    print "USAGE:  "+sys.argv[0]+ " FILE.bib\n\n  It will output the XML file: FILE.xml"
    sys.exit(2)

  biblio= BibList()
  if filepath.find('.bib') != -1:
    nitems= biblio.import_bibtex(filepath,False,False)
    print '%s\nFrom BibTeX file: %s'%(80*"*",filepath)
  elif filepath.find('.ads') != -1:
    nitems= biblio.import_ads(filepath,True)
    print '%s\nFrom ADS file: %s'%(70*"*",filepath)
  print '%d items ingresados\n'%(nitems)
  print 'Rodrig en los siguientes items:',biblio.search('Rodrig')
  print 20*'='
  print 'Items Ordenados por cite: %s' %(biblio.sort(['key']))
  print 20*'*'
  print 'Items Ordenados por Apellido de Autores: %s' %(biblio.sort(['author']))
  print 20*'*'
  print 'Items Ordenados por Fecha: %s' %(biblio.sort(['date']))
  print 20*'*'
  nn=5
  print 'Preview (At most %d items):'%(nn)
  print 20*'*'
  print biblio.preview(nn)
  print 'Preview with LaTeX symbols (At most First %d items):'%(nn)
  print 20*'*'
  print biblio.preview(nn).encode('latex')
  biblio.export_bibtex('tempo.bib',4)
  biblio.export_html('tempo.html')
  biblio.export_xml('tempo.xml',prefix='')

def main():
  test()


if __name__ == "__main__": main()

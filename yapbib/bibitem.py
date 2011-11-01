#!/usr/bin/env python
'''
Class storing a bibligraphic item (paper, book, manual, ...)

Required fields: _code, _type, author, year

Internally authors are represented as a list [first author, second author, ...]
where each author is represented itself as a list:
                                      [von, Last, First, Jr]
following the terminology of BibTeX.
Note that BibTeX would use DIFFERENTLY:  von Last, Jr, First

There are two field related to the journal: journal and journal_abbrev 

'''
import sys
import os
import textwrap
import codecs

import bibparse
import adsparse
import helper
import latex
latex.register()


# Index used for internally for each part of a name
A_VON=0; A_LAST=1; A_FIRST=2; A_JR=3
##########################################################################################
class BibItem(dict):
  """
  Class that store a bibliography item
  """

  def __init__(self,bib={},key=None,normalize=False):
    """
    Initialize the object. 
    """
    self.key=''
    self.html_style={}
    self.latex_style={}
    if bib=={}:
      self.update({})
      self.key=None
      self.set_default_styles()
    else:
      self.set(bib, key)
      if normalize: self.normalize()
    self.encoding='utf8'

  def set(self, b, key=None):
    """
    Set the values of the object to those given by the dictionary.
    If b is not a valid dictionary it will return an empty object
    """
    t= self._verify_entry(b)
    if t:
      # Copy the dictionary
      self.update(b)

      if key != None:
        self.key= key
      else:
        try: 
          if b.get_key() != None:  self.key= b.get_key()  # b is a BibItem object but has not key
          else: self.key= self.create_entrycode()
        except:  # b is a dictionary
          self.key= self.create_entrycode()

      if self.key == '':
        self.key=None
      elif self.get_field('_code','') == '':
        self.normalize()
      try:
        self.set_styles(html=b.html_style, latex= b.latex_style)
      except:
        self.set_default_styles()
    else:
      self.key=None

  def resolve_abbrevs(self, strs={}):
    bibparse.replace_abbrevs(strs,self)
  
  def _verify_entry(self,b):
    '''Verify that the entry is valid'''
    for f in helper.minimalfields:
      if not b.has_key(f):
        return False

    if b.has_key('journal'):
      if not b.has_key('journal_abbrev'):
      # Create one abbrev
        journal, abbrev= helper.identify_some_journals(b)
        b['journal_abbrev']= abbrev
        b['journal']= journal
        return True
    return True

   
  def normalize(self):
    self['_code']= self.key

  def set_default_styles(self):
    default_html_style={
      '_type'      :None,
      'author'     :(r'<span class="authors">',r'</span> '),
      'title'      :(r'<span class="title">',r'</span> '),             
      'journal'    :(r'<span class="journal">',r'</span> '),
      'school'     :(r'<span class="journal">',r'</span> '),
      'volume'     :(r'<span class="volume">',r'</span> '),
      'number'     :(r'<span class="number">',r'</span> '),
      'year'       :(r'<span class="year">',r'</span> '),
      'publisher'  :(r'<span class="publisher">',r'</span> '),
      'series'     :(r'<span class="series">',r'</span> '),
      'firstpage'  :(r' ',r''),
      'lastpage'   :(r'-',r''),
      'booktitle'  :(r'<span class="journal">',r'</span> '),             
      'chapter'    :(r'<span class="volume">',r'</span> '),
      'institution':None,
      'organization':None,
      'address'    :None,
      'edition'    :(r'<span class="volume">',r'</span> '),
      'issn'       :None,
      'isbn'       :None,
      'note'       :None,
      'annote'     :None,
      'month'      :None,
      'keywords'   :None,
      '_code':(r' <a class="button" title="Download Local Copy" href="deposito/',r'.pdf">L-C</a>'),
      'url'        :(r'  <a class="button" title="External Link" href="',r'">E-L</a>'),
      'doi'        :(r'  <a class="button" title="Get from source" href="http://dx.doi.org/',r'">DOI</a>'),
      'abstract'   :(r'<div class="abstracts button" onClick="toggle('+"'"+self.key.lower()+"'"+')">ABS</div>\n<div class="abstract" id="'+ self.key.lower()+'">',r'</div>')
      }
    default_latex_style={
      'author'     : (r'\authors{',r'}. '),
      'title'      : (r' \textbf{',r'} '),
      'journal'    : (r' \emph{',r'} '),
      'volume'     : (r' \textbf{',r'}'),
      'year'       : (r', ',r'.'),
      'firstpage'  : (r', ',r''),
      'lastpage'   : (r'-',r''),
      'number'     : (':',''),
      'school'     : ('',''),
      'url'        : (r' \url{',r'}'),
      'doi'        : (r' \url{',r'}'),
      'abstract'   : None,
      '_code': None,
      }

    self.html_style =  default_html_style
    self.latex_style= default_latex_style

  def set_styles(self,html={},latex={}):
    # Output styles
    if html != {}:
      self.html_style.update(html)
    if latex != {}:
      self.latex_style.update(latex)
  
  def get_key(self):
    return self.key

  def get_fields(self):
    return sorted(self.keys())
  

  def __str__(self):
    s= "%15s: %s\n" %("Type", self.get_field('_type'))
    s+="%15s: %s\n" %("citekey", self.get_field('_code'))
    s+="%15s: %s\n" %("internal key", self.get_key())

    for k in self.keys():
      if k.startswith('_'):
				continue;
      s+= "%15s: %s\n" %(k, helper.reg_defstrng.sub(r'\1\2',self.get_field(k,'')))
    try: 
      return unicode(s,self.encoding,'ignore')
    except:
      return s
  
  def preview(self):
    """
    Preview some information on the item. It does not print correctly when missing fields
    """
    s = "%22s: %s, " %(self.key, self.get_authors(Initial=True,smart=True))
    s+= "%s %s, " %(self.get_field('journal_abbrev',''), self.get_field('volume','') )
    s+= "%s (%s).\n" %(self.get_field('pages'), self.get_field('year','') )

    return s.encode(self.encoding,'ignore')

  def get_listnames_last(self, who='author', strict=False):
    """
    Retrieve the authors Last names and return them as a list
    Default bib.get_listnames_last() returns: [von last1, von last2, ...]
    """
    who= who.lower()
    if who not in ['author','editor']:
      raise AttributeError, "who must be author or editor, not %s"%(who)

    if who in self.keys():
      if strict: # Return Last names
        return [x[A_LAST] for x in self[who]]
      else: # Return Full last names ('von Last')
        return ['%s %s'%(x[A_VON],x[A_LAST]) for x in self[who]]
    else:
      return []

  def get_authors_last(self, separator=', '):
    "Returns a string with the last names of the authors separated by a comma"
    return separator.join(self.get_listnames_last(who='author',strict=False))

  def _format_one_author(self,auth, format=0, Initial=False):
    """Returns the author as:
    format= 0  =>   F[irst|.] M[iddle|.] von Last
    format= 1  =>   von Last, F[irst|.] M[iddle|.]
    If Initial is True, only the initials of first names are printed
    """
    
    first=''
    try:
      aa=auth[A_FIRST].split()
    except:
      print auth
      sys.exit()
    for d in aa:
      if Initial or len(d)==1:
        first += d[0]+'.'
      else:
        first+= d.strip()
      first+=' '
    first= first.strip()

    if format==1:
      autor= '%s %s'%(auth[A_VON], auth[A_LAST])
      if first!= '':
        autor +=', %s' %(first)
        if auth[A_JR].strip() != '':
          autor +=', %s' %(auth[A_JR])
    else: # Default format
      autor= ' '.join([first,auth[A_VON], auth[A_LAST]])
    return autor.replace('  ',' ')

  def get_authorsList(self, format=0, Initial=False, who='author'):
    """
    Returns a list of authors where each author is in the form:
    format= 0  =>   F[irst|.] M[iddle|.] von Last
    format= 1  =>   von Last, F[irst|.] M[iddle|.]
    """
    if self.has_key(who):
      return map(self._format_one_author,self[who],len(self[who])*[format],len(self[who])*[Initial])
    else:
      return [[]]

  def get_first_author(self):
    return self.get_authorsList(format=1,Initial=True)[0]
    
  def get_editors(self):
    aa= self.get_authorsList(format=0,Initial=False)
    if len(aa)== 1:
      return aa[0]
    else: 
      return ', '.join(aa[:-1])+ ' and ' + aa[-1]
    
  def get_authors(self, Initial=False, smart=False):
    """
    Returns a string with the authors in the form:
    author_1, author_2, author_3, ... author_n-1 and author_n
    and each author has the form: F[irst|.] M[iddle|.] [von] Last
    """
    MAX_AUTHORS=5
    aa= self.get_authorsList(format=0,Initial=Initial)
    if len(aa)== 1:
      return aa[0]
    elif len(aa) > 1:
      if smart and len(aa) > MAX_AUTHORS:
        return ', '.join(aa[:MAX_AUTHORS])+ ' et al'
      else:
        return ', '.join(aa[:-1])+ ' and ' + aa[-1]

  def get_affiliation(self):
    return ';'.join(self.get('affiliation',[]))


  def get_type(self):
    return self.get_field('_type','article')
  
  def create_entrycode(self, _create_func_=None):
    """  Creates a 'hopefully unique' key    """
    if _create_func_ == None:
      return bibparse.create_entrycode(self)
    else:
      return _create_func_(self)

  def get_field(self,field,d=None):
    if field == 'key':
      return self.key
    elif field == 'author':
      return self.get_authors()
    elif field == 'editor':
      return self.get_editors()
    elif field == 'affiliation':
      return self.get_affiliation()
    elif field == 'pages':
      return self.getpages()
    else:
      return self.get(field,d)
    
  def getpages(self):
    s=''
    if self.has_key('firstpage'):
      s+= self['firstpage'].strip()
      if self.has_key('lastpage'):
        p= self['lastpage'].strip()
        if p != '':
          s+= '-%s' % (p)
    return s

  def to_bibtex(self, indent=2, width=80):
    """
    Format an entry as a bibtex item and returns it as a string, the argument wrap is the length of the lines in output
    """
    
    initial_indent= indent*' '
    # Indent the values of the fields
    wrap= textwrap.TextWrapper(width=width,subsequent_indent= 3*initial_indent,break_long_words=False)
    s= '@%s{%s,\n' %(self['_type'].upper(),self['_code'])

    # Add list of authors
    for f in ['author','editor']:
      if self.has_key(f):
        autores= ' and '.join(self.get_authorsList(format=1,who=f))
        wrap.initial_indent=initial_indent
        s+= wrap.fill(f + ' = {' + autores +'},') + '\n'
    # Some fields that are copied literally
    for kk in helper.textualfields:
      if self.has_key(kk) and not kk.startswith('_'):
				if kk in helper.nowrapfields:  # Not wrap
					s+= '%s%s = {%s}, \n' % (initial_indent,kk , self[kk])
				else:
					s+= wrap.fill('%s = {%s},' % (kk , self[kk]))+'\n'
    # Pages field
    p= self.get_field('pages')
    if p != '':
      s+= '%spages = {%s},\n' %(initial_indent,p)
    # Close the bibitem       
    s+= '}\n'
    s= s.encode('latex','ignore')  # Convert to latex some characters using encoding
  #   s= handle_math(s,orden=1)      # Extra handling of math expressions (very simple)
    return s

  def to_xml(self,p='',indent=2):
    """
    Converts the item to xml format. The prefix is added to each entry
    """
    sp= indent
    spc=indent*' '
    s='%s<%sentry id="%s">\n' %(sp*spc,p,self.get_field('_code',''))
    sp += 1
    s+='%s<%s%s>\n' %(sp*spc,p,self.get('_type',''))

    for k,e in self.iteritems():
      if k == 'author':
        sp+=1
        space=sp*spc+'\n'
        v= space.join(['%s<%sauthor>%s</%sauthor>'%(sp*spc,p,x,p) for x in self.get_authorsList()])
        v= helper.removebraces(v)
        v= helper.replace_tags(v,'other')
        sp-=1
        s+= '%s<%s%s>\n%s\n%s</%s%s>\n' %(sp*spc,p,'authors',v,sp*spc,p,'authors')
      else:
        if helper.is_string_like(e):
          v= helper.replace_tags(e,'xml')
          v= helper.handle_math(v)
        if k=='title':
          v=helper.capitalizestring(v)
          v= helper.removebraces(v)
          v= helper.replace_tags(v,'other')
        s+= '%s<%s%s>%s</%s%s>\n' %(sp*spc,p,k,v,p,k)

    sp-=1
    s+= '%s</%s%s>\n' %(sp*spc,p,self.get('_type',''))
    s+= '%s</%sentry>\n' %(sp*spc,p)
    return s

  def to_html(self,style={}):
    """
    Converts the item to html format with the given style The style is a pair (before,
    after) surrounding the corresponding field (except for authors)
    """
    # textfields= ['journal','booktitle','series','school','volume','number','publisher','firstpage','lastpage','year','_code','url','doi','abstract']
    textualfields = ['journal', 'volume','number', 'month', 'booktitle', 'chapter', 'address', 'edition', 'howpublished','school', 'institution', 'organization', 'publisher', 'series','firstpage','lastpage',
                     'note', 'crossref', 'issn','isbn', 'year', 'keywords' ,'annote', '_code', 'doi',  'url',  'abstract']

    st= dict(self.html_style)
    st.update(style)
    tipo= self.get('_type','article')
    title= helper.handle_math(self.get_field('title',''))
    title= bibparse.helper.capitalizestring(title)
    if 'mastersthesis' == tipo:  title= 'Master Thesis. ' + title
    elif 'phdthesis' == tipo:    title= 'Phd Thesis. ' + title

    s= ''
    if title != '' and st.get('title',['','']) !=  None:
      s+= title.strip().join(st.get('title',['','']))

    if self.has_key('author') and st.get('author')!= None:
      form_aut=''
      list_aut= self.get_authorsList()
      if len(list_aut) > 10:
        list_aut=list_aut[:10]
        list_aut.append('<i>et al</i>')
      for a in list_aut:
        form_aut += '<span class="author">'+ a +'</span>, '
      form_aut= form_aut[:-2]
      s+= form_aut.join(st.get('author',['','']))
    
    for field in textualfields:
      if self.get_field(field,'') != '' and st.get(field,(' ',' ')) != None:
        value= helper.handle_math(self.get_field(field,'').strip())
        value=bibparse.helper.removebraces(value)
        s+= value.join(st.get(field,[' ',' ']))

    if st.get('_type',['','']) !=  None:
      s= s.strip().join(st.get('_type',['','']))

    s= s.decode('latex','replace')  # Convert from latex some characters using encoding
    return unicode(s)

  def to_latex(self,style={}):
    """
    As its name indicates, it converts bibtex data to a latex bibitem
    """

    textfields= ['journal','booktitle','school','volume','number','firstpage','lastpage','year','url','doi','abstract']

    st=dict(self.latex_style)
    st.update(style)
    s=''
    
    if st.get('_code') !=  None:
      s+= self.get('_code').join(st['_code'])

    if self.get('title','') != '' and st.get('title') !=  None:
      s+= self.get('title').join(st['title'])

    if self.get('author','') != '' and st.get('author') != None:
      s+= ', '.join(self.get_authorsList()).join(st['author'])

    for field in textfields:
      if self.get_field(field,'') != '' and st.get(field) != None:
        s+= self.get_field(field,'').strip().join(st[field])

    return s.encode('latex')

  def display(self, fpp=sys.stdout):
    if type(fpp)==type(''):
      fp= codecs.open(fpp,'w', encoding=self.encoding)
    else:
      fp=fpp
    s= str(self)
    fp.write(s)


	#############################################################3
	# import methods
	#############################################################3
  def from_bibtex(self,source):
    """
    Reads an item in bibtex form from a string 
    """
    try:
      source+' '
    except:
      raise TypeError, 'source must be a string'
    st,entry= bibparse.parseentry(source)
    if entry != None:
      self.set(entry)

  def from_ads(self,source):
    """
    Reads an item in bibtex form from a string 
    """
    try:
      source+' '
    except:
      raise TypeError, 'source must be a string'
    entry= adsparse.parseentry(source)
    if entry != None:
      self.set(entry)


	#############################################################3
	# matching methods
	#############################################################3

  def search(self, findstr, fields=[], caseSens=False):
    if findstr=='*': return True
    if fields==[]:   # Busca en todos los campos
      fields=self.get_fields()

    if caseSens:    s=findstr
    else:           s=findstr.lower()

    for f in fields:
      if f not in self.get_fields():
        continue
      v= self.get_field(f)
      if not caseSens:
        try:      v= v.lower()
        except:   pass
      if s in v:  return True

    # Search for string in key
    if 'key' in fields:
      if caseSens: return s in self.key
      else: return s in self.key.lower()
    else:
      return False
  
  def matchAuthorList(self,it):
    """ Test whether two publications have the same authors """
    # First we match the last (von Last) names
    a1s=self.get_listnames_last('author',False)
    a2s=it.get_listnames_last('author',False)
    for a1,a2 in zip(a1s,a2s):
      if a1.strip().lower() != a2.strip().lower():
        return False

    # In case it did worked, we check the initials
    a1s= [x[A_LAST][0] for x in self['author']]
    a2s= [x[A_LAST][0] for x in it['author']]
    for a1,a2 in zip(a1s,a2s):
      if a1 != a2:
        return False

    # Some other conditions
    # ....

    # Else they are equal
    return True

  def compare(self, it):
    """ Compare if two items are in fact the same """

    # If the doi is the same, we are done
    if self.get('doi','0') == self.get('doi','1'):
      return True

    # Check Journal and page, that should be enough (almost always)
    if self('journal_abbrev','0')== it.get('journal_abbrev','1'):
      # Same journal AND either first page or volume coincide we assume is the same
      if self.get('firstpage','-1') == it.get('firstpage','-2'):
        return True
      if self.get('volume','-1') == it.get('volume','-2'):
        return True

    if self.matchAuthorList(it):
      # If authors AND either title or first page coincide we assume is the same
      if self.get('title','0') == it.get('title','1'): 
        return True
      elif self.get('firstpage','-1') == it.get('firstpage','-2'):
        return True

    # Otherwise they are different
    return False


def test():
  """
  Test the class and its methods
  """
  
  css="""
.title a,
.title {  font-weight: bold;	color: rgb(20,20,20) ;}
ol.bibliography li{	margin-bottom:0.5em;}
.journal {  font-style: italic;}
.journal:after {content:", ";}
.publisher:before {content:" (";}
.publisher:after {content:") ";}
.series:after {content:", ";}
.year:before {content:" (";}
.year:after {content:").";}
.authors {display:block;}
.volume { font-weight: bold;}
.button {display:inline; border: 3px ridge;line-height:2.2em;margin: 0pt 10pt 0pt 0pt;padding:1pt;}
.masterthesis{content:"Master Thesis"}
.phdthesis{content:"Phd Thesis"}
div.abstracts {display: inline; font-weight: bold; text-decoration : none;  border: 3px ridge;}
div.abstract {display: none;padding: 0em 1% 0em 1%; border: 3px double rgb(130,100,110); text-align: justify;} 
"""
  hhead='''
  <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"> <html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
  <head>  <title>Paper</title>  <meta http-equiv="Content-Type"  content="text/html; charset=UTF-8" /> <meta name="author" content="J. Fiol" /> <meta name="description" content="A list of publications entries, designed for Colisiones Atomicas, CAB." /> <style type="text/css">
'''+css+'''	</style>  <script language="JavaScript" type="text/javascript">
      //<![CDATA[
      function toggle(thisid) { var thislayer=document.getElementById(thisid); if (thislayer.style.display == 'block') { thislayer.style.display='none';} else { thislayer.style.display='block';}}//]]> </script></head> <body id="page-body">
  '''
  hfoot=""" </body></html> """

  b=BibItem({'_type':'article','author':[['della', 'Picca','Renata',''],['',r'Mart{\'{\i}}nez','R. O.',''],['','Fiol','J.',''],['','Macri','P.','']],'year':'2008','firstpage':'402', 'lastpage':'406', 'abstract':u'We employ different theoretical models, both classical and quantum-mechanical, to explore the recoil-ion momentum distribution in positron atom collisions. We pay special attention to the vicinity of the kinematical threshold between ionization and positronium formation. We demonstrate that it is intertwined by dynamical constraints to the formation of highly excited and low-lying continuum electron positron states. Finally we discuss how the study of recoil- ion momentum distribution, which is characteristic of a reaction microscopy technique, might represent an alternative approach to the standard spectroscopy of electrons and positrons.',  'title' : u'Threshold effects in the ionization of atoms by positron impact',
   '_code':'Fiol07NIMB',
  'journal' : u'Nuclear Instruments and Methods in Physics Research B',
  'year' : '2008',
  'volume' : '266',
  'url' : u'http://adsabs.harvard.edu/abs/2008NIMPB.266..402B',
  'doi' : '10.1016/j.nimb.2007.12.040',
})

  btest=r"""
  @ARTICLE{Fiol07NIMB,
  author = {Renata della Picca and R. O. Mart{\'{\i}}nez and J. Fiol and P.
  Macri},
  title = {Threshold effects in the ionization of atoms by positron impact},
  journal = {Nuclear Instruments and Methods in Physics Research B},
  year = {2008},
  volume = {266},
  doi = {10.1016/j.nimb.2007.12.040},
  url = {http://adsabs.harvard.edu/abs/2008NIMPB.266..402B},
  abstract = {We employ different theoretical models, both classical and
      quantum-mechanical, to explore the recoil-ion momentum distribution in
      positron atom collisions. We pay special attention to the vicinity of the
      kinematical threshold between ionization and positronium formation. We
      demonstrate that it is intertwined by dynamical constraints to the
      formation of highly excited and low-lying continuum electron positron
      states. Finally we discuss how the study of recoil- ion momentum
      distribution, which is characteristic of a reaction microscopy technique,
      might represent an alternative approach to the standard spectroscopy of
      electrons and positrons.},
  pages = {402-406},
}
"""
  atest=u"""
%R 2008JPhB...41n5204M
%T Transfer ionization and total electron emission for 100 keV amu<SUP>-1</SUP> 
He<SUP>2+</SUP> colliding on He and H<SUB>2</SUB>
%A Mart\xednez, S.; Bernardi, G.; Focke, P.; Su\xe1rez, S.; Fregenal, D. 
%F Centro At\xf3mico Bariloche and Instituto BalseiroComisi\xf3n Nacional de Energ\xeda 
At\xf3mica and Universidad Nacional de Cuyo, Argentina., 8400 S C de Bariloche, 
R\xedo Negro, Argentina <EMAIL>bernardi@cab.cnea.gov.ar</EMAIL>
%J Journal of Physics B: Atomic, Molecular, and Optical Physics, Volume 41, 
Issue 14, pp. 145204 (2008).
%V 41
%D 7/2008 
%P 5204
%G IOP
%I ABSTRACT: Abstract;
   EJOURNAL: Electronic On-line Article (HTML);
   REFERENCES: References in the Article;
   AR: Also-Read Articles;
%U http://adsabs.harvard.edu/abs/2008JPhB...41n5204M
%B We have measured electron emission for transfer ionization (TI) and 
total electron emission (TEE, all emission processes) for 100 keV 
amu<SUP>-1</SUP> He<SUP>2+</SUP> on He and H<SUB>2</SUB> targets. Double 
differential cross sections have been obtained for emission angles 
\u03b8 = 0\xb0, 20\xb0 and 45\xb0, and electron energies ranging 
from 2 to 300 eV. Pure ionization, mainly due to single ionization, 
dominates the low-energy electron emission. The main observed structure 
in the electron spectra, a cusp centred at \u03b8 = 0\xb0 and at a 
speed equal to that of the incident projectile, presents an asymmetric 
shape. This is in contrast to the symmetric shape observed by us at 25 
keV amu<SUP>-1</SUP> for the same collision systems, suggesting a change 
in the cusp formation mechanism for TI within this energy range.
%Y DOI: 10.1088/0953-4075/41/14/145204
"""
  f=codecs.open('bibit.html','w',encoding='utf8'); f.write(hhead+b.to_html()+ hfoot); f.close()
  f=codecs.open('bibit.bib','w'); f.write(b.to_bibtex(width=80)); f.close()
  f=codecs.open('bibit.tex','w'); f.write(textwrap.fill(b.to_latex(style={'_code':(r'[',r'] ')}),width=120) ); f.close()
  f=codecs.open('bibit.xml','w'); f.write(b.to_xml()); f.close()

  # Other item copied from b
  print 80*'*'
  print 'Define one entry...'
  print 30*'*'
  b.display()   # Display to std output

  c=BibItem(b,normalize=True)
  print '\n',80*'*','\nc=BibItem(b,normalize=True)',
  print '\n',30*'*'
  print '\nc='
  print c
  print 80*'*'
  print 'Testing some Methods...'
  print 30*'*'
  print '\nc.get_key()=',c.get_key()
  print '\nc.Fields()=',c.get_fields()
  print '\nc is b? ->', c is b,',      c == b? ->', c == b

  print "c.search('colisions'): ",c.search('colisions')
  print "c.search('collisions'): ",c.search('collisions')
  print "c.search('Fiol'): ",c.search('Fiol')
  print "c.search('Nuclear'): ",c.search('Nuclear')
  print "c.search('Nuclear',['author','year']): ",c.search('Nuclear',['author','year'])
  print "c.search('Nuclear',['author','year','journal']): ",c.search('Nuclear',['author','year','journal'])

  d= BibItem()
  d.from_bibtex(btest)
  print 80*'*'
  print 'Entry from a source in BIBTEX format'
  print 30*'*'
  d.display()
  print 80*'*'
  e= BibItem()
  e.from_ads(atest)
  print 'Entry from a source in ADS PORTABLE format'
  print 30*'*'  
  e.display()

  # Display some message
  mensaje=u'Se han escrito ejemplos de una publicacion en formatos latex, bibtex, xml y html en los archivos bibit.tex, bibit.bib, bibit.xml y bibit.html'

  print '%s\n%s\n%s' %(80*'*', textwrap.fill(mensaje,width=80),80*'*')


def main():
  test()

if __name__ == "__main__": main()




# ##########################################################################################
#        ################################ Variables  ################################
# # list of additional fields, ignored by the standard BibTeX styles
# ign = ('crossref', 'code', 'url', 'annote', 'abstract');

# # lists of required and optional fields for each reference type

# required_fields = {
#   'article' :		['Author', 'Title', 'Journal', 'Year'],
#   'book' :		['Author', 'Title', 'Publisher', 'Year']
#   'booklet' :		['Title'],
#   'inbook' :		['Author', 'Title', 'Chapter', 'Pages', 
#   				'Publisher', 'Year'],
#   'incollection' :	['Author', 'Title', 'Booktitle', 'Publisher', 'Year'],
#   'inproceedings' :	['Author', 'Title', 'Booktitle', 'Year'],
#   'manual' :		['Title'],
#   'misc' : 		[],
#   'mastersthesis' :	['Author', 'Title', 'School', 'Year'],
#   'phdthesis' :		['Author', 'Title', 'School', 'Year'],
#   'proceedings' :	['Title', 'Year'],
#   'techreport' :	['Author', 'Title', 'Institution', 'Year'],
#   'unpublished' :	['Author', 'Title', 'Note']
# };

# opt_fields = {
#   'article' :		['Volume', 'Number', 'Pages', 'Month', 'Note'],
#   'book' :		['Editor', 'Volume', 'Number', 'Series', 'Address',
#   				'Edition', 'Month', 'Note'],
#   'booklet' :		['Author', 'Howpublished', 'Address', 'Month', 'Year',
#   				'Note'],
#   'inbook' :		['Editor', 'Volume', 'Series', 'Address', 'Edition',
#   				'Month', 'Note'],
#   'incollection' :	['Editor', 'Volume', 'Number', 'Series', 'Type', 
#   				'Chapter'  'Pages', 'Address', 'Edition',
# 				'Month', 'Note'],
#   'inproceedings' :	['Editor', 'Pages', 'Organization', 'Publisher', 
#   				'Address', 'Month', 'Note'],
#   'manual' :		['Author', 'Organization', 'Address', 'Edition',
#   				'Month', 'Year', 'Note'],
#   'misc' :		['Title', 'Author', 'Howpublished', 'Month', 'Year',
#   				'Note'],
#   'mastersthesis' :	['Address', 'Month', 'Note'],
#   'phdthesis' :		['Address', 'Month', 'Note'],
#   'proceedings' :	['Editor', 'Publisher', 'Organization', 'Address', 
#   				'Month', 'Note'],
#   'techreport' :	['Type', 'Number', 'Address', 'Month', 'Note'],
#   'unpublished' :	['Month', 'Year']
# };

# ################################################################################


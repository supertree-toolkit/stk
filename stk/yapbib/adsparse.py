#! /usr/bin/env python

import sys,os
import re
import codecs
import helper

ads_fields={'R': 'Bibliographic Code',
            'A': 'Author List',
            'a': 'Book Authors',
            'F': 'Author Affiliation',
            'J': 'Journal Name',
            'V': 'Journal Volume',
            'D': 'Publication Date',
            'P': 'First Page of Article',
            'L': 'Last Page of Article',
            'T': 'Title (required)',
            't': 'Original Language Title',
            'C': 'Abstract Copyright',
            'O': 'Object Name',
            'Q': 'Subject Category',
            'G': 'Origin',
            'S': 'Score from the ADS query (output only)',
            'E': 'Electronic Data Table',
            'I': 'Links to other information (output only)',
            'U': 'for Electronic Document',
            'K': 'Keywords',
            'M': 'Language (if not English)',
            'N': 'Not Documented!!!',
            'X': 'Comment',
            'W': 'Database (if submitting for more than one)',
            'Y': 'DOI',
            'B': 'Abstract Text',
            'Z': 'References'
            }

ads_literal_fields={
  # Fields that do not need post-procesing. They are just assigned to the dict.
  'R': '_code',
  'V': 'volume',
  'P': 'firstpage',
  'L': 'lastpage',
  'T': 'title',
  'U': 'url',
  'K': 'keywords',
  'B': 'abstract'
  }

reg_begin= re.compile('^[\s]*%R ',re.M)
reg_adstags=re.compile('^[\s]*%([RAaFJVDPLTtCOQGSEIUKMNXWYBZ]) ',re.M)

###########################################################################################
     ##############################  Parsing routines  ##############################
def parsedata(page):
  """
  Parse the results from ADS and store the list of references in a dictionary.
  """
  biblist={}

  page= helper.handle_math(page,1)  
  s= reg_begin.split(page)[1:] # The first item is empty, we take it out

  for paper in s:
    item= parseentry(paper)
    if item.has_key('author'):
      biblist[item['_code']]= dict(item)
  if biblist == {}: return None
  return biblist


def parseentry(paper):
  """
  Parses an ADS entry
  """
  def get_journal(t):
    reg_vol=re.compile('Vol',re.I)
    s=reg_vol.search(t)
    if s != None: t=t[0:s.start()]
    return t.strip().strip(',')

  def get_affil(t):
    reg_af= re.compile('[ ]?[A-D][A-Z](?=\()') # Regexp: Hasta un espacio, seguido de dos mayusculas, seguido de un parentesis (que no se consume)
    F= reg_af.split(t)
    if len(F) > 1: F=F[1:]
    return F

  def adsauthor(data):
    """ Returns a list of authors where each author is a list of the form:
    [von, Last, First, Jr]
    """
    return map(helper.process_name,data.split(';'))

  # Start the parsing of the entry
  Id=paper[0:paper.index('%')].strip('\n').strip()
  item={'_code':Id}

  campos= reg_adstags.split(paper)[1:]
  for i1 in range(0,len(campos),2):
    c,v=campos[i1],campos[i1+1]
    if c in ads_literal_fields.keys():
      item[ads_literal_fields[c]]=v.strip('\n')
    elif c == 'J':
      journal= get_journal(v).strip('\n')
      if 'thesis' in  journal.lower():
        item['_type']= 'phdthesis'
        item['school']= journal
      else:
        item['_type']='article'
        item['journal']= journal
    elif c == 'A':
      authors=adsauthor(v)
      item['author']= authors
    elif c == 'a':
      authors=adsauthor(v)
      item['author']= authors
      item['_type']='book'
    elif c == 'D':
      date=v.split('/')
      if len(date)==2:
        item['month']= helper.strings_month[int(date[0])-1][1]
        item['year']=date[1].strip()
      else:
        item['year']=v[-1].strip()
    elif c == 'Y':
      v= v.replace('doi: ','')
      v= v.replace('DOI: ','')
      item['doi']= re.sub('\s','',v.split(';')[0])
    elif c == 'F':
      item['affiliation']= get_affil(v)

  if item.has_key('affiliation') and len(item['affiliation']) == 1: 
    # Correct affiliations to "one for each author" even if it is the same for all
    item['affiliation']=len(item['author'])*item['affiliation']

  return item

def parsefile(fname,encoding='utf-8'):
  helper.openfile(fname)
  s= fname.read()
  db= parsedata(s)
#   db= parsedata(unicode(s,encoding=encoding))
  helper.closefile(fname)
  return db




##########################################################################################
##########################################################################################

def main():
  inputstring="""

%R 2008AmJPh..76.1146M
%T A velocity-dependent potential of a rigid body in a rotating frame
%A Moreno, G. A.; Barrachina, R. O.
%F AA(Departamento de F\xedsica J. J. Giambiagi, Facultad de Ciencias Exactas y 
Naturales, UBA, Ciudad Universitaria, Pabell\xf3n I, 1428 Buenos Aires, 
Argentina), AB(Centro At\xf3mico Bariloche and Instituto Balseiro, Comisi\xf3n 
Nacional de Energ\xeda At\xf3mica and Universidad Nacional de Cuyo, 8400 S. C. de 
Bariloche, R\xedo Negro, Argentina)
%J American Journal of Physics, Volume 76, Issue 12, pp. 1146-1149 (2008).
%V 76
%D 12/2008 
%P 1146
%L 1149
%K classical mechanics,  physics education,  rotating bodies
%G AIP
%C (c) 2008: American Institute of Physics
%I ABSTRACT: Abstract;
   EJOURNAL: Electronic On-line Article (HTML);
   REFERENCES: References in the Article;
   AR: Also-Read Articles;
%U http://adsabs.harvard.edu/abs/2008AmJPh..76.1146M
%B We derive a velocity-dependent potential for describing the dynamics of 
a rigid body in a rotating frame. We show that, as for one-particle 
systems, the different components of this potential can be associated 
with electromagnetic analogs. We provide some examples to demonstrate 
the feasibility of using the potential as an alternative description of 
rigid body problems.
%Y DOI: 10.1119/1.2982632

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
  
  b= parsedata(inputstring)
  print '%d ADS items parsed\n'%(len(b.keys()))
  for v in b.itervalues():
    s=str(v)
    print s.encode('utf8'),'\n'
################################################################################
  c= parsefile('ejemplos/ejemplo1.ads')
  print '%d ADS items parsed\n'%(len(c.keys()))
  for v in c.itervalues():
    s=str(v)
    print s.encode('utf8'),'\n'
  
if __name__ == "__main__":
  main()


### Local Variables: 
### tab-width: 2
### END:

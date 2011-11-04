#!/usr/bin/env python
"""
Set of routines to parse bibtex data and return each entry as a dictionary
It is mainly intended as a helper file to the Class BibItem (see bibitem.py)
but can be used as a standalone script

USAGE:
  strings,db = parsefile(bibtexfile)

"""


import sys
import re,string
import codecs
import latex
latex.register()

import helper

def process_pages(pages):
  """ Returns a 2-tuple (firstpage,lastpage) from a string"""
  pp=pages.split('-')
  firstpage=pp[0]
  if len(pp)==2:
    lastpage=pp[1]
  else:
    lastpage=''
  return firstpage,lastpage

def bibtexauthor(data):
  """ Returns a list of authors where each author is a list of the form:
  [von, Last, First, Jr]
  """
  return map(helper.process_name,helper.removebraces(data).split(' and '))

def get_fields(strng, strict=False):
  """
  Returns a list with pairs (field, value) from strng
  If strict is True, it will only allow known fields, defined in helper.bibtexfields
  """ 

  comma_rex=re.compile(r'\s*[,]')
  ss=strng.strip()
  
  if not ss.endswith(','): # Add the last commma if missing
    ss+=','
    
  fields=[]

  while True:
    name,sep,ss= ss.partition('=')
    name=name.strip().lower()  # This should be enough if there is no error in the entry
    if len(name.split()) > 1:   # Help recover from errors. name should be only one word anyway
      name= name.split()[-1]
    ss=ss.strip()
    if sep == '': break  # We reached the end of the string

    if ss[0] == '{':    # The value is surrounded by '{}'
      s,e= helper.match_pair(ss)
      data= ss[s+1:e-1].strip()
    elif ss[0] == '"':  # The value is surrounded by '"'
      s= ss.find(r'"')
      e= ss.find(r'"',s+1)
      data= ss[s+1:e].strip()
    else: # It should be a number or something involving a string
      e= ss.find(',')
      data= ss[0:e].strip()
      if not data.isdigit(): # Then should be some string
        dd=data.split('#')  # Test for joined strings
        if len(dd) > 1:
          for n in range(len(dd)):
            dd[n]= dd[n].strip()
            dd[n]= dd[n].replace('{','"').replace('}','"')
            if dd[n][0] != '"':
              dd[n]='definitionofstring(%s) '%(dd[n])
          data='#'.join(dd)
        else:
          data='definitionofstring(%s) '%(data.strip())
    s=ss[e].find(',')
    ss=ss[s+e+1:]
# JF: Temporario, descomentar si hay problemas
#     if name=='title':
#       data=helper.capitalizestring(data)
#     else:
#       data=helper.removebraces(data)
    if not strict or name in helper.bibtexfields:
      fields.append((name,data))
  return fields


# Creates a (hopefully) unique key code
def create_entrycode(b={}):
  """
  Creates a 'hopefully unique' entry key from a bibtex item
  """
  len_aut=7  # Length of the author surname used
  try:
    aut= helper.capitalizestring('%s%s'%(b['author'][0][0],b['author'][0][1]))
  except:
    print b['author']
    print b['_code']
  aut=helper.oversimplify(aut)
  if len(aut) > len_aut:
    bibid=aut[:len_aut]
  else:
    bibid=aut.strip()

  bibid +=  b.get('year','')
  bibid += b.get('journal_abbrev','')

  if b['_type'] == 'mastersthesis':   bibid+= 'MT'
  elif b['_type'] == 'phdthesis':    bibid+= 'PHD'
  elif b['_type'] in ['book','incollection','proceedings','conference','misc','techreport']:
    if b.has_key('booktitle'):
      bibid+= helper.create_initials(b['booktitle'])
    elif b.has_key('series'):
      bibid+= helper.create_initials(b['series'])

    if b.has_key('title'):
      bibid+= '_'+helper.create_initials(b.get('title','').upper())[:3]

  if 'thesis' not in b['_type']:
    if b.has_key('firstpage'):   bibid+= 'p'+b['firstpage'].strip()
    elif b.has_key('volume'):    bibid+= 'v'+b['volume'].strip()
  return helper.oversimplify(bibid)


def replace_abbrevs(strs,bitem):
  """ Resolve all abbreviations found in the value fields of one entry"""
  b=bitem
  for f,v in b.iteritems():
    if helper.is_string_like(v):  b[f]= helper.replace_abbrevs(strs,v)
  return b

def parsefile(fname=None):
  fi= helper.openfile(fname)
  s= fi.read()
  db= parsedata(s)
  return db

def parsedata(data):
  """
  Parses a string with a bibtex database
  """
  # Regular expressions to use
  pub_rex = re.compile('\s?@(\w*)\s*[{\(]') # A '@' followed by any word and an opening
                                             # brace or parenthesis
  ########################################################################################
              #################### Reformat the string ####################
  ss= re.sub('\s+',' ',data).strip()

  # Find entries
  strings={}
  preamble=[]
  comment=[]
  tmpentries=[]
  entries={}

  while True:
    entry={}
    m= pub_rex.search(ss)

    if m == None:
      break

    if m.group(0)[-1]=='(':
      d= helper.match_pair(ss,pair=('[(]','[)]'),start=m.end()-1)
    else:
      d= helper.match_pair(ss,start=m.end()-1)

    if d != None:
      current= ss[m.start():d[1]-1]  # Currently analyzed entry
      st,entry= parseentry(current)
      if st != None:
        strings.update(st)
      if entry != None and entry != {}:
        entries[entry['_code']]= entry
      ss=ss[d[1]+1:].strip()

  return strings,entries

def parseentry(source):
  """
  Reads an item in bibtex form from a string 
  """
  try:
    source+' '
  except:
    raise TypeError
  # Transform Latex symbols and strip newlines and multiple spaces 
  
  source= source.decode('latex+utf8','ignore')
  source.replace('\n',' ')
  source= re.sub('\s+',' ',source)

  entry={}
  st= None
  s=source.partition('{')

  if s[1]=='':
    return None,None

  arttype= s[0].strip()[1:].lower()

  if arttype == 'string':
    # Split string name and definition, removing outer "comillas" and put them in a list
    name, defin = s[2].strip().split("=")
    defin= defin.replace('"','').strip()
    if defin.startswith('{'):
      defin=defin[1:-1]
    return {name.strip():defin.strip()},None

  elif arttype in helper.alltypes:
    # Then it is a publication that we want to keep
    p = re.match('([^,]+),', s[2] ) # Look for the key followed by a comma
    entry['_type']= arttype
    entry['_code']= p.group()[:-1]

    ff= get_fields(s[2][p.end():])
    for n,d in ff:
      if n == 'author' or n == 'editor':
        entry[n]= bibtexauthor(d)
      elif n== 'pages':
        entry['firstpage'],entry['lastpage']= process_pages(d)
      elif n == 'year':
        entry[n]= d.strip('.')
      else:
        entry[n]=d
    return None,entry

  elif arttype == 'comment' or arttype == 'preamble':
    # Do nothing (for now)
    return None,None
  else:
    return None,None


def test():
  if sys.argv[1:]:
    filepath= sys.argv[1]
  else:
    print "No input file"
    print "USAGE:  "+sys.argv[0]+ " FILE.bib\n\n  It will output the XML file: FILE.xml"
    sys.exit(2)

  strings,db = parsefile(filepath)
  print db
    
def main():
  test()

if __name__ == "__main__": main()


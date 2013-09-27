import re
import string
import sys

#        ################################ Variables  ################################
# List of all possible fields.
allfields = ('_type', 'address', 'author', 'booktitle', 'chapter', 'edition','_code',
'editor', 'howpublished', 'institution', 'journal', 'month', 'number', 'organization',
'pages', 'publisher', 'school','series', 'title', 'volume','year', 'note', 'code',
'url', 'crossref', 'annote', 'abstract', 'doi','journal_abbrev','date-added','date-modified', 'file')

bibtexfields = ('author', 'title', 'journal', 'year', 'volume','number', 'pages', 'month',
'booktitle', 'chapter','address', 'edition', 'abstract', 'doi',  'url', 'editor',
'howpublished','school', 'institution', 'organization', 'publisher', 'series',
'note', 'crossref', 'annote','file')

# Fields that MUST be present
minimalfields = ('_type','author')

# Fields that are output literally in bibtex form
textualfields = ['title', 'journal', 'year', 'volume','number', 'month', 'booktitle', 'chapter',
'address', 'edition', 'howpublished','school', 'institution', 'organization', 'publisher', 'series',
'note', 'crossref', 'issn','isbn', 'keywords' ,'annote', '_code', 'doi',  'url',  'abstract','file']

# Fields that should not be wrapped (must go complete in the same line)
nowrapfields= ['url','doi','isbn','issn','crossref']

# list of all reference types. CURRENTLY NOT USED
alltypes = ('article', 'book', 'booklet','conference', 'inbook', 'incollection', 'inproceedings', 'manual',
'mastersthesis', 'misc', 'phdthesis', 'proceedings', 'techreport', 'unpublished')



strings_month = [
  ('jan', 'January'),
  ('feb', 'February'),
  ('mar', 'March'),
  ('apr', 'April'),
  ('may', 'May'),
  ('jun', 'June'),
  ('jul', 'July'),
  ('aug', 'August'),
  ('sep', 'September'),
  ('oct',  'October'),
  ('nov', 'November'),
  ('dec', 'December'),
  ]

standard_abbrev= strings_month[:]

xml_tags= [  # xml/html entities
  ('&', '&amp;'),
  ('<', '&lt;'),
  ('>', '&gt;'),
]
# Accent tags are not used. They are handled via latex codec
accent_tags= [  # Accents and other latin symbols
  (r'\"a', "&#228;"),
  (r"\`a", "&#224;"),
  (r"\'a", "&#225;"),
  (r"\~a", "&#227;"),
  (r"\^a", "&#226;"),
  (r'\"e', "&#235;"),
  (r"\`e", "&#232;"),
  (r"\'e", "&#233;"),
  (r"\^e", "&#234;"),
  (r'\"\i', "&#239;"),
  (r"\`\i", "&#236;"),
  (r"\'\i", "&#237;"),
  (r"\^\i", "&#238;"),
  (r'\"i', "&#239;"),
  (r"\`i", "&#236;"),
  (r"\'i", "&#237;"),
  (r"\^i", "&#238;"),
  (r'\"o', "&#246;"),
  (r"\`o", "&#242;"),
  (r"\'o", "&#243;"),
  (r"\~o", "&#245;"),
  (r"\^o", "&#244;"),
  (r'\"u', "&#252;"),
  (r"\`", "&#249;"),
  (r"\'", "&#250;"),
  (r"\^", "&#251;"),
  (r'\"A', "&#196;"),
  (r"\`A", "&#192;"),
  (r"\'A", "&#193;"),
  (r"\~A", "&#195;"),
  (r"\^A", "&#194;"),
  (r'\"E', "&#203;"),
  (r"\`E", "&#200;"),
  (r"\'E", "&#201;"),
  (r"\^E", "&#202;"),
  (r'\"I', "&#207;"),
  (r"\`I", "&#204;"),
  (r"\'I", "&#205;"),
  (r"\^I", "&#206;"),
  (r'\"O', "&#214;"),
  (r"\`O", "&#210;"),
  (r"\'O", "&#211;"),
  (r"\~O", "&#213;"),
  (r"\^O", "&#212;"),
  (r'\"U', "&#220;"),
  (r"\`", "&#217;"),
  (r"\'", "&#218;"),
  (r"\^", "&#219;"),
  (r"\~n", "&#241;"),
  (r"\~N", "&#209;"),
  (r"\c c", "&#231;")
  ,(r"\c C", "&#199;")
  ,(r"\circ", "o")
  ]

other_tags=[
  ('([^\\\\])~','\g<1> ') # Remove tilde (used in LaTeX for spaces)
  ,(r'\\textbf{([^{]+)}',r'<b>\g<1></b>')
  ,(r'\\\\emph{([^{]+)}',r'<em>\g<1></em>')
  ,(r'\\textit{([^{]+)}',r'<i>\1</i>')
  ,(r'\[^ {]+{(.+)}','\g<1> ') # Remove other unknown commands
]

# Some journal data.
# DOI is useful when a journal uses a common (unique) root
# ISSN is unique but ads does not provides it. We list (when available) two issn: [print, online]
# Regular expression will give us a general (but not exact) matching strategy
journal_data=[
  {'regexp':r'Nuc\w*[\.]?\s*Inst\w*[\.]?\s*(and)?\s*Meth\w*[\.]?\s*(in)?\s*(Phys(ics)?[\.]?)?\s*(R(esearch)?[\.]?)?\s*(S(ection)?[\.]?)?\s*B|nimb', 'nombre':r'Nuclear Instruments and Methods in Physics Research B', 'abbrev':'NIMB', 'doi':'10.1016/j.nimb','issn':['0168-583X']},
  {'regexp':'Int(ernational)?[\.]?\s*J(our(nal)?)?[\.]?\s*(of)?\s*Q(uantum)?[\.]?\s*Ch(em(istry)?)?[\.]?', 'nombre':'International Journal of Quantum Chemistry', 'abbrev':'IJQC','doi':'10.1002/qua','issn':['1097-461X','0020-7608']},
  {'regexp':r'J(ournal)?[\.]?\s*(of)?\s*Phys(ics)?[\.]?\s*A(\s*:\s*Math(ematical)?\s*(and)?\s*(General)?)?|jpa','nombre': r'Journal of Physics A: Mathematical and General', 'abbrev':'JPA','doi':'10.1088/0305-4470','issn':['1751-8113','1751-8121']},
  {'regexp':r'J(ournal)?[\.]?\s*(of)?\s*Phys(ics)?[\.]?\s*B(\s*:\s*At(omic)?[\.]?\s*Mol(ecular)?[\.]?\s*(and)?\s*(Opt(ical)?)?\s*Phys(ics)?)?|jpb','nombre':r'Journal of Physics B: Atomic Molecular and Optical Physics', 'abbrev':'JPB','doi':'10.1088/0953-4075','issn':['0953-4075','1361-6455']},
  {'regexp':r'Ph\w*[\.]? Rev\w* A|pra','nombre': r'Physical Review A','abbrev': 'PRA', 'doi':'10.1103/PhysRevA','issn':['1050-2947','1094-1622']},
  {'regexp':r'Ph\w*[\.]? Rew* B|prb','nombre': r'Physical Review B','abbrev': 'PRB', 'doi':'10.1103/PhysRevB','issn':['1098-0121','1550-235x']},
  {'regexp':r'Ph\w*[\.]? Rew* C|prc','nombre': r'Physical Review C','abbrev': 'PRC', 'doi':'10.1103/PhysRevC','issn':['0556-2813','1089-490X']},
  {'regexp':r'Ph\w*[\.]? Rev\w*[\.]? L\w*[\.]?|prl','nombre': r'Physical Review Letters','abbrev': 'PRL', 'doi':'10.1103/PhysRevLett','issn':['0031-9007','1079-7114']},
  {'regexp':r'Rev\w*[\.]?\s*(of)?\s*Mod(ern)?\s*Phys(ics)?|rmp','nombre': r'Review of Modern Physics','abbrev': 'RMP', 'doi':'Not Available','issn':['0034-6861','1539-0756']},
  # 
  {'regexp':r'J\w*[\.]? Phy\w*[\.]? Conf\w*[\.]?|jcps','nombre': r"Journal of Physics Conference Series",'abbrev': 'JPCS', 'doi':'10.1088/1742-6596','issn':['1742-6588 ','1742-6596']},
  {'regexp':r'Comp\w*[\.]? Phys\w*[\.]? C\w*[\.]?|cpc','nombre': r"Computer Physics Communications",'abbrev': 'CPC', 'doi':'10.1016/j.cpc','issn':['0010-4655']},
  {'regexp':r'Phys\w*[\.]? Scrip\w*[\.]?','nombre': r"Physica Scripta Volume T",'abbrev': 'PS', 'doi':'10.1238/Physica.Topical','issn':[]},
  {'regexp':r'Rad\w*[\.]? Phy\w*[\.]? Chem\w*[\.]?|rpc','nombre': r"Radiation Physics and Chemistry",'abbrev': 'RPC', 'doi':'10.1016/j.radphyschem','issn':[]},
  {'regexp':r'F\w*[\.]? Bo\w*[\.]? Sys\w*[\.]?|fbs','nombre': r"Few-Body Systems",'abbrev': 'FBS', 'doi':'10.1007/s00601','issn':[]},
  {'regexp':r'Eur\w*[\.]? J\w*[\.]? Phys\w*[\.]?|ejp','nombre': r"European Journal of Physics",'abbrev': 'EJP', 'doi':'Not Available','issn':['0143-0807','1361-6404']},
  {'regexp':r'Phys\w*[\.]? Let\w*[\.]? A|pla', 'nombre':r"Physics Letters A",'abbrev': 'PLA', 'doi':'Not Available','issn':['0375-9601']},
  # 
  {'regexp':r'Am\w*[\.]? J\w*[\.]? P|ajp', 'nombre':r"American Journal of Physics",'abbrev': 'AJP', 'doi':'10.1119/','issn':['0002-9505']},
  {'regexp':r'J\w*[\.]? Chem\w*[\.]? Phys\w*[\.]?|jcp|JCP','nombre': r"Journal of Chemical Physics",'abbrev': 'JPC', 'doi':'Not Available','issn':['0021-9606','1089-7690']}
  ]

def is_string_like(obj):
  'Return True if *obj* looks like a string (from matplotlib)'
  if isinstance(obj, (str, unicode)): return True
  try: obj + ''
  except: return False
  return True

def isIterable(obj):
  try: iter(obj)
  except: return False
  return True

def is_writable_file_like(obj):
  '''return true if *obj* looks like a file object with a *write* method (from matplotlib)'''
  return hasattr(obj, 'write') and callable(obj.write)
def is_readable_file_like(obj): # No se si funciona
  '''return true if *obj* looks like a file object with a *read* method '''
  return hasattr(obj, 'read') and callable(obj.read)

def to_filehandle(fname, flag='r', return_opened=False):
  """ from matplotlib
  *fname* can be a filename or a file handle.  Support for gzipped
  files is automatic, if the filename ends in .gz.  *flag* is a
  read/write flag for :func:`file`
  """
  if is_string_like(fname):
    if fname.endswith('.gz'):
      import gzip
      fh = gzip.open(fname, flag)
    elif fname.endswith('.bz2'):
      import bz2
      fh = bz2.BZ2File(fname,flag)
    else:
      fh = file(fname, flag)
    opened = True
  elif hasattr(fname, 'seek'):
    fh = fname
    opened = False
  else:
    raise ValueError('fname must be a string or file handle')
  if return_opened:
    return fh, opened
  return fh


def openfile(fname=None,intent='r'):
  if fname == None or fname == '-' or fname == '':
    if intent=='r': fi= sys.stdin
    else:           fi= sys.stdout
    return fi

  return to_filehandle(fname,intent)


reg_simplify= re.compile('\W')
def oversimplify(strng):
  """
  (Over)simplify a string by converting to latex and then removing everything that does not belong to a word
  """
  s=strng.encode('latex')
  s= reg_simplify.sub('',s)
  return s

def closefile(fi):
  if fi != sys.stdin and fi != sys.stdout and fi != sys.stderr:
    fi.close()


reg_defstrng= re.compile('[{]*DEFINITIONOFSTRING[(](\w+)[)][{]*(\s*[#]*\s*["]*\s*\w*\s*["]*\s*)[}]*',re.I)
# reg_defstrng= re.compile('[{]*DEFINITIONOFSTRING[(](\w+)[)][}]*',re.I)

def replace_abbrevs(strs,sourcestrng):
  if 'DEFINITIONOFSTRING' in sourcestrng or 'definitionofstring' in sourcestrng:
    v=sourcestrng
    for abbrev,defin in strs.iteritems():
      v= v.replace('DEFINITIONOFSTRING(%s)'%(abbrev),defin)
      v= v.replace('DEFINITIONOFSTRING(%s)'%(abbrev).lower(),defin)
      v= v.replace('DEFINITIONOFSTRING(%s)'%(abbrev).upper(),defin)
      v= v.replace('definitionofstring(%s)'%(abbrev),defin)
      v= v.replace('definitionofstring(%s)'%(abbrev).lower(),defin)
      v= v.replace('definitionofstring(%s)'%(abbrev).upper(),defin)
      d= ' '.join([x.strip().strip('"') for x in v.split('#')])
#       if v.find('"') != -1 and 'Phys' in v:
#         print 'v',v
#         print 'd',d
    return  d
  return sourcestrng

def process_name(name):
  """
  Process one name and separate it in '[von, Last, First, Jr]'
  """
  def getnames_form3(a):
    """
    Case with two commas: the name is of the format
    von Last, Jr, First
    like in: von Hicks, III, Michael
    """
    full_last= a[0].strip()
    full_first=a[1].strip()
    junior= a[2]
    von,last= get_vonlast(full_last)
    return [von.strip(),last.strip(),full_first.strip(),junior.strip()]

  def getnames_form2(a):
    """
    Case with one comma: the name is of the format
    von Last, First
    like in: von Hicks, Michael
    """
    full_last= a[0].strip()
    full_first=a[1].strip()
    junior= ''
    von,last= get_vonlast(full_last)
    return [von.strip(),last.strip(),full_first.strip(),junior]

  def getnames_form1(a):
    """
    Case with NO commas: the name is of the format
    First von Last
    like in: Michael von Hicks
    """
    last= a[0].split(' ')
    nfn= 0
    for l in last:
      if l !="" and not l[0].islower():
        nfn+=1
      else:
        break
    if nfn == len(last):
      nfn= -1

    full_first= ' '.join(last[:nfn])
    full_first=full_first.replace('.',' ')
    full_last=  ' '.join(last[nfn:])
    junior=" "
    von,last= get_vonlast(full_last)
    return [von.strip(),last.strip(),full_first.strip(),junior.strip()]

  def get_vonlast(full_last):
    von=""
    last=""

    for l in full_last.split(' '):
      if len(l)>0 and l[0].islower():
        von += l.lower() + " "
      else:
        last += l + " "
    return von,last

  # Start the processing
  a=name.split(',')
  if len(a) == 3:
    fullname= getnames_form3(a)
  elif len(a) == 2:
    fullname= getnames_form2(a)
  elif len(a) == 1:
    fullname= getnames_form1(a)
  else:
    fullname=[]

  return fullname



def create_initials(strng):
  return ''.join(filter(lambda x:x.isupper(),map(lambda x:x[0],strng.split())))

def identify_some_journals(bibitem,known_journals=journal_data):

  # First try to identify the ISSN
  if bibitem.has_key('issn'):
    for j in known_journals:
      if bibitem['issn']== j['issn']:
        return j['nombre'],j['abbrev']

  # Then the DOI
  if bibitem.has_key('doi'):
    for j in known_journals:
      if bibitem['doi'].find(j['doi']) != -1:
        if j['issn'] != []:      bibitem['issn']=j['issn'][0]
        return j['nombre'],j['abbrev']

  # If DOI does not work, identify the journal with the regexp
  if bibitem.has_key('journal'):
    for j in known_journals:
      if re.search(j['regexp'],bibitem['journal']) != None:
        if j['issn'] != []:      bibitem['issn']=j['issn'][0]
        return j['nombre'],j['abbrev']

    # If it is not a know journal, get the abbreviation from the first letters of each word
    abbrev= create_initials(bibitem['journal'])
    return bibitem['journal'],abbrev
  else:
    # If nothing worked return emtpy strings
    return '',''


def handle_math(str,orden=0):
  """
  Convierte entre tex <--> html. 
  Si orden =0 => bib -> html 
  Si orden =1 => html -> bib
  """
  mathexp= ([ (re.compile(r'\^([^{]){',re.I)  ,r'<sup>\1</sup>')
             ,(re.compile(r'\^{([^{]+)}',re.I),r'<sup>\1</sup>')
             ,(re.compile(r'_([^{]+){',re.I)  ,r'<sub>\1</sub>')
             ,(re.compile(r'_{([^{]+)}',re.I) ,r'<sub>\1</sub>')
             ,(re.compile(r'\\mathrm{([^{]+)}',re.I) ,r'{\1}')
             ],
            [( re.compile(r'<sub>([^<]*)</sub>',re.I),r'$_{\1}$')
             ,(re.compile(r'<sup>([^<]*)</sup>',re.I),r'$^{\1}$')
             ])
#   mathmarker= ('<math>','</math>')
  mathmarker= ('','')


  if orden==0:
    p= re.compile(r'\$([^\$]+)\$')  # Find math substrings
    if p.search(str):
      ini=0
      linecontent=''
      iterator = p.finditer(str)
      for match in iterator:
        strmath= match.group()[1:-1]
        linecontent += str[ini:match.start()]
        for i,o in mathexp[orden]:
          strmath= re.sub(i,o,strmath)
        linecontent += mathmarker[0] + strmath + mathmarker[1]
        ini= match.end()
      linecontent += str[ini:]
    else:
      return str
  else:
    for i,o in mathexp[orden]:
      str= i.sub(o,str)
    linecontent= str

  return linecontent

# return the string parameter without braces
#
rembraces_rex = re.compile('[{}]')
def removebraces(str):
  return rembraces_rex.sub('',str) 


# data = title string
# @return the capitalized string (first letter is capitalized), rest are capitalized
# only if capitalized inside braces
capitalize_rex = re.compile('({\w*})')
def capitalizestring(data):
  ss_list = capitalize_rex.split(data)
  ss = ''
  count = 0
  for phrase in ss_list:
    check = phrase.lstrip()

	 # keep phrase's capitalization the same
    if check.find('{') == 0:
      ss+= removebraces(phrase)
    else:
      # first word --> capitalize first letter (after spaces)
      if count == 0:
        ss+= phrase.capitalize() 
#         ss+= check.capitalize() 
      else:
        ss+= phrase.lower() 
      count+= 1
  return ss



def match_pair(expr, pair=(r'{',r'}'),start=0):
  """ 
  Find the outermost pair enclosing a given expresion
  
  pair is a 2-tuple containing (begin, end) where both may be characters or strings
  for instance:
    pair= ('[',']')  or
    pair= ('if','end if') or
    pair= ('<div>','</div>') or ...
    
    """

  beg=pair[0]
  fin=pair[1]

  #   find first opening
  sstart= expr.find(beg,start)

  count= 0

  if beg == fin:
    eend= expr.find(fin,sstart+1)
    return sstart,eend

  p= re.compile('('+beg +'|' + fin+')', re.M)
  ps= re.compile(beg, re.M)

  iterator = p.finditer(expr,start)

  for match in iterator:
    if ps.match(match.group()):
      count+= 1
    else:
      count+= -1
        
    if count == 0:
      return sstart, match.end()

  return None

def no_outer_parens(filecontents):
  # JF: TODO We should check/change this routine Convierte los
  # parentesis a llaves cuando contienen el item completo. 
  # Do checking for open parens will convert to braces
  paren_split = re.split('([(){}])',filecontents)

  open_paren_count = 0
  open_type = False
  look_next = False

  # rebuild filecontents
  filecontents = ''

  at_rex = re.compile('@\w*')

  for phrase in paren_split:
    if look_next:
      if phrase == '(':
        phrase = '{'
        open_paren_count += 1
      else:
        open_type = False
      look_next = False

    if phrase == '(':
      open_paren_count += 1
    elif phrase == ')':
      open_paren_count -= 1
      if open_type and open_paren_count == 0:
        phrase = '}'
        open_type = False
    elif at_rex.search( phrase ):
      open_type = True
      look_next = True

    filecontents = filecontents + phrase
  return filecontents

    
def replace_tags(strng, what='All'):
  ww=what.lower()
  if ww == 'all' or ww == 'xml':
    # encode character entities
    for i,o in xml_tags:
      strng = strng.replace(i, o )

  if ww == 'all' or ww == 'accents':
    # latex-specific character replacements
    for i,o in accent_tags:
      strng = string.replace(strng, i, o )

  if ww == 'all' or ww == 'other':
    # Other LaTeX tags, handled by regexps
    for i,o in other_tags:
      strng= re.sub(i,o,strng)

  return strng

# def filter_author(biblist, filter_options):
#   delete=[]
#   for ident,item in biblist.iteritems():
#     valid = True
#     if item.has_key('author'):
#       aut = [ ' '.join(k) for k in item['author']]
#     else:
#       print ident, item
#       sys.exit(1)


# def filter_bib(biblist, filter_options):
#   delete=[]
#   for ident,item in biblist.iteritems():
#     valid = True
#     for k,v,cond in filter_options :
#       valid= item.has_key(k) and valid
#       if valid:
#         if type(item[k]) == list:
#           if k == 'author':
#             aut = [ ' '.join( s ) for s in item['author']]
#             data= ' '.join( aut )
#           else:
#             data= join( item[k] )
#         else:
#           data= item[k]
#         valid = valid and ((v in data.lower()) == cond)

#         if not valid:
#           delete.append(ident)
#           break
#       else:
#         delete.append(ident)
#         break

#   # Collect all matching and return them
#   bib={}
#   for ident in biblist.keys():
#     if ident not in delete:
#       bib[ident]= biblist[ident].copy()

#   return bib




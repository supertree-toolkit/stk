# -*- coding: utf-8 -*-
import logging
from .constants import *

# logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('HumanName')
ENCODING = 'utf-8'

def lc(value):
    '''Lower case and remove any periods to normalize for comparison.'''
    if not value:
        return ''
    return value.lower().replace('.','')

def is_an_initial(value):
    return re_initial.match(value) or False

class BlankHumanNameError(AttributeError):
    pass

class HumanName(object):
    
    """
    Parse a person's name into individual components.
    
        * o.title
        * o.first
        * o.middle
        * o.last
        * o.suffix
     
    """
    
    def __init__(self, full_name="", titles_c=TITLES, prefixes_c=PREFICES, 
        suffixes_c=SUFFICES, punc_titles_c=PUNC_TITLES, conjunctions_c=CONJUNCTIONS,
        capitalization_exceptions_c=dict(CAPITALIZATION_EXCEPTIONS), encoding=ENCODING):
        
        self.ENCODING = encoding
        self.TITLES_C = titles_c
        self.PUNC_TITLES_C = punc_titles_c
        self.CONJUNCTIONS_C = conjunctions_c
        self.PREFIXES_C = prefixes_c
        self.SUFFIXES_C = suffixes_c
        self.CAPITALIZATION_EXCEPTIONS_C = capitalization_exceptions_c
        self.count = 0
        self._members = ['title','first','middle','last','suffix']
        self.unparsable = True
        self._full_name = ''
        self.full_name = full_name
    
    def __iter__(self):
        return self
    
    def __len__(self):
        l = 0
        for x in self:
            l += 1
        return l
    
    def __eq__(self, other):
        """
        HumanName instances are equal to other objects whose 
        lower case unicode representations are the same
        """
        return str(self).lower() == str(other).lower()
    
    def __ne__(self, other):
        return not str(self).lower() == str(other).lower()
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            return [getattr(self, x) for x in self._members[key]]
        else:
            return getattr(self, self._members[key])
    
    def __next__(self):
        if self.count >= len(self._members):
            self.count = 0
            raise StopIteration
        else:
            c = self.count
            self.count = c + 1
            return getattr(self, self._members[c]) or next(self)

    def __unicode__(self):
        return " ".join(self)
    
    def __str__(self):
        return self.__unicode__().encode(self.ENCODING)
    
    def __repr__(self):
        if self.unparsable:
            return "<%(class)s : [ Unparsable ] >" % {'class': self.__class__.__name__,}
        return "<%(class)s : [\n\tTitle: '%(title)s' \n\tFirst: '%(first)s' \n\tMiddle: '%(middle)s' \n\tLast: '%(last)s' \n\tSuffix: '%(suffix)s'\n]>" % {
            'class': self.__class__.__name__,
            'title': self.title,
            'first': self.first,
            'middle': self.middle,
            'last': self.last,
            'suffix': self.suffix,
        }
    
    @property
    def _dict(self):
        d = {}
        for m in self._members:
            d[m] = getattr(self, m)
        return d
    
    def _set_list(self, attr, value):
        setattr(self, "_"+attr+"_list", self._parse_pieces([value]))
    
    @property
    def title(self):
        return " ".join(self._title_list)
    
    @property
    def first(self):
        return " ".join(self._first_list)
    
    @property
    def middle(self):
        return " ".join(self._middle_list)
    
    @property
    def last(self):
        return " ".join(self._last_list)
    
    @property
    def suffix(self):
        return ", ".join(self._suffix_list)
    
    @title.setter
    def title(self, value):
        self._set_list('title', value)
    
    @first.setter
    def first(self, value):
        self._set_list('first', value)
    
    @middle.setter
    def middle(self, value):
        self._set_list('middle', value)
    
    @last.setter
    def last(self, value):
        self._set_list('last', value)
    
    @suffix.setter
    def suffix(self, value):
        self._set_list('suffix', value)
    
    def is_title(self, value):
        return lc(value) in self.TITLES_C or value.lower() in self.PUNC_TITLES_C
    
    def is_conjunction(self, piece):
        return lc(piece) in self.CONJUNCTIONS_C and not is_an_initial(piece)
    
    def is_prefix(self, piece):
        return lc(piece) in self.PREFIXES_C and not is_an_initial(piece)
    
    def is_suffix(self, piece):
        return lc(piece) in self.SUFFIXES_C and not is_an_initial(piece)
    
    @property
    def full_name(self):
        return self._full_name
    
    @full_name.setter
    def full_name(self, value):
        self._full_name = value
        self._title_list = []
        self._first_list = []
        self._middle_list = []
        self._last_list = []
        self._suffix_list = []
        self.unparsable = True
        
        self._parse_full_name()

    def _parse_pieces(self, parts):
        """
        Split parts on spaces and remove commas, join on conjunctions and lastname prefixes
        """
        pieces = []
        for part in parts:
            pieces += [x.strip(' ,') for x in part.split(' ')]
        
        # join conjunctions to surrounding parts: ['Mr. and Mrs.'], ['Jack and Jill'], ['Velasquez y Garcia']
        conjunctions = list(filter(self.is_conjunction, pieces))
        for conj in conjunctions:
            i = pieces.index(conj)
            pieces[i-1] = ' '.join(pieces[i-1:i+2])
            if self.is_title(pieces[i+1]):
                # if the second name is a title, assume the first one is too and add the 
                # two titles with the conjunction between them to the titles constant 
                # so the combo we just created gets parsed as a title. e.g. "Mr. and Mrs."
                self.TITLES_C.add(lc(pieces[i-1]))
            pieces.pop(i)
            pieces.pop(i)
        
        # join prefices to following lastnames: ['de la Vega'], ['van Buren']
        prefixes = list(filter(self.is_prefix, pieces))
        for prefix in prefixes:
            try:
                i = pieces.index(prefix)
            except ValueError:
                # if two prefixes in a row ("de la Vega"), have to do extra work to find the index the second time around
                def find_p(p):
                    return p.endswith(prefix) # closure on prefix
                m = list(filter(find_p, pieces))
                # I wonder if some input will throw an IndexError here. Means it can't find prefix anyore.
                i = pieces.index(m[0])
            pieces[i] = ' '.join(pieces[i:i+2])
            pieces.pop(i+1)
            
        log.debug("pieces: " + str(pieces))
        return pieces
    
    def _parse_full_name(self):
        """
        Parse full name into the buckets
        """
        if not self._full_name:
            raise BlankHumanNameError("Missing full_name")
        
        if not isinstance(self._full_name, str):
            self._full_name = str(self._full_name, self.ENCODING)
        
        # collapse multiple spaces
        self._full_name = re.sub(re_spaces, " ", self._full_name.strip() )
        
        # break up full_name by commas
        parts = [x.strip() for x in self._full_name.split(",")]
        
        log.debug("full_name: " + self._full_name)
        log.debug("parts: " + str(parts))
        
        if len(parts) == 1:
            
            # no commas, title first middle middle middle last suffix
            
            pieces = self._parse_pieces(parts)
            
            for i, piece in enumerate(pieces):
                try:
                    next = pieces[i + 1]
                except IndexError:
                    next = None
                
                if self.is_title(piece):
                    self._title_list.append(piece)
                    continue
                if not self.first:
                    self._first_list.append(piece.replace(".",""))
                    continue
                if (i == len(pieces) - 2) and self.is_suffix(next):
                    self._last_list.append(piece)
                    self._suffix_list.append(next)
                    break
                if not next:
                    self._last_list.append(piece)
                    continue
                
                self._middle_list.append(piece)
        else:
            if lc(parts[1]) in self.SUFFIXES_C:
                
                # suffix comma: title first middle last, suffix [, suffix]
                
                self._suffix_list += parts[1:]
                
                pieces = self._parse_pieces(parts[0].split(' '))
                log.debug("pieces: " + str(pieces))
                
                for i, piece in enumerate(pieces):
                    try:
                        next = pieces[i + 1]
                    except IndexError:
                        next = None

                    if self.is_title(piece):
                        self._title_list.append(piece)
                        continue
                    if not self.first:
                        self._first_list.append(piece.replace(".",""))
                        continue
                    if not next:
                        self._last_list.append(piece)
                        continue
                    self._middle_list.append(piece)
            else:
                
                # lastname comma: last, title first middles[,] suffix [,suffix]
                pieces = self._parse_pieces(parts[1].split(' '))
                
                log.debug("pieces: " + str(pieces))
                
                self._last_list.append(parts[0])
                for i, piece in enumerate(pieces):
                    
                    if self.is_title(piece):
                        self._title_list.append(piece)
                        continue
                    if not self.first:
                        self._first_list.append(piece.replace(".",""))
                        continue
                    if self.is_suffix(piece):
                        self._suffix_list.append(piece)
                        continue
                    self._middle_list.append(piece)
                try:
                    if parts[2]:
                        self._suffix_list += parts[2:]
                except IndexError:
                    pass
                
        if not self.first and len(self._middle_list) < 1 and len(self._last_list) < 1:
            log.error("Unparsable full_name: " + self._full_name)
        else:
            self.unparsable = False
    
    def cap_word(self, word):
        if self.is_prefix(word) or self.is_conjunction(word):
            return lc(word)
        if word in self.CAPITALIZATION_EXCEPTIONS_C:
            return self.CAPITALIZATION_EXCEPTIONS_C[word]
        mac_match = re_mac.match(word)
        if mac_match:
            def cap_after_mac(m):
                return m.group(1).capitalize() + m.group(2).capitalize()
            return re_mac.sub(cap_after_mac, word)
        else:
            return word.capitalize()

    def cap_piece(self, piece):
        if not piece:
            return ""
        replacement = lambda m: self.cap_word(m.group(0))
        return re.sub(re_word, replacement, piece)

    def capitalize(self):
        """
        Capitalization Support
        ----------------------

        The HumanName class can try to guess the correct capitalization 
        of name entered in all upper or lower case. It will not adjust 
        the case of names entered in mixed case.
        
        Usage::
        
            >>> name = HumanName('bob v. de la macdole-eisenhower phd')
            >>> name.capitalize()
            >>> unicode(name)
            u'Bob V. de la MacDole-Eisenhower Ph.D.'
            >>> # Don't touch good names
            >>> name = HumanName('Shirley Maclaine')
            >>> name.capitalize()
            >>> unicode(name) 
            u'Shirley Maclaine'
        
        """
        name = str(self)
        if not (name == name.upper() or name == name.lower()):
            return
        self._title_list = self.cap_piece(self.title).split(' ')
        self._first_list = self.cap_piece(self.first).split(' ')
        self._middle_list = self.cap_piece(self.middle).split(' ')
        self._last_list = self.cap_piece(self.last).split(' ')
        self._suffix_list = self.cap_piece(self.suffix).split(' ')

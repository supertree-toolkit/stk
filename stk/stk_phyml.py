#!/usr/bin/env python
#
#    Supertree Toolkit. Software for managing and manipulating sources
#    trees ready for supretree construction.
#    Copyright (C) 2011, Jon Hill, Katie Davis
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Jon Hill. jon.hill@imperial.ac.uk. 
from lxml import etree
import os
import stk_exceptions as excp
import stk_internals
import stk_trees
from collections import defaultdict


def get_project_name(XML):
    """
    Get the name of the dataset currently being worked on
    """

    xml_root = parse_xml(XML)

    return xml_root.xpath('/phylo_storage/project_name/string_value')[0].text 


def create_name(authors, year, append=''):
    """ 
    Construct a sensible from a list of authors and a year for a 
    source name.
    Input: authors - list of last (family, sur) names (string).
           year - the year (string).
           append - append something onto the end of the name.
    Output: source_name - (string)
    """

    source_name = None
    if (authors[0] == None):
        # No authors yet!
        raise NoAuthors("No authors found to sort") 
    if (len(authors) == 1):
        # single name: name_year
        source_name = authors[0] + "_" + year + append
    elif (len(authors) == 2):
        source_name = authors[0] + "_" + authors[1] + "_" + year + append
    else:
        source_name = authors[0] + "_etal_" + year + append

    return source_name


def single_sourcename(XML,append=''):
    """ Create a sensible source name based on the 
    bibliographic data.
    XML should contain the xml_root for the source that is to be
    altered only.
    NOTE: It is the responsibility of the calling process of this 
          function to check for name uniqueness.
    """

    xml_root = parse_xml(XML)

    find = etree.XPath("//authors")
    authors_ele = find(xml_root)[0]
    authors = []
    for ele in authors_ele.iter():
        if (ele.tag == "surname"):
            authors.append(ele.xpath('string_value')[0].text)
    
    find = etree.XPath("//year/integer_value")
    year = find(xml_root)[0].text
    source_name = create_name(authors, year,append)
    
    attributes = xml_root.attrib
    attributes["name"] = source_name

    XML = etree.tostring(xml_root,pretty_print=True)

    # Return the XML stub with the correct name
    return XML

def all_sourcenames(XML, trees=False):
    """
    Create a sensible sourcename for all sources in the current
    dataset. This includes appending a, b, etc for duplicate names.
    """

    xml_root = parse_xml(XML)

    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    for s in sources:
        xml_snippet = etree.tostring(s,pretty_print=True)
        xml_snippet = single_sourcename(xml_snippet)
        parent = s.getparent()
        ele_T = parse_xml(xml_snippet)
        parent.replace(s,ele_T)

    XML = etree.tostring(xml_root,pretty_print=True)
    # gah: the replacement has got rid of line breaks for some reason
    XML.replace("</source><source ", "</source>\n    <source ")
    XML.replace("</source></sources", "</source>\n  </sources") 
    XML = set_unique_names(XML)
    if (trees):
        XML = set_all_tree_names(XML,overwrite=True)
    
    return XML

def get_all_source_names(XML):
    """ From a full XML-PHYML string, extract all source names.
    """

    xml_root = parse_xml(XML)
    find = etree.XPath("//source")
    sources = find(xml_root)
    names = []
    for s in sources:
        attr = s.attrib
        name = attr['name']
        names.append(name)
    
    return names

def get_all_tree_names(XML):
    """ From a full XML-PHYML string, extract all tree names.
    """

    xml_root = parse_xml(XML)
    find = etree.XPath("//source")
    sources = find(xml_root)
    names = []
    for s in sources:
        for st in s.xpath("source_tree"):
            if 'name' in st.attrib and not st.attrib['name'] == "":
                names.append(st.attrib['name'])
    
    return names


def get_all_genera(XML):

    taxa = get_all_taxa(XML)

    generic = []
    for t in taxa:
        t = t.replace('"','')
        generic.append(t.split("_")[0])

    return generic

def set_unique_names(XML):
    """ Ensures all sources have unique names.
    """
    
    xml_root = parse_xml(XML)

    # All source names
    source_names = get_all_source_names(XML)

    # The list is stored as a dict, with the key being the name
    # The value is the number of times this names occurs
    unique_source_names = defaultdict(int)
    for n in source_names:
        unique_source_names[n] += 1

    # if they are unique (i.e. == 1), then make it == 0
    for k in unique_source_names.iterkeys():
        if unique_source_names[k] == 1:
            unique_source_names[k] = 0
    
    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    last_name = ''
    for s in sources:
        current_name = s.attrib['name']
        if (unique_source_names[current_name] > 0):
            number = unique_source_names[current_name]
            # if there are two entries for this name, we should get 'a' and 'b'
            # 'a' + 1 == b
            # 'a' + 0 == a
            letter = chr(ord('a')+(number-1)) 
            xml_snippet = etree.tostring(s,pretty_print=True)
            xml_snippet = single_sourcename(xml_snippet,append=letter)
            parent = s.getparent()
            ele_T = parse_xml(xml_snippet)
            parent.replace(s,ele_T)
            # decrement the value so our letter is not the
            # same as last time
            unique_source_names[current_name] -=1

    # sort new name
    xml_root = sort_data(xml_root)

    XML = etree.tostring(xml_root,pretty_print=True)

    return XML

def create_tree_name(XML,source_tree_element):

    """
    Creates a tree name for a given source
    Simply the source_name with a number added
    source_tree_element is the element that contains the source tree, 
    i.e. sources/source/source_tree
    """

    xml_root = parse_xml(XML)
    source = source_tree_element.getparent()
    # count current trees
    tree_count = 1
    for t in source.xpath("source_tree"):
        if 'name' in t.attrib and not t.attrib['name'] == "":
                tree_count += 1
    try:
        tree_name = source.attrib['name'] + "_" + str(tree_count)
    except KeyError:
        # no name set for source
        tree_name = str(tree_count)

    return tree_name

def set_all_tree_names(XML,overwrite=False):

    """Set all *unset* tree names
    """

    xml_root = parse_xml(XML)

    # Find all "source" trees
    sources = []
    for ele in xml_root.iter():
        if (ele.tag == "source"):
            sources.append(ele)

    if overwrite:
        # remove all the names first
        for s in sources:
            for st in s.xpath("source_tree"):
                if 'name' in st.attrib:
                    del st.attrib['name']


    for s in sources:
        for st in s.xpath("source_tree"):
            if not'name' in st.attrib:
                tree_name = create_tree_name(XML,st)
                st.attrib['name'] = tree_name
   
    XML = etree.tostring(xml_root,pretty_print=True)    
    return XML


def get_all_characters(XML,ignoreErrors=False):
    """Returns a dictionary containing a list of characters within each 
    character type"""

    xml_root = parse_xml(XML)
    find = etree.XPath("//character")
    characters = find(xml_root)

    # grab all character types first
    types = []
    for c in characters:
        try:
            types.append(c.attrib['type'])
        except KeyError:
            if (ignoreErrors):
                pass
            else:
                raise KeyError("Error getting character type. Incomplete data")

    u_types = stk_internals.uniquify(types)
    u_types.sort()

    char_dict = {}
    for t in u_types:
        char = []
        for c in characters:
            try:
                if (c.attrib['type'] == t):
                    if (not c.attrib['name'] in char):
                        char.append(c.attrib['name'])
            except KeyError:
                if (ignoreErrors):
                    pass
                else:
                    raise KeyError("Error getting character type. Incomplete data")

        char_dict[t] = char       

    return char_dict

def get_publication_year_tree(XML,name):
    """Return a dictionary of years and the number of publications
    within that year
    """

    # Our input tree has name source_no, so find the source by stripping off the number
    source_name, number = name.rsplit("_",1)
    number = int(number.replace("_",""))
    xml_root = parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    find = etree.XPath("//source")
    sources = find(xml_root)
    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        if source_name == name:
            # found the bugger!
            tree_no = 1
            for t in s.xpath("source_tree/tree/tree_string"):
                if tree_no == number:
                    # and now we have the correct tree. 
                    # Now we can get the year for this tree
                    if not t.getparent().getparent().getparent().xpath("bibliographic_information/article") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/article/year/integer_value")[0].text)
                    elif not t.getparent().getparent().getparent().xpath("bibliographic_information/book") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/book/year/integer_value")[0].text)
                    elif not t.getparent().getparent().getparent().xpath("bibliographic_information/in_book") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/in_book/year/integer_value")[0].text)
                    elif not t.getparent().getparent().getparent().xpath("bibliographic_information/in_collection") == None:
                        year = int(t.getparent().getparent().getparent().xpath("bibliographic_information/in_collection/year/integer_value")[0].text)
                    return year
                tree_no += 1

    # should raise exception here
    return None

def get_characters_from_tree(XML,name,sort=False):
    """Get the characters that were used in a particular tree
    """

    characters = []
    # Our input tree has name source_no, so find the source by stripping off the number
    source_name, number = name.rsplit("_",1)
    number = int(number.replace("_",""))
    xml_root = parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    find = etree.XPath("//source")
    sources = find(xml_root)
    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        if source_name == name:
            # found the bugger!
            tree_no = 1
            for t in s.xpath("source_tree/tree/tree_string"):
                if tree_no == number:
                    # and now we have the correct tree. 
                    # Now we can get the characters for this tree
                    chars = t.getparent().getparent().xpath("character_data/character")
                    for c in chars:
                        characters.append(c.attrib['name'])
                    if (sort):
                        characters.sort()
                    return characters
                tree_no += 1

    # should raise exception here
    return characters

def get_character_types_from_tree(XML,name,sort=False):
    """Get the character types that were used in a particular tree
    """

    characters = []
    # Our input tree has name source_no, so find the source by stripping off the number
    source_name, number = name.rsplit("_",1)
    number = int(number.replace("_",""))
    xml_root = parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    find = etree.XPath("//source")
    sources = find(xml_root)
    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        if source_name == name:
            # found the bugger!
            tree_no = 1
            for t in s.xpath("source_tree/tree/tree_string"):
                if tree_no == number:
                    # and now we have the correct tree. 
                    # Now we can get the characters for this tree
                    chars = t.getparent().getparent().xpath("character_data/character")
                    for c in chars:
                        characters.append(c.attrib['type'])
                    if (sort):
                        characters.sort()
                    return characters
                tree_no += 1

    # should raise exception here
    return characters


def get_characters_used(XML):
    """ Return a sorted, unique array of all character names used
    in this dataset
    """
 
    c_ = []
 
    xml_root = parse_xml(XML)
    find = etree.XPath("//character")
    chars = find(xml_root)

    for c in chars:
        name = c.attrib['name']
        ctype = c.attrib['type']
        c_.append((name,ctype))
 
    characters = stk_internals.uniquify(c_) 
    characters.sort(key=lambda x: x[0].lower())
 
    return characters

def get_character_numbers(XML,ignoreErrors=False):
    """ Return the number of trees that use each character
    """

    xml_root = parse_xml(XML)
    find = etree.XPath("//character")
    characters = find(xml_root)

    char_numbers = defaultdict(int)

    for c in characters:
        try:
            char_numbers[c.attrib['name']] += 1
        except KeyError:
            if (ignoreErrors):
                pass
            else:
                raise KeyError("Error getting character type. Incomplete data")

    return char_numbers

def get_taxa_from_tree(XML, tree_name, sort=False):
    """Return taxa from a single tree based on name
    """

    trees = get_all_trees(XML)
    taxa_list = []
    for t in trees:
        if t == tree_name:
            tree = stk_trees.parse_tree(trees[t]) 
            terminals = tree.getAllLeafNames(tree.root)
            for term in terminals:
                taxa_list.append(str(term))
            if (sort):
                taxa_list.sort()
            return taxa_list

    # actually need to raise exception here
    # and catch it in calling function
    return taxa_list


def get_fossil_taxa(XML):
    """Return a list of fossil taxa
    """

    f_ = []

    xml_root = parse_xml(XML)
    find = etree.XPath("//fossil")
    fossils = find(xml_root)

    for f in fossils:
        try:
            name = f.getparent().attrib['name']
            f_.append(name)
        except KeyError:
            pass

    fossil_taxa = stk_internals.uniquify(f_) 
    
    return fossil_taxa

def get_analyses_used(XML,ignoreErrors=False):
    """ Return a sorted, unique array of all analyses types used
    in this dataset
    """

    a_ = []

    xml_root = parse_xml(XML)
    find = etree.XPath("//optimality_criterion")
    analyses = find(xml_root)

    for a in analyses:
        try:
            name = a.attrib['name']
            a_.append(name)
        except KeyError:
            if (ignoreErrors):
                pass
            else:
                raise KeyError("Error parsing analyses. Incomplete data")

    analyses = stk_internals.uniquify(a_) 
    analyses.sort()

    return analyses

def get_publication_years(XML):
    """Return a dictionary of years and the number of publications
    within that year
    """

    year_dict = defaultdict(int)
    xml_root = parse_xml(XML)
    find = etree.XPath("//year")
    years = find(xml_root)

    for y in years:
        try:
            year = int(y.xpath('integer_value')[0].text)
            year_dict[year] += 1
        except TypeError:
            pass

    return year_dict

def get_all_trees(XML):
    """ Parse the XML and obtain all tree strings
    Output: dictionary of tree strings, with key indicating treename (unique)
    """

    xml_root = parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    # within that source and construct a unique name
    find = etree.XPath("//source")
    sources = find(xml_root)
    trees = {}

    # loop through all sources
    for s in sources:
        for t in s.xpath("source_tree/tree/tree_string"):
            try:
                t_name = t.getparent().getparent().attrib['name']
            except KeyError:
                # no name, so make one!
                t_name = create_tree_name(XML,t.getparent().getparent())
                t.getparent().getparent().attrib['name'] = t_name
            # append to dictionary, with source_name_tree_no = tree_string
            if (not t.xpath("string_value")[0].text == None):
                trees[t_name] = t.xpath("string_value")[0].text

    return trees


def get_all_taxa(XML, pretty=False, ignoreErrors=False):
    """ Produce a taxa list by scanning all trees within 
    a PHYML file. 

    The list is return sorted (alphabetically).

    Setting pretty=True means all underscores will be
    replaced by spaces"""

    trees = get_all_trees(XML)

    taxa_list = []

    for tname in trees.keys():
        t = trees[tname]
        try:
            taxa_list.extend(stk_trees.get_taxa(t))
        except excp.TreeParseError as detail:
            if (ignoreErrors):
                logging.warning(detail.msg)
                pass
            else:
                raise TreeParseError( detail.msg )

    # now uniquify the list of taxa
    taxa_list = stk_internals.uniquify(taxa_list)
    taxa_list.sort()

    if (pretty): #Remove underscores from names
        taxa_list = [x.replace('_', ' ') for x in taxa_list]

    return taxa_list


def get_weights(XML):
    """ Get weights for each tree. Returns dictionary of tree name (key) and weights
        (value)
    """

    xml_root = parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    # within that source and construct a unique name
    find = etree.XPath("//source")
    sources = find(xml_root)

    weights = {}

    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        for t in s.xpath("source_tree"):
            tree_name = t.attrib['name']
            if (len(t.xpath("tree/weight/real_value")) > 0):
                weights[tree_name] = float(t.xpath("tree/weight/real_value")[0].text)
            else:
                weights[tree_name] = 1.0

    min_weight = min(weights.values())
    factor = 1.0/min_weight
    for w in weights:
        weights[w] = weights[w]*factor
    
    return weights


def get_outgroup(XML):
    """ For each tree, get the outgroup defined in the schema
    """
    xml_root = parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    # within that source and construct a unique name
    find = etree.XPath("//source")
    sources = find(xml_root)

    outgroups = {}

    # loop through all sources
    for s in sources:
        # for each source, get source name
        name = s.attrib['name']
        # get trees
        tree_no = 1
        for t in s.xpath("source_tree/tree"):
            t_name = name+"_"+str(tree_no)
            if (len(t.xpath("topology/outgroup/string_value")) > 0):
                temp_outgp = t.xpath("topology/outgroup/string_value")[0].text
                temp_outgp = temp_outgp.replace("\n", ",")
                temp_outgp = temp_outgp.split(",")
                outgroups[t_name] = temp_outgp                
            tree_no += 1

    # replace spaces with _ in outgroup names
    for key in outgroups:
        og = outgroups[key]
        og = [o.strip().replace(' ', '_') for o in og]
        outgroups[key] = og

    return outgroups


def load_phyml(filename):
    """ Super simple function that returns XML
        string from PHYML file
    """
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.tostring(etree.parse(filename,parser),pretty_print=True)


def add_weights(XML, names, weight):
    """ Add weights for tree, supply array of names and a weight, they get set
        Returns a new XML
    """

    xml_root = parse_xml(XML)
    # By getting source, we can then loop over each source_tree
    find = etree.XPath("//source_tree")
    sources = find(xml_root)
    for s in sources:
        s_name = s.attrib['name']
        for n in names:
            if s_name == n:
                if s.xpath("tree/weight/real_value") == []:
                    # add weights
                    weights_element = etree.Element("weight")
                    weights_element.tail="\n"
                    real_value = etree.SubElement(weights_element,'real_value')
                    real_value.attrib['rank'] = '0'
                    real_value.tail = '\n'
                    real_value.text = str(weight)
                    t = s.xpath("tree")[0]                    
                    t.append(weights_element)
                else:
                    s.xpath("tree/weight/real_value")[0].text = str(weight)

    return etree.tostring(xml_root,pretty_print=True)



def check_uniqueness(XML):
    """ This funciton is an error check for uniqueness in 
    the keys of the sources
    """

    try:
        xml_root = parse_xml(XML)
        # By getting source, we can then loop over each source_tree
        # within that source and construct a unique name
        find = etree.XPath("//source")
        sources = find(xml_root)
    except:
        raise excp.InvalidSTKData("Error parsing the data to check uniqueness")
    
    names = []
    message = ""
    # loop through all sources
    try:
        for s in sources:
            # for each source, get source name
            names.append(s.attrib['name'])
    except:
        raise excp.InvalidSTKData("Error parsing the data to check uniqueness")

    names.sort()
    last_name = "" # This will actually throw an non-unique error if a name is empty
    # not great, but still an error!
    for name in names:
        if name == last_name:
            # if non-unique throw exception
            message = message + \
                    "The source names in the dataset are not unique. Please run the auto-name function on these data. Name: "+name+"\n"
        last_name = name

    # do same for tree names:
    names = get_all_tree_names(XML)
    names.sort()
    last_name = "" # This will actually throw an non-unique error if a name is empty
    # not great, but still an error!
    for name in names:
        if name == last_name:
            # if non-unique throw exception
            message = message + \
                    "The tree names in the dataset are not unique. Please run the auto-name function on these data with replace or edit by hand. Name: "+name+"\n"
        last_name = name

    if (not message == ""):
        raise excp.NotUniqueError(message)

    return


def swap_tree_in_XML(XML, tree, name, delete=False):
    """ Swap tree with name, 'name' with this new one.
        If tree is None, name is removed.
        If source no longer contains any trees, the source is removed
    """

    # The calling function should make sure the names are unique
    # First thing is to do is find the source name that corresponds to this tree

    xml_root = parse_xml(XML)
    t = xml_root.xpath("//source_tree[@name=\'"+name+"\']")
    if (len(t) != 1):
        raise excp.NotUniqueError("Two or more source_trees have the same name. Please fix this.")
    else:
        t = t[0]
    s = t.getparent()

    if (not tree == None):
        t.xpath("tree/tree_string/string_value")[0].text = tree
        # We can return as we're only replacing one tree
        return etree.tostring(xml_root,pretty_print=True)
    else:
        # we need to get parent and remove
        t.getparent().remove(t)
        if (delete):
            # we now need to check the source to check if there are
            # any trees in this source now, if not, remove
            if (len(s.xpath("source_tree")) == 0):
                s.getparent().remove(s)
        return etree.tostring(xml_root,pretty_print=True)

    return XML


def check_taxa(XML,delete=False):
    """ Checks that taxa in the XML are in the tree for the source thay are added to
    """

    try:
        # grab all sources
        xml_root = parse_xml(XML)
        find = etree.XPath("//source")
        sources = find(xml_root)
    except:
        raise excp.InvalidSTKData("Error parsing the data to check taxa")
    
    message = ""

    # for each source
    for s in sources:
        # get a list of taxa in the XML
        this_source = parse_xml(etree.tostring(s))
        trees = get_all_trees(etree.tostring(this_source))
        s_name = s.attrib['name']
        taxa_ele = []
        for name in trees.iterkeys():
            tree_no = 1
            for t in s.xpath("source_tree"):
                try:
                    t_name = t.attrib['name']
                except KeyError:
                    message = message + "Tree in "+s_name+" is not named. Run the name_trees function"+"\n"
                    continue
                if (t_name == name):
                    find = etree.XPath(".//taxon")
                    taxa_ele = find(t)

            tree = trees[name]
            # are the XML taxa in the tree?
            for t in taxa_ele:
                xml_taxon = t.attrib['name']
                if (tree.find(xml_taxon) == -1):
                    if (delete):
                        # remove
                        t.getparent().remove(t)
                    else:
                        # no - raise an error!
                        message = message + "Taxon: "+xml_taxon+" is not in the tree "+name+"\n"
    if not delete:               
        if (not message==""):
            raise excp.InvalidSTKData(message)
        else:
            return
    else:
        return etree.tostring(xml_root,pretty_print=True)        


def check_sources(XML,delete=True):
    """ Check that all sources in the dataset have at least one tree_string associated
        with them
    """

    try:
        xml_root = parse_xml(XML)
        # By getting source, we can then loop over each source_tree
        # within that source and construct a unique name
        find = etree.XPath("//source")
        sources = find(xml_root)
    except:
        raise excp.InvalidSTKData("Error parsing the data to check source")
            
    message = ""
    # for each source
    for s in sources:
        # get a list of taxa in the XML
        this_source = parse_xml(etree.tostring(s))
        name = s.attrib['name']
        trees = get_all_trees(etree.tostring(this_source))
        if (len(trees) < 1):
            if (not delete):
                message =+ "Source "+name+" has no trees\n"
            else:
                s.getparent().remove(s)

    if not delete:
        if (not message == ""):
            raise excp.InvalidSTKData(message)
        else:
            return
    else:
        return etree.tostring(xml_root,pretty_print=True)        



def parse_xml(xml_string):
    """ Lxml cannot parse non-unicode characters 
    so we're wrapping this up so we can strip these characters
    beforehand. We can then send it to lxml.parser as normal
    """

    xml_string = stk_internals.removeNonAscii(xml_string)
    XML = etree.fromstring(xml_string)
    return XML


def sort_data(xml_root):
    """ Grab all source names and sort them alphabetically, 
    spitting out a new XML """

    container = xml_root.find("sources")

    data = []
    for elem in container:
        key = elem.attrib['name']
        data.append((key, elem))

    data.sort()

    # insert the last item from each tuple
    container[:] = [item[-1] for item in data]
    
    return xml_root




def check_informative_trees(XML,delete=False):
    """ Checks that all trees in the data set are informative and raises error if not
    """

    try:
        trees = get_all_trees(XML)
    except:
        raise excp.InvalidSTKData("Error parsing the data to check trees")
    remove = []
    message=""
    for t in trees:
        tree = trees[t]
        tree = stk_trees.parse_tree(tree)

        # check if tree contains more than two taxa
        terminals = tree.getAllLeafNames(tree.root)
        if (len(terminals) < 3):
            message = message+"\nTree "+t+" contains only 2 taxa and is not informative"
            remove.append(t)
        # if tree contains three or more taxa, check it's rooted somewhere
        elif (tree.getDegree(tree.root) == len(terminals)):
            message = message+"\nTree "+t+" doesn't contain any clades and is not informative"
            remove.append(t)

    if (not delete):
        if (not message == ""):
            raise excp.UninformativeTreeError(message)
        else:
            return
    else:
        remove.sort(reverse=True)
        for t in remove:
            XML = swap_tree_in_XML(XML,None,t,delete=True)

        return XML


def find_trees_for_permuting(XML):
    """
    Returns any trees that contain %, i.e. non-monophyly
    """
    trees = get_all_trees(XML)
    permute_trees = {}
    for t in trees:
        if trees[t].find('%') > -1:
            # tree needs permuting - we store the 
            permute_trees[t] = trees[t]

    return permute_trees


def check_subs_against(XML,new_taxa):
    """Check that if additional taxa are being added via a substitution and issues
       a warning if any of the incoming taxa
       are not already in the dataset. This is often what is wanted, but sometimes
       it is not. We run this before we do the subs to alert the user of this
       but they may continue
    """

    dataset_taxa = get_all_taxa(XML)
    unknown_taxa = []
    generic = get_all_genera(XML)
    for taxon in new_taxa:
        if not taxon == None:
            all_taxa = taxon.split(",")
            for t in all_taxa:
                if t.find("_") == -1:
                    # just generic, so check against that
                    if not t in generic:
                        unknown_taxa.append(t)
                else:
                    if not t in dataset_taxa:
                        unknown_taxa.append(t)
    unknown_taxa = stk_internals.uniquify(unknown_taxa)
    unknown_taxa.sort()

    if (len(unknown_taxa) > 0):
        taxa_list = '\n'.join(unknown_taxa)
        msg = "These taxa are not already in the dataset, are you sure you want to substitute them in?\n"
        msg += taxa_list
        raise excp.AddingTaxaWarning(msg) 
    
    return


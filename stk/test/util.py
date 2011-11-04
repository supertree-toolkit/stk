import re
from lxml import objectify, etree

def compare(a, b):
    """Compare two basestrings, disregarding whitespace -&gt; bool"""
    return re.sub("\s*", "", a) == re.sub("\s*", "", b)

def isEqualXML(a, b):
    obj1 = objectify.fromstring(a)
    expect = etree.tostring(obj1)        
    obj2 = objectify.fromstring(b)
    result = etree.tostring(obj2)
    return expect == result


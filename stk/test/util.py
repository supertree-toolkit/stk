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

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

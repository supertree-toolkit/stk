#!/usr/bin/env python
import argparse
import os
import sys
stk_path = os.path.join( os.path.realpath(os.path.dirname(__file__)), os.pardir )
sys.path.insert(0, stk_path)
import supertree_toolkit as stk
from lxml import etree


def main():

    # do stuff
    parser = argparse.ArgumentParser(
         prog="remove poorly contrained taxa",
         description="""Remove taxa that appea in one source tree only.""",
         )
    parser.add_argument(
            '-v', 
            '--verbose', 
            action='store_true', 
            help="Verbose output: mainly progress reports.",
            default=False
            )
    parser.add_argument(
            '--delete_list', 
            help="Produce a deleted taxa list. Give filename."
            )
    parser.add_argument(
            '--poly_only', 
            default=False,
            action='store_true',
            help="Restrict removal of taxa that are in polytomies only in source trees. Default"+
                 " to removal those in polytomies *and* only in one other tree."
            )
    parser.add_argument(
            '--tree_only', 
            default=False,
            action='store_true',
            help="Restrict removal of taxa that only occur in one source tree. Default"+
                 " to removal those in polytomies *and* only in one other tree."
            )
    parser.add_argument(
            'input_phyml', 
            metavar='input_phyml',
            nargs=1,
            help="Your input phyml"
            )
    parser.add_argument(
            'input_tree', 
            metavar='input_tree',
            nargs=1,
            help="Your tree - can be NULL or None"
            )
    parser.add_argument(
            'output_tree', 
            metavar='output_tree',
            nargs=1,
            help="Your output tree or phyml - if input_tree is none, this is the Phyml"
            )


    args = parser.parse_args()
    verbose = args.verbose
    delete_list_file = args.delete_list
    if (delete_list_file == None):
        dl = False
    else:
        dl = True
    poly_only = args.poly_only
    input_tree = args.input_tree[0]
    if input_tree == 'NULL' or input_tree == 'None':
        input_tree = None
    output_file = args.output_tree[0]
    input_phyml = args.input_phyml[0]

    XML = stk.load_phyml(input_phyml)
    # load tree
    if (not input_tree == None):
        supertree = stk.import_tree(input_tree)
        taxa = stk._getTaxaFromNewick(supertree)
    else:
        supertree = None
        taxa = stk.get_all_taxa(XML) 
    # grab taxa
    delete_list = []

    # loop over taxa in supertree and get some stats
    for t in taxa:
        #print "Looking at "+t
        nTrees = 0
        nResolved = 0
        nPoly = 0

        # search each source tree
        xml_root = stk._parse_xml(XML)
        # By getting source, we can then loop over each source_tree
        find = etree.XPath("//source")
        sources = find(xml_root)
        # loop through all sources
        for s in sources:
            # for each source, get source name
            name = s.attrib['name']
            for tr in s.xpath("source_tree/tree/tree_string"):
                tree = tr.xpath("string_value")[0].text
                current_taxa = stk._getTaxaFromNewick(tree)
                # if tree contains taxa
                if (t in current_taxa):
                    nTrees += 1
                    tree_obj = stk._parse_tree(tree,fixDuplicateTaxa=True)
                    siblings = stk._get_all_siblings(tree_obj.node(t))
                    
                    # check where it occurs - polytomies only?
                    if (len(siblings) > 3): #2?
                        nPoly += 1
                    else:
                        nResolved += 1
        
        # record stats for this taxon and decide if to delete it
        if (poly_only):
            if (nPoly == nTrees): # all in polytomies
                delete_list.append(t)
        else:
            if (nPoly == nTrees or # all in polytomies
                 (nResolved == 1 and (nPoly+nResolved)==nTrees) # only 1 resolved and rest (if any) polytomies
               ):
                delete_list.append(t)

    print "Taxa: "+str(len(taxa))
    print "Deleting: "+str(len(delete_list))

    if not supertree == None:
        # done, so delete the problem taxa from the supertree
        for t in delete_list:
            # remove taxa from supertree
            supertree = stk._sub_taxa_in_tree(supertree,t)

        # save supertree
        tree = {}
        tree['Tree_1'] = supertree
        output = stk._amalgamate_trees(tree,format='nexus')
        # write file
        f = open(output_file,"w")
        f.write(output)
        f.close()
    else:
        new_phyml =  stk.substitute_taxa(XML,delete_list)
        # write file
        f = open(output_file,"w")
        f.write(new_phyml)
        f.close()



    if (dl):
        # write file
        delete_list.sort()
        f = open(delete_list_file,"w")
        string = '\n'.join(delete_list)
        f.write(string)
        f.close()

if __name__ == "__main__":
    main()

#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        clusterTaxon.py
# Purpose:     cluster each species with its own GO into its parent taxon
#              the partitioning of the taxonomy is provided as a hand made file
#              taxonConstraintsDef.txt - requires the output of speciesToGO.py
#
# Author:      stefano
#
# Created:     19/07/2019
# Copyright:   (c) stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------


import sys, argparse, copy, re
from owlready2 import *
from taxonLibrary3 import *


def main(args):

    parent_son = {}
    son_parent = {}
    Taxa = Taxon(args['taxa'],args['merge'],args['names'])
    #parse list of reference nodes file
    with open(args['constraints'],'r') as constraints:
        for line in constraints:
            if line.startswith('#'):
                continue
            #END IF
            line = line.strip()
            values = line.split("\t")
            id_taxon    = values[0].strip()
            taxon_name  = values[1].strip()
            parent_name = values[4].strip()
            stopOther   = values[3].strip()

            son_parent[id_taxon]  = taxon_name
        #END FOR
    #END WITH
    constraints.close()
    TotalCount = {}
    GO = {}
    taxon = ''
    status = False
    with open(args['species'],'r') as species:
        for line in species:
            if line.startswith('>'):
                if taxon:
                    parent = ''
                    ## check if it must be clustered
                    father = taxon
                    while True:
                        if father in son_parent.keys():
                            break
                        father = Taxa.get_father(father)
                    parent = son_parent[father]
                    if parent not in TotalCount:
                        TotalCount.setdefault(parent,{})
                            ## END IF
                        ## END IF
                    ## END WHILE
                    for go in GO:
                        if go not in TotalCount[parent]:
                            TotalCount[parent].setdefault(go,{})
                            TotalCount[parent][go] = {'freq': GO[go]['freq'], 'ev': GO[go]['ev'], 'subont': GO[go]['subont']}
                        else:
                            TotalCount[parent][go]['freq'] += GO[go]['freq']
                            if TotalCount[parent][go]['ev'] == 'IEA' and GO[go]['ev'] != 'IEA':
                                TotalCount[parent][go]['ev'] = GO[go]['ev']
                            #END IF
                        #END IF
                    #END FOR
                    GO.clear()
                    status = False
                ## END IF
                line = line.strip()
                taxon = line.replace('>','').strip()
            else:
                ### take GOs and freq
                status = True
                GOval = line.split("\t")
                GO[GOval[0].strip()] = {'freq': int(GOval[1].strip()), 'ev': GOval[2].strip(), 'subont': GOval[3].strip()}
            ## END IF
        ## END FOR
    ## END WITH
    if status:
        if taxon:
            parent = ''
            ## check if it must be clustered
            father = taxon
            while True:
                if father in son_parent.keys():
                    break
                father = Taxa.get_father(father)
            parent = son_parent[father]
            if parent not in TotalCount:
                TotalCount.setdefault(parent,{})
            for go in GO:
                if go not in TotalCount[parent]:
                    TotalCount[parent].setdefault(go,{})
                    TotalCount[parent][go] = {'freq': GO[go]['freq'], 'ev': GO[go]['ev'], 'subont': GO[go]['subont']}
                else:
                    TotalCount[parent][go]['freq'] += GO[go]['freq']
                    if TotalCount[parent][go]['ev'] == 'IEA' and GO[go]['ev'] != 'IEA':
                        TotalCount[parent][go]['ev'] = GO[go]['ev']
            GO.clear()
            status = False
        ## END IF
    ## END IF
    species.close()
    with open(args['out'],'w') as out:
        for group in TotalCount:
            goList = TotalCount[group]
            out.write(f">{group}\n")
            for goTerm in sorted(goList):
                out.write(f"{goTerm}\t{goList[goTerm]['freq']}\t{goList[goTerm]['ev']}\t{goList[goTerm]['subont']}\n")
            ##END FOR
        ##END FOR
    ##END WITH
    out.close()
#END MAIN




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Takes the output in mulfasta format of the script speciesToGO.py and the hand made file taxonConstraintsDef.txt where taxonomy hierarchy is subdivided')
    parser.add_argument('-constraints', metavar='INPUT_FILE',  help='taxonConstraintsDef.txt file containing top taxa where to cluster species', required=True)
    parser.add_argument('-species', metavar='INPUT_FILE',  help='file output of speciesToGO.py where each species and its GOs are reported in mulfasta format', required=True)
    parser.add_argument('-out', metavar='OUTPUT_FILE',  help='txt file containing output', required=True)
    parser.add_argument('-merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    args = vars(parser.parse_args())
    main(args)
#END MAIN

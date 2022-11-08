#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        speciesToGO.py
# Purpose:     Parser of taxon to produce for each species the list of GO
#              frequencies found
#
# Author:      stefano
#
# Created:     05/07/2019
# Copyright:   (c) stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys, argparse, copy, re
from owlready2 import *
from taxonLibrary3 import *


def main(args):

    listTotalOfSpecies = {}
    Taxa  = Taxon(args['taxa'],args['merge'],args['names'])
    ancestors = Taxa.ancestors_full_list()
    merged = Taxa.merging()
    #parse purged .gaf file
    with open(args['gaf'],'r') as gaf:
        for line in gaf:
            line = line.strip()
            if line.startswith("!"):
                continue
            values = line.split("\t")
            go = values[4].replace(":","_")
            evCode = values[6]
            namespace = values[8]
            taxonTmp = re.search('[0-9]+',str(values[12]))
            taxon = taxonTmp.group(0)
            if taxon not in ancestors:
                if taxon in merged:
                    taxon = merged[taxon]
                #END IF
                else:
                    print("ERROR: missing taxon", taxon, "for protein:", values[1])
                    continue
            #END IF
            if taxon not in listTotalOfSpecies:
                listTotalOfSpecies.setdefault(taxon,dict())
                tmp = str()
                for parent in ancestors[taxon]:
                    tmp += parent + ','
                tmp2 = tmp[:-1]
                listTotalOfSpecies[taxon]['ancestors'] = tmp2
            #END IF
            if go not in listTotalOfSpecies[taxon]:
                listTotalOfSpecies[taxon].setdefault(go,dict())
                listTotalOfSpecies[taxon][go] = {'counter': 1,
                                                 'evidence': evCode,
                                                 'namespace': namespace
                                                }
            else:
                if evCode != 'IEA':
                    listTotalOfSpecies[taxon][go]['evidence'] = evCode
                listTotalOfSpecies[taxon][go]['counter'] += 1
            #END IF
        #END FOR
    #END WITH
    gaf.close()
    with open(args['out'],'w') as out:
        for taxonIter,values in listTotalOfSpecies.items():
            out.write(f'>{taxonIter}\n')
            for goIter in sorted(values):
                details = values[goIter]
                if goIter.startswith('GO'):
                    out.write(f'{goIter}\t{details["counter"]}\t{details["evidence"]}\t{details["namespace"]}\n')
                #END IF
            #END FOR
        #END FOR
    #END WITH
    out.close()
#END MAIN




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Takes Taxonomy nodes.dmp and goa_uniprot_wo_parents.gaf to extract for each species a list of used GO')
    parser.add_argument('-gaf', metavar='INPUT_FILE',  help='goa_uniprot_wo_parents.gaf file', required=True)
    parser.add_argument('-merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    parser.add_argument('-out', metavar='OUTPUT_FILE',  help='txt file containing output', required=True)
    args = vars(parser.parse_args())
    main(args)
#END MAIN

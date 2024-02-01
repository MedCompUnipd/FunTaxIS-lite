#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        purgeRootsInterproFromGaf.py
# Purpose:     discard roots and optionally roots
#
# Author:      Stefano
#
# Created:     01/07/2019
# Copyright:   (c) Stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys, argparse, copy
from owlready2 import *
from owlLibrary2 import *


def main(args):

    fout = open(args['gafout'], "w")
    recorded = dict()
    accid = ''
    unclassified = set()
    with open(args['unclass'], 'r') as inp:
        for rows in inp:
            row = rows.split('\t')
            unclassified.add(row[0].strip())
        #END FOR
    #END WITH
    with open (args['gaf']) as gaf:
        for line in gaf:
            if line.startswith('!'):
                continue
            #END IF
            values = line.split("\t")
            value = values[12].split('|')
            valu = value[0].split(':')
            val = valu[1].strip()
            #keep only protein annotations
            if values[11] != "protein":
                continue
            ## END IF
            #remove root ontology terms annotations
            if  values[3] == 'NOT' or values[4] == 'GO:0005575' or values[4] == 'GO:0008150' or values[4] == 'GO:0003674' or values[6] == 'ND':
                continue
            #END IF
            #remove entries from taxonomically unclassified organisms
            if val in unclassified:
                continue
            #END IF
            #remove entries from InterPro database
            if (args['no_interpro']):
                if (values[14] == 'InterPro'):
                    continue
                ##END IF
            ##END IF
            #remove entries from PANTHER database
            if (args['no_panther']):
                different_from = values[7].split('|')
                status_panther = True
                for i in different_from:
                    if 'PANTHER' not in i and 'Pfam' not in i:
                        status_panther = False
                if status_panther:
                    continue
                ##END IF
            ##END IF
            if values[1] != accid:
                if bool(recorded):
                    for info in recorded:
                        fout.write(recorded[info])
                    ## END FOR
                    recorded.clear()
                ## END IF
                accid = values[1]
                recorded[(values[4],values[6])] = line
            else:
                recorded[(values[4],values[6])] = line
            ## END IF
        ## END FOR
    ## END WITH
    if bool(recorded):
        for info in recorded:
            fout.write(recorded[info])
        ## END FOR
    ## END IF
    gaf.close()
    fout.close()
##END DEF



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Purge goa_uniprot_all.gaf from non-protein records and GO roots annotations. InterPro annotations (optional) are also discarded if -no_interpro option is used')
    parser.add_argument('-gaf', metavar='INPUT_FILE',  help='goa_uniprot_all.gaf file', required=True)
    parser.add_argument('-unclass', metavar='INPUT_FILE', help='list of unclassified and environmental samples annotations above nodes with order rank to remove', required=False)
    parser.add_argument('-gafout', metavar='OUTPUT_FILE',  help='purged GOA file output', required=True)
    parser.add_argument('-no_interpro', help='discard annotations from InterPro origin (OPTIONAL)', action='store_true', required=False)
    parser.add_argument('-no_panther', help='discard annotations from PANTHER origin (OPTIONAL)', action='store_true', required=False)
    args = vars(parser.parse_args())
    main(args)
#END MAIN

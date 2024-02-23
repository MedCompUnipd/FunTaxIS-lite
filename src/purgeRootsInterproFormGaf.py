#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        purgeRootsInterproFromGaf.py
# Purpose:     discard roots and optionally roots
#
# Author:      Stefano, Emilio
#
# Created:     01/07/2019
# Last edited: 08/02/2024
# Copyright:   (c) Stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys
import argparse
from owlready2 import *
from owlLibrary2 import *


def get_args():
    parser = argparse.ArgumentParser(description='Purge goa_uniprot_all.gaf from non-protein records and GO roots annotations. InterPro annotations (optional) are also discarded if -no_interpro option is used')

    parser.add_argument('-g', '--gaf', metavar='INPUT_FILE',  help='goa_uniprot_all.gaf file', required=True)
    parser.add_argument('-o', '--gafout', metavar='OUTPUT_FILE',  help='purged GOA file output', required=True)
    parser.add_argument('-u', '--unclass', metavar='INPUT_FILE', help='list of unclassified and environmental samples annotations above nodes with order rank to remove', required=False, default='', type=str)
    parser.add_argument('-i', '--no_interpro', help='discard annotations from InterPro origin (OPTIONAL)', action='store_true')
    parser.add_argument('-p', '--no_panther', help='discard annotations from PANTHER origin (OPTIONAL)', action='store_true')

    return vars(parser.parse_args())


def read_unclassified(unclass):
    # when present, parse the unclassified species file and save them in a set
    with open(unclass, 'r') as inp:
        unclassified = set()
        for rows in inp:
            row = rows.split('\t')
            unclassified.add(row[0].strip())

    return unclassified


if __name__ == "__main__":
    args = get_args()
    gaf_in = args['gaf']
    gaf_out = args['gafout']
    unclass = args['unclass']
    ipr = args['no_interpro']
    pan = args['no_panther']

    if not os.path.exists(gaf_in):
        print(f'Input gaf file provided does not exist! Check: {gaf_in}', file=sys.stderr)
        raise FileNotFoundError

    out_path, basename = os.path.split(gaf_out)
    if not os.path.exists(out_path):
        print(f'WARNING: output directory {out_path} does not exist and will be created', file=sys.stderr)
        os.makedirs(out_path)

    # retrieve set of unclassified species if the input is given
    unclassified = read_unclassified(unclass) if unclass else set()

    with open (gaf_in, 'r') as gaf, open(gaf_out, 'w') as fout:
        visited = set()
        current = ''
        for line in gaf:
            if line.startswith('!'):
                # skip the header
                continue
            values = line.strip().split("\t")

            #keep only protein annotations
            if values[11] != "protein":
                continue

            #remove root ontology terms annotations
            if  values[4] == 'GO:0008150' or values[4] == 'GO:0003674' or values[4] == 'GO:0005575' or values[6] == 'ND' or values[3] == 'NOT':
                continue
            # save the taxonomy assigned to the current line's annotations, accounting for the syntax of this particular field in the GAF file and remove entries from taxonomically unclassified organisms
            tax = values[12].split('|')[0].split(':')[1]
            if tax in unclassified:
                continue

            #remove entries from InterPro database
            if ipr:
                if (values[14] == 'InterPro'):
                    continue

            #remove entries from PANTHER database
            if pan:
                different_from = values[7].split('|')
                status_panther = True
                for i in different_from:
                    if 'PANTHER' not in i and 'Pfam' not in i:
                        status_panther = False
                if status_panther:
                    continue

            if values[1] != current:
                current = values[1]
                visited = set()

            if (values[4], values[6]) not in visited:
                fout.write(line)
                visited.add((values[4], values[6]))

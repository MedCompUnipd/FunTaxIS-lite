#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        speciesToGO.py
# Purpose:     Parser of taxon to produce for each species the list of GO
#              frequencies found
#
# Author:      Stefano, Emilio
#
# Created:     05/07/2019
# Last edited: 08/02/2024
# Copyright:   (c) Stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys
import argparse
import copy
import re
import os
from owlready2 import *
from taxonLibrary3 import *


def get_args():
    parser = argparse.ArgumentParser(description='Takes Taxonomy nodes.dmp and goa_uniprot_wo_parents.gaf to extract for each species a list of used GO')

    parser.add_argument('-g', '--gaf', metavar='INPUT_FILE',  help='goa_uniprot_wo_parents.gaf file', required=True)
    parser.add_argument('-m', '--merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-t', '--taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-n', '--names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    parser.add_argument('-o', '--out', metavar='OUTPUT_FILE',  help='txt file containing output', required=True)

    return vars(parser.parse_args())


def parse_purged_gaf(gaf_file, ancestors, merged):
    with open(gaf_file, 'r') as gaf:
        list_total_of_species = {}
        for line in gaf:
            if line.startswith("!"):
                # skips header
                continue

            values = line.strip().split('\t')
            # replaces : with _ for consistency with all libraries
            go = values[4].replace(":","_")

            # marks whether the annotation comes from one of such databases
            if ('PANTHER' in values[7]) or ('Pfam' in values[7]) or ('InterPro' in values[7]):
                values[7] = 'P'
            else:
                values[7] = 'N'

            # retrieving the specie associated to the current annotation
            taxon = values[12].split('|')[0].split(':')[1]

            # managing annotations from weird taxons
            if taxon not in ancestors:
                if taxon in merged:
                    taxon = merged[taxon]
                else:
                    print("ERROR: missing taxon", taxon, "for protein:", values[1])
                    continue

            if taxon not in list_total_of_species:
                list_total_of_species[taxon] = {}
                list_total_of_species[taxon]['ancestors'] = ','.join(ancestors[taxon])

            if go not in list_total_of_species[taxon]:
                list_total_of_species[taxon][go] = {'counter': 1, 'evidence': values[6], 'namespace': values[8], 'database' : values[7]}
            else:
                if values[6] != 'IEA':
                    list_total_of_species[taxon][go]['evidence'] = values[6]
                if values[7] != 'P':
                    list_total_of_species[taxon][go]['database'] = values[7]
                list_total_of_species[taxon][go]['counter'] += 1

    return list_total_of_species


if __name__ == "__main__":
    args = get_args()
    taxa = args['taxa']
    merge = args['merge']
    names = args['names']
    gaf_file = args['gaf']
    out_file = args['out']

    if not os.path.exists(taxa) or not os.path.exists(merge) or not os.path.exists(names):
        print(f'Incorrect taxonomy! check the files given as input:\n{taxa}\n{merge}\n{names}', file=sys.stderr
        raise FileNotFoundError

    if not os.path.exists(gaf_file):
        print(f'Input GAF file {gaf_file} does not exist!', file=sys.stderr)

    out_path, basename = os.path.split(out_file)
    if not os.path.exists(out_path):
        print(f'WARNING: output path {out_path} does not exist, creating it', file=sys.stderr)
        os.makedirs(out_path)

    #parse purged .gaf file
    taxa  = Taxon(taxa, merge, names)
    list_total_of_species = parse_purged_gaf(gaf_file, taxa.ancestors_full_list(), taxa.merging())

    #write output file
    with open(out_file,'w') as out:
        for taxon, values in list_total_of_species.items():
            out.write(f'>{taxon}\n')
            for go in sorted(values):
                details = values[go]
                if go.startswith('GO'):
                    out.write(f'{go}\t{details["counter"]}\t{details["evidence"]}\t{details["namespace"]}\t{details["database"]}\n')

#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        clusterTaxon.py
# Purpose:     cluster each species with its own GO into its parent taxon
#              the partitioning of the taxonomy is provided as a hand made file
#              taxonConstraintsDef.txt - requires the output of speciesToGO.py
#
# Author:      Stefano, Emilio
#
# Created:     19/07/2019
# Last edited: 02/07/2024
# Copyright:   (c) Stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------


import sys
import argparse
import copy
import re
from owlready2 import *
from taxonLibrary3 import *


def get_args():
    parser = argparse.ArgumentParser(description='Takes the output in mulfasta format of the script speciesToGO.py and the hand made file taxonConstraintsDef.txt where taxonomy hierarchy is subdivided')

    parser.add_argument('-c', '--constraints', metavar='INPUT_FILE',  help='taxonConstraintsDef.txt file containing top taxa where to cluster species', required=True)
    parser.add_argument('-s', '--species', metavar='INPUT_FILE',  help='file output of speciesToGO.py where each species and its GOs are reported in mulfasta format', required=True)
    parser.add_argument('-o', '--out', metavar='OUTPUT_FILE',  help='txt file containing output', required=True)
    parser.add_argument('-m', '--merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-t', '--taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-n', '--names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)

    return vars(parser.parse_args())


def read_constraints(constraints):
    son_parent = {}
    with open(constraints,'r') as constraints:
        for line in constraints:
            if line.startswith('#'):
                # skipping comments
                continue

            values = line.strip().split('\t')

            # son_parent[id_taxon] = taxon_name
            son_parent[values[0]] = values[1]

    return son_parent


def get_parent(taxon, son_parent, Taxa):
    ## check if it must be clustered
    # get the first ancestor belonging to constraints

    father = taxon
    while True:
        if father in son_parent.keys():
            break
        father = Taxa.get_father(father)

    # returns the taxon name
    return son_parent[father]


def update_total_count(parent, total_count, gos):
    # update the total_count dictionary accounting for the current taxon data and for its ancestor
    if parent not in total_count:
        total_count[parent] = {}
    for go in gos:
        if go not in total_count[parent]:
            total_count[parent][go] = gos[go]
        else:
            total_count[parent][go]['freq'] += gos[go]['freq']
            if total_count[parent][go]['ev'] == 'IEA' and gos[go]['ev'] != 'IEA':
                total_count[parent][go]['ev'] = gos[go]['ev']
            if total_count[parent][go]['database'] == 'P' and gos[go]['database'] == 'N':
                total_count[parent][go]['database'] = 'N'
    gos.clear()


if __name__ == "__main__":
    args = get_args()
    taxa = args['taxa']
    merge = args['merge']
    names = args['names']
    constraints = args['constraints']
    species = args['species']
    out_file = args['out']

    if not os.path.exists(taxa) or not os.path.exists(merge) or not os.path.exists(names):
        print(f'Incorrect taxonomy! check the files given as input:\n{taxa}\n{merge}\n{names}', file=sys.stderr)
        raise FileNotFoundError

    if not os.path.exists(constraints):
        print(f'Input constraints file provided {constraints} does not exist!', file=sys.stderr)
        raise FileNotFoundError

    if not os.path.exists(species):
        print(f'Input species file provided {species} does not exist!', file=sys.stderr)
        raise FileNotFoundError

    out_path, basename = os.path.split(out_file)
    if not os.path.exists(out_path):
        print(f'WARNING: output directory {out_path} does not exist, creating it', file=sys.stderr)
        os.makedirs(out_path)

    son_parent = read_constraints(constraints)
    Taxa = Taxon(taxa, merge, names)

    #parse list of reference nodes file
    total_count = {}
    gos = {}

    with open(species, 'r') as species:
        for line in species:
            if line.startswith('>'):
                # this is a header, hence a taxon id
                if gos:
                    # hence, if this is not the first taxon parsed:
                    parent = get_parent(taxon, son_parent, Taxa)
                    update_total_count(parent, total_count, gos)

                line = line.strip()
                taxon = line.replace('>','').strip()
            else:
                ### take GOs and freq
                go, freq, ev, ont, db = line.strip().split('\t')
                gos[go] = {'freq': int(freq), 'ev': ev, 'subont': ont, 'database': db}

    if gos:
        parent = get_parent(taxon, son_parent, Taxa)
        update_total_count(parent, total_count, gos)

    # finally writing to output file all gathered data
    with open(out_file, 'w') as out:
        for group in total_count:
            # group is the reference node/taxon
            go_list = total_count[group]
            out.write(f'>{group}\n')
            for go_term in sorted(go_list):
                out.write(f"{go_term}\t{go_list[go_term]['freq']}\t{go_list[go_term]['ev']}\t{go_list[go_term]['subont']}\t{go_list[go_term]['database']}\n")

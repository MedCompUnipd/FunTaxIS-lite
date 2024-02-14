#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        taxonConstraintsGOconsortium.py
# Purpose:     Extract Taxonomic Constraints from GO owl ontology
#
# Author:      Stefano, Emilio
#
# Created:     28/12/2019
# Last edited: 08/02/2024
# Copyright:   (c) Stefa 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys
import argparse
import os
from owlready2 import *
from owlLibrary2 import *
from taxonLibrary3 import *


def get_args():
    parser = argparse.ArgumentParser(description='Extract Taxonomic Constraints from GO owl ontology')

    parser.add_argument('-w', '--owl', metavar='INPUT_FILE',  help='go-plus.owl file', required=True)
    parser.add_argument('-m', '--merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-t', '--taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-n', '--names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    parser.add_argument('-o', '--out', metavar='OUTPUT_FILE',  help='output file containining taxonomic constraints of the GO consortium', required=True)

    return vars(parser.parse_args())


def update_go(mode, go_dict, go_term, constr, details, relation):
    if mode not in go_dict[go_term]:
        go_dict[go_term][mode] = {}
    go_dict[go_term][mode][constr['taxonId']] = (constr['taxonId'], constr['taxonName'], f'{go_term}\t{details["name"]}\t{details["namespace"]}\tPLACEHOLDERID\tPLACEHOLDERNAME\t{relation}')


def extract_gos(go_owl):
    go_dict = {}
    total_go = go_owl.listing()
    for go_parent in total_go:
        constraints = go_owl.go_taxon_constraints(go_parent)
        if constraints:
            if go_parent not in go_dict:
                go_dict[go_parent] = {}

            sons = go_owl.go_descendants(go_parent)
            details = go_owl.go_single_details(go_parent)
            for index in constraints:
                relation = constraints[index]["rel"].replace('_',' ').lower()
                if relation == 'in taxon':
                    continue
                if relation == 'never in taxon':
                    update_go('NEVER', go_dict, go_parent, constraints[index], details, relation)
                elif relation == 'only in taxon':
                    update_go('IN', go_dict, go_parent, constraints[index], details, relation)
                if sons:
                    for son in sons:
                        if son not in go_dict:
                            go_dict[son] = {}
                        if relation == 'never in taxon':
                            update_go('NEVER', go_dict, son, constraints[index], sons[son], relation)
                        elif relation == 'only in taxon':
                            update_go('IN', go_dict, son, constraints[index], sons[son], relation)

    return go_dict


def get_purged(mode, go_dict, go, full_list, ancestors):
    list_purged, list_iter_taxa = set(), set()

    if mode in go_dict[go]:
        ### discard redundancy
        for taxon_id in go_dict[go][mode]:
            taxon_name = go_dict[go][mode][taxon_id][1]
            if 'NCBITaxon_Union_' in taxon_id:
                list_of_names = taxon_name.split(' or ')
                for tax_name in list_of_names:
                    if tax_name.strip() in full_list:
                        list_of_ids = full_list[tax_name.strip()]
                        for i in list_of_ids:
                            if i == '629395':
                                continue

                            list_iter_taxa.add((i, tax_name, taxon_id))

                    else:
                        print(f'{tax_name.strip()}  NOT FOUND')
                        sys.exit()
            else:
                list_iter_taxa.add((taxon_id.split('_')[1].strip(), taxon_name, taxon_id))

    return list_purged, list_iter_taxa


def update_purged(list_iter_taxa, ancestors, list_purged):
    for tax in list_iter_taxa:
        try:
            parents = ancestors[tax[0]]
            for anc in parents:
                res_taxon = [i for i in list_iter_taxa if anc in i]
                if res_taxon:
                    list_purged.add(res_taxon[0])
                    break
        except:
            list_purged.add(tax)

    return list_purged


def write_taxon(list_iter_taxa, list_purged, go_dict, go, mode, out):
    for tax in list_iter_taxa:
        if tax not in list_purged:
            first_replace = go_dict[go][mode][tax[2]][2].replace("PLACEHOLDERID", tax[0])
            second_replace = first_replace.replace("PLACEHOLDERNAME", tax[1])
            out.write(second_replace + "\n")


if __name__ == '__main__':
    args = get_args()
    taxa, merge, names = args['taxa'], args['merge'], args['names']
    out_file = args['out']
    owl_file = args['owl']

    if not os.path.exists(taxa) or not os.path.exists(merge) or not os.path.exists(names):
        print(f'Input files for Taxonomy Parsing missing, are you sure about:\n{taxa}\n{merge}\n{names}', file=sys.stderr)
        raise FileNotFoundError

    if not os.path.exists(owl_file):
        print('Input OWL file provided {owl_file} does not exist!', file=sys.stderr)

    out_path, basename = os.path.split(out_file)
    if not os.path.exists(out_path):
        print(f'WARNING: output directory {out_path} does not exist, creating it', file=sys.stderr)
        os.makedirs(out_path)

    taxa  = Taxon(taxa, merge, names)
    full_list = taxa.get_names_ids_map()
    ancestors = taxa.ancestors_full_list()

    go_dict = extract_gos(GoOwl(owl_file, "http://purl.obolibrary.org/obo/"))

    with open(out_file, 'w') as out:
        for go in sorted(go_dict.keys()):
            if 'IN' in go_dict[go]:
                mode = 'IN'
            elif 'NEVER' in go_dict[go]:
                mode = 'NEVER'
            else:
                continue

            list_purged, list_iter_taxa = get_purged(mode, go_dict, go, full_list, ancestors)
            list_purged = update_purged(list_iter_taxa, ancestors, list_purged)
            write_taxon(list_iter_taxa, list_purged, go_dict, go, mode, out)

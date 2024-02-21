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


def update_relation(go_dict, mode, go_term, constraints, info):
    if mode not in go_dict[go_term]:
        go_dict[go_term][mode] = {}
    t_id = constraints[index]["taxonId"]
    t_name = constraints[index]["taxonName"]
    placeholder = f'{go_term}\t{info["name"]}\t{info["namespace"]}\tPLACEHOLDERID\tPLACEHOLDERNAME\t{relation}'
    go_dict[go_term][mode][t_id] = (t_id, t_name, placeholder)


def get_taxa_list(check_go, full_list, mode):
    list_iter_taxa = set()
    for taxon_id in check_go[mode]:
        taxon_name = check_go[mode][taxon_id][1]
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
                    print(tax_name.strip()," NOT FOUND")
                    sys.exit()
        else:
            list_iter_taxa.add((taxon_id.split('_')[1].strip(), taxon_name, taxon_id))

    return list_iter_taxa


def get_purged(list_iter_taxa, ancestors, mode):
    list_purged = set()
    for tax in list_iter_taxa:
        try:
            parents = ancestors[tax[0]]
            for anc in parents:
                res_taxon = [i for i in list_iter_taxa if anc in i]
                if bool(res_taxon):
                    to_purge = tax if mode == 'NEVER' else res_taxon[0]
                    list_purged.add(to_purge)
                    break
        except:
            list_purged.add(tax)

    return list_purged


def filter_and_write(go_write, full_list, rel, ancestors, out):
    list_iter_taxa = get_taxa_list(go_write, full_list, rel) if rel in go_write else set()
    list_purged = get_purged(list_iter_taxa, ancestors, rel)
    for tax in list_iter_taxa:
        if tax not in list_purged:
            first_replace = go_write[rel][tax[2]][2].replace("PLACEHOLDERID", tax[0])
            second_replace = first_replace.replace("PLACEHOLDERNAME", tax[1])
            out.write(second_replace + "\n")


if __name__ == '__main__':
    args = get_args()

    taxa  = Taxon(args['taxa'],args['merge'],args['names'])
    full_list = taxa.get_names_ids_map()
    ancestors = taxa.ancestors_full_list()

    go_dict = {}
    go_owl = GoOwl(args['owl'], "http://purl.obolibrary.org/obo/")
    total_go = go_owl.listing()
    for go_parent in total_go:
        constraints = go_owl.go_taxon_constraints(go_parent)
        if bool(constraints):
            if go_parent not in go_dict:
                go_dict[go_parent] = {}
            sons = go_owl.go_descendants(go_parent)
            details = go_owl.go_single_details(go_parent)
            for index in constraints:
                relation = constraints[index]["rel"].replace('_',' ').lower()
                if relation == 'in taxon':
                    continue
                if relation == 'never in taxon':
                    update_relation(go_dict, 'NEVER', go_parent, constraints, details)
                elif relation == 'only in taxon':
                    update_relation(go_dict, 'IN', go_parent, constraints, details)
                if bool(sons):
                    for go_son in sons:
                        if go_son not in go_dict:
                            go_dict[go_son] = {}
                        if relation == 'never in taxon':
                            update_relation(go_dict, 'NEVER', go_son, constraints, sons[go_son])
                        elif relation == 'only in taxon':
                            update_relation(go_dict, 'IN', go_son, constraints, sons[go_son])

    with open(args['out'], 'w') as out:
        for go_term in sorted(go_dict.keys()):
            filter_and_write(go_dict[go_term], full_list, 'IN', ancestors, out)
            filter_and_write(go_dict[go_term], full_list, 'NEVER', ancestors, out)

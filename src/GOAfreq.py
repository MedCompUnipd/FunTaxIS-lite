#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        create
# Purpose:     output file containining statistics: 1) GO cumulated
#              frequencies in GOA, 2) GO occurrences
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
import copy
import os
from owlready2 import *
from owlLibrary2 import *


def get_args():
    parser = argparse.ArgumentParser(description='Create GO cumulated frequencies in GOA and GO occurrences in GOA')

    parser.add_argument('-w', '--owl', metavar='INPUT_FILE',  help='go-plus.owl file', required=True)
    parser.add_argument('-g', '--gaf_wo', metavar='INPUT_FILE',  help='goa_wo_parents.gaf file', required=True)
    parser.add_argument('-o', '--out_freq', metavar='OUTPUT_FILE',  help='output file containining statistics: 1) GO cumulated frequencies in GOA, 2) GO occurrences', required=True)

    return vars(parser.parse_args())


def parse_gaf(gaf_file):
    list_go = {}
    with open(gaf_file, 'r') as gaf:
        for line in gaf:
            if line.startswith('!'):
                continue
            values = line.strip().split('\t')
            # replacing : with _ for compatibility with all libraries
            goiter = values[4].replace(':','_')
            if goiter not in list_go:
                list_go[goiter] = 1
            else:
                list_go[goiter] += 1

    return list_go


def write_gaf(out_file, go_owl, list_go):
    prior_cumul  = go_owl.cumulative_freq_prior()
    corpus_cumul = go_owl.cumulative_freq_corpus(list_go)
    prior_cumul_ml  = go_owl.cumulative_freq_prior_ml()
    corpus_cumul_ml = go_owl.cumulative_freq_corpus_ml(list_go)

    with open(out_file, "w") as gafout:
        gafout.write('#go\tdescr\tsubOnt\tfreq\tCorpus_Cumul_Hierarchy\tPrior_Cumul_Hierarchy\tCorpus_Cumul_Graph\tPrior_Cumul_Graph\n')
        for go in prior_cumul:
            freq = 0
            if go in list_go:
                freq = list_go[go]

            details = go_owl.go_single_details(go)
            gafout.write(f'{go}\t{details["name"]}\t{details["namespace"]}\t{freq}\t{corpus_cumul[go]}\t{prior_cumul[go]}\t{corpus_cumul_ml[go]}\t{prior_cumul_ml[go]}\n')


if __name__ == '__main__':
    args = get_args()
    gaf_file = args['gaf_wo']
    owl_file = args['owl']
    out_file = args['out_freq']

    if not os.path.exists(gaf_file):
        print(f'Input GAF file provided {gaf_file} does not exist!', file=sys.stderr)
        raise FileNotFoundError

    if not os.path.exists(owl_file):
        print(f'Input OWL file provided {owl_file} does not exist!', file=sys.stderr)
        raise FileNotFoundError

    out_path, basename = os.path.split(out_file)
    if not os.path.exists(out_path):
        print(f'WARNING: output directory {out_path} does not exist and will be created', file=sys.stderr)
        os.makedirs(out_path)

    #parse purged .gaf file
    list_go = parse_gaf(gaf_file)

    #obtain cumulative frequencies data for each GO term in GOA
    go_owl = GoOwl(owl_file, "http://purl.obolibrary.org/obo/")

    #write output file
    write_gaf(out_file, go_owl, list_go)

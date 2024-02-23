#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        speciesFreqCumul
# Purpose:     output file containining statistics GOfreq for each taxon category
#              generated by the script clusterTaxon.py
#
# Author:      Stefano, Emilio
#
# Created:     21/08/2019
# Last edited: 08/02/2024
# Copyright:   (c) Stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys
import argparse
import os
from owlready2 import *
from owlLibrary2 import *


def get_args():
    parser = argparse.ArgumentParser(description='Create GO cumulated frequencies in GOA and GO occurrences in GOA')

    parser.add_argument('-i', '--owl', metavar='INPUT_FILE',  help='go-plus.owl file', required=True)
    parser.add_argument('-f', '--freq', metavar='INPUT_FILE',  help='file containing GO freq generated by the script clusterTaxon.py', required=True)
    parser.add_argument('-o', '--out_freq', metavar='OUTPUT_FILE',  help='output file containining cumulated freq for each taxa subdivision', required=True)

    return vars(parser.parse_args())


def write_info(taxon, go_owl, gos, gop, out):
    corpus_cumul = go_owl.cumulative_freq_corpus_ml(gos)
    out.write(f'>{taxon}\n')
    for go in sorted(corpus_cumul):
        freq = gos[go] if go in gos else 0
        pant = gop[go] if go in gop else'N'

        details = go_owl.go_single_details(go)
        out.write(f'{go}\t{corpus_cumul[go]}\t{freq}\t{details["namespace"]}\t{details["name"]}\t{pant}\n')

    gos.clear()
    gop.clear()


if __name__ == '__main__':
    args = get_args()
    owl_file = args['owl']
    freq_file = args['freq']
    out_file = args['out_freq']

    if not os.path.exists(owl_file):
        print(f'Input OWL file provided {owl_file} does not exist!', file=sys.stderr)
        raise FileNotFoundError

    if not os.path.exists(freq_file):
        print(f'Input FREQ file provided {freq_file} does not exist!', file=sys.stderr)
        raise FileNotFoundError

    out_path, basename = os.path.split(out_file)
    if not os.path.exists(out_path):
        print(f'WARNING: output path {out_path} does not exist, creating it')
        os.makedirs(out_path)

    go_owl = GoOwl(owl_file, "http://purl.obolibrary.org/obo/")

    with open(out_file, 'w') as out, open(freq_file, 'r') as cluster:
        gos, gop = {}, {}
        taxon = ''
        for line in cluster:
            if line.startswith('>'):
                if gos:
                    write_info(taxon, go_owl, gos, gop, out)
                taxon = line.strip().lstrip('>')
            else:
                values = line.strip().split('\t')
                # values[0] = go_term / values[1] = go_freq / values[4] = go_db
                gos[values[0]] = int(values[1])
                gop[values[0]] = values[4]

        if gos:
            write_info(taxon, go_owl, gos, gop, out)

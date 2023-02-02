#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        create
# Purpose:     output file containining statistics: 1) GO cumulated
#              frequencies in GOA, 2) GO occurrences
#
# Author:      stefa
#
# Created:     01/07/2019
# Copyright:   (c) stefa 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys, argparse, copy
from owlready2 import *
from owlLibrary2 import *


def main(args):

    listGO = {}

    #parse purged .gaf file
    with open(args['gaf_wo'], "r") as gaf:
        for line in gaf:
            values = line.split("\t")
            goiter = values[4].replace(":","_")
            if goiter not in listGO:
                listGO[goiter] = 1
            else:
                listGO[goiter] += 1
            #END IF
        #END FOR
    #END WITH
    gaf.close()

    #obtain cumulative frequencies data for each GO term in GOA
    goowl = GoOwl(args['owl'],"http://purl.obolibrary.org/obo/")
    priorCumul  = goowl.cumulative_freq_prior()
    corpusCumul = goowl.cumulative_freq_corpus(listGO)
    priorCumulML  = goowl.cumulative_freq_prior_ml()
    corpusCumulML = goowl.cumulative_freq_corpus_ml(listGO)
    with open(args['out_freq'], "w") as gafout:
        gafout.write(f'#go\tdescr\tsubOnt\tfreq\tCorpus_Cumul_Hierarchy\tPrior_Cumul_Hierarchy\tCorpus_Cumul_Graph\tPrior_Cumul_Graph\n')
        for go in priorCumul:
            freq = 0
            if go in listGO:
                freq = listGO[go]
            #END IF
            details = goowl.go_single_details(go)
            gafout.write(f'{go}\t{details["name"]}\t{details["namespace"]}\t{freq}\t{corpusCumul[go]}\t{priorCumul[go]}\t{corpusCumulML[go]}\t{priorCumulML[go]}\n')
        #END FOR
    #END WITH
    gafout.close()
#END MAIN




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create GO cumulated frequencies in GOA and GO occurrences in GOA')
    parser.add_argument('-owl', metavar='INPUT_FILE',  help='go-plus.owl file', required=True)
    parser.add_argument('-gaf_wo', metavar='INPUT_FILE',  help='goa_wo_parents.gaf file', required=True)
    parser.add_argument('-out_freq', metavar='OUTPUT_FILE',  help='output file containining statistics: 1) GO cumulated frequencies in GOA, 2) GO occurrences', required=True)
    args = vars(parser.parse_args())
    main(args)

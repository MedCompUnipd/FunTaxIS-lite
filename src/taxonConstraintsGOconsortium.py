#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        taxonConstraintsGOconsortium.py
# Purpose:     Extract Taxonomic Constraints from GO owl ontology
#
# Author:      stefa
#
# Created:     28/12/2019
# Copyright:   (c) stefa 2019
# Licence:     GPL
#-------------------------------------------------------------------------------

import sys, argparse, copy, re
from owlready2 import *
from owlLibrary2 import *
from taxonLibrary3 import *


def main(args):

    ##    Union Taxa currently used in GO taxon constraints
    ##    NCBITaxon_Union_0000004 Prokaryota
    ##    NCBITaxon_Union_0000006 Viridiplantae or Archaea or Bacteria
    ##    NCBITaxon_Union_0000007 Viridiplantae or Bacteria or Euglenozoa
    ##    NCBITaxon_Union_0000020 Fungi or Bacteria
    ##    NCBITaxon_Union_0000022 Fungi or Dictyostelium
    ##    NCBITaxon_Union_0000023 Fungi or Bacteria or Archaea
    ##    NCBITaxon_Union_0000031 Stramenopiles or Cryptophyta

    Taxa  = Taxon(args['taxa'],args['merge'],args['names'])
    fullList = Taxa.get_names_ids_map()
    ancestors = Taxa.ancestors_full_list()

    with open(args['out_constraints'],'w') as out:

        goDict = dict()

        goowl = GoOwl(args['owl'],"http://purl.obolibrary.org/obo/")
        totalGO = goowl.listing()
        for goParent in totalGO:
            constraints = goowl.go_taxon_constraints(goParent)
            if bool(constraints):
                if goParent not in goDict:
                    goDict[goParent] = dict()
                ##END IF
                sons = goowl.go_descendants(goParent)
                details = goowl.go_single_details(goParent)
                for index in constraints:
                    if constraints[index]["rel"] == 'in taxon':
                        continue
                    if constraints[index]["rel"] == 'Never in taxon':
                        if 'NEVER' not in goDict[goParent]:
                            goDict[goParent]['NEVER'] = dict()
                        goDict[goParent]['NEVER'][constraints[index]["taxonId"]] = (constraints[index]["taxonId"],constraints[index]["taxonName"], goParent + "\t" + details["name"] + "\t" + details["namespace"] + "\tPLACEHOLDERID\tPLACEHOLDERNAME\t" + constraints[index]["rel"])
                    elif constraints[index]["rel"] == 'only in taxon':
                        #### EVEN FOR IN do exactly what you do for NEVER than only one for that particular GO will be kept and is that with lower taxon
                        #### Union must be kept as is but when split if there is an ONLY IN with a species/class lower than one of the members of Union this will
                        #### replace it IMPORTANT .... taxa in Union are not in relationship father -> son so only in can survive for more than one.
                        if 'IN' not in goDict[goParent]:
                            goDict[goParent]['IN'] = dict()
                        goDict[goParent]['IN'][constraints[index]["taxonId"]] = (constraints[index]["taxonId"],constraints[index]["taxonName"], goParent + "\t" + details["name"] + "\t" + details["namespace"] + "\tPLACEHOLDERID\tPLACEHOLDERNAME\t" + constraints[index]["rel"])
                    if bool(sons):
                        for son in sons:
                            if son not in goDict:
                                goDict[son] = dict()
                            if constraints[index]["rel"] == 'Never in taxon':
                                if 'NEVER' not in goDict[son]:
                                    goDict[son]['NEVER'] = dict()
                                goDict[son]['NEVER'][constraints[index]["taxonId"]] = (constraints[index]["taxonId"],constraints[index]["taxonName"], son + "\t" + sons[son]["name"] + "\t" + sons[son]["namespace"] + "\tPLACEHOLDERID\tPLACEHOLDERNAME\t" + constraints[index]["rel"])
                            elif constraints[index]["rel"] == 'only in taxon':
                                if 'IN' not in goDict[son]:
                                    goDict[son]['IN'] = dict()
                                goDict[son]['IN'][constraints[index]["taxonId"]] = (constraints[index]["taxonId"],constraints[index]["taxonName"], son + "\t" + sons[son]["name"] + "\t" + sons[son]["namespace"] + "\tPLACEHOLDERID\tPLACEHOLDERNAME\t" + constraints[index]["rel"])
                            ##END IF
                        ##END FOR
                    ##END IF
                ##END FOR
            ###END IF
        ###END FOR

        for go in sorted(goDict.keys()):

            listPurged = set()
            listIterTaxa = set()

            if 'IN' in goDict[go]:
                ### discard redundancy
                for taxonId in goDict[go]['IN']:
                    taxonName = goDict[go]['IN'][taxonId][1]
                    if 'NCBITaxon_Union_' in taxonId:
                        listOfNames = taxonName.split(' or ')
                        for taxName in listOfNames:
                            if taxName.strip() in fullList:
                                listOfIds = fullList[taxName.strip()]
                                for i in listOfIds:
                                    if i == '629395':
                                        continue
                                    ##END IF
                                    listIterTaxa.add((i,taxName,taxonId))
                                ##END FOR
                            else:
                                print(taxName.strip()," NOT FOUND")
                                sys.exit()
                            ##END IF
                        ##END FOR
                    ##END IF
                    else:
                        listIterTaxa.add((taxonId.split('_')[1].strip(),taxonName,taxonId))
                    ##END IF
                ##END FOR
            ##END IF

            for tax in listIterTaxa:
                try:
                    parents = ancestors[tax[0]]
                    for anc in parents:
                        resTaxon = [i for i in listIterTaxa if anc in i]
                        ## or resTaxon = [i for i in listIterTaxa if anc == list(i)[0]] to serach only in index 0 of the tuple
                        ## it returns a list of hits
                        if bool(resTaxon):
                            listPurged.add(resTaxon[0])
                            break
                        ##END IF
                    ##END FOR
                except:
                    listPurged.add(tax)
                ##END TRY
            ##END FOR

            for tax in listIterTaxa:
                if tax not in listPurged:
                    firstreplace = goDict[go]['IN'][tax[2]][2].replace("PLACEHOLDERID", tax[0])
                    secondReplace = firstreplace.replace("PLACEHOLDERNAME", tax[1])
                    out.write(secondReplace + "\n")
                ##END IF
            ##END FOR

            listPurged = set()
            listIterTaxa = set()
            if 'NEVER' in goDict[go]:
                ### discard redundancy
                for taxonId in goDict[go]['NEVER']:
                    taxonName = goDict[go]['NEVER'][taxonId][1]
                    if 'NCBITaxon_Union_' in taxonId:
                        listOfNames = taxonName.split(' or ')
                        for taxName in listOfNames:
                            if taxName.strip() in fullList:
                                listOfIds = fullList[taxName.strip()]
                                for i in listOfIds:
                                    if i == '629395':
                                        continue
                                    ##END IF
                                    listIterTaxa.add((i,taxName,taxonId))
                                ##END FOR
                            else:
                                print(taxName.strip()," NOT FOUND")
                                sys.exit()
                            ##END IF
                        ##END FOR
                    ##END IF
                    else:
                        listIterTaxa.add((taxonId.split('_')[1].strip(),taxonName,taxonId))
                    ##END IF
                ##END FOR
            ##END IF
            for tax in listIterTaxa:
                try:
                    parents = ancestors[tax[0]]
                    for anc in parents:
                        if bool([i for i in listIterTaxa if anc in i]):
                        #if anc in listIterTaxa:
                            listPurged.add(tax)
                            break
                        ##END IF
                    ##END FOR
                except:
                    listPurged.add(tax)
                ##END TRY
            ##END FOR
            for tax in listIterTaxa:
                if tax not in listPurged:
                    firstreplace = goDict[go]['NEVER'][tax[2]][2].replace("PLACEHOLDERID", tax[0])
                    secondReplace = firstreplace.replace("PLACEHOLDERNAME", tax[1])
                    out.write(secondReplace + "\n")
                ##END IF
            ##END FOR
        ##END FOR
    ##END WITH
#END MAIN

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract Taxonomic Constraints from GO owl ontology')
    parser.add_argument('-owl', metavar='INPUT_FILE',  help='go-plus.owl file', required=True)
    parser.add_argument('-merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    parser.add_argument('-out_constraints', metavar='OUTPUT_FILE',  help='output file containining taxonomic constraints of the GO consortium', required=True)
    args = vars(parser.parse_args())
    main(args)
##END IF









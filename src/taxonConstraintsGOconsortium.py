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
            #if len(constraints) > 0:
                #print(goParent)
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








###################################################################################################################################################################
###################################################################################################################################################################
##
##            if 'IN' in goDict[go]:
##                taxonId = goDict[go]['IN'][0]
##                taxonName = goDict[go]['IN'][1]
##                if 'NCBITaxon_Union_' in taxonId:
##                    listOfNames = taxonName.split(' or ')
##                    for taxName in listOfNames:
##                        if taxName.strip() in fullList:
##                            listOfIds = fullList[taxName.strip()]
##                        else:
##                            print(taxName.strip()," NOT FOUND")
##                            sys.exit()
##                        ##END IF
##                        for taxId in listOfIds:
##                            # workaround for a misnomer "Bacteria" referred to <walking sticks> Bacteria Latreille
##                            if (taxName.strip() == 'Bacteria' or taxName.strip() == 'bacteria') and taxId == '629395':
##                                continue
##                            ##END IF
##                            firstreplace = goDict[go]['IN'][2].replace("PLACEHOLDERID", taxId)
##                            secondReplace = firstreplace.replace("PLACEHOLDERNAME", taxName)
##                            print(secondReplace)
##                        ##END FOR
##                    ##END FOR
##                ##END IF
##                else:
##                    taxonReplace = taxonId.split('_')[1].strip()
##                    firstreplace = goDict[go]['IN'][2].replace("PLACEHOLDERID", taxonReplace)
##                    secondReplace = firstreplace.replace("PLACEHOLDERNAME", taxonName)
##                    print(secondReplace)
##                ##END IF
##            ##END IF
##                for taxonId in goDict[go]['NEVER']:
##                    if 'NCBITaxon_Union_' in taxonId:
####                        taxonId2 = goDict[go]['NEVER'][taxonId][0]
##                        taxonName = goDict[go]['NEVER'][taxonId][0]
##                        listOfNames = taxonName.split(' or ')
##                        for taxName in listOfNames:
##                            if taxName.strip() in fullList:
##                                listOfIds = fullList[taxName.strip()]
##                            else:
##                                print(taxName.strip()," NOT FOUND")
##                                sys.exit()
##                            ##END IF
##                            for taxId in listOfIds:
##                                # workaround for a misnomer "Bacteria" referred to <walking sticks> Bacteria Latreille
##                                if (taxName.strip() == 'Bacteria' or taxName.strip() == 'bacteria') and taxId == '629395':
##                                    continue
##                                ##END IF
##                                firstreplace = goDict[go]['NEVER'][taxonId][2].replace("PLACEHOLDERID", taxId)
##                                secondReplace = goDict[go]['NEVER'][taxonId][2].replace("PLACEHOLDERNAME", taxName)
##                                print(secondReplace)
##                            ##END FOR
##                        ##END FOR
##                    else:
##                        taxonReplace = taxonId.split('_')[1].strip()
##                        firstreplace = goDict[go]['NEVER'][taxonId][2].replace("PLACEHOLDERID", taxonReplace)
##                        secondReplace = goDict[go]['NEVER'][taxonId][2].replace("PLACEHOLDERNAME", taxonName)
##                        print(secondReplace)
##                    ##END IF
##                ##END FOR
##            ##END IF
##
##
##
##
##                    print(goDict[go]['NEVER'][taxon])
##
##
##
##
##
##
##
##
##        for go in totalGO:
##            constraints = goowl.goTaxonConstraints(go)
##            if bool(constraints):
##                for index in constraints:
##                    if constraints[index]["rel"] == 'in taxon':
##                        continue
##                    goDict[go]['IN'] = dict()
##                    goDict[go]['NEVER'] = dict()
##                    if 'NCBITaxon_Union_' in constraints[index]["taxonId"]:
##                        listOfNames = constraints[index]["taxonName"].split(' or ')
##                        for taxName in listOfNames:
##                            if taxName.strip() in fullList:
##                                listOfIds = fullList[taxName.strip()]
##                            else:
##                                print(taxName.strip()," NOT FOUND")
##                                sys.exit()
##                            END IF
##                            for taxId in listOfIds:
##                                ### workaround for a misnomer "Bacteria" referred to <walking sticks> Bacteria Latreille
##                                if (taxName.strip() == 'Bacteria' or taxName.strip() == 'bacteria') and taxId == '629395':
##                                    continue
##                                ##END IF
##                                if constraints[index]["rel"] == 'Never in taxon':
##                                    goDict[go]['NEVER'][taxId] = go + "\t" + details["name"] + "\t" + details["namespace"] + "\t" + taxId + "\t" + constraints[index]["taxonName"] + "\t" + constraints[index]["rel"]
##                                elif constraints[index]["rel"] == 'only in taxon':
##                                    goDict[go]['IN'][taxId] = go + "\t" + details["name"] + "\t" + details["namespace"] + "\t" + taxId + "\t" + constraints[index]["taxonName"] + "\t" + constraints[index]["rel"]
##                                ##END IF
##                            ##END FOR
##                        ##END FOR
##                    else:
##                        if constraints[index]["rel"] == 'Never in taxon':
##                            goDict[go]['NEVER'][constraints[index]["taxonId"].split("_")[1]] = go + "\t" + details["name"] + "\t" + details["namespace"] + "\t" + constraints[index]["taxonId"].split("_")[1] + "\t" + constraints[index]["taxonName"] + "\t" + constraints[index]["rel"]
##                        elif constraints[index]["rel"] == 'only in taxon':
##                            goDict[go]['IN'][constraints[index]["taxonId"].split("_")[1]] = go + "\t" + details["name"] + "\t" + details["namespace"] + "\t" + constraints[index]["taxonId"].split("_")[1] + "\t" + constraints[index]["taxonName"] + "\t" + constraints[index]["rel"]
##                        ##END IF
##                    ##END IF
##                ##END FOR
##            ##END IF
##        ##END FOR
##        discard = dict()
##        for goParent in goDict:
##            sons = goowl.go_descendants(goParent)
##            details = goowl.go_single_details(goParent)
##            for goSon in sons: ### consider the children terms of the goParent
##                if goSon in goDict: #### see if they have other constraints
##                    ### do some consideration
##                    #status = False
##                    for taxonSon in goDict[goSon]['IN']:           ### look at the taxa of these children and ...
##                        for taxonParent in goDict[goParent]['IN']: ### compare with the taxa of the parent
##                            if taxonParent in ancestors[taxonSon]: ### this means that if a taxonParent is higher in hierarchy to that of a particulara taxonSon
##                                status = True                      ### hence in case of "only in taxon" I must discard the constraint for that particular taxon and GO
##                                continue                           ### for this sonGO I MUST NOT inherit from the taxonParent
##                                discard[goSon]['IN'] = goParent ##[taxonSon] = False
##                            ##END IF
##                        ##END FOR
##                    ##END FOR
##                    if status:
##                        discard[goSon]['IN'][taxonSon]
##
##                else:
##                    ###replicate the constraints
##                out.write(f'{son}\t{sons[son]["name"]}\t{sons[son]["namespace"]}\t{taxId}\t{constraints[index]["taxonName"]}\t{constraints[index]["rel"]}\n')
##            ##END FOR
##
##
##
##
##                sons = goowl.go_descendants(go)
##                details = goowl.go_single_details(go)
##                for index in constraints:
##                    if 'NCBITaxon_Union_' in constraints[index]["taxonId"]:
##                        listOfNames = constraints[index]["taxonName"].split(' or ')
##                        for taxName in listOfNames:
##                            if taxName.strip() in fullList:
##                                listOfIds = fullList[taxName.strip()]
##                            else:
##                                print(taxName.strip()," NOT FOUND")
##                                sys.exit()
##                            for taxId in listOfIds:
##                                ### workaround for a misnomer "Bacteria" referred to <walking sticks> Bacteria Latreille
##                                if (taxName.strip() == 'Bacteria' or taxName.strip() == 'bacteria') and taxId == '629395':
##                                    continue
##                                ##END IF
##                                out.write(f'{go}\t{details["name"]}\t{details["namespace"]}\t{taxId}\t{constraints[index]["taxonName"]}\t{constraints[index]["rel"]}\n')
##                                if bool(sons):
##                                    for son in sons:
##                                        out.write(f'{son}\t{sons[son]["name"]}\t{sons[son]["namespace"]}\t{taxId}\t{constraints[index]["taxonName"]}\t{constraints[index]["rel"]}\n')
##                                    ##END FOR
##                                ##END IF
##                                if constraints[index]["rel"] == 'only in taxon':
##                                    out.write(f'{go}\t{details["name"]}\t{details["namespace"]}\tNOT {taxId}\tNOT {constraints[index]["taxonName"]}\tNever in taxon\n')
##                                    if bool(sons):
##                                        for son in sons:
##                                            out.write(f'{son}\t{sons[son]["name"]}\t{sons[son]["namespace"]}\tNOT {taxId}\tNOT {constraints[index]["taxonName"]}\tNever in taxon\n')
##                                        ##END FOR
##                                    ##END IF
##                                ##END IF
##                            ##END FOR
##                        ##END FOR
##                    else:
##                        out.write(f'{go}\t{details["name"]}\t{details["namespace"]}\t{constraints[index]["taxonId"].split("_")[1]}\t{constraints[index]["taxonName"]}\t{constraints[index]["rel"]}\n')
##                        if bool(sons):
##                            for son in sons:
##                                out.write(f'{son}\t{sons[son]["name"]}\t{sons[son]["namespace"]}\t{constraints[index]["taxonId"].split("_")[1]}\t{constraints[index]["taxonName"]}\t{constraints[index]["rel"]}\n')
##                            ##END FOR
##                        ##END IF
##                        if constraints[index]["rel"] == 'only in taxon':
##                            out.write(f'{go}\t{details["name"]}\t{details["namespace"]}\tNOT {constraints[index]["taxonId"].split("_")[1]}\tNOT {constraints[index]["taxonName"]}\tNever in taxon\n')
##                            if bool(sons):
##                                for son in sons:
##                                    out.write(f'{son}\t{sons[son]["name"]}\t{sons[son]["namespace"]}\tNOT {constraints[index]["taxonId"].split("_")[1]}\tNOT {constraints[index]["taxonName"]}\tNever in taxon\n')
##                                ##END FOR
##                            ##END IF
##                        ##END IF
##                    ##END IF
##                ##END FOR
##            ##END IF
##        ##END FOR
##    ##END WITH
##    out.close()
##    #### create a NR taxon constraint
##    with open(args['out_constraints'],'r') as const:
##        goDict = dict()
##        for line in const:
##            line = line.strip()
##            fields = line.split('\t')
##            if fields[0] not in goDict:
##                goDict[fields[0]] = dict()
##                goDict[fields[0]]['IN'] = dict()
##                goDict[fields[0]]['NOT'] = dict()
##            if re.search('NOT',fields[3]):
####                if not goDict[fields[0]]['NOT']:
####                    goDict[fields[0]]['NOT'] = dict()
##                goDict[fields[0]]['NOT'][fields[3].split(' ')[1].strip()] = line
##            else:
####                if not goDict[fields[0]]['IN']:
####                    goDict[fields[0]]['IN'] = dict()
##                goDict[fields[0]]['IN'][fields[3].strip()] = line
##        ##END FOR
##    ##END WITH
##    NRconst = dict()
##    const.close()
##    for go in goDict:
####        if go == 'GO_0009556':
##
##            if 'NOT' in goDict[go]: #### these are ONLY IN TAXON hence NEVER IN for all the rest
####                print('inizio NOT',goDict[go]['NOT'],"\n\n")
##                for taxon in goDict[go]['NOT']:
##                    parents = ancestors[taxon]
##                    NRconst[taxon] = parents
##                for taxon in NRconst:
##                    for parent in NRconst[taxon]:
##                        if parent in goDict[go]['NOT']:
##                            ## discard because there is already a parent taxon included
####                            print(f'AAAAAAAAAAAAAAAA {parent} {go} {taxon} {goDict[go]["NOT"]}\n')
####                            print (f'\t{go}\n\t{goDict[go]["NOT"]}\n\t{taxon}\n\t{goDict[go]["NOT"][taxon]}\n\n\n')
##                            del goDict[go]['NOT'][taxon]
##                        ##END IF
##                    ##END FOR
##                ##END FOR
##                NRconst.clear()
##            elif 'IN' in goDict[go]:  #### these are ONLY IN TAXON hence NEVER IN the rest
##                print('inizio IN',goDict[go]['IN'],"\n\n")
##                for taxon in goDict[go]['IN']:
##                    parents = ancestors[taxon]
##                    NRconst[taxon] = parents
##                for taxon in NRconst:
##                    for parent in NRconst[taxon]:
##                        if parent in goDict[go]['NOT']:
##                            ## discard because there is already a parent taxon included
##                            del goDict[go]['IN'][taxon]
##                        ##END IF
##                    ##END FOR
##                ##END FOR
##            ##END IF
##    ##END FOR
##    for i in sorted (goDict.keys()):
##        if 'NOT' in goDict[i]:
##            for a in goDict[i]['NOT']:
##                print(goDict[i]['NOT'][a])
##            ##END FOR
##        ##END IF
##    ##END FOR
##    for i in sorted (goDict.keys()):
##        if 'IN' in goDict[i]:
##            for a in goDict[i]['IN']:
##                print(goDict[i]['IN'][a])
##            ##END FOR
##        ##END IF
##    ##END FOR








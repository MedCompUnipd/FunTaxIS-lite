#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        createConstraintsMergedAndSpecific.py
# Purpose:     merge constraints from automatic procedure, GO consortium and
#              personal manual constraints (optional)
#              for each species specified in a file (option -list).
#              Store result in a directory (-outdir)
#
# Author:      stefano
#
# Created:     02/01/2020
# Copyright:   (c) stefano 2019
# Licence:     GPL
#-------------------------------------------------------------------------------


import argparse
import types
import urllib.request
from taxonLibrary3 import *
from owlLibrary2 import *
from os.path import join

try:
    from bs4 import BeautifulSoup
except ImportError:
    pass

# Set of the non module imports (from ... import ...) used in imports() function
non_module_import = {'owlLibrary2', 'taxonLibrary', 'taxonLibrary2', 'bs4'}


def imports():
    # Return a list of the imported module and the non module imported module.
    imported_module_list = []

    for name, val in globals().items():  # Get the map of all the necessary information about the program.
        if isinstance(val, types.ModuleType):  # Verify if is a module
            imported_module_list.append(val.__name__)
        elif hasattr(val, '__class__'):  # Verify if is a class
            for mdl in non_module_import:
                if mdl in str(val):
                    imported_module_list.append(mdl)

    return imported_module_list


def find_new_taxon(taxonomy, taxid):
    # Search in the NCBI site the new taxid given the old taxid by parsing the HTML code.
    url = f'https://www.ncbi.nlm.nih.gov/taxonomy/?term={taxid}'
    file = BeautifulSoup(urllib.request.urlopen(url).read(), 'html.parser') # HTML parser
    taxon_data = ''
    taxa_status = 'not exists'
    new_taxa = None
    new_taxa_name = None
    taxa_level = None

    # Find the div tag
    for element in file.find_all('div'):
        try:
            # Find the div with class rprt
            if 'rprt' in element.div['class']:
                taxon_data = element
                break
        except:
            pass

    # Verify if the taxonomic ID was merged
    if 'merged' in str(taxon_data):
        # Get all the a tags
        for anchor in taxon_data.find_all('a'):
            try:
                # Get the taxonomic ID where the taxid was merged
                new_taxa = str(int(anchor.contents[0]))
                # Get the merged taxonID name
                new_taxa_name = taxonomy.get_name(new_taxa)
            except ValueError:
                pass
        taxa_status = 'merged'
    elif 'deleted' in str(taxon_data): # Verify if the taxonomic ID was deleted
        # Get all the p tags
        for paragraph in taxon_data.find_all('p'):
            # Get the tag p with class title
            if 'title' in paragraph['class']:
                taxa_name = paragraph.contents[0]
                continue
            # Get the tag p with class desc
            if 'desc' in paragraph['class']:
                taxa_level = paragraph.contents[0]
                continue

        taxa_status = 'deleted'
        new_taxon_ids = taxonomy.get_ids(taxa_name)
        if taxa_level is not None:
            for tax_id in new_taxon_ids:
                parent = taxonomy.get_ancestor_at_rank(tax_id, taxa_level)
                if parent is not None:
                    new_taxa = parent
                    break
            new_taxa_name = taxonomy.get_name(new_taxa)

    return new_taxa, new_taxa_name, taxa_status


def main(args):

    ## example of file format taxonConstraintsDef.txt
    ##
    ## # fields are
    ## # Taxa	Taxa_name	Taxa_description	type	Classification
    ## # 'other' is a placeholder at the moment
    ## 1	Unknown	Unknown environmental metagenomic	other	Unknown
    ## 2157	Archaea	Archaea and Bacteria	other	Archaea_Bacteria
    ## 2	Bacteria	Archaea and Bacteria	other	Archaea_Bacteria
    ## 33630	Alveolata	Ciliati dinoflagellati	other	Protozoa
    ## 554915	Amoebozoa	Amebe	other	Protozoa
    ## 554296	Apusozoa	Flagellati	other	Protozoa
    ## 1401294	Breviatea	Ameboide	other	Protozoa

    import_list = imports()
    taxa = Taxon(args['taxa'],args['merge'],args['names'])
    ancestors = taxa.ancestors_full_list()
    descendants = taxa.descendants_full_list()
    merge_delete = 0
    tax_constr_def = []

    list_of_total_taxa_constraints = dict()
    with open(args['partition'],'r') as list_of_partition:
        for line in list_of_partition:
            line = line.strip()
            if line.startswith('#'):
                pass
            else:
                tax_def_data = line.strip().split('\t')
                taxon_tmp = tax_def_data[0]
                if taxon_tmp not in ancestors:
                    # Verify if the bs4 library wasn't imported.
                    if 'bs4' not in import_list:
                        print(f'WARNING!!! {taxon_tmp} does not found, so is not considered.\nCheck the link https://www.ncbi.nlm.nih.gov/taxonomy/?term={taxon_tmp} and modify the taxonConstraintsDef.txt file.')
                        continue
                    else:
                        # Check the taxon_tmp status in the NCBI site using the function find_new_taxon.
                        new_taxon, new_taxon_name, tmp_taxon_status = find_new_taxon(taxa, taxon_tmp)
                        if new_taxon is not None and tmp_taxon_status == 'merged': # Merged case
                            if new_taxon in ancestors:
                                print(f'WARNING!!! {taxon_tmp} was merged into taxid {new_taxon}. The last one is used.')
                                taxon_tmp = new_taxon
                            else:
                                print(f'WARNING!!! {taxon_tmp} not found, so is not considered.\nCheck the link https://www.ncbi.nlm.nih.gov/taxonomy/?term={taxon_tmp} and modify the taxonConstraintsDef.txt file.')
                                continue
                        elif tmp_taxon_status == 'deleted': # Deleted case
                            if new_taxon is not None and new_taxon in ancestors:
                                print(f'WARNING!!! {taxon_tmp} was deleted, so {new_taxon} ({new_taxon_name}) is considered.')
                                taxon_tmp = new_taxon
                            else:
                                print(f'WARNING!!! {taxon_tmp} not found, so is not considered.\nCheck the link https://www.ncbi.nlm.nih.gov/taxonomy/?term={taxon_tmp} and modify the taxonConstraintsDef.txt file.')
                                continue
                        elif tmp_taxon_status == 'not exists': # Not exist case
                            print(f'WARNING!!! {taxon_tmp} does not exist, so is not considered.')
                            continue
                        tax_constr_def.append((new_taxon, new_taxon_name, 'Unknown', 'other', 'Unknown', 'NEW'))
                        merge_delete += 1
                ##END IF
                else:
                    tax_constr_def.append(tuple(tax_def_data))

                anc_tmp = ancestors[taxon_tmp]
                list_of_total_taxa_constraints[taxon_tmp] = anc_tmp
            ##END IF
        ##END FOR
    ##END WITH
    list_of_partition.close()

    # Write in taxonConstraintsDefAuto.txt the taxonnomic nodes found and the updated taxons (identiied by a ***NEW*** string.)
    if merge_delete > 0 and 'bs4' in import_list:
        tax_const_def_file_path = ''
        data = args['partition'].strip().split('/')
        for text in data[0:len(data)-1]:
            tax_const_def_file_path += f'{text}/'

        with open(join(tax_const_def_file_path, 'taxonConstraintsDefAuto.txt'), 'w') as tcda_file:
            for tp in tax_constr_def:
                # print(tp)
                tcda_file.write(f'{tp[0]}\t{tp[1]}\t{tp[2]}\t{tp[3]}\t{tp[4]}')
                if len(tp) < 6:
                    tcda_file.write('\n')
                else:
                    tcda_file.write(f'\t***{tp[5]}***\n')

    go_owl = GoOwl(args['owl'],"http://purl.obolibrary.org/obo/")
    total = go_owl.listing()
    log_file = open(args['log'], "w")
    output_dir = args['outdir']

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    ##END IF

    ##load species for which to create a constraint
    list_of_species = list()
    merged = taxa.merging()
    ##check if any taxonID have been merged into another
    with open(args['list'],'r') as list_of_species_file:
        for line in list_of_species_file:
            try:
                list_of_species.append(merged[line.strip()])
                print('%s substituted in %s' % (line.strip(), merged[line.strip()]))
            except KeyError:
                list_of_species.append(line.strip())
        ##END FOR
    ##END WITH
    list_of_species_file.close()

    list_of_constraints_per_species_go = dict()
    list_of_constraints_per_species_auto = dict()
    dict_only_in = dict()
    #### to check whether the GO only_in derives form union, create a dictionary with keys GO e set of potential taxons that are
    #### allowed because derived form a Union
    union_only_in_GO_consortium = dict()

    ### load constraints from GO consortium
    if args['go_const'] is not None:
        with open(args['go_const'],'r') as go_const:
            for line in go_const:
                line = line.strip()
                values = line.split('\t')
                if values[5] == 'only in taxon':
                    if values[3] not in dict_only_in:
                        dict_only_in[values[3]] = list()
                    ##END IF
                    dict_only_in[values[3]].append(values[0])
                ##END IF
                for taxon in list_of_species:
                    if taxon not in list_of_constraints_per_species_go:
                        list_of_constraints_per_species_go[taxon] = dict()
                        list_of_constraints_per_species_go[taxon]['ONLY_IN'] = dict()
                        list_of_constraints_per_species_go[taxon]['NEVER_IN'] = dict()
                    ##END IF
                    anc = ancestors[taxon]
                    if values[3] in anc or taxon == values[3]:
                        if values[5] == 'Never in taxon':
                            go_temp_desc = go_owl.go_descendants_using_valid_edges(values[0])
                            list_of_constraints_per_species_go[taxon]['NEVER_IN'][values[0]] = (values[3],line)
                            for go in go_temp_desc:
                                list_of_constraints_per_species_go[taxon]['NEVER_IN'][go] = (values[3],line)
                        elif values[5] == 'only in taxon':
                            if values[0] not in union_only_in_GO_consortium:
                                union_only_in_GO_consortium[values[0]] = set()
                            ##END IF
                            union_only_in_GO_consortium[values[0]].add(values[3])
                            list_of_constraints_per_species_go[taxon]['ONLY_IN'][values[0]] = (values[3],line)
                        ##END IF
                    ##END IF
                ##END FOR
            ##END FOR
        ##END WITH
        go_const.close()

    ##load GO constraints from my pipeline (discard Garbage)
    fullListOf_AUTO_Never_IN_patched = dict()

    ## Initialize the dictionary with the distance from taxonomy root of any taxon found in the list
    ## of the general taxa nodes used to determine the taxonomy subdivision

    for taxon_in_def_constraints in list_of_total_taxa_constraints:
        fullListOf_AUTO_Never_IN_patched[taxon_in_def_constraints] = dict()
        fullListOf_AUTO_Never_IN_patched[taxon_in_def_constraints]['NEVER_IN'] = set()
        anc = ancestors[taxon_in_def_constraints]
        #distance = len(anc)
        distance = taxa.get_distance_from(taxon_in_def_constraints,'1')
        fullListOf_AUTO_Never_IN_patched[taxon_in_def_constraints]['POS'] = distance ## distance fron taxonomy root
        fullListOf_AUTO_Never_IN_patched[taxon_in_def_constraints]['LINE'] = dict()
    ##END FOR

    if args['aut_const'] is not None:
        ### now fill in with the data of automatic NEVER_IN constraints file
        with open(args['aut_const'],'r') as aut_const:
            for line in aut_const:
                line = line.strip()
                values = line.split('\t')
                if values[4] == 'Garbage':
                    continue
                ##END IF
                ## values[3] is the taxon and values[0] is GO
                if values[3] in fullListOf_AUTO_Never_IN_patched:
                    fullListOf_AUTO_Never_IN_patched[values[3]]['NEVER_IN'].add(values[0])
                    fullListOf_AUTO_Never_IN_patched[values[3]]['LINE'][values[0]] = line
            ##END FOR
        ##END WITH
        aut_const.close()

    for taxon in list_of_species:       #### those for which we need the constraints
        if taxon not in list_of_constraints_per_species_auto:
            list_of_constraints_per_species_auto[taxon] = dict()
            list_of_constraints_per_species_auto[taxon]['NEVER_IN'] = dict()
        ##END IF

        ## before placing a NEVER_IN check the ancestor tree of othet species present in ListOfTotalTaxaConstraints
        ## i.e. if there is Opisthokonta that is never_in but there is not an explicit NEVER_IN in Mammalia and we have Homo sapiens
        ## this means that if we do not check Homo sapiens turns to be NEVER_IN but this is wrong
        ## now we have to check this behaviour: Is there a another lower taxonomic level that if a NOT EXPLICIT in_taxon ?
        ## (in the example above this is Mammalia for Homo

        anc = ancestors[taxon] ## it is a list and last index is the root of the taxonomy of the species for which we need the constraints
        if taxon in list_of_total_taxa_constraints:
            anc.add(taxon)
        MAX = -1
        defTax = ''
        ### now position the species 'taxon' variable for which we must "inherit" the taxon constraints from dict 'FullListOf_AUTO_Never_IN_patched'
        ### we place 'taxon' in the most distant taxonomic group from taxonomy root so POS must be MAXIMIZED
        for tax in fullListOf_AUTO_Never_IN_patched:
            if tax in anc:
                pos = fullListOf_AUTO_Never_IN_patched[tax]['POS']
                if pos > MAX:
                    MAX = pos
                    defTax = tax
                ##END IF
            ##END IF
        ##END FOR
        for goFiller in fullListOf_AUTO_Never_IN_patched[defTax]['NEVER_IN']:
            list_of_constraints_per_species_auto[taxon]['NEVER_IN'][goFiller] = (defTax,fullListOf_AUTO_Never_IN_patched[defTax]['LINE'][goFiller])
        ##END FOR
    ##END FOR


    discard_never_in_MANUAL = dict()
    add_never_in_MANUAL = dict()
    add_in_MANUAL = dict()
    add_never_in = dict()

    for taxon in list_of_species:
        discard_never_in_MANUAL[taxon] = dict()
        add_never_in_MANUAL[taxon] = dict()
        add_in_MANUAL[taxon] = dict()
        add_never_in[taxon] = dict()
    ##END FOR

    #### give top priority to MANUAL !!!! OVER THE REST !!!!

    list_of_constraints_per_species_MANUAL = dict()

    if 'manual' in args:
        with open(args['manual'],'r') as manual:
            for line in manual:
                if line.startswith('#'):
                    continue
                line = line.strip()
                values = line.split('\t')
                listOfGO = go_owl.go_descendants_using_valid_edges(values[0])
                if values[5] == 'Never in taxon':
                    for taxon in list_of_species:
                        if taxon not in list_of_constraints_per_species_MANUAL:
                            list_of_constraints_per_species_MANUAL[taxon] = dict()
                            list_of_constraints_per_species_MANUAL[taxon]['NEVER_IN'] = dict()
                            list_of_constraints_per_species_MANUAL[taxon]['IN'] = dict()
                        ##END IF
                        anc = ancestors[taxon]
                        if values[3] in anc or taxon == values[3]:
                            list_of_constraints_per_species_MANUAL[taxon]['NEVER_IN'][values[0]] = values[3]
                            log_file.write(f'add a NEVER_IN for {values[0]} in {taxon}\n')
                            add_never_in_MANUAL[taxon][values[0]] = values[0]
                            for goSon in listOfGO:
                                log_file.write(f'add a NEVER_IN for {goSon} in {taxon}\n')
                                list_of_constraints_per_species_MANUAL[taxon]['NEVER_IN'][goSon] = values[3]
                                add_never_in_MANUAL[taxon][goSon] = goSon
                            ##END FOR
                        ##END IF
                    ##END FOR
                elif values[5] == 'in taxon':
                    for taxon in list_of_species:
                        if taxon not in list_of_constraints_per_species_MANUAL:
                            list_of_constraints_per_species_MANUAL[taxon] = dict()
                            list_of_constraints_per_species_MANUAL[taxon]['NEVER_IN'] = dict()
                            list_of_constraints_per_species_MANUAL[taxon]['IN'] = dict()
                        ##END IF
                        anc = ancestors[taxon]
                        if values[3] in anc or taxon == values[3]:
                            list_of_constraints_per_species_MANUAL[taxon]['IN'][values[0]] = values[3]
                            add_in_MANUAL[taxon][values[0]] = values[0]
                            log_file.write(f'add a IN for {values[0]} in {taxon}\n')
                            for goSon in listOfGO:
                                list_of_constraints_per_species_MANUAL[taxon]['IN'][goSon] = values[3]
                                log_file.write(f'add a IN for {goSon} in {taxon}\n')
                                add_in_MANUAL[taxon][goSon] = goSon
                            ##END FOR
                        ##END IF
                    ##END FOR
                ##END IF
            ##END FOR
        ##END WITH
        manual.close()
    ##END IF

    ### gives priority to GO consortium because manually curated (hopefully!)

    ### see if I must add a NEVER_IN to my constraints
    for taxon in list_of_species:
        try:
            desc = descendants[taxon]
        except KeyError:
            desc = set()
        anc = ancestors[taxon]
        for tax in dict_only_in:
            if tax not in anc and tax not in desc and tax != taxon:
            #### check if taxon from GOC only in constraint is not part of either ancestors or descendants of taxon from funtaxis input list
            #### we want never in constraints to be created for all the other taxon
                for go in dict_only_in[tax]:
                    go_temp = go_owl.go_descendants_using_valid_edges(go)
                    if go not in add_never_in[taxon] and go not in list_of_constraints_per_species_go[taxon]['ONLY_IN']:
                    #### add a never in for the taxon if it is only in for another taxon
                    #### if go is only in for taxon we do not add a never in
                        add_never_in[taxon][go] = go
                        log_file.write(f'add a never_in for {go} of {taxon} because "only_in" for {tax} and {taxon} is not part of the hierarchy of {tax}')
                    else:
                        log_file.write(f'OVERRULE because {go} is a IN in for MANUAL of {taxon} -> DO NOT add a never_in for {go} of {taxon} because "only_in" for {tax} and {taxon} is not part of the hierarchy of {tax}')
                    #### now extend the newly created never-in for all child term for this go
                    for go_sons in go_temp:
                        if go_sons not in add_never_in[taxon] and go_sons not in list_of_constraints_per_species_go[taxon]['ONLY_IN']:
                            add_never_in[taxon][go_sons] = go_sons
                            log_file.write(f'add a never_in for {go_sons} of {taxon} because "only_in" for {tax} and {taxon} is not part of the hierarchy of {tax} and {go_sons} is a child term of {go}')
                        else:
                            log_file.write(f'OVERRULE because {go_sons} is a IN in for MANUAL of {taxon} -> DO NOT add a never_in for {go_sons} of {taxon} because "only_in" for {tax} and {taxon} is not part of the hierarchy of {tax}')

                    ##END IF
                ##END FOR
            ##END IF
        ##END FOR
    ##END FOR

    ### see if I must discard a NEVER_IN from my constraints
    for taxon in list_of_constraints_per_species_auto:
        for go in list_of_constraints_per_species_auto[taxon]['NEVER_IN']:
            if len(list_of_constraints_per_species_go) > 0 and go in list_of_constraints_per_species_go[taxon]['ONLY_IN']:
                taxon_GO_CONST = list_of_constraints_per_species_go[taxon]['ONLY_IN'][go][0]
                taxon_AUTO = list_of_constraints_per_species_auto[taxon]['NEVER_IN'][go][0]
                ## I do not do anything because taxon of GO consortium is father of my automatic constraints and is only an indication that that GO can be used
                ## by the taxon but not necessary from all of its sons
                ## this is only pertinent for tax that are NOT descendants of this taxon and that MUST NOT have this GO
                ## it's a matter of choice ... in the past we can change behaviour. In this case, for example, GO_0000001 mitichondrial inheritance is only_in Eukaryota
                ## for GO consortium but is only used in Fungi and highly frequent (over 3000) and automatic constraints, with this idea,
                ## this term have been discarded for mammalia, and all other Eukaryota apart from Fungi where is an accepted GO.
                ## Is it right or not? Prbably in this case it is not but other examples may be differently interpreted and fit this present rule
                ## other example: sexual reproduction GO:0019953 can be used for most Eukaryota but one of its sons GO:0034293 sexual sporulation can be true
                ## only for plants, fungi etc. but not for mammalia so I have to keep never_in of this term for mammalia (for example)
                if taxon_GO_CONST in ancestors[taxon_AUTO]:
                     if go not in add_never_in_MANUAL[taxon]:
                        discard_never_in_MANUAL[taxon][go] = go
                ##END IF
                if taxon_AUTO in ancestors[taxon_GO_CONST] or taxon == taxon_GO_CONST or taxon_AUTO == taxon_GO_CONST:
                    ## I must discard this never_in because taxon_AUTO is a father of taxon_GO_CONST hence constraints generated by GO consortium are at a lower taxonomic level and then
                    ## I must discard this never_in. Example. I have GO1 never_in for mammalia but GO consortium says GO1 is only_in for primates. Than for species Homo
                    ## I must accept this GO and overrule its never_in that must be discarded.
                    log_file.write(f'discard never_in of {go} in {taxon} because it is "only_in" for {taxon_GO_CONST} that is a son of {taxon_AUTO} that generated the constraints for the {go} of {taxon}  -> {list_of_constraints_per_species_auto[taxon]["NEVER_IN"][go][1]}\n')
                    ### if go not present in MANDATORY manual never_in we can discard this constraint
                    if go not in add_never_in_MANUAL[taxon]:
                        discard_never_in_MANUAL[taxon][go] = go
                        log_file.write(f'discard never_in of {go} in {taxon} because it is "only_in" for {taxon_GO_CONST} that is a son of {taxon_AUTO} that generated the constraints for the {go} of {taxon}  -> {list_of_constraints_per_species_auto[taxon]["NEVER_IN"][go][1]}\n')
                    else:
                        log_file.write(f'OVERRULE because {go} is a never in for MANUAL of {taxon} -> DO NOT discard never_in of {go} in {taxon} because it is "only_in" for {taxon_GO_CONST} that is a son of {taxon_AUTO} that generated the constraints for the {go} of {taxon}  -> {list_of_constraints_per_species_auto[taxon]["NEVER_IN"][go][1]}\n')
                    ##END IF
                    ### if go present in IN MANUAL we MUST discard this constraint never in
                    ### useless !!!!
                    ### if go in add_in_MANUAL[taxon]:
                    ###    discardNeverIn[taxon] = go
                    ##END IF
                ##END IF
            ##END IF
        ##END FOR
    ##END FOR

    never_in_def = dict()

    for taxon in list_of_species:
        never_in_def[taxon] = dict()
    ##END FOR

    ### now I have the two different dictionary to print list_of_constraints_per_species_MANUAL already evaluated
    for taxon in list_of_constraints_per_species_auto:
        for go in add_never_in[taxon]:
            if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')

        for go in add_never_in_MANUAL[taxon]:
            if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
            ##END IF
        ##END FOR
        for go in list_of_constraints_per_species_auto[taxon]['NEVER_IN']:
            ### if it is present in discard_never_in_MANUAL this means that I have to discard the constraint never_in
            ### if it is NOT present in discard_never_in_MANUAL this means that I can keep the constraint never_in
            ### and I can store it in never_in_def
            if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
            ##END IF
        ##END FOR
        if len(list_of_constraints_per_species_go) > 0:
            for go in list_of_constraints_per_species_go[taxon]['NEVER_IN']:
                if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                    details = go_owl.go_single_details(go)
                    never_in_def[taxon][go] = (details['name'],details['namespace'])
                else:
                    log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
                ##END IF
            ##END FOR
        ##END IF
    ##END FOR

    for taxon in list_of_constraints_per_species_go:
        for go in add_never_in[taxon]:
            if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')

        for go in add_never_in_MANUAL[taxon]:
            if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
            ##END IF
        ##END FOR
        for go in list_of_constraints_per_species_go[taxon]['NEVER_IN']:
            ### if it is present in discard_never_in_MANUAL this means that I have to discard the constraint never_in
            ### if it is NOT present in discard_never_in_MANUAL this means that I can keep the constraint never_in
            ### and I can store it in never_in_def
            if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
            ##END IF
        for go in list_of_constraints_per_species_auto[taxon]['NEVER_IN']:
            if go not in discard_never_in_MANUAL[taxon] and go not in add_in_MANUAL[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
            ##END IF
    ##END FOR

    log_file.close()

    for taxon in add_never_in_MANUAL:
        for go in add_never_in_MANUAL[taxon]:
            details = go_owl.go_single_details(go)
            never_in_def[taxon][go] = (details['name'],details['namespace'])
        ##END FOR
    ##END FOR

    for taxon in sorted(never_in_def.keys()):
        taxon_name = taxa.get_name(taxon)
        taxon_name = taxon_name.replace(' ','_')
        with open(output_dir + '/' + taxon + '_' + taxon_name + '_constraints.txt', "w") as output:
            for go in never_in_def[taxon]:
                name = never_in_def[taxon][go][0]
                namespace = never_in_def[taxon][go][1]
                go = go.replace('_', ':', 1)
                output.write(f'{go}\t{name}\t{namespace}\n')
            ##END FOR
        ##END WITH
        output.close()
    ##END FOR

##END MAIN


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='merge constraints from automatic procedure, GO consortium, and manual (optional) constraints for each species specified in a file (option -list). Store results in a directory (-outdir)')
    parser.add_argument('-go_const', metavar='INPUT_FILE',  help='constraints from GO consortium generated by taxonConstraintsGOconsortium.py', required=False)
    parser.add_argument('-aut_const', metavar='INPUT_FILE',  help='automatic GO constraints generated by wrapperTaxonConstraints.py', required=False)
    parser.add_argument('-manual', metavar='INPUT_FILE',  help='NEVER_IN constraints manually defined (go <tab> taxid) (optional)', required=False)
    parser.add_argument('-owl', metavar='INPUT_FILE', help='go-plus.owl file is required', required=True)
    parser.add_argument('-list', metavar='INPUT_FILE',  help='list of species for which generate merged constraints', required=True)
    parser.add_argument('-partition', metavar='INPUT_FILE',  help='list of taxa subdivision in whigh taxonomy has been divided (taxonConstraintsDef.txt)', required=True)
    parser.add_argument('-merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    parser.add_argument('-outdir', metavar='DIRECTORY',  help='directory containing files of constraints for each species', required=True)
    parser.add_argument('-log', metavar='LOG_FILE',  help='log_file of actions taken', required=True)

    args = vars(parser.parse_args())
    main(args)
#END MAIN




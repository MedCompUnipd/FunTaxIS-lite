#!/usr/bin/env python3

#-------------------------------------------------------------------------------
# Name:        createConstraintsMergedAndSpecific.py
# Purpose:     merge constraints from automatic procedure, GO consortium and
#              personal manual constraints (optional)
#              for each species specified in a file (option -list).
#              Store result in a directory (-outdir)
#
# Author:      Stefano, Emilio
#
# Created:     02/01/2020
# Last edited: 08/02/2024
# Copyright:   (c) Stefano 2019
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


def get_args():
    parser = argparse.ArgumentParser(description='merge constraints from automatic procedure, GO consortium, and manual (optional) constraints for each species specified in a file (option -list). Store results in a directory (-outdir)')

    parser.add_argument('-g', '--go_const', metavar='INPUT_FILE',  help='constraints from GO consortium generated by taxonConstraintsGOconsortium.py', required=False)
    parser.add_argument('-a', '--aut_const', metavar='INPUT_FILE',  help='automatic GO constraints generated by wrapperTaxonConstraints.py', required=False)
    parser.add_argument('-c', '--manual', metavar='INPUT_FILE',  help='NEVER_IN constraints manually defined (go <tab> taxid) (optional)', required=False)
    parser.add_argument('-w', '--owl', metavar='INPUT_FILE', help='go-plus.owl file is required', required=True)
    parser.add_argument('-s', '--species', metavar='INPUT_FILE',  help='list of species for which generate merged constraints', required=True)
    parser.add_argument('-p', '--partition', metavar='INPUT_FILE',  help='list of taxa subdivision in whigh taxonomy has been divided (taxonConstraintsDef.txt)', required=True)
    parser.add_argument('-m', '--merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-t', '--taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-n', '--names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    parser.add_argument('-o', '--outdir', metavar='DIRECTORY',  help='directory containing files of constraints for each species', required=True)
    parser.add_argument('-l', '--log', metavar='LOG_FILE',  help='log_file of actions taken', required=False, default='')

    return vars(parser.parse_args())


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


def parse_partition(partition_file, taxa, ancestors):
    list_of_total_taxa_constraints = {}
    tax_constr_def = []
    merge_delete = 0
    ref_nodes = set()

    with open(partition_file, 'r') as list_of_partition:
        for line in list_of_partition:
            if line.startswith('#'):
                pass
            else:
                tax_def_data = line.strip().split('\t')
                taxon_tmp = tax_def_data[0]
                if taxon_tmp not in ancestors:
                    # Verify if the bs4 library wasn't imported.
                    if 'bs4' not in imports():
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
                else:
                    tax_constr_def.append(tuple(tax_def_data))
                    ref_nodes.add(taxon_tmp)

                anc_tmp = ancestors[taxon_tmp]
                list_of_total_taxa_constraints[taxon_tmp] = anc_tmp

    return list_of_total_taxa_constraints, tax_constr_def, ref_nodes, merge_delete


def write_taxnodes(partition, tax_constr_def):
    path_components = partition.split('/')
    tax_const_def_file_path = os.path.join(*path_components[:-1])

    with open(join(tax_const_def_file_path, 'taxonConstraintsDefAuto.txt'), 'w') as tcda_file:
        for tp in tax_constr_def:
            tcda_file.write(f'{tp[0]}\t{tp[1]}\t{tp[2]}\t{tp[3]}\t{tp[4]}')
            if len(tp) < 6:
                tcda_file.write('\n')
            else:
                tcda_file.write(f'\t***{tp[5]}***\n')


def get_species_list(merged, list_file):
    list_of_species = list()
    with open(list_file, 'r') as list_of_species_file:
        for line in list_of_species_file:
            try:
                list_of_species.append(merged[line.strip()])
                print('%s substituted in %s' % (line.strip(), merged[line.strip()]))
            except KeyError:
                list_of_species.append(line.strip())

    return list_of_species


def load_consortium(go_const, dict_only_in, ancestors, go_owl, list_of_constraints_per_species_go, union_taxon):
    ### load constraints from GO consortium
    with open(go_const, 'r') as go_const:
        for line in go_const:
            values = line.strip().split('\t')
            if values[5] == 'only in taxon':
                #build dictionary of only_in constrains to be converted to never_ins for other species
                if values[3] not in dict_only_in:
                    dict_only_in[values[3]] = set()
                dict_only_in[values[3]].add(values[0])
            for taxon in list_of_species:
                anc = ancestors[taxon]
                if values[5] == 'never in taxon':
                    #place a never_in for every child in the taxonomy tree
                    if taxon == values[3] or values[3] in anc:
                        go_temp_desc = go_owl.go_descendants_using_valid_edges(values[0])
                        list_of_constraints_per_species_go[taxon]['NEVER_IN'].add(values[0])
                        for go in go_temp_desc:
                            list_of_constraints_per_species_go[taxon]['NEVER_IN'].add(go)
                elif values[5] == 'only in taxon':
                    #only_in constraints overrule automatic never_ins in the node indicated in the constraint
                    if taxon == values[3]:
                        go_temp_desc = go_owl.go_descendants_using_valid_edges(values[0])
                        list_of_constraints_per_species_go[taxon]['ONLY_IN'].add(values[0])
                        for go in go_temp_desc:
                            list_of_constraints_per_species_go[taxon]['ONLY_IN'].add(go)
                    #union taxon that have been split into the respective taxon and have an only_in constraint muste be recorded to avoid conflicts
                    elif values[3] in anc or taxon == values[3]:
                        union_taxon[taxon].add(values[0])


def load_auto(aut_const, list_of_constraints_per_species_auto):
    with open(aut_const,'r') as aut_const:
        for line in aut_const:
            line = line.strip().split('\t')
            if line[3] in list_of_constraints_per_species_auto:
                list_of_constraints_per_species_auto[line[3]].add(line[0])


def load_manual(man_constr, go_owl, list_of_species, list_of_constraints_per_species_manual, add_never_in_manual, add_in_manual, ancestors, descendants, log_file):
    with open(man_constr, 'r') as manual:
        for line in manual:
            if line.startswith('#'):
                continue
            values = line.strip().split('\t')
            list_of_go = go_owl.go_descendants_using_valid_edges(values[0])
            if values[5] == 'never in taxon':
                for taxon in list_of_species:
                    if taxon not in list_of_constraints_per_species_manual:
                        list_of_constraints_per_species_manual[taxon] = {'NEVER_IN': {}, 'IN': {}}

                    anc = ancestors[taxon]
                    if values[3] in anc or taxon == values[3]:
                        list_of_constraints_per_species_manual[taxon]['NEVER_IN'][values[0]] = values[3]
                        log_file.write(f'add a never_in for {values[0]} in {taxon}\n')
                        add_never_in_manual[taxon].add(values[0])
                        for go_son in list_of_go:
                            log_file.write(f'add a never_in for {go_son} in {taxon}\n')
                            list_of_constraints_per_species_manual[taxon]['NEVER_IN'][go_son] = values[3]
                            add_never_in_manual[taxon].add(go_son)
            elif values[5] == 'in taxon':
                for taxon in list_of_species:
                    if taxon not in list_of_constraints_per_species_manual:
                        list_of_constraints_per_species_manual[taxon] = {'NEVER_IN': {}, 'IN': {}}
                    try:
                        desc = descendants[taxon]
                    except KeyError:
                        desc = set()
                    anc = ancestors[taxon]
                    if values[3] in anc or taxon == values[3]:
                        list_of_constraints_per_species_manual[taxon]['IN'][values[0]] = values[3]
                        add_in_manual[taxon].add(values[0])
                        log_file.write(f'add a in for {values[0]} in {taxon}\n')
                        for go_son in list_of_go:
                            list_of_constraints_per_species_manual[taxon]['in'][go_son] = values[3]
                            log_file.write(f'add a in for {go_son} in {taxon}\n')
                            add_in_manual[taxon].add(go_son)


def update_never_from_only(dict_only_in, list_of_species, ancestors, go_owl, never_from_only, union_taxon, log_file):
    for taxon in list_of_species:
        anc = ancestors[taxon]
        for tax in dict_only_in:
            if tax not in anc  and tax != taxon:
                for go in dict_only_in[tax]:
                    go_temp = go_owl.go_descendants_using_valid_edges(go)
                    if go not in never_from_only[taxon] and go not in union_taxon[taxon]:
                        never_from_only[taxon].add(go)
                        log_file.write(f'add a never_in for {go} of {taxon} because "only_in" for {tax} and {taxon} is not part of the hierarchy of {tax}')
                    else:
                        log_file.write(f'OVERRULE because {go} comes from an union taxon and thus is not a never_in')
                    for go_sons in go_temp:
                        if go_sons not in never_from_only[taxon] and go_sons not in union_taxon[taxon]:
                            never_from_only[taxon].add(go_sons)
                            log_file.write(f'add a never_in for {go_sons} of {taxon} because "only_in" for {tax} and {taxon} is not part of the hierarchy of {tax} and {go_sons} is a child term of {go}')
                        else:
                            log_file.write(f'OVERRULE because {go} comes from an union taxon and thus is not a never_in')


def update_never_in_def(list_of_species, list_of_constraints_per_species_auto, list_of_constraints_per_species_go, never_from_only, never_in_def, add_in_manual, go_owl, taxa, log_file):
    for taxon in list_of_species:
        tax = taxon
        while True:
            if tax in list_of_constraints_per_species_auto:
                break
            tax = taxa.get_father(tax)
        for go in list_of_constraints_per_species_auto[tax]:
            if go not in add_in_manual[taxon] and go not in list_of_constraints_per_species_go[taxon]['ONLY_IN']:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
        for go in never_from_only[taxon]:
            if go not in add_in_manual[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')
        for go in list_of_constraints_per_species_go[taxon]['NEVER_IN']:
            if go not in add_in_manual[taxon]:
                details = go_owl.go_single_details(go)
                never_in_def[taxon][go] = (details['name'],details['namespace'])
            else:
                log_file.write(f'OVERRULE because {go} is a IN in for MANUAL/GO_CONSORTIUM of {taxon} -> NEVER_IN is ERASED!!\n')


if __name__ == "__main__":
    args = get_args()
    manual = args['manual']

    taxon, merge, names = args['taxa'], args['merge'], args['names']
    if not os.path.exists(taxon) or not os.path.exists(merge)or not os.path.exists(names):
         print(f'Incorrect taxonomy! check the files given as input:\n{taxon}\n{merge}\n{names}', file=sys.stderr)
         raise FileNotFoundError

    go_const = args['go_const']
    aut_const = args['aut_const']
    if not os.path.exists(go_const) and not os.path.exists(aut_const):
        print('Incorrect usage: at least one of the arguments -g/--go_const | -a/--aut_const must be given!', file=sys.stderr)
        raise FilNotFoundError

    output_dir = args['outdir']
    if not os.path.exists(output_dir):
        print(f'WARNING: output directory {output_dir} does not exist, creating it', file=sys.stderr)
        os.makedirs(output_dir)

    owl = args['owl']
    if not os.path.exists(owl):
        print(f'Provided OWL file {owl} does not exist!', file=sys.stderr)
        raise FilNotFoundError

    species = args['species']
    if not os.path.exists(species):
        print(f'Provided SPECIES LIST file {species} does not exist!', file=sys.stderr)
        raise FilNotFoundError

    partition = args['partition']
    if not os.path.exists(partition):
        print(f'Provided PARTITION file {partition} does not exist!', file=sys.stderr)
        raise FilNotFoundError

    log_file = args['log']
    if not log_file:
        intermediate, _ = os.path.split(species)
        log_file = osp.ath.join(intermediate, 'log_file.txt')
        print(f'WARNING: using default log file {log_file}', file=sys.stderr)

    taxa = Taxon(taxon, merge, names)

    descendants = taxa.descendants_full_list()
    ancestors = taxa.ancestors_full_list()

    list_of_total_taxa_constraints, tax_constr_def, ref_nodes, merge_delete = parse_partition(partition, taxa, ancestors)

    # Write in taxonConstraintsDefAuto.txt the taxonnomic nodes found and the updated taxons (identiied by a ***NEW*** string.)
    if merge_delete > 0 and 'bs4' in imports():
        write_taxnodes(partition, tax_constr_def)

    go_owl = GoOwl(owl,"http://purl.obolibrary.org/obo/")
    total = go_owl.listing()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    list_of_species = get_species_list(taxa.merging(), species)

    list_of_constraints_per_species_go = {}
    union_taxon = {}
    for taxon in list_of_species:
        if taxon not in list_of_constraints_per_species_go:
            list_of_constraints_per_species_go[taxon] = {'ONLY_IN': set(), 'NEVER_IN': set()}
        if taxon not in union_taxon:
            union_taxon[taxon] = set()

    dict_only_in = {}
    log_file = open(log_file, "w")

    ### load constraints from GO consortium
    if go_const is not None:
         load_consortium(go_const, dict_only_in, ancestors, go_owl, list_of_constraints_per_species_go, union_taxon)

    list_of_constraints_per_species_auto = {}
    for taxon in ref_nodes:
        if taxon not in list_of_constraints_per_species_auto:
            list_of_constraints_per_species_auto[taxon] = set()

    ### load/calculate automatic constraints
    if aut_const is not None:
        load_auto(aut_const, list_of_constraints_per_species_auto)

    list_of_constraints_per_species_manual = {}

    never_from_only = {}
    never_in_def = {}
    add_never_in_manual = {}
    add_in_manual = {}

    for taxon in list_of_species:
        never_from_only[taxon] = set()
        never_in_def[taxon] = dict()
        add_never_in_manual[taxon] = set()
        add_in_manual[taxon] = set()

    if manual is not None:
        load_manual(manual, go_owl, list_of_species, list_of_constraints_per_species_manual, add_never_in_manual, add_in_manual, ancestors, descendants, log_file)

    update_never_from_only(dict_only_in, list_of_species, ancestors, go_owl, never_from_only, union_taxon, log_file)
    update_never_in_def(list_of_species, list_of_constraints_per_species_auto, list_of_constraints_per_species_go, never_from_only, never_in_def, add_in_manual, go_owl, taxa, log_file)

    log_file.close()

    # do this
    for taxon in add_never_in_manual:
        for go in add_never_in_manual[taxon]:
            details = go_owl.go_single_details(go)
            never_in_def[taxon][go] = (details['name'],details['namespace'])

    # write that
    for taxon in sorted(never_in_def.keys()):
        taxon_name = taxa.get_name(taxon)
        taxon_name = taxon_name.replace(' ','_')
        out_file = os.path.join(output_dir, f'{taxon}_{taxon_name}_constraints.txt')
        with open(out_file, "w") as output:
            for go in never_in_def[taxon]:
                name = never_in_def[taxon][go][0]
                namespace = never_in_def[taxon][go][1]
                go = go.replace('_', ':', 1)
                output.write(f'{go}\t{name}\t{namespace}\n')

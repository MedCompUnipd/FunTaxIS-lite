#!/usr/bin/env python3
#  -------------------------------------------------------------------------------
#  Name:        GoOwl library
#  Purpose:     parsing go-plus.owl file
#
#  Author:      Stefano
#
#  Created:     21/05/2019
#  Last modified: 22/07/2021
#  Copyright:   (c) Stefano 2019
#  Licence:     GPL
#  -------------------------------------------------------------------------------

import math
import copy
from owlready2 import *


def e_print(*args, **kwargs):
    # print to standard error
    print(*args, file=sys.stderr, **kwargs)
    sys.exit()


def parse_obo_file(obo_file):
    available_keys = {'id', 'name', 'namespace', 'def', 'is_a', 'alt_id', 'relationship', 'is_obsolete', 'consider',
                      'comment', 'property_value'}
    multiple_data_keys = {'is_a', 'alt_id', 'relationship', 'is_obsolete', 'consider', 'property_value'}
    read_lines = False
    num_term = 0
    go_data = {}
    parent_found = set()
    with open(obo_file, 'r') as obo:
        for line in obo:
            if line.startswith('[Term]'):
                if num_term != 0 and len(term_data) > 0:
                    go_data[term_data['id']] = term_data
                term_data = {}
                read_lines = True
                parent_found.clear()
                num_term += 1
                continue
            if line.startswith('[Typedef]'):
                if num_term != 0 and len(term_data) > 0:
                    go_data[term_data['id']] = term_data
                read_lines = False
            if read_lines:
                if line == '\n':
                    continue
                data = line.strip().split(': ')
                key = data[0]
                if key not in available_keys:
                    continue
                if key == 'id':
                    value = data[1].strip().replace(':', '_')
                    term_data[key] = value
                    continue
                if key == 'name' or key == 'namespace':
                    value = data[1].strip()
                    term_data[key] = value
                    continue
                if key == 'def':
                    value = data[1].strip().split('"')[1]
                    term_data[key] = value
                    continue
                if key == 'comment':
                    term_data[key] = value
                    continue
                if key in multiple_data_keys and key not in term_data:
                    term_data[key] = []
                if key == 'property_value':
                    dt = data[1].strip().split()[1]
                    term_data[key].append(dt)
                    continue
                if key != 'is_a' and key != 'relationship':
                    value = data[1].strip().replace(':', '_')
                    if data[1] not in parent_found:
                        term_data[key].append(value)
                        parent_found.add(data[1])
                    continue
                if key == 'relationship':
                    dt = data[1].split('!')[0].strip().split()
                    if dt[0] == 'has_part':
                        continue
                    value = (dt[0], dt[1].replace(':', '_'))
                    if dt[1] not in parent_found:
                        term_data[key].append(value)
                        parent_found.add(dt[1])
                    continue
                if key == 'is_a':
                    value = data[1].split('!')[0].strip().replace(':', '_')
                    parent_found.add(value)
                    term_data[key].append(value)

    return go_data


class GoOwl:

    def __init__(self, owl, namespace='', goa_file='', by_ontology=False, use_all_evidence=True,
                 valid_evidence=('EXP', 'IDA', 'IPI', 'IMP', 'IGI', 'IEP', 'TAS', 'IC'), edges=('is a', 'part of', 'regulates', 'positively regulates', 'negatively regulates', 'occurs in', 'capable of', 'capable of part of')):
        self.__owl = owl
        self.__ns = namespace
        self.__global = {}
        self.__global_total = {}
        self.__deprecated = {}
        self.__obsolete = {}
        self.__deprecated_bis = {}
        self.__obsolete_bis = {}
        self.__triplets_son_father = {}
        self.__triplets_father_son = {}
        self.__triplets_son_father_go_only = {}
        self.__triplets_father_son_go_only = {}
        self.__secondary_ids_to_primary = {}
        self.__primary_to_secondary_ids = {}
        self.__mf_root = 'GO_0003674'
        self.__bp_root = 'GO_0008150'
        self.__cc_root = 'GO_0005575'
        self.__roots = {'GO_0008150', 'GO_003674', 'GO_0005575'}
        self.__valid_edges = set(e for e in edges)
        self.__valid_evidence = set(valid_evidence)  # GOA evidence codes used for the IC computation
        self.__by_ontology = by_ontology
        self.__use_all_evidence = use_all_evidence
        self.__file_extension = str(owl).strip().split('.')[-1]
        self.__ontology_converter = {'BPO': 'biological_process', 'MFO': 'molecular_function',
                                     'CCO': 'cellular_component', 'B': 'biological_process', 'P': 'biological_process',
                                     'M': 'molecular_function', 'F': 'molecular_function', 'C': 'cellular_component'}
        self.loading()
        self.__ic_gos = {}
        self.__gos_ic = {}
        if len(goa_file) > 0:
            self.compute_ic(goa_file)

    #  END DEF

    def loading(self):
        if self.__file_extension == 'obo':
            obo_data = parse_obo_file(self.__owl)
            self.__loading_obo(obo_data)
        else:
            if len(self.__ns) == 0:
                e_print('Namespace required. Use "http://purl.obolibrary.org/obo/" as namespace.')
            self.__loading_owl()

    def __loading_obo(self, go_data):
        for go_id, data in go_data.items():
            self.__global_total.setdefault(go_id, data)
            if 'is_obsolete' not in data:
                self.__global.setdefault(go_id, {'GO': data['id'],
                                                 'name': data['name'],
                                                 'descr': data['def'],
                                                 'namespace': data['namespace']})
                if 'alt_id' in data:
                    self.__primary_to_secondary_ids.setdefault(go_id, set())
                    for alt_id in data['alt_id']:
                        self.__primary_to_secondary_ids[go_id].add(alt_id)
                        self.__secondary_ids_to_primary[alt_id] = go_id

                self.__triplets_son_father.setdefault(go_id, set())
                self.__triplets_son_father_go_only.setdefault(go_id, set())
                self.__triplets_father_son.setdefault(go_id, set())
                self.__triplets_father_son_go_only.setdefault(go_id, set())

                if 'is_a' in data:
                    for father_id in data['is_a']:
                        father_data = go_data[father_id]
                        self.__triplets_father_son_go_only.setdefault(father_id, set())
                        self.__triplets_father_son.setdefault(father_id, set())

                        self.__triplets_son_father_go_only[go_id].add(father_id)
                        self.__triplets_son_father[go_id].add((father_data['id'],
                                                               'is a',
                                                               father_data['namespace'],
                                                               father_data['name'],
                                                               father_data['def']))
                        self.__triplets_father_son_go_only[father_id].add(go_id)
                        self.__triplets_father_son[father_id].add((go_id,
                                                                   'is a',
                                                                   data['namespace'],
                                                                   data['name'],
                                                                   data['def']))

                if 'relationship' in data:
                    for tp in data['relationship']:
                        father_data = go_data[tp[1]]
                        self.__triplets_father_son_go_only.setdefault(father_data['id'], set())
                        self.__triplets_father_son.setdefault(father_data['id'], set())

                        self.__triplets_son_father_go_only[go_id].add(father_data['id'])
                        self.__triplets_son_father[go_id].add((father_data['id'],
                                                               str(tp[0]).replace('_', ' '),
                                                               father_data['namespace'],
                                                               father_data['name'],
                                                               father_data['def']))
                        self.__triplets_father_son_go_only[father_data['id']].add(go_id)
                        self.__triplets_father_son[father_data['id']].add((go_id,
                                                                           str(tp[0]).replace('_', ' '),
                                                                           data['namespace'],
                                                                           data['name'],
                                                                           data['def']))
            else:
                self.__obsolete_bis.setdefault(go_id, set())
                if 'comment' in data and 'deleted' in data['comment'] and len(data['consider']) == 0:
                    self.__obsolete_bis[go_id].add('DELETE')
                elif 'consider' in data:
                    for go_id_cons in data['consider']:
                        self.__obsolete_bis[go_id].add(go_id_cons)

        fathers = self.__triplets_son_father['GO_0018924']
        n_fathers = len(fathers)

    def __loading_owl(self):
        go_load = get_ontology(self.__owl).load()
        #  obo = go_load.get_namespace(self.ns)

        for go_name_son in go_load.classes():
            if go_name_son.name.startswith('GO_'):
                self.__global_total.setdefault(go_name_son.name, go_name_son)
                try:
                    if not go_name_son.label.first().startswith("obsolete"):
                        self.__global.setdefault(go_name_son.name, go_name_son)
                        detail_description = self.go_single_details(go_name_son.name)
                        if len(go_name_son.hasAlternativeId) > 0:
                            self.__primary_to_secondary_ids.setdefault(go_name_son.name, set())
                            for alt_id in go_name_son.hasAlternativeId:
                                owl_alt_id = str(alt_id).replace(':', '_')
                                self.__secondary_ids_to_primary[owl_alt_id] = go_name_son.name
                                self.__primary_to_secondary_ids[go_name_son.name].add(owl_alt_id)
                        #  list of GO in OWL
                        #  create dictionary of dictionary of tuple for parents and sons

                        #  set defaults for dictionary
                        if go_name_son.name not in self.__triplets_son_father:
                            self.__triplets_son_father.setdefault(go_name_son.name, set())
                        if go_name_son.name not in self.__triplets_son_father_go_only:
                            self.__triplets_son_father_go_only.setdefault(go_name_son.name, set())
                        if go_name_son.name not in self.__triplets_father_son:
                            self.__triplets_father_son.setdefault(go_name_son.name, set())
                        if go_name_son.name not in self.__triplets_father_son_go_only:
                            self.__triplets_father_son_go_only.setdefault(go_name_son.name, set())

                        go_list_parents = self.__go_parents(go_name_son.name)
                        if go_list_parents:
                            #  extract info
                            #  triplets  SON -> FATHERS
                            #  self.__triplets_son_father.setdefault(go_name_son.name, set())
                            #  self.__triplets_son_father_go_only.setdefault(go_name_son.name, set())

                            for go_name_parents, detail in go_list_parents.items():

                                #  triplets  SON -> FATHERS
                                self.__triplets_son_father[go_name_son.name].add((go_name_parents, detail["rel"],
                                                                                  detail['namespace'], detail['name'],
                                                                                  detail['descr']))  # adding PARENTS
                                self.__triplets_son_father_go_only[go_name_son.name].add(go_name_parents)  # adding SON

                                #  triplets  FATHER -> SONS
                                if go_name_parents not in self.__triplets_father_son:
                                    self.__triplets_father_son.setdefault(go_name_parents, set())
                                # adding SON
                                self.__triplets_father_son[go_name_parents].add((go_name_son.name, detail["rel"],
                                                                                 detail_description['namespace'],
                                                                                 detail_description['name'],
                                                                                 detail_description['descr']))

                                if go_name_parents not in self.__triplets_father_son_go_only:
                                    self.__triplets_father_son_go_only.setdefault(go_name_parents, set())
                                self.__triplets_father_son_go_only[go_name_parents].add(go_name_son.name)  # adding SON
                                #  triplets SON -> FATHERS
                            #  END FOR
                        #  END IF
                    #  END IF
                except:
                    pass
                #  END TRY
            #  END IF
        #  END FOR
        # return go_load
    #  END DEF

    def obsolete_deprecated(self):
        if self.__file_extension == 'owl':
            for go, go_name_son in self.__global_total.items():
                if go_name_son.name.startswith('GO_'):
                    #  deprecated node
                    if not go_name_son.label.first():
                        if go_name_son.IAO_0100001.first().name == 'GO_0005575' or go_name_son.IAO_0100001.first().name == 'GO_0008150' or go_name_son.IAO_0100001.first().name == 'GO_0003674':
                            if go_name_son.name not in self.__deprecated:
                                self.__deprecated.setdefault(go_name_son.name, set())
                            #  END IF
                            self.__deprecated[go_name_son.name].add('DELETE')
                        else:
                            if go_name_son.name not in self.__deprecated:
                                self.__deprecated.setdefault(go_name_son.name, set())
                            #  END IF
                            self.__deprecated[go_name_son.name].add(go_name_son.IAO_0100001.first().name)
                        #  END IF
                    #  END IF
                    #  obsolete node
                    else:
                        if go_name_son.label.first().startswith("obsolete"):
                            if go_name_son.consider:
                                if go_name_son.name not in self.__obsolete:
                                    self.__obsolete.setdefault(go_name_son.name, set())
                                #  END IF
                                for a in go_name_son.consider:
                                    aa = a.replace(':', '_')
                                    if aa == 'GO_0005575' or aa == 'GO_0008150' or aa == 'GO_0003674':
                                        self.__obsolete[go_name_son.name].add('DELETE')
                                    else:
                                        self.__obsolete[go_name_son.name].add(aa)
                                    #  END IF
                                #  END FOR
                            else:
                                if go_name_son.name not in self.__obsolete:
                                    self.__obsolete.setdefault(go_name_son.name, set())
                                #  END IF
                                self.__obsolete[go_name_son.name].add('DELETE')
                            #  END IF
                        #  END IF
                    #  END IF
                #  END IF
            #  END FOR

            self.__deprecated_bis = copy.deepcopy(self.__deprecated)

            for a, b in self.__deprecated.items():
                for c in b:
                    if c in self.__obsolete:
                        if self.__obsolete[c] == 'DELETE':
                            self.__deprecated_bis[a].remove(c)
                            self.__deprecated_bis[a].add('DELETE')
                        else:
                            self.__deprecated_bis[a].remove(c)
                            for d in self.__obsolete[c]:
                                self.__deprecated_bis[a].add(d)
                            #  END FOR
                        #  END IF
                    #  END IF
                #  END FOR
            #  END FOR

            self.__obsolete_bis = copy.deepcopy(self.__obsolete)

            for a, b in self.__obsolete.items():
                for c in b:
                    if c in self.__deprecated_bis:
                        if self.__deprecated_bis[c] == 'DELETE':
                            self.__obsolete_bis[a].remove(c)
                            self.__obsolete_bis[a].add('DELETE')
                        else:
                            self.__obsolete_bis[a].remove(c)
                            for d in self.__deprecated_bis[c]:
                                self.__obsolete_bis[a].add(d)
                            #  END FOR
                        #  END IF
                    #  END IF
                #  END FOR
            #  END FOR
    #  END DEF

    def get_obsolete_deprecated_list(self):
        return self.__obsolete_bis, self.__deprecated_bis
    #  END DEF

    def get_go(self, go):
        return self.__global_total[go]

    def go_single_details(self, go_name):
        orig_details = {'GO': False,
                        'name': False,
                        'descr': False,
                        'namespace': False}
        if self.__file_extension == 'obo':
            if go_name in self.__global:
                orig_details = self.__global[go_name]
            elif go_name in self.__secondary_ids_to_primary:
                orig_details = self.__global[self.__secondary_ids_to_primary[go_name]]
        else:
            if go_name in self.__global.keys():
                go_concept = self.__global[go_name]
            elif go_name in self.__secondary_ids_to_primary:
                go_concept = self.__global[self.__secondary_ids_to_primary[go_name]]
            else:
                return orig_details

            if go_concept.label.first():
                if not go_concept.label.first().startswith("obsolete"):
                    try:
                        description = go_concept.hasDefinition.first().label.first()
                    except AttributeError:
                        description = go_concept.IAO_0000115.first()

                    orig_details = {'GO': go_concept.name,
                                    'name': go_concept.label.first(),
                                    'descr': description,
                                    'namespace': go_concept.hasOBONamespace.first(),
                                    }
                    #  END IF
                #  END IF
            #  END IF
        #  END IF
        return orig_details
    #  END DEF

    def get_leaves(self):
        leaves = set()
        for go_id, sons_data in self.__triplets_father_son_go_only.items():
            if len(sons_data) == 0:
                leaves.add(go_id)

        return leaves

    def get_leaves_by_ontology(self, ontology):
        leaves = set()
        for go_id, sons_data in self.__triplets_father_son_go_only.items():
            if len(sons_data) == 0 and self.go_single_details(go_id)['namespace'] == ontology:
                leaves.add(go_id)

        return leaves

    def go_children(self, go):
        if go in self.__secondary_ids_to_primary:
            go = self.__secondary_ids_to_primary[go]

        if go in self.__triplets_father_son.keys():
            go_children = self.__triplets_father_son[go]
            #  return a set where in position:
            #  0  go name of the child
            #  1  type of relation with parent
            #  2  namespace (biological process etc)
            #  3  brief description of the GO
            #  4  long description of the GO
            go_done = {}
            for go_p in go_children:
                go_done[go_p[0]] = {'rel': go_p[1],
                                    'name': go_p[3],
                                    'descr': go_p[4],
                                    'namespace': go_p[2]
                                    }
            #  END FOR
            return go_done
        else:
            return False
    #  END DEF

    def go_children_by_ontology(self, go_name):
        go_done = {}
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return go_done

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        if go_name not in self.__triplets_father_son:
            return go_done

        ontology = self.go_single_details(go_name)['namespace']
        go_children = self.__triplets_father_son[go_name]
        #  return a set where in position:
        #  0  go name of the child
        #  1  type of relation with parent
        #  2  namespace (biological process etc)
        #  3  brief description of the GO
        #  4  long description of the GO
        for go_p in go_children:
            if go_p[2] == ontology:
                go_done[go_p[0]] = {'rel': go_p[1],
                                    'name': go_p[3],
                                    'descr': go_p[4],
                                    'namespace': go_p[2]
                                    }
        #  END FOR
        return go_done
    #  END DEF

    def go_children_by_ontology_using_valid_edges(self, go_name):
        go_done = {}
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return go_done

        if go_name in self.__secondary_ids_to_primary[go_name]:
            go_name = self.__secondary_ids_to_primary[go_name]

        if go_name not in self.__triplets_father_son:
            return go_done

        ontology = self.go_single_details(go_name)['namespace']
        go_children = self.__triplets_father_son[go_name]
        #  return a set where in position:
        #  0  go name of the child
        #  1  type of relation with parent
        #  2  namespace (biological process etc)
        #  3  brief description of the GO
        #  4  long description of the GO
        for go_p in go_children:
            if go_p[2] == ontology and go_p[1] in self.__valid_edges:
                go_done[go_p[0]] = {'rel': go_p[1],
                                    'name': go_p[3],
                                    'descr': go_p[4],
                                    'namespace': go_p[2]
                                    }
        #  END FOR
        return go_done
    #  END DEF

    def go_children_using_valid_edges(self, go_name):
        go_done = {}

        if go_name not in self.__triplets_father_son and go_name in self.__secondary_ids_to_primary:
            return go_done

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        if go_name in self.__triplets_father_son:
            return go_done

        go_children = self.__triplets_father_son[go_name]
        #  return a set where in position:
        #  0  go name of the child
        #  1  type of relation with parent
        #  2  namespace (biological process etc
        #  3  brief description of the GO
        #  4  long description of the GO
        for go_p in go_children:
            if go_p[1] in self.__valid_edges:
                go_done[go_p[0]] = {'rel': go_p[1],
                                    'name': go_p[3],
                                    'descr': go_p[4],
                                    'namespace': go_p[2]
                                    }
        #  END FOR
        return go_done
    #  END DEF

    def get_go_son_father(self):
        return self.__triplets_son_father_go_only
    #  END DEF

    def get_go_father_son(self):
        return self.__triplets_father_son_go_only
    #  END DEF

    def get_go_fathers(self, go_name):
        if go_name not in self.__triplets_son_father_go_only and self.__secondary_ids_to_primary:
            return set()
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_son_father_go_only:
            return set()
        return self.__triplets_son_father_go_only[go_name]

    def get_go_fathers_by_ontology_using_valid_edges(self, go_name):
        fathers = set()
        if go_name not in self.__triplets_son_father and go_name not in self.__secondary_ids_to_primary:
            return fathers
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_son_father:
            return fathers

        ontology = self.go_single_details(go_name)['namespace']

        for go_data in self.__triplets_son_father[go_name]:
            if go_data[2] == ontology and go_data[1] in self.__valid_edges:
                fathers.add(go_data[0])

        return fathers

    def get_go_fathers_by_ontology(self, go_name):
        fathers = set()
        if go_name not in self.__triplets_son_father and go_name not in self.__secondary_ids_to_primary:
            return fathers
        if go_name is self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_son_father:
            return fathers

        ontology = self.go_single_details(go_name)['namespace']

        for go_data in self.__triplets_son_father[go_name]:
            if go_data[2] == ontology:
                fathers.add(go_data[0])

        return fathers

    def get_go_fathers_using_valid_edges(self, go_name):
        fathers = set()
        if go_name not in self.__triplets_son_father and go_name not in self.__secondary_ids_to_primary:
            return fathers
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_son_father:
            return fathers

        for go_data in self.__triplets_son_father[go_name]:
            if go_data[1] in self.__valid_edges:
                fathers.add(go_data[0])

        return fathers

    def get_go_sons(self, go_name):
        if go_name not in self.__triplets_father_son_go_only and go_name not in self.__secondary_ids_to_primary:
            return set()
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_father_son_go_only:
            return set()
        return self.__triplets_father_son_go_only[go_name]

    def get_go_sons_by_ontology_using_valid_edges(self, go_name):
        sons = set()
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return sons
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_father_son:
            return sons

        ontology = self.go_single_details(go_name)['namespace']

        for go_data in self.__triplets_father_son[go_name]:
            if go_data[2] == ontology and go_data[1] in self.__valid_edges:
                sons.add(go_data[0])

        return sons

    def get_go_sons_by_ontology(self, go_name):
        sons = set()
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return sons
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_father_son:
            return sons

        ontology = self.go_single_details(go_name)['namespace']

        for go_data in self.__triplets_father_son[go_name]:
            if go_data[2] == ontology:
                sons.add(go_data[0])

        return sons

    def get_go_sons_using_valid_edges(self, go_name):
        sons = set()
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return sons
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_father_son:
            return sons

        for go_data in self.__triplets_father_son[go_name]:
            if go_data[1] in self.__valid_edges:
                sons.add(go_data[0])

        return sons

    def get_sons(self):
        return self.__triplets_father_son

    def get_secondary_ids(self):
        return self.__secondary_ids_to_primary

    def is_secondary_id(self, go_name):
        return go_name in self.__secondary_ids_to_primary

    def get_primary_go_from_secondary_id(self, go_name):
        if not self.is_secondary_id(go_name):
            return None
        return self.__secondary_ids_to_primary[go_name]

    def get_secondary_ids_from_go(self, go_name):
        if go_name not in self.__primary_to_secondary_ids:
            return set()
        return self.__primary_to_secondary_ids[go_name]

    def go_descendants(self, go):
        go_done = {}
        go_list = []
        #  children to iterate
        #  go_children contains a set where:
        #  0  go name of the child
        #  1  type of relation with parent
        #  2  namespace (biological process etc)
        #  3  brief description of the GO
        #  4  long description of the GO
        if go not in self.__triplets_father_son and go not in self.__secondary_ids_to_primary:
            return go_done
        if go in self.__secondary_ids_to_primary:
            go = self.__secondary_ids_to_primary[go]
        if go not in self.__triplets_father_son:
            return go_done

        go_children = self.__triplets_father_son[go]
        #  initialize the list of iteration
        go_list.append(go_children)
        while len(go_list) > 0:
            #  take the list of children of one parent one by one
            go_set = go_list.pop(0)
            #  iterate the list of descendants
            for go_p in go_set:
                if go_p[0] in go_done:
                    continue
                if go_p[0].startswith("GO_"):
                    go_done[go_p[0]] = {'rel': go_p[1],
                                        'name': go_p[3],
                                        'descr': go_p[4],
                                        'namespace': go_p[2]
                                        }  # put something
                    if go_p[0] in self.__triplets_father_son.keys() and len(self.__triplets_father_son[go_p[0]]) > 0:
                        go_list.append(self.__triplets_father_son[go_p[0]])
                    #  END IF
                #  END IF
            #  END FOR
        #  END WHILE
        #  return dictionary with GO and brief description
        return go_done
    #  END DEF

    def go_descendants_by_ontology(self, go_name):
        go_done = {}
        go_list = []
        #  children to iterate
        #  go_children contains a set where:
        #  0  go name of the child
        #  1  type of relation with parent
        #  2  namespace (biological process etc)
        #  3  brief description of the GO
        #  4  long description of the GO
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return go_done
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_father_son:
            return go_done

        ontology = self.go_single_details(go_name)['namespace']

        go_children = self.__triplets_father_son[go_name]
        #  initialize the list of iteration
        go_list.append(go_children)
        while len(go_list) > 0:
            #  take the list of children of one parent one by one
            go_set = go_list.pop(0)
            #  iterate the list of descendants
            for go_p in go_set:
                if go_p[0] in go_done:
                    continue
                if go_p[0].startswith("GO_") and go_p[2] == ontology:
                    go_done[go_p[0]] = {'rel': go_p[1],
                                        'name': go_p[3],
                                        'descr': go_p[4],
                                        'namespace': go_p[2]
                                        }  # put something
                    if go_p[0] in self.__triplets_father_son and len(self.__triplets_father_son[go_p[0]]) > 0:
                        go_list.append(self.__triplets_father_son[go_p[0]])
                    #  END IF
                #  END IF
            #  END FOR
        #  END WHILE
        #  return dictionary with GO and brief description
        return go_done
    #  END DEF

    def go_descendants_using_valid_edges(self, go_name):
        go_done = {}
        go_list = []
        #  children to iterate
        #  go_children contains a set where:
        #  0  go name of the child
        #  1  type of relation with parent
        #  2  namespace (biological process etc)
        #  3  brief description of the GO
        #  4  long description of the GO
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return go_done
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_father_son:
            return go_done

        go_children = self.__triplets_father_son[go_name]
        #  initialize the list of iteration
        go_list.append(go_children)
        while len(go_list) > 0:
            #  take the list of children of one parent one by one
            go_set = go_list.pop(0)
            #  iterate the list of descendants
            for go_p in go_set:
                if go_p[0] in go_done:
                    continue
                if go_p[0].startswith("GO_") and go_p[1] in self.__valid_edges:
                    go_done[go_p[0]] = {'rel': go_p[1],
                                        'name': go_p[3],
                                        'descr': go_p[4],
                                        'namespace': go_p[2]
                                        }  # put something
                    if go_p[0] in self.__triplets_father_son.keys() and len(self.__triplets_father_son[go_p[0]]) > 0:
                        go_list.append(self.__triplets_father_son[go_p[0]])
                    #  END IF
                #  END IF
            #  END FOR
        #  END WHILE
        #  return dictionary with GO and brief description
        return go_done
    #  END DEF

    def go_descendants_by_ontology_using_valid_edges(self, go_name):
        go_done = {}
        go_list = []
        #  children to iterate
        #  go_children contains a set where:
        #  0  go name of the child
        #  1  type of relation with parent
        #  2  namespace (biological process etc)
        #  3  brief description of the GO
        #  4  long description of the GO
        if go_name not in self.__triplets_father_son and go_name not in self.__secondary_ids_to_primary:
            return go_done
        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]
        if go_name not in self.__triplets_father_son:
            return go_done

        ontology = self.go_single_details(go_name)['namespace']
        go_children = self.__triplets_father_son[go_name]
        #  initialize the list of iteration
        go_list.append(go_children)
        while len(go_list) > 0:
            #  take the list of children of one parent one by one
            go_set = go_list.pop(0)
            #  iterate the list of descendants
            for go_p in go_set:
                if go_p[0] in go_done:
                    continue
                if go_p[0].startswith("GO_") and go_p[1] in self.__valid_edges and go_p[2] == ontology:
                    go_done[go_p[0]] = {'rel': go_p[1],
                                        'name': go_p[3],
                                        'descr': go_p[4],
                                        'namespace': go_p[2]
                                        }  # put something
                    if go_p[0] in self.__triplets_father_son.keys() and len(self.__triplets_father_son[go_p[0]]) > 0:
                        go_list.append(self.__triplets_father_son[go_p[0]])
                    #  END IF
                #  END IF
            #  END FOR
        #  END WHILE
        #  return dictionary with GO and brief description
        return go_done
    #  END DEF

    def listing(self):
        return self.__global
    #  END DEF

    def listing_by_ontology(self, ontology):
        nodes = set()
        for go in self.__global.keys():
            if self.go_single_details(go)['namespace'] == self.__ontology_converter[str(ontology).upper()]:
                nodes.add(go)

        return nodes

    def listing_by_ontology_without_root(self, ontology):
        nodes = set()
        for go in self.__global.keys():
            if go in self.__roots:
                continue
            if self.go_single_details(go)['namespace'] == self.__ontology_converter[str(ontology).upper()]:
                nodes.add(go)

        return nodes

    def listing_total(self):
        return self.__global_total

    def go_taxon_constraints(self, go_name):
        if 'go-plus' not in self.__owl:
            e_print('The method go_taxon_constraints only works with the go-plus.')
        taxon_constraints = {}
        i = 1
        if go_name in self.__global.keys():
            go_concept = self.__global[go_name]
            taxon = go_concept.RO_0002161
            for i in range(len(taxon)):
                taxon[i] = int(str(taxon[i]).strip().split('/')[-1].strip().split('_')[-1])

            for parent in go_concept.is_a:
                #print(type(parent))
                if isinstance(parent, Restriction):
                    if isinstance(parent.value, Not):
                        if parent.property.label.first().find('taxon') >= 0:
                            taxon_constraints[i] = {'rel': 'Never ' + parent.property.label.first(),
                                                    'taxonId': parent.value.Class.name,
                                                    'taxonName': parent.value.Class.label.first()
                                                    }
                            i += 1
                        #  END IF
                    else:
                        if parent.property.label.first().find('taxon') >= 0:
                            taxon_constraints[i] = {'rel': parent.property.label.first(),
                                                    'taxonId': parent.value.name,
                                                    'taxonName': parent.value.label.first()
                                                    }
                            i += 1
                        #  END IF
                    #  END IF
                #  END IF
            #  END FOR
        return taxon_constraints
    #  END DEF

    def get_gos_by_distance(self, node, d=0):
        distance_list = []
        distance_queue = []
        visited = set()

        for i in range(d + 2):
            distance_queue.append([])
            distance_list.append([])

        distance_queue[0].append(node)
        distance_list[0].append(node)

        if d <= 0:
            return set(distance_list[0])

        j = 0
        while True:
            if j >= d and len(distance_queue[d]) == 0:
                break

            while len(distance_queue[j]) > 0:
                curr_node = distance_queue[j].pop(0)
                if curr_node in visited:
                    continue
                visited.add(curr_node)
                new_nodes = self.get_go_fathers(curr_node) | self.get_go_sons(curr_node)
                distance_list[j + 1].extend(list(new_nodes))
                distance_queue[j + 1].extend(list(new_nodes))

            j += 1

        nodes_set = set()
        for i in range(d + 1):
            nodes_set |= set(distance_list[i])

        return nodes_set

    def get_gos_by_ontology_by_distance(self, node, d=0):
        distance_list = []
        distance_queue = []
        visited = set()

        for i in range(d + 2):
            distance_queue.append([])
            distance_list.append([])

        distance_queue[0].append(node)
        distance_list[0].append(node)

        if d <= 0:
            return set(distance_list[0])

        j = 0
        while True:
            if j >= d and len(distance_queue[d]) == 0:
                break

            while len(distance_queue[j]) > 0:
                curr_node = distance_queue[j].pop(0)
                if curr_node in visited:
                    continue
                visited.add(curr_node)
                new_nodes = self.get_go_fathers_by_ontology(curr_node) | self.get_go_sons_by_ontology(curr_node)
                distance_list[j + 1].extend(list(new_nodes))
                distance_queue[j + 1].extend(list(new_nodes))

            j += 1

        nodes_set = set()
        for i in range(d + 1):
            nodes_set |= set(distance_list[i])

        return nodes_set

    def get_gos_using_valid_edges_by_distance(self, node, d=0):
        distance_list = []
        distance_queue = []
        visited = set()

        for i in range(d + 2):
            distance_queue.append([])
            distance_list.append([])

        distance_queue[0].append(node)
        distance_list[0].append(node)

        if d <= 0:
            return set(distance_list[0])

        j = 0
        while True:
            if j >= d and len(distance_queue[d]) == 0:
                break

            while len(distance_queue[j]) > 0:
                curr_node = distance_queue[j].pop(0)
                if curr_node in visited:
                    continue
                visited.add(curr_node)
                new_nodes = self.get_go_fathers_using_valid_edges(curr_node) | self.get_go_sons_using_valid_edges(
                    curr_node)
                distance_list[j + 1].extend(list(new_nodes))
                distance_queue[j + 1].extend(list(new_nodes))

            j += 1

        nodes_set = set()
        for i in range(d + 1):
            nodes_set |= set(distance_list[i])

        return nodes_set

    def get_gos_by_ontology_using_valid_edges_by_distance(self, node, d=0, descend=False):
        distance_list = []
        distance_queue = []
        visited = set()

        for i in range(d + 2):
            distance_queue.append([])
            distance_list.append([])

        distance_queue[0].append(node)
        distance_list[0].append(node)

        if d <= 0:
            return set(distance_list[0])

        j = 0
        while True:
            if j >= d and len(distance_queue[d]) == 0:
                break

            while len(distance_queue[j]) > 0:
                curr_node = distance_queue[j].pop(0)
                if curr_node in visited:
                    continue
                visited.add(curr_node)
                new_nodes = self.get_go_fathers_by_ontology_using_valid_edges(curr_node)
                if descend:
                    new_nodes |= self.get_go_sons_by_ontology_using_valid_edges(curr_node)
                distance_list[j + 1].extend(list(new_nodes))
                distance_queue[j + 1].extend(list(new_nodes))

            j += 1

        nodes_set = set()
        for i in range(d + 1):
            nodes_set |= set(distance_list[i])

        return nodes_set

    ################################################################################################
    #  CUMULATIVE MEMORY AWARE (as if it were a hierarchy rather than a graph)
    ################################################################################################

    def cumulative_freq_prior(self):
        #  fill cumulative
        cumulative = {}
        for go in self.__global:
            cumulative[go] = 1
        #  END FOR
        for go in self.__global:  # any GO
            cumulative = self.bfs_prior(go, cumulative)
        #  END FOR
        return cumulative

    #  END DEF

    def bfs_prior(self, start, cumulative):
        visited = set()
        queue = [start]
        while queue:
            vertex = queue.pop(0)
            if vertex not in visited:
                if vertex != start:
                    cumulative[vertex] += 1
                #  END IF
                visited.add(vertex)
                queue.extend(self.__triplets_son_father_go_only[vertex] - visited)
            #  END IF
        #  END WHILE
        return cumulative

    #  END DEF

    def cumulative_freq_corpus(self, list_goa):
        #  fill cumulative
        cumulative = {}
        #  initialize listGOA with corpus in the cumulative dictionary
        #  that will grow when cycling over
        for go in self.__global:
            if go in list_goa:
                cumulative[go] = list_goa[go]
            else:
                cumulative[go] = 0
            #  END IF
        #  END FOR
        for go in self.__global:  # any GO
            cumulative = self.bfs_corpus(go, cumulative, list_goa)
        #  END FOR
        return cumulative

    #  END DEF

    def bfs_corpus(self, start, cumulative, list_goa):
        visited = set()
        queue = [start]
        #  initialize add that is the real use of that GO in GOA (stored in listGOA
        #  and propagate it over whole ancestors of "start" using cumulative that will store
        #  the overall iterative growing occurrences
        add = 0
        if start in list_goa:
            add = list_goa[start]
        #  END IF
        while queue:
            vertex = queue.pop(0)
            if vertex not in visited:
                if vertex != start:
                    cumulative[vertex] += add
                #  END IF
                visited.add(vertex)
                queue.extend(self.__triplets_son_father_go_only[vertex] - visited)
            #  END IF
        #  END WHILE
        return cumulative

    #  END DEF

    ################################################################################################
    #  CUMULATIVE MEMORYLESS. Do any path to root even if passing through the same node many times
    #          Takes into account all of the edges that create different paths in the graph
    #          If it were a hierarchy, the result would exactly the same obtained by
    #          CUMULATIVE MEMORY AWARE (see above)
    ################################################################################################
    def cumulative_freq_prior_ml(self):
        #  fill cumulative
        cumulative = {}
        for go in self.__global:
            cumulative[go] = 1
        #  END FOR
        for go in self.__global:  # any GO
            cumulative = self.bfs_prior_ml(go, cumulative)
        #  END FOR
        return cumulative

    #  END DEF

    def bfs_prior_ml(self, start, cumulative):
        queue = [start]
        while queue:
            vertex = queue.pop(0)
            if vertex != start:
                cumulative[vertex] += 1
            #  END IF
            queue.extend(self.__triplets_son_father_go_only[vertex])
        #  END WHILE
        return cumulative

    #  END DEF

    def cumulative_freq_corpus_ml(self, list_goa):
        #  fill cumulative
        cumulative = {}
        #  initialize listGOA with corpus in the cumulative dictionary
        #  that will grow when cycling over
        for go in self.__global:
            if go in list_goa:
                cumulative[go] = list_goa[go]
            else:
                cumulative[go] = 0
            #  END IF
        #  END FOR
        for go in self.__global:  # any GO
            cumulative = self.bfs_corpus_ml(go, cumulative, list_goa)
        # END FOR
        return cumulative

    #  END DEF

    def bfs_corpus_ml(self, start, cumulative, list_goa):
        if start in self.__secondary_ids_to_primary:
            start = self.__secondary_ids_to_primary[start]

        queue = [start]
        #  initialize add that is the real use of that GO in GOA (stored in list_goa
        #  and propagate it over whole ancestors of "start" using cumulative that will store
        #  the overall iterative growing occurrences
        add = 0
        if start in list_goa:
            add = list_goa[start]
        #  END IF
        while queue:
            vertex = queue.pop(0)
            if vertex != start:
                cumulative[vertex] += add
            #  END IF
            queue.extend(self.__triplets_son_father_go_only[vertex])
        #  END WHILE
        return cumulative

    #  END DEF

    def cumulative_freq_corpus_ml_by_ontology(self, list_goa):
        #  fill cumulative
        cumulative = {}
        #  initialize listGOA with corpus in the cumulative dictionary
        #  that will grow when cycling over
        for go in self.__global:
            if go in list_goa:
                cumulative[go] = list_goa[go]
            else:
                cumulative[go] = 0
            # END IF
        # END FOR
        for go in self.__global:  # any GO
            cumulative = self.bfs_corpus_ml_by_ontology(go, cumulative, list_goa)
        # END FOR
        return cumulative

    # END DEF

    def bfs_corpus_ml_by_ontology(self, start, cumulative, list_goa):
        if start in self.__secondary_ids_to_primary:
            start = self.__secondary_ids_to_primary[start]

        ontology = self.go_single_details(start)['namespace']
        queue = [start]
        #  initialize add that is the real use of that GO in GOA (stored in list_goa
        #  and propagate it over whole ancestors of "start" using cumulative that will store
        #  the overall iterative growing occurrences
        add = 0
        if start in list_goa:
            add = list_goa[start]
        #  END IF
        while queue:
            vertex = queue.pop(0)
            if vertex != start:
                cumulative[vertex] += add
            #  END IF
            try:
                for son in self.__triplets_son_father[vertex]:
                    if son[2] == ontology and son[1] in self.__valid_edges:
                        queue.append(son[0])
                    #  END IF
                #  END FOR
            except KeyError:
                continue
        #  END WHILE
        return cumulative
        #  END DEF

    ###################################################################################

    def __go_parents(self, go_name):
        #  find children first level of a GO (with restriction and limited to those
        #  that have transitive properties and these are
        #    is a
        #    part of
        #    regulates
        #    positively regulates
        #    negatively regulates
        #    occurs in
        #    capable of
        #    capable of part of
        #  for go_concept in obo.classes():
        parents = {}
        if go_name in self.__global.keys():
            go_concept = self.__global[go_name]
            #  try to record here specific restrictions of this GO
            if go_concept.label.first():
                if not go_concept.label.first().startswith("obsolete"):
                    for parent in go_concept.is_a:
                        if isinstance(parent, Restriction):
                            if isinstance(parent.value, Not):
                                pass
                            else:
                                if parent.value.name.startswith("GO_"):
                                    if parent.property.label.first() == 'part of' or parent.property.label.first().find(
                                            "regulates") >= 0 or parent.property.label.first() == 'occurs in' or parent.property.label.first().find(
                                            'capable of') >= 0:
                                        #  create parent description
                                        try:
                                            description = parent.value.hasDefinition.first().label.first()
                                        except AttributeError:
                                            description = parent.value.IAO_0000115.first()

                                        parents[parent.value.name] = {'rel': parent.property.label.first(),
                                                                      'name': parent.value.label.first(),
                                                                      'descr': description,
                                                                      'namespace': parent.value.hasOBONamespace.first()
                                                                      }
                                #  END IF
                            #  END IF
                        else:
                            if parent.name.startswith("GO_"):
                                try:
                                    description = parent.hasDefinition.first().label.first()
                                except AttributeError:
                                    description = parent.IAO_0000115.first()

                                parents[parent.name] = {'rel': 'is a',
                                                        'name': parent.label.first(),
                                                        'descr': description,
                                                        'namespace': parent.hasOBONamespace.first()
                                                        }
                            #  END IF
                        #  END IF
                    #  END FOR
                    for equiv in go_concept.INDIRECT_equivalent_to:
                        if isinstance(equiv, And):
                            for equiv_parent in equiv.Classes:
                                if isinstance(equiv_parent, Restriction):
                                    if equiv_parent.value.name.startswith("GO_"):
                                        if equiv_parent.property.label.first() == 'part of' or equiv_parent.property.label.first().find(
                                                "regulates") >= 0 or equiv_parent.property.label.first() == 'occurs in' or equiv_parent.property.label.first().find(
                                                'capable of') >= 0:
                                            try:
                                                description = equiv_parent.value.hasDefinition.first().label.first()
                                            except AttributeError:
                                                description = equiv_parent.value.IAO_0000115.first()
                                            parents[equiv_parent.value.name] = {
                                                'rel': equiv_parent.property.label.first(),
                                                'name': equiv_parent.value.label.first(),
                                                'descr': description,
                                                'namespace': equiv_parent.value.hasOBONamespace.first()
                                                }
            #       DISCARD THIS PART OF CODE BECAUSE: this is not a is_a relationship but an intersection_of. In other words, what
            #                   is "intercepted" by this part of the code is the "name" of, for example, a GO that lets the
            #                   "intersection" then the "relationship" with what is reported in in the "if" statement above i.e. the
            #                   "restriction" part. THAT AND ONLY THAT, the restriction of the if statement, can be linked,
            #                       by means of the reported relationship, with the starting GO of the record
            #                                else:
            #                                    if equiv_parent.name.startswith("GO_"):
            #                                        parents[equiv_parent.name] = {'rel': 'is a',
            #                                                                      'name': equiv_parent.label.first(),
            #                                                                      'descr': equiv_parent.IAO_0000115.first(),
            #                                                                      'namespace': equiv_parent.hasOBONamespace.first()
            #                                                                      }
            #  END IF
            #  END FOR
            #  END IF
            #  END FOR
            #  END IF
            #  END IF
            return parents
        else:
            return parents
        #  END IF

    #  END DEF

    def go_parents(self, go_name):
        parents = {}

        if go_name not in self.__global and go_name not in self.__secondary_ids_to_primary:
            return parents

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        if go_name not in self.__triplets_son_father:
            return parents

        for parent_data in self.__triplets_son_father[go_name]:
            parents[parent_data[0]] = {'rel': parent_data[1],
                                       'name': parent_data[3],
                                       'descr': parent_data[4],
                                       'namespace': parent_data[2]}

        return parents

    def go_parents_using_valid_edges(self, go_name):
        #  find children first level of a GO (with restriction and limited to those
        #  that have transitive properties and these are
        #    is a
        #    part of
        #    regulates
        #    positively regulates
        #    negatively regulates
        #    occurs in
        #    capable of
        #    capable of part of
        #  for go_concept in obo.classes():
        parents = {}

        if go_name not in self.__global and go_name not in self.__secondary_ids_to_primary:
            return parents

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        if go_name not in self.__triplets_son_father:
            return parents

        for parent_data in self.__triplets_son_father[go_name]:
            if parent_data[1] in self.__valid_edges:
                parents[parent_data[0]] = {'rel': parent_data[1],
                                           'name': parent_data[3],
                                           'descr': parent_data[4],
                                           'namespace': parent_data[2]}

        return parents

    #  END DEF

    def go_parents_by_ontology(self, go_name):
        #  find children first level of a GO (with restriction and limited to those
        #  that have transitive properties and these are
        #    is a
        #    part of
        #    regulates
        #    positively regulates
        #    negatively regulates
        #    occurs in
        #    capable of
        #    capable of part of
        #  for go_concept in obo.classes():
        ontology = self.go_single_details(go_name)['namespace']
        parents = {}

        if go_name not in self.__global and go_name not in self.__secondary_ids_to_primary:
            return parents

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        if go_name not in self.__triplets_son_father:
            return parents

        for parent_data in self.__triplets_son_father[go_name]:
            if parent_data[2] == ontology:
                parents[parent_data[0]] = {'rel': parent_data[1],
                                           'name': parent_data[3],
                                           'descr': parent_data[4],
                                           'namespace': parent_data[2]}
        '''
        if go_name in self.__global.keys():
            go_concept = self.__global[go_name]
            #  try to record here specific restrictions of this GO
            if go_concept.label.first():
                if not go_concept.label.first().startswith("obsolete"):
                    for parent in go_concept.is_a:
                        if isinstance(parent, Restriction):
                            if isinstance(parent.value, Not):
                                pass
                            else:
                                if parent.value.name.startswith("GO_"):
                                    if parent.value.hasOBONamespace.first() == ontology:
                                        #  create parent description
                                        try:
                                            description = parent.value.hasDefinition.first().label.first()
                                        except AttributeError:
                                            description = parent.value.IAO_0000115.first()

                                        parents[parent.value.name] = {'rel': parent.property.label.first(),
                                                                      'name': parent.value.label.first(),
                                                                      'descr': description,
                                                                      'namespace': parent.value.hasOBONamespace.first()
                                                                      }
                                #  END IF
                            #  END IF
                        else:
                            if parent.name.startswith("GO_") and parent.hasOBONamespace.first() == namespace:
                                try:
                                    description = parent.hasDefinition.first().label.first()
                                except AttributeError:
                                    description = parent.IAO_0000115.first()

                                parents[parent.name] = {'rel': 'is a',
                                                        'name': parent.label.first(),
                                                        'descr': description,
                                                        'namespace': parent.hasOBONamespace.first()
                                                        }
                            #  END IF
                        #  END IF
                    #  END FOR
                    for equiv in go_concept.INDIRECT_equivalent_to:
                        if isinstance(equiv, And):
                            for equiv_parent in equiv.Classes:
                                if isinstance(equiv_parent, Restriction):
                                    if equiv_parent.value.name.startswith("GO_"):
                                        if equiv_parent.value.hasOBONamespace.first() == ontology:
                                            try:
                                                description = equiv_parent.value.hasDefinition.first().label.first()
                                            except AttributeError:
                                                description = equiv_parent.value.IAO_0000115.first()

                                            parents[equiv_parent.value.name] = {
                                                'rel': equiv_parent.property.label.first(),
                                                'name': equiv_parent.value.label.first(),
                                                'descr': description,
                                                'namespace': equiv_parent.value.hasOBONamespace.first()
                                                }
            return parents
        else:
            return parents
        #  END IF
        '''
        return parents

    #  END DEF

    def go_parents_by_ontology_using_valid_edges(self, go_name):
        #  find children first level of a GO (with restriction and limited to those
        #  that have transitive properties and these are
        #    is a
        #    part of
        #    regulates
        #    positively regulates
        #    negatively regulates
        #    occurs in
        #    capable of
        #    capable of part of
        #  for go_concept in obo.classes():
        ontology = self.go_single_details(go_name)['namespace']
        parents = {}

        if go_name not in self.__global and go_name not in self.__secondary_ids_to_primary:
            return parents

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        if go_name not in self.__triplets_son_father:
            return parents

        for parent_data in self.__triplets_son_father[go_name]:
            if parent_data[2] == ontology and parent_data[1] in self.__valid_edges:
                parents[parent_data[0]] = {'rel': parent_data[1],
                                           'name': parent_data[3],
                                           'descr': parent_data[4],
                                           'namespace': parent_data[2]}

        '''
        if go_name in self.__global.keys():
            go_concept = self.__global[go_name]
            #  try to record here specific restrictions of this GO
            if go_concept.label.first():
                if not go_concept.label.first().startswith("obsolete"):
                    for parent in go_concept.is_a:
                        if isinstance(parent, Restriction):
                            if isinstance(parent.value, Not):
                                pass
                            else:
                                if parent.value.name.startswith("GO_"):
                                    if parent.property.label.first() in self.__valid_edges and parent.value.hasOBONamespace.first() == ontology:
                                        try:
                                            description = parent.value.hasDefinition.first().label.first()
                                        except AttributeError:
                                            description = parent.value.IAO_0000115.first()

                                        parents[parent.value.name] = {'rel': parent.property.label.first(),
                                                                      'name': parent.value.label.first(),
                                                                      'descr': description,
                                                                      'namespace': parent.value.hasOBONamespace.first()
                                                                      }
                                #  END IF
                            #  END IF
                        else:
                            if parent.name.startswith("GO_") and parent.hasOBONamespace.first() == ontology:
                                try:
                                    description = parent.hasDefinition.first().label.first()
                                except AttributeError:
                                    description = parent.IAO_0000115.first()

                                parents[parent.name] = {'rel': 'is a',
                                                        'name': parent.label.first(),
                                                        'descr': description,
                                                        'namespace': parent.hasOBONamespace.first()
                                                        }
                            #  END IF
                        #  END IF
                    #  END FOR
                    for equiv in go_concept.INDIRECT_equivalent_to:
                        if isinstance(equiv, And):
                            for equiv_parent in equiv.Classes:
                                if isinstance(equiv_parent, Restriction):
                                    if equiv_parent.value.name.startswith("GO_"):
                                        if equiv_parent.property.label.first() in self.__valid_edges and equiv_parent.value.hasOBONamespace.first() == ontology:
                                            try:
                                                description = equiv_parent.value.hasDefinition.first().label.first()
                                            except AttributeError:
                                                description = equiv_parent.value.IAO_0000115.first()

                                            parents[equiv_parent.value.name] = {
                                                'rel': equiv_parent.property.label.first(),
                                                'name': equiv_parent.value.label.first(),
                                                'descr': description,
                                                'namespace': equiv_parent.value.hasOBONamespace.first()
                                                }
            return parents
        else:
            return parents
        #  END IF
        '''
        return parents

    #  END DEF

    def go_ancestors(self, go_name):
        go_done = {}
        go_list = []

        if go_name not in self.__triplets_son_father and go_name not in self.__secondary_ids_to_primary:
            return go_done

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        go_list.append(go_name)

        while len(go_list) > 0:
            current_node = go_list.pop(0)
            try:
                parents = self.__triplets_son_father[current_node]
                for parent_data in parents:
                    if parent_data[0] in go_done:
                        continue
                    go_list.append(parent_data[0])
                    go_done[parent_data[0]] = {'rel': parent_data[1],
                                               'name': parent_data[3],
                                               'descr': parent_data[4],
                                               'namespace': parent_data[2]}
            except KeyError:
                continue
        '''
        go_done = {}
        go_iter_lst = []
        go_list = self.go_parents(go_name)
        go_iter_lst.append(go_list)
        i = 0
        status = True
        while status:
            try:
                go_lst = go_iter_lst[i]
                for go_p, details in go_lst.items():
                    if go_p not in go_done and go_p.startswith("GO_"):
                        go_done[go_p] = details
                        go_list2 = self.go_parents(go_p)
                        go_iter_lst.append(go_list2)
                        #  put the relations here?
                    #  END IF
                #  END FOR
                i = i+1
            except:
                break
            #  END TRY
        #  END WHILE
        '''
        return go_done

    #  END DEF

    def go_ancestors_using_valid_edges(self, go_name):
        go_done = {}
        go_list = []
        if go_name not in self.__triplets_son_father and go_name not in self.__secondary_ids_to_primary:
            return go_done

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        go_list.append(go_name)

        while len(go_list) > 0:
            current_node = go_list.pop(0)
            try:
                parents = self.__triplets_son_father[current_node]
                for parent_data in parents:
                    if parent_data[0] in go_done or parent_data[1] not in self.__valid_edges:
                        continue
                    go_list.append(parent_data[0])
                    go_done[parent_data[0]] = {'rel': parent_data[1],
                                               'name': parent_data[3],
                                               'descr': parent_data[4],
                                               'namespace': parent_data[2]}
            except KeyError:
                continue
        '''
        go_done = {}
        go_iter_lst = []
        go_list = self.go_parents(go_name)
        tmp_list = {}
        for go_id in go_list:
            if go_list[go_id]['rel'] in self.__valid_edges:
                tmp_list[go_id] = go_list[go_id]

        go_iter_lst.append(tmp_list)
        i = 0
        while True:
            try:
                go_lst = go_iter_lst[i]
                for go_p, details in go_lst.items():
                    if go_p not in go_done and go_p.startswith("GO_"):
                        go_done[go_p] = details
                        go_list2 = self.go_parents(go_p)
                        tmp_list2 = {}
                        for go_id in go_list2:
                            if go_list2[go_id]['rel'] in self.__valid_edges:
                                tmp_list2[go_id] = go_list2[go_id]
                        go_iter_lst.append(tmp_list2)
                    #  END IF
                #  END FOR
                i = i+1
            except:
                break
            #  END TRY
        #  END WHILE
        '''
        return go_done

    #  END DEF

    def go_ancestors_by_ontology(self, go_name):
        go_done = {}
        go_list = []
        if go_name not in self.__triplets_son_father and go_name not in self.__secondary_ids_to_primary:
            return go_done

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        ontology = self.go_single_details(go_name)['namespace']
        go_list.append(go_name)

        while len(go_list) > 0:
            current_node = go_list.pop(0)
            try:
                parents = self.__triplets_son_father[current_node]
                for parent_data in parents:
                    if parent_data[0] in go_done or parent_data[2] != ontology:
                        continue
                    go_list.append(parent_data[0])
                    go_done[parent_data[0]] = {'rel': parent_data[1],
                                               'name': parent_data[3],
                                               'descr': parent_data[4],
                                               'namespace': parent_data[2]}
            except KeyError:
                continue
        '''
        go_done = {}
        go_iter_lst = []
        ontology = self.go_single_details(go_name)['namespace']
        go_list = self.go_parents(go_name)
        tmp_list = {}
        for go_id in go_list:
            if go_list[go_id]['namespace'] == ontology:
                tmp_list[go_id] = go_list[go_id]

        go_iter_lst.append(tmp_list)
        i = 0
        while True:
            try:
                go_lst = go_iter_lst[i]
                for go_p, details in go_lst.items():
                    if go_p not in go_done and go_p.startswith("GO_"):
                        go_done[go_p] = details
                        go_list2 = self.go_parents(go_p)
                        tmp_list2 = {}
                        for go_id in go_list2:
                            if go_list2[go_id]['namespace'] == ontology:
                                tmp_list2[go_id] = go_list2[go_id]
                        go_iter_lst.append(tmp_list2)
                    #  END IF
                #  END FOR
                i = i+1
            except:
                break
            #  END TRY
        #  END WHILE
        '''
        return go_done

    #  END DEF

    def go_ancestors_by_ontology_using_valid_edges(self, go_name):
        go_done = {}
        go_list = []

        if go_name in self.__secondary_ids_to_primary:
            go_name = self.__secondary_ids_to_primary[go_name]

        ontology = self.go_single_details(go_name)['namespace']
        go_list.append(go_name)

        while len(go_list) > 0:
            current_node = go_list.pop(0)
            try:
                parents = self.__triplets_son_father[current_node]
                for parent_data in parents:
                    if parent_data[0] in go_done or parent_data[2] != ontology or parent_data[1] not in self.__valid_edges:
                        continue
                    go_list.append(parent_data[0])
                    go_done[parent_data[0]] = {'rel': parent_data[1],
                                               'name': parent_data[3],
                                               'descr': parent_data[4],
                                               'namespace': parent_data[2]}
            except KeyError:
                continue

        '''
        go_done = {}
        go_iter_lst = []
        ontology = self.go_single_details(go_name)['namespace']
        go_list = self.go_parents(go_name)
        tmp_list = {}
        for go_id in go_list:
            if go_list[go_id]['namespace'] == ontology and go_list[go_id]['rel'] in self.__valid_edges:
                tmp_list[go_id] = go_list[go_id]

        go_iter_lst.append(tmp_list)
        i = 0
        while True:
            try:
                for go_p, details in go_iter_lst[i].items():
                    if go_p not in go_done and go_p.startswith("GO_"):
                        go_done[go_p] = details
                        go_list2 = self.go_parents(go_p)
                        tmp_list2 = {}
                        for go_id in go_list2:
                            if go_list2[go_id]['namespace'] == ontology and go_list2[go_id]['rel'] in self.__valid_edges:
                                tmp_list2[go_id] = go_list2[go_id]
                        go_iter_lst.append(tmp_list2)
                    #  END IF
                #  END FOR
                i += 1
            except:
                break
            #  END TRY
        #  END WHILE
        '''
        return go_done

    #  END DEF

    def compute_simgic(self, go_1, go_2):
        if self.__by_ontology:
            set_1 = set(self.go_ancestors_by_ontology_using_valid_edges(go_1).keys())
            set_2 = set(self.go_ancestors_by_ontology_using_valid_edges(go_2).keys())
        else:
            set_1 = set(self.go_ancestors(go_1).keys())
            set_2 = set(self.go_ancestors(go_2).keys())

        set_1.add(go_1)
        set_2.add(go_2)
        intersect = set_1.intersection(set_2)
        union = set_1.union(set_2)
        ic_intersect = 0.0
        ic_union = 0.0

        for item in intersect:
            if item in self.__gos_ic:
                ic_intersect += self.__gos_ic[item]

        for item in union:
            if item in self.__gos_ic:
                ic_union += self.__gos_ic[item]

        try:
            return ic_intersect / ic_union
        except ZeroDivisionError:
            return 0.0

    def compute_ic(self, goa_file):
        gos = {}
        with open(goa_file, 'r') as GOA:
            for line in GOA:
                if line.startswith('!'):
                    continue

                data = line.strip().split('\t')
                if len(data) > 5:
                    if not self.__use_all_evidence:
                        if data[3] == 'NOT' or data[6] not in self.__valid_evidence or data[6] in {'ND', 'NR'}:
                            continue
                    else:
                        if data[3] == 'NOT' or data[6] in {'ND', 'NR'}:
                            continue

                    go = data[4].replace(':', '_')
                else:
                    go = data[1].replace(":", "_")

                if go in self.__secondary_ids_to_primary:
                    go = self.__secondary_ids_to_primary[go]

                if go not in gos:
                    gos[go] = 1
                else:
                    gos[go] += 1

        if self.__by_ontology:
            cumulative = self.cumulative_freq_corpus_ml_by_ontology(gos)
        else:
            cumulative = self.cumulative_freq_corpus_ml(gos)

        for go in cumulative:
            sub_ontology = self.go_single_details(go)['namespace']
            frequency = cumulative[go]

            if sub_ontology == 'molecular_function':
                ic = - math.log((frequency + 1) / (cumulative[self.__mf_root] + 1))
                self.__gos_ic[go] = ic
                self.__ic_gos.setdefault(ic, set())
                self.__ic_gos[ic].add((go, sub_ontology, ic))

            elif sub_ontology == 'biological_process':
                ic = - math.log((frequency + 1) / (cumulative[self.__bp_root] + 1))
                self.__gos_ic[go] = ic
                self.__ic_gos.setdefault(ic, set())
                self.__ic_gos[ic].add((go, sub_ontology, ic))

            elif sub_ontology == 'cellular_component':
                ic = - math.log((frequency + 1) / (cumulative[self.__cc_root] + 1))
                self.__gos_ic[go] = ic
                self.__ic_gos.setdefault(ic, set())
                self.__ic_gos[ic].add((go, sub_ontology, ic))

    def get_gos_ic(self):
        return self.__gos_ic

    def get_go_ic(self, go_id):
        if self.is_secondary_id(go_id):
            go_id = self.__secondary_ids_to_primary[go_id]

        try:
            return self.__gos_ic[go_id]
        except KeyError:
            return 0.0

    def get_ic_gos(self):
        return self.__ic_gos

    def get_gos_in_ic_range(self, low=0, hi=sys.float_info.max):
        gos = set()

        for ic in self.__ic_gos:
            if low <= ic <= hi:
                gos |= self.__ic_gos[ic]

        return gos

    def get_gos_by_ontology_in_ic_range(self, ontology, low=0, hi=sys.float_info.max):
        gos = set()

        for ic in self.__ic_gos:
            if low <= ic <= hi:
                for go_data in self.__ic_gos[ic]:
                    if self.go_single_details(go_data[0])['namespace'] == ontology:
                        gos.add(go_data[0])

        return gos
#  END CLASS

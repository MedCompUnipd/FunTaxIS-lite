# -------------------------------------------------------------------------------
# Name:        Taxon library
# Purpose:     parsing nodes.dmp Taxonomy from NCBI
#
# Author:      Stefano
#
# Created:     01/07/2019
# Copyright:   (c) Stefano 2019
# Licence:     GPL
# -------------------------------------------------------------------------------

import sys


class Taxon:
    def __init__(self, taxon_nodes, merged, file_of_names):
        self.__taxon_nodes_file = taxon_nodes
        self.__merged_file = merged
        self.__names_file = file_of_names
        self.__son_father = {}
        self.__father_son = {}
        self.__son_ancestors = {}
        self.__father_descendants = {}
        self.__merged_map = {}
        self.__name_id_map = {}
        self.__id_name_map = {}
        self.__rank_list = {}
        self.__valid_ranks = set()
        self.__valid_name_class = set()
        self.__loading()

    # END DEF

    def __loading(self):
        with open(self.__taxon_nodes_file, 'r') as fin:
            for line in fin:
                values = line.split("|")
                son = values[0].rstrip()
                son = son.lstrip()
                father = values[1].rstrip()
                father = father.lstrip()
                rank = values[2].rstrip()
                rank = rank.lstrip()
                self.__son_father[son] = father
                if father not in self.__father_son:
                    self.__father_son.setdefault(father, [])
                    self.__father_son[father].append(son)
                else:
                    self.__father_son[father].append(son)
                self.__rank_list[son] = rank
                if rank != 'no rank' and 'species' not in rank and 'sub' not in rank:
                    self.__valid_ranks.add(rank)
            # END FOR
        # END WITH
        fin.close()
        self.__valid_ranks.add('species')

        # Parse merged file
        with open(self.__merged_file) as fin:
            for line in fin:
                values = line.split("|")
                orig = values[0].rstrip()
                orig = orig.lstrip()
                substitute = values[1].rstrip()
                substitute = substitute.lstrip()
                self.__merged_map[orig] = substitute
            # END FOR
        # END WITH
        fin.close()

        # Parse names file
        with open(self.__names_file, 'r') as names:
            for line in names:
                line = line.strip()
                values = line.split('\t')
                name = values[2]
                taxon_id = values[0]
                name_class = values[6]
                self.__name_id_map.setdefault(name, set())
                self.__id_name_map.setdefault(taxon_id, set())
                self.__name_id_map[name].add(taxon_id)
                self.__id_name_map[taxon_id].add((name, name_class))
                self.__valid_name_class.add(name_class)
            # END FOR
        # END WITH
        names.close()
    # END DEF

    def merging(self):
        return self.__merged_map
    # END DEF

    def ancestors_full_list(self):
        for son, father in self.__son_father.items():
            son_iter = son
            father_iter = father
            status = True
            if son_iter not in self.__son_ancestors:
                self.__son_ancestors.setdefault(son_iter, [])
            # END IF
            while status:
                self.__son_ancestors[son_iter].append(father_iter)
                if father_iter == '1':
                    status = False
                    continue
                # END IF
                father_iter = self.__son_father[father_iter]
        # END WHILE
        # END FOR
        return self.__son_ancestors
    # END DEF

    def descendants_list(self, father):
        self.__father_descendants.setdefault(father, [])
        son = self.__father_son[father]
        queue = son.copy()
        while queue:
            vertex = queue.pop(0)
            self.__father_descendants[father].append(vertex)
            if vertex in self.__father_son:
                queue.extend(self.__father_son[vertex])
            # END IF
        # END WHILE
        return self.__father_descendants
    # END DEF

    def get_names_ids_map(self):
        return self.__name_id_map
    # END DEF

    def get_id_names_map(self):
        return self.__id_name_map

    def get_ids(self, name):
        if name not in self.__name_id_map:
            for taxon_name in self.__name_id_map.keys():
                if name in taxon_name:
                    return self.__name_id_map[taxon_name]
            return None
        return self.__name_id_map[name]

    def get_name(self, node, name_class='scientific name'):
        name = None

        if name_class not in self.__valid_name_class or node not in self.__id_name_map:
            return name

        for tp in self.__id_name_map[node]:
            if tp[1] == name_class:
                name = tp[0]
                break

        return name

    def get_node_rank(self, node):
        if node not in self.__rank_list:
            return None

        return self.__rank_list[node]

    def get_all_ancestors(self, node):
        ancestors = set()
        cur_node = node
        if node not in self.__son_father:
            return ancestors

        while True:
            cur_node = self.__son_father[cur_node]
            if cur_node == '1':
                break
            ancestors.add(cur_node)

        return ancestors

    def get_ancestor_at_rank(self, node, rank):
        if rank not in self.__valid_ranks or node not in self.__rank_list or node not in self.__son_father or rank in self.__rank_list[node]:
            return None

        if self.__rank_list[node] == rank:
            return node

        queue = [node]
        node_found = None

        while len(queue) > 0:
            cur_node = queue.pop(0)
            if cur_node == '1':
                break
            if cur_node in self.__rank_list:
                if rank not in self.__rank_list[cur_node] or self.__rank_list[cur_node] not in self.__valid_ranks:
                    queue.append(self.__son_father[cur_node])
                else:
                    node_found = cur_node
                    break

        return node_found

    def get_all_descendants(self, stating_node):
        queue = [stating_node]
        descendants = set()
        descendants.add(stating_node)

        while len(queue) > 0:
            father = queue.pop(0)
            if father not in self.__father_son:
                continue
            sons = self.__father_son[father]
            for son in sons:
                queue.append(son)
                descendants.add(son)

        return descendants

    def get_children(self, node):
        try:
            return self.__father_son[node]
        except KeyError:
            return set()

    def get_father(self, node):
        try:
            return self.__son_father[node]
        except KeyError:
            return set()

    def get_distance_from_node(self, stnode, destnode):
        father = self.get_father(stnode)
        d = 1
        while father != destnode:
            try:
                father = self.get_father(father)
                d += 1
                if father == '1' and destnode != '1':
                    d = -1
                    print('nodes are not connected')
                    break
            except KeyError:
                d = -1
                print('node is not connected to root')
                break
        return d


# END CLASS

# -------------------------------------------------------------------------------
# Name:        Taxon library
# Purpose:     parsing nodes.dmp Taxonomy from NCBI
#
# Author:      Stefano - Emilio - Ermanno
#
# Created:     21/01/2022
# Copyright:   (c) Stefano 2019
# Licence:     GPL
# -------------------------------------------------------------------------------

import sys
import time

sys.setrecursionlimit(10000)

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
                values = line.split('|')
                son = values[0].strip()
                father = values[1].strip()
                rank = values[2].strip()
                if son not in self.__son_father:
                    self.__son_father[son] = father
                if father not in self.__father_son:
                    self.__father_son[father] = []
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
                values = line.split('|')
                orig = values[0].strip()
                substitute = values[1].strip()
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
                if name not in self.__name_id_map:
                    self.__name_id_map[name] = set()
                if taxon_id not in self.__id_name_map:
                    self.__id_name_map[taxon_id] = set()
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


    def ancestors_full_list(self):  # OK (12 seconds)
        for son, father in self.__son_father.items():
            if son not in self.__son_ancestors:
                self.__son_ancestors[son] = set()
            # END IF

            self.__son_ancestors[son].add(father)
            while father != '1':
                father = self.__son_father[father]
                self.__son_ancestors[son].add(father)
            # END WHILE
        # END FOR

        return self.__son_ancestors
    # END DEF


    def descendants_full_list(self):  # OK (25 secondi)
        fathers = list(self.__father_son.keys())
        for father in fathers:
            if father not in self.__father_descendants:
                self.__father_descendants[father] = self.get_all_descendants(father)
            # END IF
        # END FOR

        return self.__father_descendants
    # END DEF


    def get_all_ancestors(self, node):  # OK (<< 1 second)
        ancestors = set()
        cur_node = node
        if node not in self.__son_father:
            return ancestors
        # END IF

        while True:
            cur_node = self.__son_father[cur_node]
            if cur_node == '1':
                ancestors.add(cur_node)
                break
            # END IF

            ancestors.add(cur_node)
        # END WHILE

        return ancestors
    # END DEF


    def get_all_descendants(self, starting_node, descendants=set(), first=True):  # OK (<= 1 second)
        if first:
            descendants = set()
        # END IF

        if starting_node == '1':
            for child in self.get_children(starting_node):
                descendants.update(self.get_all_descendants(child, descendants, False))
            # END FOR

        else:
            father = starting_node
            descendants.add(father)
            if father in self.__father_son:
                for child in self.__father_son[father]:
                    descendants.update(self.get_all_descendants(child, descendants, False))
                # END FOR

            else:
                descendants.add(father)
            # END IF
        # END IF

        if first:
            descendants.discard(starting_node)
        # END IF

        return descendants
    # END DEF


    def get_ancestor_at_rank(self, node, rank):  # OK (<< 1 second)
        if rank not in self.__valid_ranks or node not in self.__rank_list or node not in self.__son_father or rank in self.__rank_list[node]:
            return None
        # END IF

        if self.__rank_list[node] == rank:
            return node
        # END IF

        queue = [node]
        node_found = None

        while len(queue) > 0:
            cur_node = queue.pop(0)
            if cur_node == '1':
                break
            # END IF
            if cur_node in self.__rank_list:
                if rank not in self.__rank_list[cur_node] or self.__rank_list[cur_node] not in self.__valid_ranks:
                    queue.append(self.__son_father[cur_node])
                else:
                    node_found = cur_node
                    break
                # END IF
            # END IF
        # END WHILE

        return node_found
    # END DEF


    def get_children(self, node):  # OK  (<< 1 second)
        try:
            children = self.__father_son[node].copy()
            if node == '1':
                children.remove('1')
            # END IF

            return children
        except KeyError:
            return set()
        # END TRY
    # END DEF


    def get_father(self, node):  # OK (<< 1 second)
        try:
            return self.__son_father[node]
        except KeyError:
            return set()
        # END TRY
    # END DEF


    def get_names_ids_map(self):  # OK (<< 1 second)
        return self.__name_id_map
    # END DEF


    def get_ids(self, name):  # OK (< 1 second)
        if name not in self.__name_id_map:
            for taxon_name in self.__name_id_map.keys():
                if name in taxon_name:
                    return self.__name_id_map[taxon_name]
                # END IF
            # END FOR

            return None
        # END IF

        return self.__name_id_map[name]
    # END DEF


    def get_id_names_map(self):  # OK (<< 1 second)
        return self.__id_name_map
    # END DEF


    def get_name(self, node, name_class='scientific name'):  # OK (< 1 second)
        name = None

        if name_class not in self.__valid_name_class or node not in self.__id_name_map:
            return name
        # END IF

        for tp in self.__id_name_map[node]:
            if tp[1] == name_class:
                name = tp[0]
                break
            # END IF
        # END FOR

        return name
    # END DEF


    def get_node_rank(self, node):  # OK (<< 1 second)
        if node not in self.__rank_list:
            return None
        # END IF

        return self.__rank_list[node]
    # END DEF


    def get_distance_from(self, node, target):  # OK (<< 1 second)
        father = node
        if father == '1' and target != '1':
            print('connection not found')

            return -1
        # END IF

        d = 0
        while father != target:
            father = self.get_father(father)
            d += 1
            if father == '1' and target != '1':
                print('connection not found')

                return -1
            # END IF
        # END WHILE

        return d
    # END DEF

# END CLASS

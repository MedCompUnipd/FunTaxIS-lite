#!/usr/bin/env python3
from taxonLibrary3 import *
import argparse

def main(args):
    nodes = []
    taxa = Taxon(args['taxa'],args['merge'],args['names'])
    with open(args['constraints'],'r') as input:
        for lines in input:
            line = lines.split('\t')
            line[0] = line[0].strip()
            rank = taxa.get_node_rank(line[0])
            if rank == 'order':
                nodes.append(line[0])
    descendants_full = taxa.get_all_descendants('1')
    descendants_nodes = set()
    list = ['environmental samples','unclassified','uncultured','Candidatus','candidate','incertae sedis',' x ',' vector','plasmid','Plasmid','Vector']
    for values in nodes:
        desc = taxa.get_all_descendants(values)
        descendants_nodes.add(values)
        for value in desc:
            descendants_nodes.add(value)
    descendants_remain = descendants_full - descendants_nodes
    excluded = set()
    for rows in descendants_remain:
        father = taxa.get_father(rows)
        namef = taxa.get_name(father)
        namer = taxa.get_name(rows)
        if any(c in namer for c in list):
            excluded.add(rows)
        if any(d in namef for d in list):
            excluded.add(father)
            sons = taxa.get_all_descendants(father)
            for x in sons:
                excluded.add(x)
    with open(args['out'],'w') as out:
        for row in excluded:
            name = taxa.get_name(row)
            out.write(f'{row}\t{name}\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Removes the environmental samples, unclassified, uncultured, Candidatus, candidate, incertae sedis, x, vector, plasmid, Plasmid, Vector from reference nodes')
    parser.add_argument('-merge', metavar='INPUT_FILE',  help='merged.dmp file where some taxa have been substitued with others', required=True)
    parser.add_argument('-taxa', metavar='INPUT_FILE',  help='nodes.dmp file containining taxa from Taxonomy', required=True)
    parser.add_argument('-names', metavar='INPUT_FILE',  help='names.dmp file containining correspondence of names and id numbers from Taxonomy', required=True)
    parser.add_argument('-constraints', metavar='INPUT_FILE',  help='taxonConstraintsDef.txt file containing top taxa where to cluster species', required=True)
    parser.add_argument('-out', metavar='OUTPUT_FILE',  help='txt file containing output', required=True)
    args = vars(parser.parse_args())
    main(args)

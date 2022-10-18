#!/bin/bash

option='f'
opt_tag=''

# Options parser
while getopts ':a:d:f:s:' opt
do
    case ${opt}
    in
        a) option='a'; opt_tag=${OPTARG};;
        d) option='d'; opt_tag=${OPTARG};;
        f) option='f'; opt_tag=${OPTARG};;
        s) option='s'; opt_tag=${OPTARG};;
    esac
done

# Based on the case run a specific script
case ${option}
in
    a) bash generate_all_taxon_constraints.sh "${opt_tag}";;
    d) bash download.sh "${opt_tag}";;
    f) bash run.sh "${opt_tag}";;
    s) bash generate_species_taxon_constraints.sh "${opt_tag}";;
    *) echo 'Wrong option. Available options are';\
       echo '-a: to generate the taxonomic constraints of all the species found in the input data.';\
       echo '-d: to download all the necessary data to correctly run FunTaxIS-lite.';\
       echo '-f: to use the complete FunTaxIS pipeline.';\
       echo '-s: to generate the taxonomic constraints of the species chosen by the user.';;
esac

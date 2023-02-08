#!/bin/bash

option='f'
opt_tag=''

# Options parser
while getopts ':i:d:f:c:' opt
do
    case ${opt}
    in
        i) option='i'; opt_tag=${OPTARG};;
        d) option='d'; opt_tag=${OPTARG};;
        f) option='f'; opt_tag=${OPTARG};;
        c) option='c'; opt_tag=${OPTARG};;
    esac
done

# Based on the case run a specific script
case ${option}
in
    i) bash ../generate_intermediate.sh "${opt_tag}";;
    d) bash ../download.sh "${opt_tag}";;
    f) bash ../run.sh "${opt_tag}";;
    c) bash ../generate_constraints.sh "${opt_tag}";;
    *) echo 'Wrong option. Available options are:';\
       echo '-i: to generate the taxonomic constraints of all the species found in the input data.';\
       echo '-d: to download all the necessary data to correctly run FunTaxIS-lite.';\
       echo '-f: to use the complete FunTaxIS pipeline.';\
       echo '-c: to generate the taxonomic constraints of the species chosen by the user.';\
       echo 'The configuration file must be passed as argument after the selected options.';;
esac

#!/bin/bash

intermediate=0
download=0
full=0
constraints=0

# Options parser
while getopts "idfcs:" opt
do
    case "${opt}" in
        i) intermediate=1;;
        d) download=1;;
        f) full=1;;
        c) constraints=1;;
        s) setting=${OPTARG};;
    esac
done

if [ ${full} -eq 1 ]
then
    bash ./download.sh $setting
    bash ./generate_intermediate.sh $setting
    bash ./generate_constraints.sh $setting
else
    if [ ${download} -eq 1 ]
    then
        bash ./download.sh $setting
    fi

    if [ ${intermediate} -eq 1 ]
    then
        bash ./generate_intermediate.sh $setting
    fi

    if [ ${constraints} -eq 1 ]
    then
        bash ./generate_constraints.sh $setting
    fi
fi

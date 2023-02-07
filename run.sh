#!/bin/bash

intermediate=0
download=0
full=0
constraints=0

usage() {
    echo "Usage: $0 [-h <>] [-d <>] [-i <>] [-c <>] [-f <>] [-s <path/to/file>]" 1>&2
    echo "-h prints this help message"
    echo "-d flag to execute the download.sh script"
    echo "-i flag to execute the generate_intermediate.sh script"
    echo "-c flag to execute the generate_constraints.sh script"
    echo "-f flag to execute the full pipeline, overrides any other flag"
    echo "-s (REQUIRED) the configuration file"
    exit 1
}

[ $# -eq 0 ] && usage

# Options parser
while getopts "hidfcs:" opt
do
    case "${opt}" in
        i) intermediate=1;;
        d) download=1;;
        f) full=1;;
        c) constraints=1;;
        s) setting=${OPTARG};;
        h | *) usage;;
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

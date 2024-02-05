#!/bin/bash

# Default options
intermediate=0
download=0
full=0
constraints=0
setting=""

usage() {
    echo "Usage: $0 -s/--settings [CONFIG_FILE] [OPTIONS]"
    echo "-h | --help:          print this help message"
    echo "-s | --settings:      specify the path to the configuration file (MANDATORY)"
    echo "-d | --download:      downloads the data needed to run the subsequent pipeline steps"
    echo "-i | --intermediate:  creates the intermediate files using existing data (either downloaded or specified by user in the config file)"
    echo "-c | --constraints:   computes the taxonomic constraints using existing intermediate files"
    echo "-f | --full:          executes the whole FunTaxIS-lite pipeline"
}

[ $# -eq 0 ] && usage


# Options parser
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h | --help) usage;;
        -i | --intermediate) intermediate=1;;
        -d | --download) download=1;;
        -f | --full) full=1;;
        -c | --constraints) constraints=1;;
        -s | --settings)
            shift
            if [[ $# -eq 0 ]]; then
                echo "Option -s requires an argument." >&2
                exit 1
            fi
            setting="$1"
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Invalid option: $1" >&2
            usage
            ;;
    esac
    shift
done

if [ ${full} -eq 1 ]; then
    bash /funtaxis-lite/download.sh "$setting"
    bash /funtaxis-lite/generate_intermediate.sh "$setting" /funtaxis-lite/src/
    bash /funtaxis-lite/generate_constraints.sh "$setting" /funtaxis-lite/src/
else
    if [ ${download} -eq 1 ]; then
        bash /funtaxis-lite/download.sh "$setting" /funtaxis-lite/src/
    fi

    if [ ${intermediate} -eq 1 ]; then
        bash /funtaxis-lite/generate_intermediate.sh "$setting" /funtaxis-lite/src/
    fi

    if [ ${constraints} -eq 1 ]; then
        bash /funtaxis-lite/generate_constraints.sh "$setting" /funtaxis-lite/src/
    fi
fi

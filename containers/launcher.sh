#!/bin/bash

# Default options
intermediate=0
download=0
full=0
constraints=0
setting=""
chmod +x /funtaxis-lite/src/*

# Usage
usage() {
    echo 'dopo'
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
    bash /funtaxis-lite/generate_intermediate.sh "$setting"
    bash /funtaxis-lite/generate_constraints.sh "$setting"
else
    if [ ${download} -eq 1 ]; then
        bash /funtaxis-lite/download.sh "$setting"
    fi

    if [ ${intermediate} -eq 1 ]; then
        bash /funtaxis-lite/generate_intermediate.sh "$setting"
    fi

    if [ ${constraints} -eq 1 ]; then
        bash /funtaxis-lite/generate_constraints.sh "$setting"
    fi
fi

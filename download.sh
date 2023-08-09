#!/bin/bash

# The necessary files download links.
goa_dl_site='ftp://ftp.ebi.ac.uk/pub/databases/GO/goa/UNIPROT/goa_uniprot_all.gaf.gz'
go_plus_dl_site='http://purl.obolibrary.org/obo/go/extensions/go-plus.owl'
taxon_dl_site='https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz'


# Function to download the file and save it in a specific folder.
# Parameters:
#  $1: the file's download link.
#  $2: the folder where we save the file.
function download () {
    wget "$1" -P "$2"
}


# Function to decompress .tar.gz and .gz files to the specified folder.
# Parameters:
#  $1: the compressed file.
#  $2: the folder where we save the file.
function decompress () {
    if [[ "$1" =~ .*.tar.gz ]]
    then
       tar -xzf "$1" -C "$2"
    elif [[ "$1" =~ .*.gz ]]
    then
      gzip -c -d "$1" > "$2""goa_uniprot_all.gaf"
    fi

    rm "$1"
}


# Function to download and decompress the file to the specified folder.
# Parameters:
#  $1: the file's download link.
#  $2: the folder where we save the file.
function dl_and_decompress () {
    download "$1" "$2"

    for file in "$2"*
    do
        decompress "${file}" "$2"
    done
}


# Function to verify the presence of the gene ontology file. If not present, we download it.
# Parameters:
#  $1: the path where we save the gene ontology file.
function verifyGoFilePresence() {
    # Count the number of file with .owl extention.
    count=`ls -1 "$1"*.owl 2> /dev/null | wc -l`
    if [ ! -d "$1" ]
    then
        mkdir -p "$1"
        download "${go_plus_dl_site}" "$1"
    elif [ $count -eq 0 ]
    then
        download "${go_plus_dl_site}" "$1"
    fi
}

# Function to verify the presence of the gene ontology annotation file. If not present, we download it.
# Parameters:
#  $1: the path where we save the gene ontology annotation file.
function verifyGoaFilePresence() {
    # Count the number of file with .gaf extension.
    count=`ls -1 "$1"*.gaf 2> /dev/null | wc -l`
    if [ ! -d "$1" ]
    then
        mkdir -p "$1"
        dl_and_decompress "${goa_dl_site}" "$1"
    elif [ $count -eq 0 ]
    then
        dl_and_decompress "${goa_dl_site}" "$1"
    fi
}

# Function to verify the presence of the taxonomy tree files. If not present, we download it.
# Parameters:
#  $1: the path where we save the taxonomy tree files.
function verifyTaxonomyFilesPresence() {
    # Count the number of file with .dmp extention.
    count=`ls -1 "$1"*.dmp 2> /dev/null | wc -l`
    if [ ! -d "$1" ]
    then
        mkdir -p "$1"
        dl_and_decompress "${taaxon_dl_site}" "$1"
    elif [ $count -eq 0 ]
    then
        dl_and_decompress "${taxon_dl_site}" "$1"
    fi
}


## Configuration file parser.
declare -A config_array # Array declaration.

if [[ ${#1} -eq 0 ]]
then
    echo 'Configuration file is required.'
    exit 0
fi

IFS=":" # Internal Field Separator for the read command.
# Read the configuration file.
# Parameters:
#  $1: the configuration file path.
while read -r name v
do
    key=$(echo "${name}" | sed -e 's/^[ \t]*//')
    value=$(echo "${v}" | sed -e 's/^[ \t]*//')

    if [[ "$key" =~ ^#.*  ]] || [[ "$key" =~ ^--.* ]] || [[ ${#value} -eq 0 ]]
    then
       continue
    fi

    config_array+=( [$key]=$value )
done < $1
##


# Variables
base_folder="${config_array[folder]}" # it's the path where all the files are saved. It's the path given by the parameter 'folder' in the configuration file.
go_folder="${config_array[go]}" # It's the gene ontology file path. It's the path given by the parameter 'go' in the configuration file. If not provided, an empty string is saved.
goa_folder="${config_array[goa]}" # It's the gene ontology annotation file path. It's the path given by the parameter 'goa' in the configuration file. If not provided, an empty string is saved.
taxonomy_folder="${config_array[taxonomy]}" # It's the taxonomy folder path, It's the path given by the parameter 'taxonomy' in the configuration file. If not provided, an empty string is saved.
output_folder="${config_array[results]}/" # It's the results folder path. It's given by the parameter 'results' in the configuration file.
type="${config_array[type]}" # It's the type of taxonomic constraints we want to be generated. It's given by the parameter 'type' in the configuration file. If not provided an empty string is saved and all the type (manual, automatic) are used.
debug="${config_array[debug]}" # It's  the intermediate files are removed or not. It's given by the parameter 'debug' in the configuration file. If not provided an empty string is saved and the intermediate files are removed.
used_go='' # It's the gene ontology file name.
used_goa='goa_uniprot_all.gaf' # It's the gene ontology annotation file name.


# Sets the taxonomy folder if not defined in the configuration file.
if [[ ${#taxonomy_folder} -eq 0 ]]
then
   taxonomy_folder="${base_folder}input/taxonomy/"
fi

# Sets the gene ontology folder and the gene ontology file name if the gene ontology file path is not defined in the configuration file.
# Otherwise, from the given path extracts the folder path and the file name.
if [[ ${#go_folder} -eq 0 ]]
then
    go_folder="${base_folder}input/go/"
    used_go='go-plus.owl'
else
    case "${go_folder}" in
        *go-plus.owl*) used_go=$(echo "${go_folder}" | awk -F/ '{print $NF}'); go_folder=${go_folder%"${used_go}"} ;; # Extract the gene ontology file name and the path.
        *) echo 'ERROR: Gene ontology graph is not in the owl format or is not the plus version.'; exit 1 ;;
    esac
fi

# Sets the gene ontology annotation folder if the goa file path is not defined in the configuration file.
# Otherwise, from the given path extracts the folder path and the file name.
if [[ ${#goa_folder} -eq 0 ]]
then
    goa_folder="${base_folder}input/goa/"
else
    used_goa=$(echo "${goa_folder}" | awk -F/ '{print $NF}')
    goa_folder=${goa_folder%"${used_goa}"}
fi

# Check if the gene ontology and the taxonomy files are present.
verifyGoFilePresence "${go_folder}"
verifyTaxonomyFilesPresence "${taxonomy_folder}"
# Check if the gene ontology annotation is present only if the type of constraints isn't "goc".
case "${type}" in
    "GOConsortium"|"goc"|"g" ) ;;
    * ) verifyGoaFilePresence "${goa_folder}"
esac

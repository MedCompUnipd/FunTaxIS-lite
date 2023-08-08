#!/bin/bash

# Function to transform a string to boolean and save the value in a variable.
# Parameters:
#  $1: the variable.
#  $2: the string we convert.
function setBoolean() {
    local v
    if (( $# != 2 )); then
        echo "Err: setBoolean usage" 1>&2; exit 1 ;
    fi

    case "$2" in
       "true"|"t" ) v=true ;;
       "false"|"f" ) v=false ;;
       *) echo "Err: Unknown boolean value \"$2\"" 1>&2; exit 1 ;;
    esac

    eval $1=$v
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
real_path="$(dirname $(realpath $0))" # Get the run.sh script path.
src_folder="${real_path}/src/" # The python script folder.
base_folder="${config_array[folder]}" # it's the path where all the files are saved. It's the path given by the parameter 'folder' in the configuration file.
go_folder="${config_array[go]}" # It's the gene ontology file path. It's the path given by the parameter 'go' in the configuration file. If not provided, an empty string is saved.
goa_folder="${config_array[goa]}" # It's the gene ontology annotation file path. It's the path given by the parameter 'goa' in the configuration file. If not provided, an empty string is saved.
taxonomy_folder="${config_array[taxonomy]}" # It's the taxonomy folder path, It's the path given by the parameter 'taxonomy' in the configuration file. If not provided, an empty string is saved.
tax_constr_def_file="${config_array[taxon-def]}" # It's the taxonomic definitions file path. It's the path given by the parameter 'taxon-def' in the configuration file. If not provided, an empty string is saved.
species_list_file="${config_array[species]}" # It's the list of species file path. It's the path given by the parameter 'species' in the configuration file. If not provided, an empty string is saved.
manual_constr_file="${config_array[manual-constraints]}" # It's the manual constraints definition file. It's given by the parameter 'manual-constratins' in the configuration file. If not provided, an empty string is saved.
int_file_folder="${base_folder}intermediate_files/" # It's the folder where the intermediate files are saved.
cut_off="${config_array[cutoff]}" # It's the GO's frequency threshold used to define constraints. It's given by the parameter 'cutoff' in the configuration file. If not provided an empty string is saved.
output_folder="${config_array[results]}/" # It's the results folder path. It's given by the parameter 'results' in the configuration file.
type="${config_array[type]}" # It's the type of taxonomic constraints we want to be generated. It's given by the parameter 'type' in the configuration file. If not provided an empty string is saved and all the type (manual, automatic) are used.
used_go='' # It's the gene ontology file name.
used_goa='goa_uniprot_all.gaf' # It's the gene ontology annotation file name.


# Sets the taxonomy folder if not defined in the configuration file.
if [[ ${#taxonomy_folder} -eq 0 ]]
then
   taxonomy_folder="${base_folder}/input/taxonomy/"
fi

# Sets the gene ontology folder and the gene ontology file name if the gene ontology file path is not defined in the configuration file.
# Otherwise, from the given path extracts the folder path and the file name.
if [[ ${#go_folder} -eq 0 ]]
then
    go_folder="${base_folder}/input/go/"
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
    goa_folder="${base_folder}/input/goa/"
else
    used_goa=$(echo "${goa_folder}" | awk -F/ '{print $NF}')
    goa_folder=${goa_folder%"${used_goa}"}
fi

# Sets the taxonomic definition file in the add_files folder if it is not definied in the configuration file.
if [[ ${#tax_constr_def_file} -eq 0 ]]
then
    tax_constr_def_file="${real_path}/input/add_files/taxonConstraintsDef.txt"
fi

# Sets the list of species file in the add_files folder if it is not definied in the configuration file.
if [[ ${#species_list_file} -eq 0 ]]
then
    species_list_file="${real_path}/input/add_files/listOfSpecies.txt"
fi

# Sets the manual constratins in the add_files if it is not defined in the configuration file.
if [[ ${#manual_constr_file} -eq 0 ]]
then
    manual_constr_file="${real_path}/input/add_files/manualConstraints.txt"
fi

# Sets the cut-off value to 500 if it is not defined in the configuration file.
if [[ ${#cut_off} -eq 0 ]]
then
    cut_off=500
fi


# Check if the gene ontology and the taxonomy files are present.
verifyGoFilePresence "${go_folder}"
verifyTaxonomyFilesPresence "${taxonomy_folder}"
# Check if the gene ontology annotation is present only if the type of constraints isn't manual.
case "${type}" in
    "GOConsortium"|"goc"|"g" ) ;;
    * ) verifyGoaFilePresence "${goa_folder}"
esac


# Verify if the intermediate files folder exists. If not, stop.
count=0
if [ ! -d "${int_file_folder}" ]
then
    echo 'Run generate_all_taxon_constraints.sh before running generate_species_taxon_constraints.sh'
    exit 1
fi

# Verify if the necessary files exists. If the files exist increment count.
for file in "${int_file_folder}"*
do
	case "${file}" in
		"${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt"|"${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt" ) ((count+=1)) ;;
		* )	;;
	esac
done

# Verify if the number of files is 1 or 2. If it isn't, stop.
case "${count}" in 
	"1"|"2" ) ;;
	* ) echo 'Run generate_all_taxon_constraints.sh before running generate_species_taxon_constraints.sh'; exit 1 ;;
esac

# Verify if the output folder exists. If not, make it.
if [ ! -d "${output_folder}" ]
then
    mkdir -p "${output_folder}"
fi


# Only the taxonomic constraints of the choosed species are generated using the taxonomic constraints of the lowest ancestor of the species in exam defined in the $taxon_constr_def_file file.
case "${type}" in
    # For each species in $species_list_file get the manual taxonomic constraints. 
    "GOConsortium"|"goc"|"g" ) echo 'Generate manual GO taxon constraints' ;
                         "${src_folder}"./createConstraintsMergedAndSpecific.py -go_const "${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt" \
                         -list "${species_list_file}" -merge "${taxonomy_folder}merged.dmp" \
                         -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -outdir "${output_folder}" -log "${int_file_folder}logfile.txt" -manual "${manual_constr_file}" \
                         -owl "${go_folder}${used_go}" -partition "${tax_constr_def_file}" ;;
    # For each species in $species_list_file get the automatic taxonomic constraints.
    "automatic"|"a"|"auto" ) echo 'Generate automatic GO taxon constraints' ;
                             "${src_folder}"./createConstraintsMergedAndSpecific.py -aut_const "${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt" \
                             -list "${species_list_file}" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -outdir "${output_folder}" \
                             -log "${int_file_folder}logfile.txt" -manual "${manual_constr_file}" -owl "${go_folder}${used_go}" -partition "${tax_constr_def_file}" ;;
    # For each species in $species_list_file get the manual and automatic taxonomic constraints.
    * ) echo 'Merge the automatic constraints with the manual GO taxon constraints' ;
        "${src_folder}"./createConstraintsMergedAndSpecific.py -go_const "${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt" \
        -aut_const "${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt" -list "${species_list_file}" -merge "${taxonomy_folder}merged.dmp" \
        -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -outdir "${output_folder}" -log "${int_file_folder}logfile.txt" -manual "${manual_constr_file}" \
        -owl "${go_folder}${used_go}" -partition "${tax_constr_def_file}" ;;
esac

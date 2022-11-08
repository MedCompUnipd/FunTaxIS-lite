#!/bin/bash

# Function to verify the presence of the gene ontology file. If not present, we download it.
# Parameters:
#  $1: the path where we save the gene ontology file.
function verifyGoFilePresence() {
    # Count the number of file with .owl extention.
    count=`ls -1 "$1"*.owl 2> /dev/null | wc -l`
    if [ ! -d "$1" ]
    then
        mkdir -p "$1"
    fi

    if [ $count -eq 0 ]
    then
    	"$2/./download.sh $3"
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
    fi

    if [ $count -eq 0 ]
    then
        "$2/./download.sh $3"
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
    fi

    if [ $count -eq 0 ]
    then
        "$2/./download.sh $3"
    fi
}


## Configuration file parser.
declare -A config_array # Array declaration.

config_file=$1

if [[ ${#config_file} -eq 0 ]]
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
type="${config_array[type]}" # It's the type of taxonomic constraints we want to be generated. It's given by the parameter 'type' in the configuration file. If not provided an empty string is saved and all the type (manual, automatic) are used.
used_go='' # It's the gene ontology file name.
used_goa='goa_uniprot_all.gaf' # It's the gene ontology annotation file name.
unclassified_file="${config_array[unclassified]}" # list of unclassified and other nodes above order rank to remove their annotation contribution


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

# Sets the list of species file in the add_files folder if it is not definied in the configuration file.
if [[ ${#unclassified_file} -eq 0 ]]
then
    unclassified_file="${real_path}/input/add_files/excluded_nodes.txt"
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
verifyGoFilePresence "${go_folder}" "${real_path}" "${config_file}"
verifyTaxonomyFilesPresence "${taxonomy_folder}" "${real_path}" "${config_file}"
# Check if the gene ontology annotation is present only if the type of constraints isn't manual.
case "${type}" in
    "manual"|"m"|"man" ) ;;
    * ) verifyGoaFilePresence "${goa_folder}" "${real_path}" "${config_file}"
esac


# Verify if the intermediate files folder exists. If not, make it.
if [ ! -d "${int_file_folder}" ]
then
    mkdir -p "${int_file_folder}"
fi

# All the taxonomic constraints are generated.
case "${type}" in
    # Generate only automatic taxonomic constraints using the data from the filtered gene ontology annotation file.
    "automatic"|"a"|"auto" )
                         echo 'Remove unclassified organisms';
                         "${src_folder}"./get_unclassified_id.py -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -constraints "${tax_constr_def_file}" -out "${unclassified_file}"
                         echo 'Discard ND, roots and InterPro and PANTHER hits from GOA' ;
                         "${src_folder}"./purgeRootsInterproFormGaf.py -gaf "${goa_folder}${used_goa}" -unclass "${unclassified_file}" -gafout "${int_file_folder}goa_uniprot_all_no_interpro_no_panther.gaf" -no_interpro -no_panther ;

                         echo 'Calculate GO frequencies from purged GOA file' ;
                         "${src_folder}"./GOAfreq.py -owl "${go_folder}${used_go}" -gaf_wo "${int_file_folder}goa_uniprot_all_no_interpro_no_panther.gaf" \
                         -out_freq "${int_file_folder}goa_uniprot_all_no_interpro_no_panther_CumulFreq.txt" ;

                         echo 'Produce for each species the list of GO occurrences found' ;
                         "${src_folder}"./speciesToGO.py -gaf "${int_file_folder}goa_uniprot_all_no_interpro_no_panther.gaf" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" \
                         -names "${taxonomy_folder}names.dmp" -out "${int_file_folder}speciesGOusage_no_interpro_no_panther.txt" > "${int_file_folder}speciesGOusage_no_interpro_no_panther_MISSING_taxon.txt" ;

                         echo 'Cluster species together and their corresponding GO' ;
                         "${src_folder}"./clusterTaxon.py -constraints "${tax_constr_def_file}" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -species "${int_file_folder}speciesGOusage_no_interpro_no_panther.txt" \
                         -out "${int_file_folder}cluster_speciesGOusage_no_interpro_no_panther.txt" ;

                         echo 'Compute the cumulative occurrence of GO terms in defined subdivisions using the graph of GO Memory Less' ;
                         "${src_folder}"./speciesFreqCumul.py -owl "${go_folder}${used_go}" -freq "${int_file_folder}cluster_speciesGOusage_no_interpro_no_panther.txt" \
                         -out_freq "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther.txt" ;

                         echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision' ;
                         "${src_folder}"./createNeverIN.py -goa_freq "${int_file_folder}goa_uniprot_all_no_interpro_no_panther_CumulFreq.txt" -cutoff "${cut_off}" \
                         -cumul "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther.txt" -owl "${go_folder}${used_go}" -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" ;

                         echo 'Wrapper to make output identical' ;
                         "${src_folder}"./wrapperTaxonConstraints.py -constraints "${tax_constr_def_file}" -never_in "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" \
                         -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN_reformat.txt" ;;

    # Generate only manual constraints using the data from the gene ontology consortium.
    "manual"|"m"|"man" )
                         echo 'Consider taxon constraints from consortium' ;
                         "${src_folder}"./taxonConstraintsGOconsortium.py -owl "${go_folder}${used_go}" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" \
                         -out_constraints "${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt" ;;

    # Generate only constraints dependant on cutoff value.
    "cutoff_only"|"c"|"cut" )
                         echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision' ;
                         "${src_folder}"./createNeverIN.py -goa_freq "${int_file_folder}goa_uniprot_all_no_interpro_no_panther_CumulFreq.txt" -cutoff "${cut_off}" \
                         -cumul "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther.txt" -owl "${go_folder}${used_go}" -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" ;

                          echo 'Wrapper to make output identical' ;
                         "${src_folder}"./wrapperTaxonConstraints.py -constraints "${tax_constr_def_file}" -never_in "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" \
                         -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN_reformat.txt" ;;

    #Generate new files based on different taxonomic reference nodes.
    "taxonDef"|"t"|"tax" )
                         echo 'Cluster species together and their corresponding GO' ;
                         "${src_folder}"./clusterTaxon.py -constraints "${tax_constr_def_file}" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -species "${int_file_folder}speciesGOusage_no_interpro_no_panther.txt" \
                         -out "${int_file_folder}cluster_speciesGOusage_no_interpro_no_panther.txt" ;

                         echo 'Compute the cumulative occurrence of GO terms in defined subdivisions using the graph of GO Memory Less' ;
                         "${src_folder}"./speciesFreqCumul.py -owl "${go_folder}${used_go}" -freq "${int_file_folder}cluster_speciesGOusage_no_interpro_no_panther.txt" \
                         -out_freq "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther.txt" ;

                         echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision' ;
                         "${src_folder}"./createNeverIN.py -goa_freq "${int_file_folder}goa_uniprot_all_no_interpro_no_panther_CumulFreq.txt" -cutoff "${cut_off}" \
                         -cumul "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther.txt" -owl "${go_folder}${used_go}" -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" ;

                         echo 'Wrapper to make output identical' ;
                         "${src_folder}"./wrapperTaxonConstraints.py -constraints "${tax_constr_def_file}" -never_in "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" \
                         -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN_reformat.txt" ;;

    # Generate the taxonomic constraints using data from the gene ontology consortium and the gene ontology annotation. The first ones are more important than the second ones. 
    * )
        
        echo 'Remove unclassified organisms';
        "${src_folder}"./get_unclassified_id.py -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -constraints "${tax_constr_def_file}" -out "${unclassified_file}"
        
        echo 'Discard ND, roots and InterPro and PANTHER hits from GOA' ;
        "${src_folder}"./purgeRootsInterproFormGaf.py -gaf "${goa_folder}${used_goa}" -unclass "${unclassified_file}" -gafout "${int_file_folder}goa_uniprot_all_no_interpro_no_panther.gaf" -no_interpro -no_panther ;

        echo 'Calculate GO frequencies from purged GOA file' ;
        "${src_folder}"./GOAfreq.py -owl "${go_folder}${used_go}" -gaf_wo "${int_file_folder}goa_uniprot_all_no_interpro_no_panther.gaf" \
        -out_freq "${int_file_folder}goa_uniprot_all_no_interpro_no_panther_CumulFreq.txt" ;

        echo 'Produce for each species the list of GO occurrences found' ;
        "${src_folder}"./speciesToGO.py -gaf "${int_file_folder}goa_uniprot_all_no_interpro_no_panther.gaf" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" \
        -names "${taxonomy_folder}names.dmp" -out "${int_file_folder}speciesGOusage_no_interpro_no_panther.txt" > "${int_file_folder}speciesGOusage_no_interpro_no_panther_MISSING_taxon.txt" ;

        echo 'Cluster species together and their corresponding GO' ;
        "${src_folder}"./clusterTaxon.py -constraints "${tax_constr_def_file}" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" -species "${int_file_folder}speciesGOusage_no_interpro_no_panther.txt" \
        -out "${int_file_folder}cluster_speciesGOusage_no_interpro_no_panther.txt" ;

        echo 'Compute the cumulative occurrence of GO terms in defined subdivisions using the graph of GO Memory Less' ;
        "${src_folder}"./speciesFreqCumul.py -owl "${go_folder}${used_go}" -freq "${int_file_folder}cluster_speciesGOusage_no_interpro_no_panther.txt" \
        -out_freq "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther.txt" ;

        echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision' ;
        "${src_folder}"./createNeverIN.py -goa_freq "${int_file_folder}goa_uniprot_all_no_interpro_no_panther_CumulFreq.txt" -cutoff "${cut_off}" \
        -cumul "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther.txt" -owl "${go_folder}${used_go}" -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" ;

        echo 'Wrapper to make output identical' ;
        "${src_folder}"./wrapperTaxonConstraints.py -constraints "${tax_constr_def_file}" -never_in "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN.txt" \
        -out "${int_file_folder}freqCumul_cluster_speciesGOusage_no_interpro_no_panther_NEVER_IN_reformat.txt" ;

        echo 'Consider taxon constraints from consortium';
        "${src_folder}"./taxonConstraintsGOconsortium.py -owl "${go_folder}${used_go}" -merge "${taxonomy_folder}merged.dmp" -taxa "${taxonomy_folder}nodes.dmp" -names "${taxonomy_folder}names.dmp" \
        -out_constraints "${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt" ;;
esac

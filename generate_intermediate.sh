#!/bin/bash


# Function to verify the presence of the taxonomy tree files. If not present, we download it.
# Parameters:
#   $1: the path where we save the taxonomy tree files.
#   $2: the real path from the where this script is called
#   $3: the configutation file
verifyTaxonomyFilesPresence() {
    # Count the number of file with .dmp extention.
    count=$(ls -1 "$1"*.dmp 2> /dev/null | wc -l)
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
    fi

    if [ $count -eq 0 ]; then
        "$2/download.sh $3"
    fi
}


# DEFAULT - HARD-CODED
real_path="$(dirname $(realpath $0))"                                           # Get the run.sh script path.
src_folder="${real_path}/src/"                                                  # Folder where to find all necessary python scripts
used_go="go-plus.owl"                                                           # Filename for the OWL file.
used_goa="goa_uniprot_all.gaf"                                                  # Filename for the GAF file.
used_constr_def_file="taxonConstraintsDef.txt"
used_unclassified_file="excluded_nodes.txt"


# DEFAULT - SOFT-CODED
go_folder="${real_path}/input/go/"                                              # Folder where the OWL file is.
goa_folder="${real_path}/input/goa/"                                            # Folder where the GAF file is.
taxonomy_folder="${real_path}/input/taxonomy/"                                  # Folder where the taxonomy taxdump files are.
add_files_folder="${real_path}/input/add_files/"                                # Folder where the desired add_files are.
cut_off=500                                                                     # Default value for ...
int_file_folder="${real_path}/intermediate_files/"                              # Folder where to create all necessary intermediate files.
type="all"                                                                      # Mode for the FUnTaxIS-lite pipeline


while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -w|--owl)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                if [ -f "$2" ]; then
                    case "$2" in
                        *go-plus.owl*) used_go=$(echo "$2" | awk -F/ '{print $NF}'); go_folder=${2%"${used_go}"} ;; # Extract the gene ontology file name and the path.
                        *) echo 'ERROR: Gene ontology graph is not in the owl format or is not the plus version.'; usage;;
                    esac
                else
                    owls=$(find "$2" -type f -name *go-plus.owl* 2> /dev/null |wc -l)
                    if [ $owls -eq 1 ]; then
                        used_go=$(find "$2" -type f -name *go-plus.owl* -printf "%f\n")
                        go_folder="$2"
                    elif [ $owls -eq 0]; then
                        echo "Downloading go-plus.owl in the provided folder since it was empty"
                        "${base_folder}/download.sh" -w "$2"
                        used_go="go-plus.owl"
                        go_folder="$2"
                    else
                        echo "Too many files named *go-plus.owl* in the provided folder, please chose a specific one!"
                        usage
                    fi
                fi
            else
                echo "Expected argument after option -w/--owl!"
                usage
            fi
            shift
            shift;;

        -g|--goa)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                if [ -f "$2" ]; then
                    case "$2" in
                        *.gaf*) used_goa=$(echo "$2" | awk -F/ '{print $NF}'); goa_folder=${2%"${used_goa}"} ;; # Extract the gene ontology file name and the path.
                        *) echo 'ERROR: Gene annotation file is not in the .gaf format!'; usage;;
                    esac
                else
                    gafs=$(find "$2" -type f -name *.gaf* 2> /dev/null |wc -l)
                    if [ $gafs -eq 1 ]; then
                        used_goa=$(find "$2" -type f -name *.gaf* -printf "%f\n")
                        goa_folder="$2"
                    elif [ $gafs -eq 0]; then
                        echo "Downloading (and decompressing) goa_uniprot_all.gaf in the provided folder since it was empty"
                        "${base_folder}/download.sh" -g "$2"
                        used_goa="goa_uniprot_all.gaf"
                        goa_folder="$2"
                    else
                        echo "Too many files named *.gaf* in the provided folder, please chose a specific one!"
                        usage
                    fi
                fi
            else
                echo "Expected argument after option -g/--goa!"
                usage
            fi
            shift
            shift;;

        -t|--taxonomy)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                if [ -f "$2" ]; then
                    echo "This argument required a folder, not a file!"
                    usage
                elif [ ! -f "$2/names.dmp" ] || [ ! -f "$2/nodes.dmp" ] || [ ! -f "$2/merged.dmp" ]; then
                    echo "The taxonomy is empty or corrupted, files names.dmp, nodes.dmp, merged.dmp are all expecterd to be in the provided folder!"
                    echo "If you want the latest version to be downloaded there, please answer yes to the upcoming checkpoint"
                    "${src_folder}/download.sh" -t "$2"
                    taxonomy_folder="$2"
                else
                    taxonomy_folder="$2"
                fi
            else
                echo "Expected argument after option -t/--taxonomy!"
                usage
            fi
            shift
            shift;;
        -a|--files)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                if [ -f "$2" ]; then
                    echo "This argument requires a folder, not a file!"
                    usage
                elif [ ! -d "$2" ]; then
                    echo "This argument must point to an existing directory where the required additional files are!"
                    usage
                else
                    add_files="$2"
                fi
            else
                echo "Expected argument after option -a/--files !"
                usage
            fi
            shift
            shift;;
        -i|--intermediate)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                if [ -f "$2" ]; then
                    echo "This argument requires a folder, not a file!"
                    usage
                elif [ ! -d "$2" ]; then
                    mkdir -p "$2"
                    intermediate_files="$2"
                else
                    intermediate_files="$2"
                fi
            else
                echo "Expected argument after option -i/--intermediate !"
                usage
            fi
            shift
            shift;;
        -m|--type)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                type="$2"
            else
                echo "Expected argument after option -t/--type !"
                usage
            fi
            shift
            shift;;
        -c|--cutoff)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                cutoff="$2"
            else
                echo "Expected argument after option -c/--cutoff !"
                usage
            fi
            shift
            shift;;
        -h|--help)
            usage;;
        *)
            echo "Error: Unknown option $1"
            usage;;
    esac
done


# All the taxonomic constraints are generated.
case "${type}" in
    # Generate only automatic taxonomic constraints using the data from the filtered gene ontology annotation file.
    "automatic"|"a"|"auto" )
        echo 'Discard ND, roots and RNACentral hits from GOA'
        goa_file="${goa_folder}${used_goa}"
        purged_goa="${int_file_folder}goa_uniprot_all.gaf"
        "${src_folder}"./purgeRootsInterproFormGaf.py -g "${goa_file}" -u "${unclassified_file}" -o "${purged_goa}"

        echo 'Calculate GO frequencies from purged GOA file'
        owl_file="${go_folder}${used_go}"
        cumul_freq_file="${int_file_folder}goa_uniprot_all_CumulFreq.txt"
        "${src_folder}"./GOAfreq.py -w "${owl_file}" -g "${purged_goa}" -o "${cumul_freq_file}"

        echo 'Produce for each species the list of GO occurrences found'
        merged_file="${taxonomy_folder}merged.dmp"
        nodes_file="${taxonomy_folder}nodes.dmp"
        names_file="${taxonomy_folder}names.dmp"
        go_usage="${int_file_folder}speciesGOusage.txt"
        go_missing="${int_file_folder}speciesGOusage_MISSING_taxon.txt"
        "${src_folder}"./speciesToGO.py -g "${purged_goa}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -o "${go_usage}" > "${go_missing}"

        echo 'Cluster species together and their corresponding GO'
        cluster_go_usage="${int_file_folder}cluster_speciesGOusage.txt"
        "${src_folder}"./clusterTaxon.py -c "${tax_constr_def_file}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -s "${go_usage}" -o "${cluster_go_usage}"

        echo 'Compute the cumulative occurrence of GO terms in defined subdivisions using the graph of GO Memory Less'
        freq_cluster_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage.txt"
        "${src_folder}"./speciesFreqCumul.py -i "${owl_file}" -f "${cluster_go_usage}" -o "${freq_cluster_go_usage}"

        echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision'
        never_in_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN.txt"
        "${src_folder}"./createNeverIN.py -g "${cumul_freq_file}" -c "${cut_off}" -u "${freq_cluster_go_usage}" -w "${owl_file}" -o "${never_in_go_usage}"

        echo 'Wrapper to make output identical'
        never_in_reformat="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        "${src_folder}"./wrapperTaxonConstraints.py -c "${tax_constr_def_file}" -n "${never_in_go_usage}" -o "${never_in_reformat}";;

    # Generate all files except purged GOA and GOAfreq.
    "fast"|"f"|"fst" )
        echo 'Calculate GO frequencies from purged GOA file'
        owl_file="${go_folder}${used_go}"
        cumul_freq_file="${int_file_folder}goa_uniprot_all_CumulFreq.txt"
        goa_file="${goa_folder}${used_goa}"
        "${src_folder}"./GOAfreq.py -w "${owl_file}" -g "${goa_file}" -o "${cumul_freq_file}"

        echo 'Produce for each species the list of GO occurrences found'
        merged_file="${taxonomy_folder}merged.dmp"
        nodes_file="${taxonomy_folder}nodes.dmp"
        names_file="${taxonomy_folder}names.dmp"
        go_usage="${int_file_folder}speciesGOusage.txt"
        go_missing="${int_file_folder}speciesGOusage_MISSING_taxon.txt"
        "${src_folder}"./speciesToGO.py -g "${goa_file}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -o "${go_usage}" > "${go_missing}"

        echo 'Cluster species together and their corresponding GO'
        cluster_go_usage="${int_file_folder}cluster_speciesGOusage.txt"
        "${src_folder}"./clusterTaxon.py -c "${tax_constr_def_file}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -s "${go_usage}" -o "${cluster_go_usage}"

        echo 'Compute the cumulative occurrence of GO terms in defined subdivisions using the graph of GO Memory Less'
        freq_cluster_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage.txt"
        "${src_folder}"./speciesFreqCumul.py -i "${owl_file}" -f "${cluster_go_usage}" -o "${freq_cluster_go_usage}"

        echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision'
        never_in_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN.txt"
        "${src_folder}"./createNeverIN.py -g "${cumul_freq_file}" -c "${cut_off}" -u "${freq_cluster_go_usage}" -w "${owl_file}" -o "${never_in_go_usage}"

        echo 'Wrapper to make output identical'
        never_in_reformat="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        "${src_folder}"./wrapperTaxonConstraints.py -c "${tax_constr_def_file}" -n "${never_in_go_usage}" -o "${never_in_reformat}";;

    # Generate only manual constraints using the data from the gene ontology consortium.
    "GOConsortium"|"goc"|"g" )
        echo 'Consider taxon constraints from consortium'
        owl_file="${go_folder}${used_go}"
        merged_file="${taxonomy_folder}merged.dmp"
        nodes_file="${taxonomy_folder}nodes.dmp"
        names_file="${taxonomy_folder}names.dmp"
        output_file="${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt"
        "${src_folder}"./taxonConstraintsGOconsortium.py -w "${owl_file}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -o "${output_file}" ;;

    # Generate only constraints dependant on cutoff value.
    "cutoff_only"|"c"|"cut" )
        echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision'
        cumul_freq_file="${int_file_folder}goa_uniprot_all_CumulFreq.txt"
        freq_cluster_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage.txt"
        never_in_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN.txt"
        "${src_folder}"./createNeverIN.py -g "${cumul_freq_file}" -c "${cut_off}" -u "${freq_cluster_go_usage}" -w "${owl_file}" -o "${never_in_go_usage}"

        echo 'Wrapper to make output identical'
        never_in_reformat="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        "${src_folder}"./wrapperTaxonConstraints.py -c "${tax_constr_def_file}" -n "${never_in_go_usage}" -o "${never_in_reformat}";;

    #Generate new files based on different taxonomic reference nodes.
    "taxonDef"|"t"|"tax" )
        echo 'Cluster species together and their corresponding GO'
        merged_file="${taxonomy_folder}merged.dmp"
        nodes_file="${taxonomy_folder}nodes.dmp"
        names_file="${taxonomy_folder}names.dmp"
        go_usage="${int_file_folder}speciesGOusage.txt"
        cluster_go_usage="${int_file_folder}cluster_speciesGOusage.txt"
        "${src_folder}"./clusterTaxon.py -c "${tax_constr_def_file}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -s "${go_usage}" -o "${cluster_go_usage}"

        echo 'Compute the cumulative occurrence of GO terms in defined subdivisions using the graph of GO Memory Less'
        freq_cluster_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage.txt"
        "${src_folder}"./speciesFreqCumul.py -i "${owl_file}" -f "${cluster_go_usage}" -o "${freq_cluster_go_usage}"

        echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision'
        never_in_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN.txt"
        "${src_folder}"./createNeverIN.py -g "${cumul_freq_file}" -c "${cut_off}" -u "${freq_cluster_go_usage}" -w "${owl_file}" -o "${never_in_go_usage}"

        echo 'Wrapper to make output identical'
        never_in_reformat="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        "${src_folder}"./wrapperTaxonConstraints.py -c "${tax_constr_def_file}" -n "${never_in_go_usage}" -o "${never_in_reformat}";;

    # Generate the taxonomic constraints using data from the gene ontology consortium and the gene ontology annotation. The first ones are more important than the second ones.
    * )
        echo 'Discard ND, roots and RNACentral hits from GOA'
        goa_file="${goa_folder}${used_goa}"
        purged_goa="${int_file_folder}goa_uniprot_all.gaf"
        "${src_folder}"./purgeRootsInterproFormGaf.py -g "${goa_file}" -u "${unclassified_file}" -o "${purged_goa}"

        echo 'Calculate GO frequencies from purged GOA file'
        owl_file="${go_folder}${used_go}"
        cumul_freq_file="${int_file_folder}goa_uniprot_all_CumulFreq.txt"
        "${src_folder}"./GOAfreq.py -w "${owl_file}" -g "${purged_goa}" -o "${cumul_freq_file}"

        echo 'Produce for each species the list of GO occurrences found'
        merged_file="${taxonomy_folder}merged.dmp"
        nodes_file="${taxonomy_folder}nodes.dmp"
        names_file="${taxonomy_folder}names.dmp"
        go_usage="${int_file_folder}speciesGOusage.txt"
        go_missing="${int_file_folder}speciesGOusage_MISSING_taxon.txt"
        "${src_folder}"./speciesToGO.py -g "${purged_goa}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -o "${go_usage}" > "${go_missing}"

        echo 'Cluster species together and their corresponding GO'
        cluster_go_usage="${int_file_folder}cluster_speciesGOusage.txt"
        "${src_folder}"./clusterTaxon.py -c "${tax_constr_def_file}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -s "${go_usage}" -o "${cluster_go_usage}"

        echo 'Compute the cumulative occurrence of GO terms in defined subdivisions using the graph of GO Memory Less'
        freq_cluster_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage.txt"
        "${src_folder}"./speciesFreqCumul.py -i "${owl_file}" -f "${cluster_go_usage}" -o "${freq_cluster_go_usage}"

        echo 'Create never_in considering what we have produced from the cumulated corpus of each subdivision'
        never_in_go_usage="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN.txt"
        "${src_folder}"./createNeverIN.py -g "${cumul_freq_file}" -c "${cut_off}" -u "${freq_cluster_go_usage}" -w "${owl_file}" -o "${never_in_go_usage}"

        echo 'Wrapper to make output identical'
        never_in_reformat="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        "${src_folder}"./wrapperTaxonConstraints.py -c "${tax_constr_def_file}" -n "${never_in_go_usage}" -o "${never_in_reformat}"

        echo 'Consider taxon constraints from consortium'
        output_file="${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt"
        "${src_folder}"./taxonConstraintsGOconsortium.py -w "${owl_file}" -m "${merged_file}" -t "${nodes_file}" -n "${names_file}" -o "${output_file}";;
esac

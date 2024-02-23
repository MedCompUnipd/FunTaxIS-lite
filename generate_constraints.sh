#!/bin/bash


usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "This script generates all necessary intermediate files needed to run the FunTaxIS-lite pipeline. It uses:"
    echo " - go-plus.owl:           the GO graph file"
    echo " - taxondump/ :           the taxonomy taxondump folder"
    echo "These files, if not explcitly provided, will be downloaded inside the default directory ./input, subdirectory of the path where $0 is."
    echo "Specifically in ./input/go/ and ./input/taxonomy/ respectively."
    echo ""
    echo "This script must also be given the folder where the additional files are (taxonConstraintsDef.txt, listOfSpecies.txt, manualConstraints.txt). The first two mandatory, the latter compulsory"
    echo "The default option is to look for them in ./input/add_files/, but this path can be customised via the specific option"
    echo "OPTIONS:"
    echo "-h, --help:               Print this help message"
    echo ""
    echo "-w, --owl:                If a file is given: it will be used as OWL_FILE. If a directory is given: the file named go-plus.owl inside it will be used. DEFAULT: ./input/go/go-plus.owl"
    echo "-t, --taxonomy:           Folder where the taxonomy taxdump files are, mandatory files are: merged.dmp, nodes.dmp, names.dmp. DEFAULT: ./input/taxonomy/"
    echo "In the case of empty folders, or folders without the required files inside, a download attempt will me bade"
    echo ""
    echo "-a, --files:              Folder where the files taxonConstraintsDef.txt and excluded_nodes.txt will be looked for. DEFAULT: ./input/add_files/"
    echo "-i, --intermediate        Folder where the intermediate files will be written. DEFAULT: ./input/intermediate_files/"
    echo "-c, --cutoff              The cutoff value applied to significant annotations when generating the automatic taxonomic constraints. DEFAULT: 500"
    echo ""
    echo "-m, --type                The mode for which the FunTaxIS-lite pipeline will be run. DEFAULT: all"
    echo "Admitted modes:"
    echo "  automatic|a|auto:       computes only the automatic constraints"
    echo "  GOConsortium|goc|g:     computes only the constraints from the GO Consortium"
    echo "  all|*:                  computes all types of constraints and merges them prioritizing the manually curated ones"
    echo ""
    echo "-o, --outdir              The folder where the final constraints will be written. DEFAULT: ./outputs/"
    exit 1
}


# DEFAULT - HARD-CODED
real_path="$(dirname $(realpath $0))"
src_folder="${real_path}/src/"
used_go="go-plus.owl"
used_goa="goa_uniprot_all.gaf"
used_tax_constr_file="taxonConstraintsDef.txt"
used_man_constr_file="manualConstraints.txt"
used_species_list_file="species.txt"

# DEFAULT - SOFT-CODED
go_folder="${real_path}/input/go/"
goa_folder="${real_path}/input/goa/"
taxonomy_folder="${real_path}/input/taxonomy/"
add_files_folder="${real_path}/input/add_files/"
output_folder="${real_path}/outputs/"
int_file_folder="${real_path}/intermediate_files/"
type="all"
cut_off=500


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
                    add_files_folder="$2"
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
                    int_file_folder="$2"
                else
                    int_file_folder="$2"
                fi
            else
                echo "Expected argument after option -i/--intermediate !"
                usage
            fi
            shift
            shift;;
        -o|--outdir)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                if [ -f "$2" ]; then
                    echo "This argument requires a folder, not a file!"
                    usage
                elif [ ! -d "$2" ]; then
                    mkdir -p "$2"
                    output_folder="$2"
                else
                    output_folder="$2"
                fi
            else
                echo "Expected argument after option -o/--outdir !"
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



# Only the taxonomic constraints of the choosed species are generated using the taxonomic constraints of the lowest ancestor of the species in exam defined in the $taxon_constr_def_file file.
case "${type}" in
    # For each species in $species_list_file get the manual taxonomic constraints.
    "GOConsortium"|"goc"|"g" )
        # For each species in $species_list_file get the automatic taxonomic constraints.
        echo 'Generate manual GO taxon constraints'

        go_const="${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt"
        species_list="${add_files_folder}${used_species_list_file}"
        merged="${taxonomy_folder}merged.dmp"
        nodes="${taxonomy_folder}nodes.dmp"
        names="${taxonomy_folder}names.dmp"
        log_file="${int_file_folder}logfile.txt"
        owl_file="${go_folder}${used_go}"
        manual_constr="${add_files_folder}${used_man_constr_file}"
        tax_constr="${add_files_folder}${used_tax_constr_file}"

        "${src_folder}"./old_createConstraintsMergedAndSpecific.py -g "${go_const}" -s "${species_list}" -m "${merged}" -t "${nodes}" -n "${names}" -o "${output_folder}" -l "${log_file}" -c "${manual_constr}" -w "${owl_file}" -p "${tax_constr}" ;;
    "automatic"|"a"|"auto" )
        # For each species in $species_list_file get the manual and automatic taxonomic constraints.
        echo 'Generate automatic GO taxon constraints'

        aut_const="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        species_list="${add_files_folder}${used_species_list_file}"
        merged="${taxonomy_folder}merged.dmp"
        nodes="${taxonomy_folder}nodes.dmp"
        names="${taxonomy_folder}names.dmp"
        log_file="${int_file_folder}logfile.txt"
        owl_file="${go_folder}${used_go}"
        manual_constr="${add_files_folder}${used_man_constr_file}"
        tax_constr="${add_files_folder}${used_tax_constr_file}"

        "${src_folder}"./old_createConstraintsMergedAndSpecific.py -a "${aut_const}" -s "${species_list}" -m "${merged}" -t "${nodes}" -n "${names}" -o "${output_folder}" -l "${log_file}" -c "${manual_constr}" -w "${owl_file}" -p "${tax_constr}" ;;
    * )
        echo 'Merge the automatic constraints with the manual GO taxon constraints'

        go_const="${int_file_folder}constraintsCorrectNR_and_splitUnionNEW.txt"
        aut_const="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        aut_const="${int_file_folder}freqCumul_cluster_speciesGOusage_NEVER_IN_reformat.txt"
        species_list="${add_files_folder}${used_species_list_file}"
        merged="${taxonomy_folder}merged.dmp"
        nodes="${taxonomy_folder}nodes.dmp"
        names="${taxonomy_folder}names.dmp"
        log_file="${int_file_folder}logfile.txt"
        owl_file="${go_folder}${used_go}"
        manual_constr="${add_files_folder}${used_man_constr_file}"
        tax_constr="${add_files_folder}${used_tax_constr_file}"

        "${src_folder}"./old_createConstraintsMergedAndSpecific.py -g "${go_const}" -a "${aut_const}" -s "${species_list}" -m "${merged}" -t "${nodes}" -n "${names}" -o "${output_folder}" -l "${log_file}" -c "${manual_constr}" -w "${owl_file}" -p "${tax_constr}" ;;
esac

#!/bin/bash

# The necessary files download links.
goa_dl_site='ftp://ftp.ebi.ac.uk/pub/databases/GO/goa/UNIPROT/goa_uniprot_all.gaf.gz'
go_plus_dl_site='http://purl.obolibrary.org/obo/go/extensions/go-plus.owl'
taxon_dl_site='https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz'


# Function to download the file and save it in a specific folder.
# Parameters:
#  $1: the file's download link.
#  $2: the folder where we save the file.
#  $3: the filename.
download() {
    wget "$1" -O "$2"/"$3"
}


# Function to decompress .tar.gz and .gz files to the specified folder.
# Parameters:
#  $1: the compressed file.
#  $2: the folder where we save the file.
decompress() {
    if [[ "$1" =~ .*.tar.gz ]]
    then
       tar -xzf "$1" -C "$2"
    elif [[ "$1" =~ .*.gz ]]
    then
      gzip -c -d "$1" > "$2"/"goa_uniprot_all.gaf"
    fi

    rm "$1"
}


# Function to download and decompress the file to the specified folder.
# Parameters:
#  $1: the file's download link.
#  $2: the folder where we save the file.
#  $3: the downloaded filename.
dl_and_decompress() {
    download "$1" "$2" "$3"

    file="${2}/${3}"
    decompress "${file}" "$2"
}


# Function to verify the presence of the gene ontology file. If not present, we download it.
# Parameters:
#  $1: the path where we save the gene ontology file.
verifyGoFilePresence() {
    # Count the number of file with .owl extention.
    count=$(ls -1 "$1"/go-plus.owl 2> /dev/null | wc -l)
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        download "${go_plus_dl_site}" "$1" "go-plus.owl"
    elif [ $count -eq 0 ]; then
        download "${go_plus_dl_site}" "$1" "go-plus.owl"
    else
        echo "In the provided directory there exist already a go-plus.owl file, are you want to woverwrite it? (yes/no)"
        read answer
        case $answer in
            "Y"|"y"|"YES"|"Yes"|"yes")
                download "${go_plus_dl_site}" "$1" "go-plus.owl";;
            *)
                echo "Accepted affirmative answers are Y | YES | Yes | yes | y"
                echo "Interrupting the script"
                exit 1;;
        esac
    fi
}

# Function to verify the presence of the gene ontology annotation file. If not present, we download it.
# Parameters:
#  $1: the path where we save the gene ontology annotation file.
verifyGoaFilePresence() {
    # Count the number of file with .gaf extension.
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        dl_and_decompress "${goa_dl_site}" "$1" "goa_uniprot_all.gaf.gz"
    elif [ ! -f "$1"/goa_uniprot_all.gaf.gz ]; then
        check=$(ls -1 "$1"/*.gaf 2> /dev/null | wc -l)
        if [ $check -gt 0 ]; then
            echo "In the provided directory there exist already a GAF file, do you want to download the latest goa_uniprot_all.gaf.gz? (yes/no)"
            read answer
            case $answer in
                "Y"|"y"|"YES"|"Yes"|"yes")
                    dl_and_decompress "${go_plus_dl_site}" "$1" "goa_uniprot_all.gaf.gz";;
                *)
                    echo "Accepted affirmative answers are Y | YES | Yes | yes | y"
                    echo "Interrupting the script"
                    exit 1;;
            esac
        else
            dl_and_decompress "${goa_dl_site}" "$1" "goa_uniprot_all.gaf.gz"
        fi
    else
        echo "In the provided directory there exist already a goa_uniprot_all.gaf.gz file, are you sure to overwrite it? (yes/no)"
        read answer
        case $answer in
            "Y"|"y"|"YES"|"Yes"|"yes")
                dl_and_decompress "${go_plus_dl_site}" "$1" "goa_uniprot_all.gaf.gz";;
            *)
                echo "Accepted affirmative answers are Y | YES | Yes | yes | y"
                echo "Interrupting the script"
                exit 1;;
        esac
    fi
}

# Function to verify the presence of the taxonomy tree files. If not present, we download it.
# Parameters:
#  $1: the path where we save the taxonomy tree files.
verifyTaxonomyFilesPresence() {
    # Count the number of file with .dmp extention.
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        dl_and_decompress "${taxon_dl_site}" "$1" "taxdump.tar.gz"
    elif [ ! -f "$1"/taxdump.tar.gz ]; then
        check=$(ls -1 "$1"/*.dmp 2> /dev/null | wc -l)
        if [ $check -gt 0 ]; then
            echo "In the provided directory there exist already a taxdump folder, do you want to download the latest taxdump.tar.gz? (yes/no)"
            read answer
            case $answer in
                "Y"|"y"|"YES"|"Yes"|"yes")
                    dl_and_decompress "${taxon_dl_site}" "$1" "taxdump.tar.gz";;
                *)
                    echo "Accepted affirmative answers are Y | YES | Yes | yes | y"
                    echo "Interrupting the script"
                    exit 1;;
            esac
        else
            dl_and_decompress "${taxon_dl_site}" "$1" "taxdump.tar.gz"
        fi
    else
        echo "In the provided directory there exist already a taxdump.tar.gz file, are you sure to overwrite it? (yes/no)"
        read answer
        case $answer in
            "Y"|"y"|"YES"|"Yes"|"yes")
                dl_and_decompress "${taxon_dl_site}" "$1" "taxdump.tar.gz";;
            *)
                echo "Accepted affirmative answers are Y | YES | Yes | yes | y"
                echo "Interrupting the script"
                exit 1;;
        esac
    fi
}


usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "This script downloads from the latest version databases all the necessary data to run the FunTaxIS-lite pipeline, them being:"
    echo " - go-plus.owl:           the GO graph file"
    echo " - goa_uniprot_all.gaf:   the GOA gaf file"
    echo " - taxondump/ :           the taxonomy taxondump folder"
    echo "If no option is used, all files are downloaded in the default directory ./input/, specifically in sub-directories ./input/go/ , ./input/goa/ , ./input/taxonomy/"
    echo ""
    echo "OPTIONS:"
    echo ""
    echo "-w, --owl:        Folder where to save the go-plus.owl file (default is ./input/go/)."
    echo "-g, --goa:        Folder where to save the goa_uniprot_all.gaf file (default is ./input/goa/)."
    echo "-t, --taxonomy:   Folder where to save all the taxdump files (default is ./input/taxonomy/)."
    exit 1
}


# DEFAULT VALUES
go_folder="./input/go/"                 # It's the gene ontology file path.
goa_folder="./input/goa/"               # It's the gene ontology annotation file path.
taxonomy_folder="./input/taxonomy/"     # It's the taxonomy folder path.

download_all=1
download_owl=0
download_goa=0
download_taxonomy=0

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -w|--owl)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                go_folder="$2"
                download_owl=1
                download_all=0
            else
                echo "Expected argument after option -w/--owl!"
                usage
            fi
            shift
            shift;;

        -g|--goa)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                goa_folder="$2"
                download_goa=1
                download_all=0
            else
                echo "Expected argument after option -g/--goa!"
                usage
            fi
            shift
            shift;;

        -t|--taxonomy)
            if [[ $# -gt 1 && ! $2 == -* ]]; then
                taxonomy_folder="$2"
                download_taxonomy=1
                download_all=0
            else
                echo "Expected argument after option -t/--taxonomy!"
                usage
            fi
            shift
            shift;;
        -h|--help)
            usage;;
        *)
            # unknown option
            echo "Error: Unknown option $1"
            usage
            ;;
    esac
done

# Check
if [ $download_all -eq 1 ] || [ $download_owl -eq 1 ]; then
    verifyGoFilePresence "${go_folder}"
fi

# Check
if [ $download_all -eq 1 ] || [ $download_taxonomy -eq 1 ]; then
    verifyTaxonomyFilesPresence "${taxonomy_folder}"
fi

# Check
if [ $download_all -eq 1 ] || [ $download_goa -eq 1 ]; then
    verifyGoaFilePresence "${goa_folder}"
fi

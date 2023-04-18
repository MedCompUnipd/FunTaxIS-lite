# FunTaxIS-lite
FunTaxIS-lite is a faster version of the [FunTaxIS](https://www.nature.com/articles/srep31971) algorithm. FunTaxIS-lite is a tool devised to define what are the protein functions that are allowed in all living organisms.To accomplish this task, the tool can infer taxon-based constraints applied to Gene Ontology (GO) terms, greatly extending and improving those provided by the GO consortium. The algorithm is based on a set of rules to explore and propagate the constraints at taxon hierarchy level and GO graph level respectively. Data are routinely extracted from the NCBI taxonomy database, available GO annotations in GOA database, and GO graph. The tool is aimed at improving automatic function prediction annotation algorithms filtering out potentially wrong annotations and to help in assessing the electronically inferred annotations (IEA) of the GOA database.
## Dependencies
The required dependencies, to successfully run FunTaxIS-lite, are the following:

* C/C++ compiler
* [Cython](https://pypi.org/project/Cython/)
* [Owlready2](https://pypi.org/project/Owlready2/)
* [argparse](https://pypi.org/project/argparse/)



Optional dependence is the following:

 * [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

The Beautiful Soup library is used to automatically get the new taxonomic ID when an ID writes in the taxonConstraintsDef.txt file is not found in the tree. Otherwise a warning is thrown.

## Info
This repository contains four scripts, three folders and one configuration file (that can be edited by the user):

- `run.sh` to run FunTaxIS-lite;
- `download.sh` to download the latest release of GOA, go.owl and taxonomy (required by FunTaxIS-lite). This files are saved in the input folder by default.
- `generate_intermediates.sh` to generates the intermediate files (needed to generate taxonomic constraints). The script can be run if the go, GOA, and taxonomy data exist.
- `generate_constraints.sh` to generate the taxonomic constraints. It can be run either after the `generate_all_taxon_constraints.sh` script or if the required intermediate files exist.
- `/src`, which contains the source code
- `/input`, which contains the required input files and the `add_files` folder with:
    - `excluded_nodes.txt`,  file with all the excluded node from taxonomy
    - `manualConstraints.txt`, the manual constraints file (that can be edited by the user)
    - `taxonConstraintsDef.txt`, file containing all the taxon reference nodes
- `/containers`, which contains the Docker file and the Singularity definition file.
- `config_file.cfg`, the configuration file that contains the following parameters:
    - `folder`: the folder containing all the required files to correctly run FunTaxIS-lite and the intermediate files generated by FunTaxIS-lite. (Mandatory.)
    - `go`: the GO graph file path. The file must be in OWL format and the PLUS version. Without the parameter the script downloads the latest release of the Gene Ontology graph. (Optional. Default: GO's latest release.)
    - `goa`: the GOA file path. The file must be in GAF format. Without the parameter the script downloads the latest release of the Gene Ontology Annotation. (Optional. Default: GOA's latest release.)
    - `taxonomy`: the NCBI's taxonomy taxdump folder. Without the parameter the script downloads the latest release of the NCBI's taxonomy tree. (Optional. Default: Taxonomy's latest release.)
    - `taxon-def`: the taxonomy nodes ID list at species level and above used to define the taxonomic constraints. Without the parameter the script uses the taxonConstraintDef.txt file in add_files folder. (Optional. Default: use the taxonomy definition file in add_files folder.)
    - `species`: the list of species of interest. Without the parameter the script uses the species.txt file in add_files folder. (Optional. Default: use the species file in add_files directory.)
    - `manual-constraints`: list of specific constraints that overrule the existing constraints. Without the parameter the script uses the manualConstraints.txt file in add_files folder. (Optional. Default: use the manual constratins file in add_files folder.)
    - `cutoff`: the GO's frequency threshold used to define constraints. (Optional. Default: 500)
    - `debug`: if true, maintains the intermediary files. Allowed values are `true`, `t`, `false`, and `f`. (Optional. Default: false.)
    - `type`: the type of taxonomic constraints generated. Allowed values are `automatic`, `auto`, `a`, `manual`, `man`, and `m`. (Optional. Default: manual and automatic.)
    - `results`: the output files folder. (Mandatory.)

## Usage
Before running FunTaxIS-lite, allow all permission (rwx) on src folder by typing the following command:

<code>chmod -R 777 src/ </code>
   
Then you can run FunTaxIS-lite in two ways:

1.  Running the whole pipeline from scratch using one command
2.  Running only the desired modules of the pipeline (using the `run.sh` script or by hand)

To run FunTaxIS-lite use the `run.sh` script as follow:

    ./run.sh <options>

with options:

- `-h` for help message
- `-f` to run the full pipeline
- `-d` to only execute the downloads
- `-i` to only generate the intermediate files (existing initial downloads are needed)
- `-c` to only generate the constraints (existing intermediate files are needed)
- `-s` to pass the configuration file to the scripts requiring it (mandatory)

For example, if you want to run the whole pipeline, including downloading the latest release of goa, go and taxonomy, run the script as follow:

    ./run.sh -f -s config_file.cfg

`run.sh` executes `download.sh`, `generate_intermediates.sh` and `generate_constraints.sh` in order. 
However, it can be overrun by executing specific step scripts. If you just want to download goa, go and taxonomy, run one of the following commands:

    ./run.sh -d -s config_file.cfg 
      
    ./download.sh config_file.cfg

If you've already downloaded the goa, go and taxonomy files or you want to generate constraints starting from different releases of goa, go and taxonomy, you can skip the download script and run the pipeline with one of the following commands:

    ./run.sh -i -s config_file.cfg
    
    ./generate_intermediates.sh config_file.cfg

Finally, if you've already generated the intermediate files and you just need to generate taxon constraints, you can just run the last script using one of the following commands:
    
    ./run.sh -c -s config_file.cfg
    
    ./generate_constraints.sh config_file.cfg

NOTE: The intermediate files strictly depends on goa, go and taxonomy releases. If you use different releases you have to regenerate the intermediate files before generate constraints!

## Containers

In the `containers` folder contains the [Docker](https://www.docker.com/) and [Singularity](https://sylabs.io/singularity/) definition files.

The `launcher.sh` is used inside the container to correctly run one of the above scripts.

To build the container use one of the following commands (with root permission) inside the FunTaxIS-lite folder:

    docker build -t <image_name> -f <dockerfile_path>

or

    singularity build -F <image_name> <definition_file_path>

for Docker and Singularity respectively.

After the container is builted, the container can be used with one of the following commands:

    docker run <image_name> [options] <config_file_path>

or

    singularity run <image_name> [options] <config_file_path>

The available options are the following:
* `-a`: to generate the taxonomic constraints of all the species found in the input data.
* `-d`: to download all the necessary data to correctly run FunTaxIS-lite.
* `-f`: to use the complete FunTaxIS pipeline.
* `-s`: to generate the taxonomic constraints of the species chosen by the user.

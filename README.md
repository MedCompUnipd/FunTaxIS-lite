# FunTaxIS-Lite
FunTaxIS-lite is a faster version of the FunTaxIS algorithm. FunTaxIS considers Gene Ontology (GO) terms and their frequencies found in the Gene Ontology Annotation (GOA) database. Since annotations are linked to proteins and species, the frequencies of GO terms can be associated with the species (identified by an ID) which the proteins belong to. This association between GO terms and taxonomic ID is exploited to infer which terms are allowed or forbidden for annotating proteins of a particular species, providing a set of constraints between them.
# Dependencies
The required dependencies, to successfully run FunTaxIS-lite, are the following:

* C/C++ compiler
* [Cython](https://pypi.org/project/Cython/)
* [Owlready2](https://pypi.org/project/Owlready2/)
* [argparse](https://pypi.org/project/argparse/)



Optional dependence is the following:

 * [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

The Beautiful Soup library is used to automatically get the new taxonomic ID when an ID writes in the taxonConstraintsDef.txt file is not found in the tree. Otherwise a warning is thrown.

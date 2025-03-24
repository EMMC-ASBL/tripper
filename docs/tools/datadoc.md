Datadoc
=======
`datadoc` is a command-line tool for data documentation which comes with Tripper.
It provides functionality for both populating a triplestore with data documentation and to search for and find the documentation at a later stage.

Running `datadoc --help` from the shell will show the following help message:

```
usage: datadoc [-h] [--config CONFIG] [--triplestore TRIPLESTORE]
               [--backend BACKEND] [--base-iri BASE_IRI] [--database DATABASE]
               [--package PACKAGE] [--parse LOCATION]
               [--parse-format PARSE_FORMAT] [--prefix PREFIX=URL]
               {add,find,fetch} ...

Tool for data documentation. It allows populating and searching a triplestore
for existing documentation.

positional arguments:
  {add,find,fetch}      Subcommands:
    add                 Populate the triplestore with data documentation.
    find                Find documented resources in the triplestore.
    fetch               Fetch documented dataset from a storage.

options:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Session configuration file.
  --triplestore TRIPLESTORE, -t TRIPLESTORE
                        Name of triplestore to connect to. The name should be
                        defined in the session configuration file.
  --backend BACKEND, -b BACKEND
                        Triplestore backend to use. Defaults to "rdflib" - an
                        in-memory rdflib triplestore, that can be pre-loaded
                        with --parse.
  --base-iri BASE_IRI, -B BASE_IRI
                        Base IRI of the triplestore.
  --database DATABASE, -d DATABASE
                        Name of database to connect to (for backends
                        supporting it).
  --package PACKAGE     Only needed when `backend` is a relative module.
  --parse LOCATION, -p LOCATION
                        Load triplestore from this location.
  --parse-format PARSE_FORMAT, -F PARSE_FORMAT
                        Used with `--parse`. Format to use when parsing
                        triplestore.
  --prefix PREFIX=URL, -P PREFIX=URL
                        Namespace prefix to bind to the triplestore. This
                        option can be given multiple times.
```

Currently, `datadoc` has currently three sub-commands, `add`, `find` and `load` for populating  the triplestore, searching  the triplestore and accessing a dataset documented the triplestore, respectively.

### General options

* The `--config`, `--triplestore`, `--backend`, `--base-iri`, `--database` and `--package` options are all for connecting to a triplestore.
  The most convenient method is to configure a [session] and use the `--triplestore` argument to select the triplestore to connect to.

* The `--parse`, `--parse-format` and `--prefix` options are for pre-loading the triplestore with triples from an external source, like a ntriples or turtle file, and for adding namespace prefixes.
They are typically used with the default "rdflib" in-memory backend.


Subcommands
----------

### add
Populates the triplestore with data documentation.
Running `datadoc add --help` will show the following help message:

```
usage: datadoc add [-h] [--input-format {yaml,csv}]
                   [--csv-options OPTION=VALUE [OPTION=VALUE ...]]
                   [--context CONTEXT] [--dump FILENAME] [--format FORMAT]
                   input

positional arguments:
  input                 Path or URL to the input the triplestore should be
                        populated from.

options:
  -h, --help            show this help message and exit
  --input-format {yaml,csv}, -i {yaml,csv}
                        Input format. By default it is inferred from the file
                        extension of the `input` argument.
  --csv-options OPTION=VALUE [OPTION=VALUE ...]
                        Options describing the CSV dialect for --input-
                        format=csv. Common options are 'dialect', 'delimiter'
                        and 'quotechar'.
  --context CONTEXT     Path or URL to custom JSON-LD context for the input.
  --dump FILENAME, -d FILENAME
                        File to dump the populated triplestore to.
  --format FORMAT, -f FORMAT
                        Format to use with `--dump`. Default is "turtle".
```

The positional `input` argument is the path or URL to the source from which to populate the triplestore.
The `--input-format`, `--csv-options` and `--context` options provide more details about the input.

The `--dump` and `--format` options allow to dump the populated triplestore to file.
This is useful if you are working with an in-memory triplestore.

!!! example

    The `tests/input/` folder in the source code contain the `semdata.csv` CSV file documenting four datasets, a SEM image, two nested dataset series and the sample the image was acquired from as shown in the figure below (click on it to see it in full size).

    [![semdata.csv](/figs/semdata.png)](/figs/semdata.png)

    Running the following command from the root folder of the source code will populate an in-memory rdflib store with the data documented in the `semdata.csv` file.

    ```shell
    datadoc add tests/input/semdata.csv --context tests/input/semdata-context.json --dump kb.ttl
    ```

    The `--context` option provides a user-defined context defining prefixes and keywords used by the input.

    The `--dump` option dumps the in-memory triplestore to the file `kb.ttl`.
    If you open the file, you will notice that it in addition to the four datasets listed in the input, also include the `SEMImage` class and its properties, providing structural documentation of the `SEMImage` individuals.

    ??? abstract "Generated turtle file"

        ```turtle
        @prefix chameo: <https://w3id.org/emmo/domain/characterisation-methodology/chameo#> .
        @prefix dcat: <http://www.w3.org/ns/dcat#> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix emmo: <https://w3id.org/emmo#> .
        @prefix oteio: <https://w3id.org/emmo/domain/oteio#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix skos: <http://www.w3.org/2004/02/skos/core#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage> a owl:Class ;
            rdfs:subClassOf [ a owl:Restriction ;
                    owl:onClass <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data> ;
                    owl:onProperty emmo:EMMO_b19aacfc_5f73_4c33_9456_469c1e89a53e ;
                    owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ],
                [ a owl:Restriction ;
                    owl:onClass <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#labels> ;
                    owl:onProperty emmo:EMMO_b19aacfc_5f73_4c33_9456_469c1e89a53e ;
                    owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ],
                [ a owl:Restriction ;
                    owl:onClass <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#metadata> ;
                    owl:onProperty emmo:EMMO_b19aacfc_5f73_4c33_9456_469c1e89a53e ;
                    owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ],
                [ a owl:Restriction ;
                    owl:onClass <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#pixelheight> ;
                    owl:onProperty emmo:EMMO_b19aacfc_5f73_4c33_9456_469c1e89a53e ;
                    owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ],
                [ a owl:Restriction ;
                    owl:onClass <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#pixelwidth> ;
                    owl:onProperty emmo:EMMO_b19aacfc_5f73_4c33_9456_469c1e89a53e ;
                    owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ],
                emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
            skos:prefLabel "SEMImage"@en ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "SEM image with elemental mappings. Represented as a stack of elemental mapping\\nfollowed by the image formed by the back-scattered electrons (BSE).\\nSet `nelements=0` if you only have the back-scattered image.\\n"@en ;
            oteio:hasURI "http://onto-ns.com/meta/matchmaker/0.2/SEMImage"^^xsd:anyURI .

        <https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001> a dcat:Dataset,
                <https://w3id.com/emmo/domain/sem/0.1#SEMImage>,
                emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
            dcterms:creator "Sigurd Wenner" ;
            dcterms:description "Back-scattered SEM image of cement sample 77600 from Heidelberg, polished with 1 µm diamond compound." ;
            dcterms:title "SEM image of cement" ;
            dcat:contactPoint "Sigurd Wenner <Sigurd.Wenner@sintef.no>" ;
            dcat:distribution [ a dcat:Distribution ;
                    <http://sintef.no/dlite/parser#> "http://sintef.no/dlite/parser#sem_hitachi" ;
                    dcat:downloadURL "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/master/tests/input/77600-23-001_5kV_400x_m001.tif" ;
                    dcat:mediaType "image/tiff" ] ;
            dcat:inSeries <https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001> ;
            emmo:EMMO_f702bad4_fc77_41f0_a26d_79f6444fd4f3 <https://he-matchmaker.eu/material/concrete1> ;
            oteio:hasDatamodel "http://onto-ns.com/meta/matchmaker/0.2/SEMImage" ;
            oteio:hasDatamodelStorage "https://github.com/HEU-MatCHMaker/DataDocumentation/blob/master/SEM/datamodels/SEMImage.yaml" .

        <https://he-matchmaker.eu/sample/SEM_cement_batch2/77600-23-001> a dcat:Dataset,
                emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a,
                chameo:Sample ;
            dcterms:title "Series for SEM images for sample 77600-23-001." .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data> a owl:Class ;
            rdfs:subClassOf [ a owl:Restriction ;
                    owl:hasValue <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data_dimension0> ;
                    owl:onProperty emmo:EMMO_0a9ae0cb_526d_4377_9a11_63d1ce5b3499 ],
                [ a owl:Restriction ;
                    owl:onProperty emmo:EMMO_e5a34647_a955_40bc_8d81_9b784f0ac527 ;
                    owl:someValuesFrom emmo:EMMO_ac9e518d_b403_4d8b_97e2_06f9d40bac01 ],
                emmo:EMMO_28fbea28_2204_4613_87ff_6d877b855fcd,
                emmo:EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a ;
            skos:prefLabel "Data"@en ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Image data - a stack of images for each channel"@en ;
            oteio:datasize "4"^^xsd:nonNegativeInteger .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data_dimension0> a emmo:EMMO_b4c97fa0_d82c_406a_bda7_597d6e190654 ;
            skos:prefLabel "data_dimension0"@en ;
            emmo:EMMO_23b579e1_8088_45b5_9975_064014026c42 "channels"^^xsd:string ;
            emmo:EMMO_499e24a5_5072_4c83_8625_fe3f96ae4a8d <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data_dimension1> ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Number of channels."@en .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data_dimension1> a emmo:EMMO_b4c97fa0_d82c_406a_bda7_597d6e190654 ;
            skos:prefLabel "data_dimension1"@en ;
            emmo:EMMO_23b579e1_8088_45b5_9975_064014026c42 "height"^^xsd:string ;
            emmo:EMMO_499e24a5_5072_4c83_8625_fe3f96ae4a8d <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data_dimension2> ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Number of pixels along the image height."@en .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#data_dimension2> a emmo:EMMO_b4c97fa0_d82c_406a_bda7_597d6e190654 ;
            skos:prefLabel "data_dimension2"@en ;
            emmo:EMMO_23b579e1_8088_45b5_9975_064014026c42 "width"^^xsd:string ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Number of pixels along the image width."@en .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#labels> a owl:Class ;
            rdfs:subClassOf [ a owl:Restriction ;
                    owl:hasValue <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#labels_dimension0> ;
                    owl:onProperty emmo:EMMO_0a9ae0cb_526d_4377_9a11_63d1ce5b3499 ],
                [ a owl:Restriction ;
                    owl:onProperty emmo:EMMO_e5a34647_a955_40bc_8d81_9b784f0ac527 ;
                    owl:someValuesFrom emmo:EMMO_5f334606_f67d_4f0e_acb9_eeb21cb10c66 ],
                emmo:EMMO_28fbea28_2204_4613_87ff_6d877b855fcd,
                emmo:EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a ;
            skos:prefLabel "Labels"@en ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "The label of each channel. For elemental mapping this should be the chemical symbol of the element or BSE for the back-scattered image."@en .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#labels_dimension0> a emmo:EMMO_b4c97fa0_d82c_406a_bda7_597d6e190654 ;
            skos:prefLabel "labels_dimension0"@en ;
            emmo:EMMO_23b579e1_8088_45b5_9975_064014026c42 "channels"^^xsd:string ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Number of channels."@en .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#metadata> a owl:Class ;
            rdfs:subClassOf emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a,
                emmo:EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a ;
            skos:prefLabel "Metadata"@en ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Reference to data model for SEM metadata."@en .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#pixelheight> a owl:Class ;
            rdfs:subClassOf [ a owl:Restriction ;
                    owl:onClass emmo:Metre ;
                    owl:onProperty emmo:EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569 ;
                    owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ],
                emmo:EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a,
                emmo:EMMO_52fa9c76_fc42_4eca_a5c1_6095a1c9caab ;
            skos:prefLabel "Pixelheight"@en ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Height of each pixel."@en ;
            oteio:datasize "8"^^xsd:nonNegativeInteger .

        <http://onto-ns.com/meta/matchmaker/0.2/SEMImage#pixelwidth> a owl:Class ;
            rdfs:subClassOf [ a owl:Restriction ;
                    owl:onClass emmo:Metre ;
                    owl:onProperty emmo:EMMO_bed1d005_b04e_4a90_94cf_02bc678a8569 ;
                    owl:qualifiedCardinality "1"^^xsd:nonNegativeInteger ],
                emmo:EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a,
                emmo:EMMO_52fa9c76_fc42_4eca_a5c1_6095a1c9caab ;
            skos:prefLabel "Pixelwidth"@en ;
            emmo:EMMO_967080e5_2f42_4eb2_a3a9_c58143e835f9 "Width of each pixel."@en ;
            oteio:datasize "8"^^xsd:nonNegativeInteger .

        <https://he-matchmaker.eu/data/sem/SEM_cement_batch2> a dcat:Dataset,
                <https://w3id.com/emmo/domain/sem/0.1#SEMImageSeries>,
                emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
            dcterms:creator "Sigurd Wenner" ;
            dcterms:description "..." ;
            dcterms:title "Nested series of SEM images of cement batch2" ;
            dcat:contactPoint "Sigurd Wenner <Sigurd.Wenner@sintef.no>" ;
            dcat:distribution [ a dcat:Distribution ;
                    dcat:downloadURL "sftp://nas.aimen.es/P_MATCHMAKER_SHARE_SINTEF/SEM_cement_batch2" ;
                    dcat:mediaType "inode/directory" ] .

        <https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001> a dcat:Dataset,
                <https://w3id.com/emmo/domain/sem/0.1#SEMImageSeries>,
                emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
            dcterms:creator "Sigurd Wenner" ;
            dcterms:description "Back-scattered SEM image of cement sample 77600, polished with 1 µm diamond compound." ;
            dcterms:title "Series of SEM image of cement sample 77600" ;
            dcat:contactPoint "Sigurd Wenner <Sigurd.Wenner@sintef.no>" ;
            dcat:distribution [ a dcat:Distribution ;
                    dcat:downloadURL "sftp://nas.aimen.es/P_MATCHMAKER_SHARE_SINTEF/SEM_cement_batch2/77600-23-001" ;
                    dcat:mediaType "inode/directory" ] ;
            dcat:inSeries <https://he-matchmaker.eu/data/sem/SEM_cement_batch2> .

        ```


### find
Search the triplestore for documented resources.
Running `datadoc find --help` will show the following help message:

```
usage: datadoc find [-h] [--type TYPE]
                    [--criteria KEYWORD=VALUE [KEYWORD=VALUE ...]]
                    [--output FILENAME] [--format {iris,json,turtle,csv}]

options:
  -h, --help            show this help message and exit
  --type TYPE, -t TYPE  Either a resource type (ex: "dataset", "distribution",
                        ...) or the IRI of a class to limit the search to.
  --criteria IRI=VALUE, -c IRI=VALUE
                        Matching criteria for resources to find. The IRI may
                        be written using a namespace prefix, like
                        `tcterms:title="My title"`. Currently only exact
                        matching is supported. This option can be given
                        multiple times.
  --output FILENAME, -o FILENAME
                        Write matching output to the given file. The default
                        is to write to standard output.
  --format {iris,json,turtle,csv}, -f {iris,json,turtle,csv}
                        Output format to list the matched resources. The
                        default is to infer from the file extension if
                        --output is given. Otherwise it defaults to "iris".
```

The `--type` and `--criteria` options provide search criteria.
The `--type` option can be any of the recognised [resource types] to limit the search to.
Alternatively, it may be the IRI of a class.
This limits the search to only resources that are individuals of this class.

The `--output` option allows to write the matching output to file instead of standard output.

The `--format` option controls how the search result should be presented.
The following formats are currently available:

- **iris**: Return the IRIs of matching resources.
- **json**: Return a JSON array with documentation of matching resources.
- **turtle**: Return a turtle representation of matching resources.

      *Note*: In case the matching resources are datasets with a `datamodel` keyword, the serialised data model will also be included in the turtle output.

- **csv**: Return a CSV table with the matching resources.

!!! example "Examples"

    For all the examples below, we use `--parse` option to pre-load the triplestore from the `kb.ttl` file that we generated in the previous example.

    **Ex 1**: List IRIs of all datasets:

    ```shell
    $ datadoc --parse=kb.ttl find --type=dataset
    https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001
    https://he-matchmaker.eu/sample/SEM_cement_batch2/77600-23-001
    https://he-matchmaker.eu/data/sem/SEM_cement_batch2
    https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001
    ```

    **Ex 2**: List IRIs of all samples (individuals of `chameo:Sample`):

    ```shell
    $ datadoc --parse=kb.ttl find --type=chameo:Sample
    https://he-matchmaker.eu/sample/SEM_cement_batch2/77600-23-001
    ```

    **Ex 3**: List IRIs of all resources with a given title:

    ```shell
    $ datadoc --parse=kb.ttl find --criteria dcterms:title="Series of SEM image of cement sample 77600"
    https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001
    ```

    **Ex 4**: List all sample individuals as JSON:

    ```shell
    $ datadoc --parse=kb.ttl find --type=chameo:Sample --format=json
    ```

    ```json
    [
      {
        "@id": "https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001",
        "@type": [
          "http://www.w3.org/ns/dcat#Dataset",
          "https://w3id.com/emmo/domain/sem/0.1#SEMImageSeries",
          "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a"
        ],
        "creator": "Sigurd Wenner",
        "description": "Back-scattered SEM image of cement sample 77600, polished with 1 \u00b5m diamond compound.",
        "title": "Series of SEM image of cement sample 77600",
        "contactPoint": "Sigurd Wenner <Sigurd.Wenner@sintef.no>",
        "distribution": {
          "@id": "_:nac2552b949a94ef391080807ca2a02e4b14",
          "@type": "http://www.w3.org/ns/dcat#Distribution",
          "downloadURL": "sftp://nas.aimen.es/P_MATCHMAKER_SHARE_SINTEF/SEM_cement_batch2/77600-23-001",
          "mediaType": "inode/directory"
        },
        "inSeries": "https://he-matchmaker.eu/data/sem/SEM_cement_batch2"
      }
    ]
    ```

    **Ex 5**: Show the documentation of a resource with a given IRI as JSON:

    ```shell
    $ datadoc --parse=kb.ttl find --criteria @id=https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001 --format=json
    ```

    This will show the same output as in Ex 4.


### fetch
Fetch documented dataset from a storage.
Running `datadoc fetch --help` will show the following help message:

```
usage: datadoc fetch [-h] [--output FILENAME] iri

positional arguments:
  iri                   IRI of dataset to fetch.

options:
  -h, --help            show this help message and exit
  --output FILENAME, -o FILENAME
                        Write the dataset to the given file. The default is to
                        write to standard output.
```

!!! note
    The `fetch` subcommand is specific for datasets since it uses DCAT documentation of how to fetch the dataset.

The positional `iri` argument is the IRI of the documented dataset to fetch.

The `--output` option allows to write the dataset to a local file.


!!! example

    Save the dataset `https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001` documented in `kb.ttl` to file:

    ```shell
    $ datadoc -p kb.ttl fetch https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001 -o cement.tif
    ```

    This should create the file `cement.tif` containing the image data.




[resource types]: ../datadoc/introduction.md/#resource-types
[session]: ../session.md

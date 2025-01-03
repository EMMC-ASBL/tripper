Customisations
==============


User-defined prefixes
---------------------
A namespace prefix is a mapping from a *prefix* to a *namespace URL*.
For example

    owl: http://www.w3.org/2002/07/owl#

Tripper already include a default list of [predefined prefixes].
Additional prefixed can be provided in two ways.

### With the `prefixes` argument
Several functions in the API (like [save_dict()], [as_jsonld()] and [TableDoc.parse_csv()]) takes a `prefixes` argument with which additional namespace prefixes can provided.

This may be handy when used from the Python API.


### With custom context
Additional prefixes can also be provided via a custom JSON-LD context as a `"prefix": "namespace URL"` mapping.

See [User-defined keywords] for how this is done.


User-defined keywords
---------------------
Tripper already include a long list of [predefined keywords], that are defined in the [default JSON-LD context].
A description of how to define new concepts in the JSON-LD context is given by [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/) document, and can be tested in the [JSON-LD Playground](https://json-ld.org/playground/).

A new custom keyword can be added by providing mapping in a custom JSON-LD context from the keyword to the IRI of the corresponding concept in an ontology.

Lets assume that you already have a domain ontology with base IRI http://example.com/myonto#, that defines the concepts for the keywords you want to use for the data documentation.

First, you can add the prefix for the base IRI of your domain ontology to a custom JSON-LD context

    "myonto": "http://example.com/myonto#",

How the keywords should be specified in the context depends on whether they correspond to a data property or an object property in the ontology and whether a given datatype is expected.

### Simple literal
Simple literals keywords correspond to data properties with no specific datatype (just a plain string).

Assume you want to add the keyword `batchNumber` to relate documented samples to the number assigned to the batch they are taken from.
It corresponds to the data property http://example.com/myonto#batchNumber in your domain ontology.
By adding the following mapping to your custom JSON-LD context, `batchNumber` becomes available as a keyword for your data documentation:

    "batchNumber": "myonto:batchNumber",

### Literal with specific datatype
If `batchNumber` must always be an integer, you can specify this by replacing the above mapping with the following:

    "batchNumber": {
        "@id": "myonto:batchNumber",
        "@type": "xsd:integer"
    },

Here "@id" refer to the IRI `batchNumber` is mapped to and "@type" its datatype. In this case we use `xsd:integer`, which is defined in the W3C `xsd` vocabulary.

### Object property
Object properties are relations between two individuals in the knowledge base.

If you want to say more about the batches, you may want to store them as individuals in the knowledge base.
In that case, you may want to add a keyword `fromBatch` which relate your sample to the batch it was taken from.
In your ontology you may define `fromBatch` as a object property with IRI: http://example.com/myonto/fromBatch.


    "fromBatch": {
        "@id": "myonto:fromBatch",
        "@type": "@id"
    },

Here the special value "@id" for the "@type" means that the value of `fromBatch` must be an IRI.


Providing a custom context
--------------------------
Custom context can be provided for all the interfaces described in the section [Documenting a resource].

In the YAML documentation, Custom context can be provided with the "@context"


User-defined resource types
---------------------------
TODO

Extending the list of predefined [resource types] it not implemented yet.

Since JSON-LD is not designed for categorisation, new resource types should not be added in a custom JSON-LD context.
Instead, the list of available resource types should be stored and retrieved from the knowledge base.



[Documenting a resource]: ../documenting-a-resource
[With custom context]: #with-custom-context
[User-defined keywords]: #user-defined-keywords
[resource types]: ../introduction#resource-types
[predefined prefixes]: ../prefixes
[predefined keywords]: ../keywords
[save_dict()]: ../../api_reference/dataset/dataset/#tripper.dataset.dataset.save_dict
[as_jsonld()]: ../../api_reference/dataset/dataset/#tripper.dataset.dataset.as_jsonld
[save_datadoc()]:
../../api_reference/dataset/dataset/#tripper.dataset.dataset.save_datadoc
[TableDoc.parse_csv()]: ../../api_reference/dataset/tabledoc/#tripper.dataset.tabledoc.TableDoc.parse_csv
[default JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.2/context.json

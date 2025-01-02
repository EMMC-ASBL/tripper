Data documentation
==================
<!-- markdownlint-disable MD007 -->


Introduction
------------
The data documentation is based on small [JSON-LD documents], each documenting a single resource.
Examples of resources can be a dataset, an instrument, a sample, etc.
All resources are uniquely identified by their IRI.

The primary focus of the [tripper.dataset] module is to document datasets such that they are consistent with the [DCAT vocabulary], but at the same time easily extended additional semantic meaning provided by other ontologies.
It is also easy to add and relate the datasets to other types of documents, like people, instruments and samples.

The [tripper.dataset] module provides a Python API for documenting resources at all four levels of data documentation, including:

- **Cataloguing**: Storing and accessing *documents* based on their IRI and data properties.
  (Addressed FAIR aspects: *findability* and *accessibility*).
- **Structural documentation**: The structure of a dataset. Provided via [DLite] data models.
  (Addressed FAIR aspects: *interoperability*).
- **Contextual documentation**: Relations between resources, i.e. *linked data*. Enables contextual search.
  (Addressed FAIR aspects: *findability* and *reusability*).
- **Semantic documentation**: Describe what the resource *is* using ontologies. In combination with structural documentation, maps the properties of a data model to ontological concepts.
  (Addressed FAIR aspects: *findability*, *interoperability* and *reusability*).

The figure below shows illustrates how a dataset is documented in a triplestore.

![Documentation of a dataset](https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/docs/figs/dataset-Dataset.png)


Resource types
--------------
The [tripper.dataset] module include the following set of predefined resource types:

- **dataset**: Individual of [dcat:Dataset] and [emmo:DataSet].
- **distribution**: Individual of [dcat:Distribution].
- **accessService**: Individual of [dcat:AccessService].
- **generator**: Individual of [oteio:Generator].
- **parser**: Individual of [oteio:Parser].
- **resource**: Any other documented resource, with no implicit type.

Future releases will support adding custom resource types.


Documenting a resource
----------------------
In the Python API are the JSON-LD documents describing the resources internally represented as Python dicts.
However, the [tripper.dataset] module tries to hide away the complexities of  [JSON-LD] behind a simple interface.


### Documenting as a Python dict
The API supports two Python dict representations, one for documenting a single resource and one for documenting multiple resources.


#### Single-resource dict
Below is a simple example of how to document a SEM image dataset as a Python dict:

```python
>>> dataset = {
...     "@id": "kb:image1",
...     "@type": "sem:SEMImage",
...     "creator": "Sigurd Wenner",
...     "description": "Back-scattered SEM image of cement, polished with 1 µm diamond compound.",
...     "distribution": {
...         "downloadURL": "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/master/tests/input/77600-23-001_5kV_400x_m001.tif",
...         "mediaType": "image/tiff"
...     }
... }

```

The keywords are defined in the [default JSON-LD context] and documented under [Predefined keywords].

This example uses two namespace prefixes not included in the [predefined prefixes].
We therefore have to define them explicitly

```python
>>> prefixes = {
...     "sem": "https://w3id.com/emmo/domain/sem/0.1#",
...     "kb": "http://example.com/kb/"
... }

```

!!! note "Side note"

    This dict is actually a [JSON-LD] document with an implicit context.
    You can use [as_jsonld()] to create a valid JSON-LD document from it.
    In addition to add a `@context` field, this function also adds some implicit `@type` declarations.

    ```python
    >>> import json
    >>> from tripper.dataset import as_jsonld
    >>> d = as_jsonld(dataset, prefixes=prefixes)
    >>> print(json.dumps(d, indent=2))
    {
      "@context": "https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.2/context.json",
      "@type": [
        "http://www.w3.org/ns/dcat#Dataset",
        "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
        "https://w3id.com/emmo/domain/sem/0.1#SEMImage"
      ],
      "@id": "http://example.com/kb/image1",
      "creator": "Sigurd Wenner",
      "description": "Back-scattered SEM image of cement, polished with 1 \u00b5m diamond compound.",
      "distribution": {
        "@type": "http://www.w3.org/ns/dcat#Distribution",
        "downloadURL": "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/master/tests/input/77600-23-001_5kV_400x_m001.tif",
        "mediaType": "image/tiff"
      }
    }

    ```

You can use [save_dict()] to save this documentation to a triplestore.
Since the prefixes "sem" and "kb" are not included in the [Predefined prefixes], they are have to be provided explicitly.

```python
>>> from tripper import Triplestore
>>> from tripper.dataset import save_dict
>>> ts = Triplestore(backend="rdflib")
>>> save_dict(ts, dataset, prefixes=prefixes)  # doctest: +ELLIPSIS
AttrDict(...)

```

You can use `ts.serialize()` to list the content of the triplestore (defaults to turtle):

```python
>>> print(ts.serialize())
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix emmo: <https://w3id.org/emmo#> .
@prefix kb: <http://example.com/kb/> .
@prefix sem: <https://w3id.com/emmo/domain/sem/0.1#> .
<BLANKLINE>
kb:image1 a dcat:Dataset,
        sem:SEMImage,
        emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a ;
    dcterms:creator "Sigurd Wenner" ;
    dcterms:description "Back-scattered SEM image of cement, polished with 1 µm diamond compound." ;
    dcat:distribution [ a dcat:Distribution ;
            dcat:downloadURL "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/master/tests/input/77600-23-001_5kV_400x_m001.tif" ;
            dcat:mediaType "image/tiff" ] .
<BLANKLINE>
<BLANKLINE>

```

Note that the image implicitly has been declared to be an individual of the classes `dcat:Dataset` and `emmo:DataSet`.
This is because the `type` argument of [save_dict()] defaults to "dataset".


#### Multi-resource dict
It is also possible to document multiple resources as a Python dict.

!!! note

    Unlike the single-resource dict representation, the multi-resource dict representation is not valid (possible incomplete) JSON-LD.

This dict representation accepts the following keywords:

- **@context**: Optional user-defined context to be appended to the documentation of all resources.
- **prefixes**: A dict mapping namespace prefixes to their corresponding URLs.
- **datasets**/**distributions**/**accessServices**/**generators**/**parsers**/**resources**: A list of valid [single-resource](#single-resource-dict) dict of the given [resource type](#resource-types).

See [semdata.yaml] for an example of a [YAML] representation of a multi-resource dict documentation.


### Documenting as a YAML file
The [save_datadoc()] function allow to save a [YAML] file in [multi-resource](#multi-resource-dict) format to a triplestore.

See [semdata.yaml] for an example.


### Documenting as table
The [TableDoc] class can be used to document multiple resources as rows in a table.

The table must have a header row with defined keywords (either [predefined][predefined keywords] or provided with a custom context).
Nested fields may be specified as dot-separated keywords. For example, the table

| @id | distribution.downloadURL |
| --- | ------------------------ |
| :a  | http://example.com/a.txt |
| :b  | http://example.com/b.txt |

correspond to the following turtle representation:

```turtle
:a dcat:distribution [
    a dcat:Distribution ;
    downloadURL "http://example.com/a.txt" ] .

:b dcat:distribution [
    a dcat:Distribution ;
    downloadURL "http://example.com/b.txt" ] .
```

The below example shows how to save all datasets listed in the CSV file [semdata.csv] to a triplestore.

```python
>>> from tripper.dataset import TableDoc

>>> td = TableDoc.parse_csv(
...     "https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/tabledoc-csv/tests/input/semdata.csv",
...     delimiter=";",
...     prefixes={
...         "sem": "https://w3id.com/emmo/domain/sem/0.1#",
...         "semdata": "https://he-matchmaker.eu/data/sem/",
...         "sample": "https://he-matchmaker.eu/sample/",
...         "mat": "https://he-matchmaker.eu/material/",
...         "dm": "http://onto-ns.com/meta/characterisation/0.1/SEMImage#",
...         "parser": "http://sintef.no/dlite/parser#",
...         "gen": "http://sintef.no/dlite/generator#",
...     },
... )
>>> td.save(ts)

```


[tripper.dataset]: https://emmc-asbl.github.io/tripper/latest/api_reference/dataset/dataset
[DCAT vocabulary]: https://www.w3.org/TR/vocab-dcat-3/
[DLite]: https://github.com/SINTEF/dlite
[YAML]: https://yaml.org/
[JSON-LD documents]: https://json-ld.org/
[JSON-LD]: https://www.w3.org/TR/json-ld/
[default JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.2/context.json
[predefined prefixes]: datadoc-prefixes.md
[predefined keywords]: datadoc-keywords.md
[dcat:Dataset]: https://www.w3.org/TR/vocab-dcat-3/#Class:Dataset
[dcat:Distribution]: https://www.w3.org/TR/vocab-dcat-3/#Class:Distribution
[dcat:AccessService]: https://www.w3.org/TR/vocab-dcat-3/#Class:AccessService
[emmo:DataSet]: https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a
[oteio:Generator]: https://w3id.org/emmo/domain/oteio/Generator
[oteio:Parser]: https://w3id.org/emmo/domain/oteio/Parser
[save_dict()]: https://emmc-asbl.github.io/tripper/latest/api_reference/dataset/dataset/#tripper.dataset.dataset.save_dict
[save_datadoc()]: https://emmc-asbl.github.io/tripper/latest/api_reference/dataset/dataset/#tripper.dataset.dataset.save_datadoc
[semdata.yaml]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tests/input/semdata.yaml
[semdata.csv]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/tabledoc-csv/tests/input/semdata.csv
[TableDoc]: https://emmc-asbl.github.io/tripper/latest/api_reference/dataset/dataset/#tripper.dataset.tabledoc.TableDoc

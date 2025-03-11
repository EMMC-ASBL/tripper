Data documentation
==================
<!-- markdownlint-disable MD007 -->


Introduction
------------
The data documentation is based on small [JSON-LD documents], each documenting a single resource.
Examples of resources can be a dataset, an instrument, a sample, etc.
All resources are uniquely identified by their IRI.

The primary focus of the [tripper.datadoc] module is to document datasets such that they are consistent with the [DCAT vocabulary], but at the same time easily extended additional semantic meaning provided by other ontologies.
It is also easy to add and relate the datasets to other types of documents, like people, instruments and samples.

The [tripper.datadoc] module provides a Python API for documenting resources at all four levels of data documentation, including:

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
The [tripper.datadoc] module include the following set of predefined resource types:

- **dataset**: Individual of [dcat:Dataset] and [emmo:Dataset].
- **distribution**: Individual of [dcat:Distribution].
- **accessService**: Individual of [dcat:AccessService].
- **generator**: Individual of [oteio:Generator].
- **parser**: Individual of [oteio:Parser].
- **resource**: Any other documented resource, with no implicit type.

Future releases will support adding custom resource types.



[tripper.datadoc]: https://emmc-asbl.github.io/tripper/latest/datadoc/introduction
[DCAT vocabulary]: https://www.w3.org/TR/vocab-dcat-3/
[DLite]: https://github.com/SINTEF/dlite
[YAML]: https://yaml.org/
[JSON-LD documents]: https://json-ld.org/
[JSON-LD]: https://www.w3.org/TR/json-ld/
[default JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.2/context.json
[predefined prefixes]: prefixes.md
[predefined keywords]: keywords.md
[dcat:Dataset]: https://www.w3.org/TR/vocab-dcat-3/#Class:Dataset
[dcat:Distribution]: https://www.w3.org/TR/vocab-dcat-3/#Class:Distribution
[dcat:AccessService]: https://www.w3.org/TR/vocab-dcat-3/#Class:AccessService
[emmo:Dataset]: https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a
[oteio:Generator]: https://w3id.org/emmo/domain/oteio/Generator
[oteio:Parser]: https://w3id.org/emmo/domain/oteio/Parser
[save_dict()]: ../../api_reference/datadoc/dataset/#tripper.datadoc.dataset.save_dict
[as_jsonld()]: ../../api_reference/datadoc/dataset/#tripper.datadoc.dataset.as_jsonld
[save_datadoc()]:
../../api_reference/datadoc/dataset/#tripper.datadoc.dataset.save_datadoc
[semdata.yaml]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tests/input/semdata.yaml
[semdata.csv]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tests/input/semdata.csv
[TableDoc]: https://emmc-asbl.github.io/tripper/latest/api_reference/datadoc/tabledoc/#tripper.datadoc.tabledoc.TableDoc

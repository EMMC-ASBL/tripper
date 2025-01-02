Predefined keywords
===================
All keywords listed on this page (except for the special "@"-prefixed keywords) are defined in the [default JSON-LD context].


Special keywords for JSON-LD
----------------------------
See the [JSON-LD documentation] for a complete list of "@"-prefixed keywords.
Here we only list those that are commonly used for data documentation with Tripper.

- **@context** (*IRI*): URL to or dict with user-defined JSON-LD context.
      Used to extend the keywords listed on this page with domain- or application-specific keywords.
- **@id** (*IRI*): IRI of the documented resource.
- **@type** (*IRI*): IRI of ontological class that the resource is an individual of.


General properties on resources used by DCAT
--------------------------------------------
These can also be used on datasets and distributions.
See the DCAT documentation for [dcat:Dataset] and [dcat:Distribution] for recommendations.

- **[accessRights]** (*Literal*): Information about who can access the resource or an indication of its security status.
- **[conformsTo]** (*Literal*): An established standard to which the described resource conforms.
- **[contactPoint]** (*Literal*): Relevant contact information for the cataloged resource. Use of [vCard] is recommended.
- **[creator]** (*Literal*): The entity responsible for producing the resource.
- **[description]** (*Literal*): A free-text account of the resource.
- **[hasCurrentVersion]** (*Literal*): This resource has a more specific, versioned resource with equivalent content.
- **[hasPart]** (*IRI*): A related resource that is included either physically or logically in the described resource.
- **[hasPolicy]** (*Literal*): An ODRL conformant policy expressing the rights associated with the resource.
- **[hasVersion]** (*Literal*): This resource has a more specific, versioned resource.
- **[identifier]** (*Literal*): A unique identifier of the resource being described or cataloged.
- **[isReferencedBy]** (*Literal*): A related resource, such as a publication, that references, cites, or otherwise points to the cataloged resource.
- **[issued]** (*Literal*): Date of formal issuance (e.g., publication) of the resource.
- **[keyword]** (*Literal*): A keyword or tag describing the resource.
- **[landingPage]** (*Literal*): A Web page that can be navigated to in a Web browser to gain access to the catalog, a dataset, its distributions and/or additional information.
- **[language]** (*Literal*): A language of the resource. This refers to the natural language used for textual metadata (i.e., titles, descriptions, etc.) of a cataloged resource (i.e., dataset or service) or the textual values of a dataset distribution.
- **[license]** (*Literal*): A legal document under which the resource is made available.
- **[modified]** (*Literal*): Most recent date on which the resource was changed, updated or modified.
- **[publisher]** (*Literal*): The entity responsible for making the resource available.
- **[qualifiedAttribution]** (*IRI*): Link to an Agent having some form of responsibility for the resource.
- **[qualifiedRelation]** (*IRI*): Link to a description of a relationship with another resource.
- **[relation]** (*IRI*): A resource with an unspecified relationship to the cataloged resource.
- **[replaces]** (*IRI*): A related resource that is supplanted, displaced, or superseded by the described resource.
- **[rights]** (*Literal*): A statement that concerns all rights not addressed with `license` or `accessRights`, such as copyright statements.
- **[status]** (*Literal*): The status of the resource in the context of a particular workflow process.
- **[theme]** (*Literal*): A main category of the resource. A resource can have multiple themes.
- **[title]** (*Literal*): A name given to the resource.
- **[type]** (*Literal*): The nature or genre of the resource.
- **[version]** (*Literal*): The version indicator (name or identifier) of a resource.
- **[versionNotes]** (*Literal*): A description of changes between this version and the previous version of the resource.


Other general properties on resources
-------------------------------------

- **[abstract]** (*Literal*): A summary of the resource.
- **[bibliographicCitation]** (*Literal*): A bibliographic reference for the resource. Recommended practice is to include sufficient bibliographic detail to identify the resource as unambiguously as possible.
- **[comment]** (*Literal*): A description of the subject resource.
- **[deprecated]** (*Literal*): The annotation property that indicates that a given entity has been deprecated.  It should equal to `"true"^^xsd:boolean`.
- **[isDefinedBy]** (*Literal*): Indicate a resource defining the subject resource. This property may be used to indicate an RDF vocabulary in which a resource is described.
- **[label]** (*Literal*): Provides a human-readable version of a resource's name.
- **[seeAlso]** (*Literal*): Indicates a resource that might provide additional information about the subject resource.
- **[source]** (*Literal*): A related resource from which the described resource is derived.
- **[statements]** (*Literal*): A list of subject-predicate-object triples with additional RDF statements documenting the resource.


Properties specific for datasets
--------------------------------

- **[datamodel]** (*Literal*): URI of DLite datamodel for the dataset.
- **[datamodelStorage]** (*Literal*): URL to DLite storage plugin where the datamodel is stored.
- **[distribution]** (*IRI*): An available distribution of the dataset.
- **[hasDatum]** (*IRI*): Relates a dataset to its datum parts. `hasDatum` relations are normally specified manually, since they are generated from the DLite data model.
- **[inSeries]** (*IRI*): A dataset series of which the dataset is part.
- **[isInputOf]** (*IRI*): A process that this dataset is the input to.
- **[isOutputOf]** (*IRI*): A process that this dataset is the output of.
- **[mappings]** (*Literal*): A list of subject-predicate-object triples mapping the datamodel to ontological concepts.
- **[mappingURL]** (*Literal*): URL to a document defining the mappings of the datamodel.
      The file format is given by `mappingFormat`.
      Defaults to turtle.
- **[mappingFormat]** (*Literal*): File format for `mappingURL`. Defaults to turtle.
- **[spatial]** (*Literal*): The geographical area covered by the dataset.
- **[spatialResolutionMeters]** (*Literal*): Minimum spatial separation resolvable in a dataset, measured in meters.
- **[temporal]** (*Literal*): The temporal period that the dataset covers.
- **[temporalResolution]** (*Literal*): Minimum time period resolvable in the dataset.
- **[wasGeneratedBy]** (*Literal*): An activity that generated, or provides the business context for, the creation of the dataset.



Properties specific for distributions
-------------------------------------
- **[accessService]** (*IRI*): A data service that gives access to the distribution of the dataset.
- **[accessURL]** (*Literal*): A URL of the resource that gives access to a distribution of the dataset. E.g., landing page, feed, SPARQL endpoint.
- **[byteSize]** (*Literal*): The size of a distribution in bytes.
- **[checksum]** (*IRI*): The checksum property provides a mechanism that can be used to verify that the contents of a file or package have not changed.
- **[compressFormat]** (*Literal*): The compression format of the distribution in which the data is contained in a compressed form, e.g., to reduce the size of the downloadable file.
- **[downloadURL]** (*Literal*): The URL of the downloadable file in a given format. E.g., CSV file or RDF file. The format is indicated by the distribution's `format` and/or `mediaType`.
- **[format]** (*Literal*): The file format of the distribution.
      Use `mediaType` instead if the type of the distribution is defined by [IANA].
- **[generator]** (*IRI*): A generator that can create the distribution.
- **[mediaType]** (*Literal*): The media type of the distribution as defined by [IANA].
- **[packageFormat]** (*Literal*): The package format of the distribution in which one or more data files are grouped together, e.g., to enable a set of related files to be downloaded together.
- **[parser]** (*IRI*): A parser that can parse the distribution.


Properties for parsers and generators
-------------------------------------
- **[configuration]** (*Literal*): A JSON string with configurations specific to the parser or generator.
- **[generatorType]** (*Literal*): Generator type. Ex: `application/vnd.dlite-generate`.
- **[parserType]** (*Literal*): Parser type. Ex: `application/vnd.dlite-parse`.

<!--
- **[functionType]**:
- **[filterType]**:

- **[hasDataSink]**:
- **[storeURL]**:

- **[subject]**:
- **[predicate]**:
- **[object]**:

- **[prefixes]**:
-->

[default JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.2/context.json
[JSON-LD documentation]: https://www.w3.org/TR/json-ld/#syntax-tokens-and-keywords

[accessRights]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_access_rights
[conformsTo]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_conforms_to
[contactPoint]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_contact_point
[creator]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_creator
[description]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_description
[hasCurrentVersion]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_has_current_version
[hasPart]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_has_part
[hasPolicy]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_has_policy
[hasVersion]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_has_version
[identifier]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_identifier
[isReferencedBy]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_is_referenced_by
[issued]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_release_date
[keyword]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_keyword
[landingPage]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_landing_page
[language]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_language
[license]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_license
[modified]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_update_date
[publisher]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_publisher
[qualifiedAttribution]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_qualified_attribution
[qualifiedRelation]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_qualified_relation
[relation]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_relation
[replaces]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_replaces
[rights]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_rights
[status]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_status
[theme]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_theme
[title]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_title
[type]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_type
[version]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_version
[versionNotes]: https://www.w3.org/TR/vocab-dcat-3/#Property:resource_version_notes


[abstract]: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/abstract
[bibliographicCitation]: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/bibliographicCitation
[comment]: https://www.w3.org/TR/rdf12-schema/#ch_comment
[deprecated]: https://www.w3.org/TR/owl2-quick-reference/
[isDefinedBy]: https://www.w3.org/TR/rdf12-schema/#ch_isdefinedby
[label]: https://www.w3.org/TR/rdf12-schema/#ch_label
[seeAlso]: https://www.w3.org/TR/rdf12-schema/#ch_seealso
[source]: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/#http://purl.org/dc/terms/source


[datamodel]: https://w3id.org/emmo/domain/oteio#hasDatamodel
[datamodelStorage]: https://w3id.org/emmo/domain/oteio#hasDatamodelStorage
[distribution]: https://www.w3.org/TR/vocab-dcat-3/#Property:dataset_distribution
[hasDatum]: https://w3id.org/emmo#EMMO_b19aacfc_5f73_4c33_9456_469c1e89a53e
[inSeries]: https://www.w3.org/TR/vocab-dcat-3/#Property:dataset_in_series
[isInputOf]: https://w3id.org/emmo#EMMO_1494c1a9_00e1_40c2_a9cc_9bbf302a1cac
[isOutputOf]: https://w3id.org/emmo#EMMO_2bb50428_568d_46e8_b8bf_59a4c5656461
[mappings]: https://w3id.org/emmo/domain/oteio#mapping
[mappingFormat]: https://w3id.org/emmo/domain/oteio#mappingFormat
[mappingURL]: https://w3id.org/emmo/domain/oteio#mappingURL
[spatial]: https://www.w3.org/TR/vocab-dcat-3/#Property:dataset_spatial
[spatialResolutionMeters]: https://www.w3.org/TR/vocab-dcat-3/#Property:dataset_spatial_resolution
[temporal]: https://www.w3.org/TR/vocab-dcat-3/#Property:dataset_temporal
[temporalResolution]: https://www.w3.org/TR/vocab-dcat-3/#Property:dataset_temporal_resolution
[wasGeneratedBy]: https://www.w3.org/TR/vocab-dcat-3/#Property:dataset_was_generated_by
[statements]: https://w3id.org/emmo/domain/oteio#statement


[accessService]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_access_service
[accessURL]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_access_url
[byteSize]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_size
[checksum]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_checksum
[compressFormat]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_compression_format
[downloadURL]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_download_url
[format]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_format
[mediaType]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_media_type
[packageFormat]: https://www.w3.org/TR/vocab-dcat-3/#Property:distribution_packaging_format
[generator]: https://w3id.org/emmo/domain/oteio#generator
[parser]: https://w3id.org/emmo/domain/oteio#parser


[configuration]: https://w3id.org/emmo/domain/oteio#configuration
[generatorType]: https://w3id.org/emmo/domain/oteio#generatorType
[parserType]: https://w3id.org/emmo/domain/oteio#parserType

<!--
[functionType]:
[filterType]:

[hasDataSink]:
[storeURL]:

[subject]:
[predicate]:
[object]:

[prefixes]:
-->


[DCAT]: https://www.w3.org/TR/vocab-dcat-3/
[dcat:Dataset]: https://www.w3.org/TR/vocab-dcat-3/#Class:Dataset
[dcat:Distribution]: https://www.w3.org/TR/vocab-dcat-3/#Class:Distribution
[vCard]: https://www.w3.org/TR/vcard-rdf/
[IANA]: https://www.iana.org/assignments/media-types/media-types.xhtml

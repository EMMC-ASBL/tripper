<!-- Do not edit! This file is generated with Tripper. Edit the keywords.yaml file instead. -->

# Keywords for domain: default
The tables below lists the keywords the domain default.

The meaning of the columns are as follows:

- **Keyword**: The keyword referring to a property used for the data documentation.
- **Range**: Refer to the class for the values of the keyword.
- **Conformance**: Whether the keyword is mandatory, recommended or optional when documenting the given type of resources.
- **Definition**: The definition of the keyword.
- **Usage note**: Notes about how to use the keyword.


## Properties on [Resource]
Resource published or curated by an agent.

| Keyword                 | Range                                          | Conformance | Definition                                                                                                                                   | Usage note                                                                                                                                                                                            |
| ----------------------- | ---------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [description]           | [rdfs:Literal]<br>(rdf:langString)             | mandatory   | A free-text account of the resource.                                                                                                         | This property can be repeated for parallel language versions of the description.                                                                                                                      |
| [title]                 | [rdfs:Literal]<br>(rdf:langString)             | mandatory   | A name given to the resource.                                                                                                                | This property can be repeated for parallel language versions of the name.                                                                                                                             |
| [contactPoint]          | [vcard:Kind]                                   | recommended | Contact information that can be used for sending comments about the resource.                                                                |                                                                                                                                                                                                       |
| [keyword]               | [rdfs:Literal]<br>(rdf:langString)             | recommended | A keyword or tag describing the resource.                                                                                                    |                                                                                                                                                                                                       |
| [publisher]             | [foaf:Agent]                                   | recommended | Agent responsible for making the resource available.                                                                                         |                                                                                                                                                                                                       |
| [theme]                 | [skos:Concept]                                 | recommended | A category of the resource.  A resource may be associated with multiple themes.                                                              | The set of themes used to categorize the resources are organized in a skos:ConceptScheme, skos:Collection, owl:Ontology or similar, describing all the categories and their relations in the catalog. |
| [accessRights]          | [dcterms:RightsStatement]                      | optional    | Information about who can access the resource or an indication of its security status.                                                       |                                                                                                                                                                                                       |
| [applicableLegislation] | [eli:LegalResource]                            | optional    | The legislation that mandates the creation or management of the resource.                                                                    |                                                                                                                                                                                                       |
| [conformsTo]            | [dcterms:Standard]                             | optional    | An implementing rule or other specification.                                                                                                 |                                                                                                                                                                                                       |
| [creator]               | [foaf:Agent]                                   | optional    | An entity responsible for producing the resource.                                                                                            |                                                                                                                                                                                                       |
| [documentation]         | [foaf:Document]<br>(xsd:anyURI)                | optional    | A page or document about this resource.                                                                                                      |                                                                                                                                                                                                       |
| [hasVersion]            | [rdfs:Resource]                                | optional    | A related resource that is a version, edition, or adaptation of the described resource.                                                      | This property is intended for relating a non-versioned or abstract resource to several versioned resources, e.g., snapshots.                                                                          |
| [identifier]            | [rdfs:Literal]                                 | optional    | URI or other unique identifier of the resource being described or cataloged.                                                                 |                                                                                                                                                                                                       |
| [isReferencedBy]        | [rdfs:Resource]                                | optional    | A related resource, such as a publication, that references, cites, or otherwise points to the documented resource.                           |                                                                                                                                                                                                       |
| [landingPage]           | [foaf:Document]<br>(xsd:anyURI)                | optional    | A web page that provides access to the resource and/or additional information (e.g. the distribution for a dataset).                         | It is intended to point to a landing page at the original data provider, not to a page on a site of a third party, such as an aggregator.                                                             |
| [language]              | [dcterms:LinguisticSystem]<br>(rdf:langString) | optional    | A language of the resource.                                                                                                                  | This property can be repeated if the resource is expressed with multiple languages.                                                                                                                   |
| [license]               | [dcterms:LicenseDocument]                      | optional    | A licence under which the resource is made available.                                                                                        |                                                                                                                                                                                                       |
| [modificationDate]      | [rdfs:Literal]<br>(xsd:date)                   | optional    | The most recent date on which the resource was changed or modified.                                                                          |                                                                                                                                                                                                       |
| [qualifiedAttribution]  | [prov:Attribution]                             | optional    | An Agent having some form of responsibility for the resource.                                                                                |                                                                                                                                                                                                       |
| [qualifiedRelation]     | [dcat:Relationship]                            | optional    | A description of a relationship with another resource.                                                                                       |                                                                                                                                                                                                       |
| [relatedResource]       | [rdfs:Resource]                                | optional    | A resource with an unspecified relationship to the cataloged resource.                                                                       |                                                                                                                                                                                                       |
| [releaseDate]           | [rdfs:Literal]<br>(xsd:date)                   | optional    | The date of formal issuance (e.g., publication) of the resource.                                                                             |                                                                                                                                                                                                       |
| [type]                  | [skos:Concept]                                 | optional    | A type of the resource.                                                                                                                      | A recommended controlled vocabulary data-type is foreseen.                                                                                                                                            |
| [version]               | [rdfs:Literal]                                 | optional    | Version indicator (name or identifier) of a resource.                                                                                        |                                                                                                                                                                                                       |
| [versionNotes]          | [rdfs:Literal]                                 | optional    | A description of the differences between this version and a previous version of the resource.                                                | This property can be repeated for parallel language versions of the version notes.                                                                                                                    |
| [abstract]              | [rdfs:Literal]<br>(rdf:langString)             |             | A summary of the resource.                                                                                                                   |                                                                                                                                                                                                       |
| [bibliographicCitation] | [rdfs:Literal]                                 |             | A bibliographic reference for the resource.                                                                                                  | Recommended practice is to include sufficient bibliographic detail to identify the resource as unambiguously as possible.                                                                             |
| [comment]               | [rdfs:Literal]                                 |             | A description of the subject resource. Use `description` instead.                                                                            |                                                                                                                                                                                                       |
| [deprecated]            | [rdfs:Literal]<br>(xsd:boolean)                |             | The annotation property that indicates that a given entity has been deprecated. It should equal to `"true"^^xsd:boolean`.                    |                                                                                                                                                                                                       |
| [isDefinedBy]           | [skos:Concept]                                 |             | Indicate a resource defining the subject resource. This property may be used to indicate an RDF vocabulary in which a resource is described. |                                                                                                                                                                                                       |
| [label]                 | [rdfs:Literal]                                 |             | Provides a human-readable version of a resource's name.                                                                                      |                                                                                                                                                                                                       |
| [seeAlso]               | [skos:Concept]                                 |             | Indicates a resource that might provide additional information about the subject resource.                                                   |                                                                                                                                                                                                       |
| [statements]            | [rdfs:Literal]<br>(rdf:JSON)                   |             | A list of subject-predicate-object triples with additional RDF statements documenting the resource.                                          |                                                                                                                                                                                                       |


## Properties on [Dataset]
A collection of data, published or curated by an agent, and available for access or download in one or more representations.

- subClassOf: [dcat:Resource], [emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a]

| Keyword                | Range                                            | Conformance | Definition                                                                                                                 | Usage note                                                                                                    |
| ---------------------- | ------------------------------------------------ | ----------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| [distribution]         | [dcat:Distribution]                              | recommended | An available distribution for the dataset.                                                                                 |                                                                                                               |
| [geographicalCoverage] | [dcterms:Location]                               | recommended | A geographic region that is covered by the dataset.                                                                        |                                                                                                               |
| [temporalCoverage]     | [dcterms:PeriodOfTime]                           | recommended | A temporal period that the Dataset covers.                                                                                 |                                                                                                               |
| [frequency]            | [dcterms:Frequency]                              | optional    | The frequency at which the Dataset is updated.                                                                             |                                                                                                               |
| [inSeries]             | [dcat:DatasetSeries]                             | optional    | A dataset series of which the dataset is part.                                                                             |                                                                                                               |
| [otherIdentifier]      | [adms:Identifier]                                | optional    | A secondary identifier of the Dataset                                                                                      |                                                                                                               |
| [sample]               | [dcat:Distribution]                              | optional    | A sample distribution of the dataset.                                                                                      |                                                                                                               |
| [source]               | [dcat:Dataset]                                   | optional    | A related Dataset from which the described Dataset is derived.                                                             |                                                                                                               |
| [spatialResolution]    | [rdfs:Literal]<br>(xsd:decimal)                  | optional    | The minimum spatial separation resolvable in a dataset, measured in meters.                                                |                                                                                                               |
| [temporalResolution]   | [rdfs:Literal]<br>(xsd:duration)                 | optional    | The minimum time period resolvable in the dataset.                                                                         |                                                                                                               |
| [wasGeneratedBy]       | [prov:Activity]                                  | optional    | An activity that generated, or provides the business context for, the creation of the dataset.                             |                                                                                                               |
| [datamodel]            | [oteio:Datamodel]                                |             | URI of DLite datamodel for the dataset.                                                                                    |                                                                                                               |
| [datamodelStorage]     | [rdfs:Literal]<br>(xsd:anyURI)                   |             | URL to DLite storage plugin where the datamodel is stored.                                                                 |                                                                                                               |
| [hasDatum]             | [emmo:EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a] |             | Relates a dataset to its datum parts.                                                                                      | `hasDatum` relations are normally NOT specified manually, since they are generated from the DLite data model. |
| [isDescriptionFor]     | [dcat:Resource]                                  |             | An object (e.g. a material) that this dataset describes.                                                                   |                                                                                                               |
| [isInputOf]            | [emmo:EMMO_43e9a05d_98af_41b4_92f6_00f79a09bfce] |             | A process that this dataset is the input to.                                                                               |                                                                                                               |
| [isOutputOf]           | [emmo:EMMO_43e9a05d_98af_41b4_92f6_00f79a09bfce] |             | A process that this dataset is the output to.                                                                              |                                                                                                               |
| [mappings]             | [rdfs:Literal]<br>(rdf:JSON)                     |             | A list of subject-predicate-object triples mapping the datamodel to ontological concepts.                                  |                                                                                                               |
| [mappingURL]           | [rdfs:Literal]<br>(xsd:anyURI)                   |             | URL to a document defining the mappings of the datamodel. The file format is given by `mappingFormat`. Defaults to turtle. |                                                                                                               |
| [mappingFormat]        | [rdfs:Literal]                                   |             | File format for `mappingURL`. Defaults to "turtle".                                                                        |                                                                                                               |


## Properties on [Distribution]
A physical embodiment of the Dataset in a particular format.

- subClassOf: [dcat:Resource]

| Keyword          | Range                                      | Conformance | Definition                                                                                                                                                         | Usage note                                                                                                                                                                                                                                  |
| ---------------- | ------------------------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [accessURL]      | [rdfs:Resource]                            | mandatory   | A URL that gives access to a Distribution of the Dataset.                                                                                                          | The resource at the access URL may contain information about how to get the Dataset.                                                                                                                                                        |
| [availability]   | [rdfs:Literal]<br>(xsd:date)               | recommended | An indication how long it is planned to keep the Distribution of the Dataset available.                                                                            |                                                                                                                                                                                                                                             |
| [mediaType]      | [dcterms:MediaType]                        | recommended | The media type of the Distribution as defined in the official register of media types managed by [IANA](https://www.w3.org/TR/vocab-dcat-3/#bib-iana-media-types). |                                                                                                                                                                                                                                             |
| [accessService]  | [dcat:DataService]                         | optional    | A data service that gives access to the distribution of the dataset.                                                                                               |                                                                                                                                                                                                                                             |
| [byteSize]       | [rdfs:Literal]<br>(xsd:nonNegativeInteger) | optional    | The size of a Distribution in bytes.                                                                                                                               |                                                                                                                                                                                                                                             |
| [checksum]       | [spdx:Checksum]                            | optional    | A mechanism that can be used to verify that the contents of a distribution have not changed.                                                                       | The checksum is related to the downloadURL.                                                                                                                                                                                                 |
| [compressFormat] | [dcterms:MediaType]                        | optional    | The format of the file in which the data is contained in a compressed form, e.g. to reduce the size of the downloadable file.                                      | It SHOULD be expressed using a media type as defined in the official register of media types managed by [IANA](https://www.w3.org/TR/vocab-dcat-3/#bib-iana-media-types).                                                                   |
| [downloadURL]    | [rdfs:Literal]<br>(xsd:anyURI)             | optional    | A URL that is a direct link to a downloadable file in a given format.                                                                                              |                                                                                                                                                                                                                                             |
| [format]         | [dcterms:MediaTypeOrExtent]                | optional    | The file format of the Distribution.                                                                                                                               | dcat:mediaType SHOULD be used if the type of the distribution is defined by [IANA](https://www.w3.org/TR/vocab-dcat-3/#bib-iana-media-types).                                                                                               |
| [packageFormat]  | [dcterms:MediaType]                        | optional    | The format of the file in which one or more data files are grouped together, e.g. to enable a set of related files to be downloaded together.                      | It SHOULD be expressed using a media type as defined in the official register of media types managed by [IANA](https://www.w3.org/TR/vocab-dcat-3/#bib-iana-media-types) and prefixed with `https://www.iana.org/assignments/media-types/`. |
| [status]         | [rdfs:Literal]                             | optional    | The status of the distribution in the context of maturity lifecycle.                                                                                               | It MUST take one of the values: 'Completed', 'Deprecated', 'Under Development', 'Withdrawn'.                                                                                                                                                |
| [generator]      | [oteio:Generator]                          |             | A generator that can create the distribution.                                                                                                                      |                                                                                                                                                                                                                                             |
| [parser]         | [oteio:Parser]                             |             | A parser that can parse the distribution.                                                                                                                          |                                                                                                                                                                                                                                             |


## Properties on [Parser]
A parser that can parse a distribution into an instance of a datamodel.

| Keyword         | Range                        | Conformance | Definition                                                             | Usage note |
| --------------- | ---------------------------- | ----------- | ---------------------------------------------------------------------- | ---------- |
| [configuration] | [rdfs:Literal]<br>(rdf:JSON) |             | A JSON string with configurations specific to the parser or generator. |            |
| [parserType]    | [rdfs:Literal]               |             | Parser type. Ex: `application/vnd.dlite-parse`.                        |            |


## Properties on [Generator]
A generator that can serialise an instance of a datamodel into a distribution.

- subClassOf: [oteio:Parser]

| Keyword         | Range          | Conformance | Definition                                            | Usage note |
| --------------- | -------------- | ----------- | ----------------------------------------------------- | ---------- |
| [generatorType] | [rdfs:Literal] |             | Generator type. Ex: `application/vnd.dlite-generate`. |            |


## Properties on [Agent]
Any entity carrying out actions with respect to the entities Catalogue and the Catalogued Resources.

- subClassOf: [emmo:EMMO_2480b72b_db8d_460f_9a5f_c2912f979046]

| Keyword      | Range                          | Conformance | Definition                                          | Usage note                                                                                                                                    |
| ------------ | ------------------------------ | ----------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| [name]       | [rdfs:Literal]<br>(xsd:string) | mandatory   | A name of the agent.                                |                                                                                                                                               |
| [identifier] | [rdfs:Literal]                 | recommended | Identifier for the agent. E.g. organisation number. |                                                                                                                                               |
| [type]       | [skos:Concept]                 | optional    | The nature of the agent.                            | The value should be chosen from [ADMS publisher type](https://raw.githubusercontent.com/SEMICeu/ADMS-AP/master/purl.org/ADMS_SKOS_v1.00.rdf). |


## Properties on [Attribution]
An agent that has some form of responsibility for a resource, but which is not a publisher nor a creator of the resource.

- subClassOf: [foaf:Agent]


## Properties on [Checksum]
A preferred label of the concept.

| Keyword         | Range                             | Conformance | Definition                                                                         | Usage note |
| --------------- | --------------------------------- | ----------- | ---------------------------------------------------------------------------------- | ---------- |
| [algorithm]     | [spdx:ChecksumAlgorithm]          |             | The algorithm used to produce the subject Checksum.                                |            |
| [checksumValue] | [rdfs:Literal]<br>(xsd:hexBinary) |             | A lower case hexadecimal encoded digest value produced using a specific algorithm. |            |


## Properties on [ChecksumAlgorithm]
Algorithm for Checksums.


## Properties on [Concept]
An idea or notion; a unit of thought.

| Keyword     | Range          | Conformance | Definition                        | Usage note |
| ----------- | -------------- | ----------- | --------------------------------- | ---------- |
| [prefLabel] | [rdfs:Literal] |             | A preferred label of the concept. |            |


## Properties on [DataService]
A collection of operations that provides access to one or more datasets or data processing functions.

- subClassOf: [rdfs:Resource]

| Keyword               | Range                          | Conformance | Definition                                                                                              | Usage note |
| --------------------- | ------------------------------ | ----------- | ------------------------------------------------------------------------------------------------------- | ---------- |
| [endpointURL]         | [rdfs:Literal]<br>(xsd:anyURI) | mandatory   | The root location or primary endpoint of the service (an IRI).                                          |            |
| [endpointDescription] | [rdfs:Resource]                | recommended | A description of the services available via the end-points, including their operations, parameters etc. |            |
| [servesDataset]       | [dcat:Dataset]                 | recommended | This property refers to a collection of data that this data service can distribute.                     |            |
| [parser]              | [oteio:Parser]                 |             | A parser that can parse the distribution.                                                               |            |


## Properties on [DatasetSeries]
A collection of datasets that are published separately, but share some characteristics that group them.

- subClassOf: [dcat:Dataset]


## Properties on [Geometry]
The locn:Geometry class provides the means to identify a location as a point, line, polygon, etc. expressed using coordinates in some coordinate reference system.


## Properties on [Kind]
A description following the vCard specification, e.g. to provide telephone number and e-mail address for a contact point.

| Keyword               | Range          | Conformance | Definition | Usage note |
| --------------------- | -------------- | ----------- | ---------- | ---------- |
| [hasAddress]          | [rdfs:Literal] |             |            |            |
| [hasCountryName]      | [rdfs:Literal] |             |            |            |
| [hasEmail]            | [rdfs:Literal] |             |            |            |
| [hasFamilyName]       | [rdfs:Literal] |             |            |            |
| [hasGender]           | [rdfs:Literal] |             |            |            |
| [hasGeo]              | [rdfs:Literal] |             |            |            |
| [hasGivenName]        | [rdfs:Literal] |             |            |            |
| [hasHonorificPrefix]  | [rdfs:Literal] |             |            |            |
| [hasHonorificSuffix]  | [rdfs:Literal] |             |            |            |
| [hasKey]              | [rdfs:Literal] |             |            |            |
| [hasLanguage]         | [rdfs:Literal] |             |            |            |
| [hasLogo]             | [rdfs:Literal] |             |            |            |
| [hasMember]           | [rdfs:Literal] |             |            |            |
| [hasInstantMessage]   | [rdfs:Literal] |             |            |            |
| [hasName]             | [rdfs:Literal] |             |            |            |
| [hasNickname]         | [rdfs:Literal] |             |            |            |
| [hasNote]             | [rdfs:Literal] |             |            |            |
| [hasOrganizationName] | [rdfs:Literal] |             |            |            |
| [hasOrganizationUnit] | [rdfs:Literal] |             |            |            |
| [hasPhoto]            | [rdfs:Literal] |             |            |            |
| [hasPostalCode]       | [rdfs:Literal] |             |            |            |
| [hasRegion]           | [rdfs:Literal] |             |            |            |
| [hasStreetAddress]    | [rdfs:Literal] |             |            |            |
| [hasTelephone]        | [rdfs:Literal] |             |            |            |
| [hasUID]              | [rdfs:Literal] |             |            |            |
| [hasURL]              | [rdfs:Literal] |             |            |            |


## Properties on [LicenseDocument]
A legal document giving official permission to do something with a resource.

| Keyword | Range          | Conformance | Definition                                                                  | Usage note |
| ------- | -------------- | ----------- | --------------------------------------------------------------------------- | ---------- |
| [type]  | [skos:Concept] |             | A type of licence, e.g. indicating 'public domain' or 'royalties required'. |            |


## Properties on [Location]
A spatial region or named place.

| Keyword    | Range           | Conformance | Definition                                      | Usage note |
| ---------- | --------------- | ----------- | ----------------------------------------------- | ---------- |
| [bbox]     | [rdfs:Literal]  | recommended | The geographic bounding box of a resource.      |            |
| [centroid] | [rdfs:Literal]  | recommended | The geographic center (centroid) of a resource. |            |
| [geometry] | [locn:Geometry] | optional    | The geographic center (centroid) of a resource. |            |


## Properties on [Relationship]
An association class for attaching additional information to a relationship between DCAT Resources.

| Keyword    | Range           | Conformance | Definition                                                                   | Usage note |
| ---------- | --------------- | ----------- | ---------------------------------------------------------------------------- | ---------- |
| [hasRole]  | [dcat:Role]     |             | A function of an entity or agent with respect to another entity or resource. |            |
| [relation] | [rdfs:Resource] |             | A resource related to the source resource.                                   |            |


## Properties on [RightsStatement]
A statement about the intellectual property rights (IPR) held in or over a resource, a legal document giving official permission to do something with a resource, or a statement about access rights.


## Properties on [LegalResource]
This class represents the legislation, policy or policies that lie behind the Rules that govern the service.


## Properties on [Standard]
A standard or other specification to which a resource conforms.


## Properties on [MediaType]
A media type, e.g. the format of a computer file.


## Properties on [GenericResource]
A generic resource.




[Resource]: http://www.w3.org/ns/dcat#Resource
[accessRights]: http://purl.org/dc/terms/accessRights
[dcterms:RightsStatement]: http://purl.org/dc/terms/RightsStatement
[applicableLegislation]: http://data.europa.eu/r5r/applicableLegislation
[eli:LegalResource]: http://data.europa.eu/eli/ontology#LegalResource
[conformsTo]: http://purl.org/dc/terms/conformsTo
[dcterms:Standard]: http://purl.org/dc/terms/Standard
[contactPoint]: http://www.w3.org/ns/dcat#contactPoint
[vcard:Kind]: http://www.w3.org/2006/vcard/ns#Kind
[creator]: http://purl.org/dc/terms/creator
[foaf:Agent]: http://xmlns.com/foaf/0.1/Agent
[description]: http://purl.org/dc/terms/description
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[documentation]: http://xmlns.com/foaf/0.1/documentation
[foaf:Document]: http://xmlns.com/foaf/0.1/Document
[hasVersion]: http://www.w3.org/ns/dcat#hasVersion
[rdfs:Resource]: http://www.w3.org/2000/01/rdf-schema#Resource
[identifier]: http://purl.org/dc/terms/identifier
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[isReferencedBy]: http://purl.org/dc/terms/isReferencedBy
[rdfs:Resource]: http://www.w3.org/2000/01/rdf-schema#Resource
[keyword]: http://www.w3.org/ns/dcat#keyword
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[landingPage]: http://www.w3.org/ns/dcat#landingPage
[foaf:Document]: http://xmlns.com/foaf/0.1/Document
[language]: http://purl.org/dc/terms/language
[dcterms:LinguisticSystem]: http://purl.org/dc/terms/LinguisticSystem
[license]: http://purl.org/dc/terms/license
[dcterms:LicenseDocument]: http://purl.org/dc/terms/LicenseDocument
[modificationDate]: http://purl.org/dc/terms/modified
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[publisher]: http://purl.org/dc/terms/publisher
[foaf:Agent]: http://xmlns.com/foaf/0.1/Agent
[qualifiedAttribution]: http://www.w3.org/ns/prov#qualifiedAttribution
[prov:Attribution]: http://www.w3.org/ns/prov#Attribution
[qualifiedRelation]: http://www.w3.org/ns/dcat#qualifiedRelation
[dcat:Relationship]: http://www.w3.org/ns/dcat#Relationship
[relatedResource]: http://purl.org/dc/terms/relation
[rdfs:Resource]: http://www.w3.org/2000/01/rdf-schema#Resource
[releaseDate]: http://purl.org/dc/terms/issued
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[theme]: http://www.w3.org/ns/dcat#theme
[skos:Concept]: http://www.w3.org/2004/02/skos/core#Concept
[title]: http://purl.org/dc/terms/title
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[type]: http://purl.org/dc/terms/type
[skos:Concept]: http://www.w3.org/2004/02/skos/core#Concept
[version]: http://www.w3.org/ns/dcat#version
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[versionNotes]: http://www.w3.org/ns/adms#versionNotes
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[abstract]: http://purl.org/dc/terms/abstract
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[bibliographicCitation]: http://purl.org/dc/terms/bibliographicCitation
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[comment]: http://www.w3.org/2000/01/rdf-schema#comment
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[deprecated]: http://www.w3.org/2002/07/owl#deprecated
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[isDefinedBy]: http://www.w3.org/2000/01/rdf-schema#isDefinedBy
[skos:Concept]: http://www.w3.org/2004/02/skos/core#Concept
[label]: http://www.w3.org/2000/01/rdf-schema#label
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[seeAlso]: http://www.w3.org/2000/01/rdf-schema#seeAlso
[skos:Concept]: http://www.w3.org/2004/02/skos/core#Concept
[statements]: https://w3id.org/emmo/domain/oteio#statement
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[dcat:Resource]: http://www.w3.org/ns/dcat#Resource
[emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a]: https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a
[Dataset]: http://www.w3.org/ns/dcat#Dataset
[distribution]: http://www.w3.org/ns/dcat#distribution
[dcat:Distribution]: http://www.w3.org/ns/dcat#Distribution
[frequency]: http://purl.org/dc/terms/accrualPeriodicity
[dcterms:Frequency]: http://purl.org/dc/terms/Frequency
[geographicalCoverage]: http://purl.org/dc/terms/spatial
[dcterms:Location]: http://purl.org/dc/terms/Location
[inSeries]: http://www.w3.org/ns/dcat#inSeries
[dcat:DatasetSeries]: http://www.w3.org/ns/dcat#DatasetSeries
[otherIdentifier]: http://www.w3.org/ns/adms#identifier
[adms:Identifier]: http://www.w3.org/ns/adms#Identifier
[sample]: http://www.w3.org/ns/adms#sample
[dcat:Distribution]: http://www.w3.org/ns/dcat#Distribution
[source]: http://purl.org/dc/terms/source
[dcat:Dataset]: http://www.w3.org/ns/dcat#Dataset
[spatialResolution]: http://www.w3.org/ns/dcat#spatialResolutionInMeters
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[temporalCoverage]: http://purl.org/dc/terms/temporal
[dcterms:PeriodOfTime]: http://purl.org/dc/terms/PeriodOfTime
[temporalResolution]: http://www.w3.org/ns/dcat#temporalResolution
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[wasGeneratedBy]: http://www.w3.org/ns/prov#wasGeneratedBy
[prov:Activity]: http://www.w3.org/ns/prov#Activity
[datamodel]: https://w3id.org/emmo/domain/oteio#hasDatamodel
[oteio:Datamodel]: https://w3id.org/emmo/domain/oteio#Datamodel
[datamodelStorage]: https://w3id.org/emmo/domain/oteio#hasDatamodelStorage
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasDatum]: https://w3id.org/emmo#EMMO_b19aacfc_5f73_4c33_9456_469c1e89a53e
[emmo:EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a]: https://w3id.org/emmo#EMMO_50d6236a_7667_4883_8ae1_9bb5d190423a
[isDescriptionFor]: https://w3id.org/emmo#EMMO_f702bad4_fc77_41f0_a26d_79f6444fd4f3
[dcat:Resource]: http://www.w3.org/ns/dcat#Resource
[isInputOf]: https://w3id.org/emmo#EMMO_1494c1a9_00e1_40c2_a9cc_9bbf302a1cac
[emmo:EMMO_43e9a05d_98af_41b4_92f6_00f79a09bfce]: https://w3id.org/emmo#EMMO_43e9a05d_98af_41b4_92f6_00f79a09bfce
[isOutputOf]: https://w3id.org/emmo#EMMO_2bb50428_568d_46e8_b8bf_59a4c5656461
[emmo:EMMO_43e9a05d_98af_41b4_92f6_00f79a09bfce]: https://w3id.org/emmo#EMMO_43e9a05d_98af_41b4_92f6_00f79a09bfce
[mappings]: https://w3id.org/emmo/domain/oteio#mapping
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[mappingURL]: https://w3id.org/emmo/domain/oteio#mappingURL
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[mappingFormat]: https://w3id.org/emmo/domain/oteio#mappingFormat
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[dcat:Resource]: http://www.w3.org/ns/dcat#Resource
[Distribution]: http://www.w3.org/ns/dcat#Distribution
[accessService]: http://www.w3.org/ns/dcat#accessService
[dcat:DataService]: http://www.w3.org/ns/dcat#DataService
[accessURL]: http://www.w3.org/ns/dcat#accessURL
[rdfs:Resource]: http://www.w3.org/2000/01/rdf-schema#Resource
[availability]: http://data.europa.eu/r5r/availability
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[byteSize]: http://www.w3.org/ns/dcat#byteSize
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[checksum]: http://spdx.org/rdf/terms#checksum
[spdx:Checksum]: http://spdx.org/rdf/terms#Checksum
[compressFormat]: http://www.w3.org/ns/dcat#compressFormat
[dcterms:MediaType]: http://purl.org/dc/terms/MediaType
[downloadURL]: http://www.w3.org/ns/dcat#downloadURL
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[format]: http://purl.org/dc/terms/format
[dcterms:MediaTypeOrExtent]: http://purl.org/dc/terms/MediaTypeOrExtent
[generator]: https://w3id.org/emmo/domain/oteio#generator
[oteio:Generator]: https://w3id.org/emmo/domain/oteio#Generator
[mediaType]: http://www.w3.org/ns/dcat#mediaType
[dcterms:MediaType]: http://purl.org/dc/terms/MediaType
[packageFormat]: http://www.w3.org/ns/dcat#packageFormat
[dcterms:MediaType]: http://purl.org/dc/terms/MediaType
[parser]: https://w3id.org/emmo/domain/oteio#parser
[oteio:Parser]: https://w3id.org/emmo/domain/oteio#Parser
[status]: http://www.w3.org/ns/adms#status
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[Parser]: https://w3id.org/emmo/domain/oteio#Parser
[configuration]: https://w3id.org/emmo/domain/oteio#hasConfiguration
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[parserType]: https://w3id.org/emmo/domain/oteio#parserType
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[oteio:Parser]: https://w3id.org/emmo/domain/oteio#Parser
[Generator]: https://w3id.org/emmo/domain/oteio#Generator
[generatorType]: https://w3id.org/emmo/domain/oteio#generatorType
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[emmo:EMMO_2480b72b_db8d_460f_9a5f_c2912f979046]: https://w3id.org/emmo#EMMO_2480b72b_db8d_460f_9a5f_c2912f979046
[Agent]: http://xmlns.com/foaf/0.1/Agent
[name]: http://xmlns.com/foaf/0.1/name
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[identifier]: http://purl.org/dc/terms/identifier
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[type]: http://purl.org/dc/terms/type
[skos:Concept]: http://www.w3.org/2004/02/skos/core#Concept
[foaf:Agent]: http://xmlns.com/foaf/0.1/Agent
[Attribution]: http://www.w3.org/ns/prov#Attribution
[Checksum]: http://spdx.org/rdf/terms#Checksum
[algorithm]: http://spdx.org/rdf/terms#algorithm
[spdx:ChecksumAlgorithm]: http://spdx.org/rdf/terms#ChecksumAlgorithm
[checksumValue]: http://spdx.org/rdf/terms#checksumValue
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[ChecksumAlgorithm]: http://spdx.org/rdf/terms#ChecksumAlgorithm
[Concept]: http://www.w3.org/2004/02/skos/core#Concept
[prefLabel]: http://www.w3.org/2004/02/skos/core#prefLabel
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[rdfs:Resource]: http://www.w3.org/2000/01/rdf-schema#Resource
[DataService]: http://www.w3.org/ns/dcat#DataService
[endpointDescription]: http://www.w3.org/ns/dcat#endpointDescription
[rdfs:Resource]: http://www.w3.org/2000/01/rdf-schema#Resource
[endpointURL]: http://www.w3.org/ns/dcat#endpointURL
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[servesDataset]: http://www.w3.org/ns/dcat#servesDataset
[dcat:Dataset]: http://www.w3.org/ns/dcat#Dataset
[parser]: https://w3id.org/emmo/domain/oteio#parser
[oteio:Parser]: https://w3id.org/emmo/domain/oteio#Parser
[dcat:Dataset]: http://www.w3.org/ns/dcat#Dataset
[DatasetSeries]: http://www.w3.org/ns/dcat#DatasetSeries
[Geometry]: http://www.w3.org/ns/locn#Geometry
[Kind]: http://www.w3.org/2006/vcard/ns#Kind
[hasAddress]: http://www.w3.org/2006/vcard/ns#hasAddress
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasCountryName]: http://www.w3.org/2006/vcard/ns#hasCountryName
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasEmail]: http://www.w3.org/2006/vcard/ns#hasEmail
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasFamilyName]: http://www.w3.org/2006/vcard/ns#hasFamilyName
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasGender]: http://www.w3.org/2006/vcard/ns#hasGender
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasGeo]: http://www.w3.org/2006/vcard/ns#hasGeo
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasGivenName]: http://www.w3.org/2006/vcard/ns#hasGivenName
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasHonorificPrefix]: http://www.w3.org/2006/vcard/ns#hasHonorificPrefix
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasHonorificSuffix]: http://www.w3.org/2006/vcard/ns#hasHonorificSuffix
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasKey]: http://www.w3.org/2006/vcard/ns#hasKey
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasLanguage]: http://www.w3.org/2006/vcard/ns#hasLanguage
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasLogo]: http://www.w3.org/2006/vcard/ns#hasLogo
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasMember]: http://www.w3.org/2006/vcard/ns#hasMember
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasInstantMessage]: http://www.w3.org/2006/vcard/ns#hasInstantMessage
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasName]: http://www.w3.org/2006/vcard/ns#hasName
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasNickname]: http://www.w3.org/2006/vcard/ns#hasNickname
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasNote]: http://www.w3.org/2006/vcard/ns#hasNote
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasOrganizationName]: http://www.w3.org/2006/vcard/ns#hasOrganizationName
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasOrganizationUnit]: http://www.w3.org/2006/vcard/ns#hasOrganizationUnit
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasPhoto]: http://www.w3.org/2006/vcard/ns#hasPhoto
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasPostalCode]: http://www.w3.org/2006/vcard/ns#hasPostalCode
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasRegion]: http://www.w3.org/2006/vcard/ns#hasRegion
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasStreetAddress]: http://www.w3.org/2006/vcard/ns#hasStreetAddress
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasTelephone]: http://www.w3.org/2006/vcard/ns#hasTelephone
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasUID]: http://www.w3.org/2006/vcard/ns#hasUID
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[hasURL]: http://www.w3.org/2006/vcard/ns#hasURL
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[LicenseDocument]: http://purl.org/dc/terms/LicenseDocument
[type]: http://purl.org/dc/terms/type
[skos:Concept]: http://www.w3.org/2004/02/skos/core#Concept
[Location]: http://purl.org/dc/terms/Location
[bbox]: http://www.w3.org/ns/dcat#bbox
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[centroid]: http://www.w3.org/ns/dcat#centroid
[rdfs:Literal]: http://www.w3.org/2000/01/rdf-schema#Literal
[geometry]: http://www.w3.org/ns/locn#geometry
[locn:Geometry]: http://www.w3.org/ns/locn#Geometry
[Relationship]: http://www.w3.org/ns/dcat#Relationship
[hasRole]: http://www.w3.org/ns/dcat#hasRole
[dcat:Role]: http://www.w3.org/ns/dcat#Role
[relation]: http://purl.org/dc/terms/relation
[rdfs:Resource]: http://www.w3.org/2000/01/rdf-schema#Resource
[RightsStatement]: http://purl.org/dc/terms/RightsStatement
[LegalResource]: http://data.europa.eu/eli/ontology#LegalResource
[Standard]: http://purl.org/dc/terms/Standard
[MediaType]: http://purl.org/dc/terms/MediaType
[GenericResource]: http://www.w3.org/2000/01/rdf-schema#Resource

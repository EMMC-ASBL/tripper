# Changelog

## [v0.4.2](https://github.com/EMMC-ASBL/tripper/tree/v0.4.2) (2025-04-22)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.4.1...v0.4.2)

**Merged pull requests:**

- Development branch that merges loose ends together [\#380](https://github.com/EMMC-ASBL/tripper/pull/380) ([jesper-friis](https://github.com/jesper-friis))

## [v0.4.1](https://github.com/EMMC-ASBL/tripper/tree/v0.4.1) (2025-04-19)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.4.0...v0.4.1)

**Closed issues:**

- ts.remove does not work in sparqlwrapper. [\#350](https://github.com/EMMC-ASBL/tripper/issues/350)
- exapand\_iri, documentation formatted wrongly. [\#348](https://github.com/EMMC-ASBL/tripper/issues/348)
- Attrdict return non-expanded iris, is this correct? [\#341](https://github.com/EMMC-ASBL/tripper/issues/341)
- The CONSTRUCT sparql query in \_load\_sparql used in load\_dict returns all datasets [\#336](https://github.com/EMMC-ASBL/tripper/issues/336)
- Adding text in graphDB trough save\_datadoc is done incorrectly? [\#333](https://github.com/EMMC-ASBL/tripper/issues/333)
- datadoc.dataset.\_load\_sparql uses a CONSTRUCT query, which is not implemented in the SPARQLWrapper [\#330](https://github.com/EMMC-ASBL/tripper/issues/330)
- Include the JSON-LD context in the installed package [\#326](https://github.com/EMMC-ASBL/tripper/issues/326)
- It is not possible to search for Literals in the graphdb backend [\#320](https://github.com/EMMC-ASBL/tripper/issues/320)
- Validator for schema [\#294](https://github.com/EMMC-ASBL/tripper/issues/294)

**Merged pull requests:**

- Corrected DataSetvice to DataService [\#374](https://github.com/EMMC-ASBL/tripper/pull/374) ([francescalb](https://github.com/francescalb))
- Fix typo in keywords documentation [\#373](https://github.com/EMMC-ASBL/tripper/pull/373) ([jesper-friis](https://github.com/jesper-friis))
- Updated keywords documentation [\#371](https://github.com/EMMC-ASBL/tripper/pull/371) ([jesper-friis](https://github.com/jesper-friis))
- Adding logos [\#368](https://github.com/EMMC-ASBL/tripper/pull/368) ([jesper-friis](https://github.com/jesper-friis))
- Add resources \(classes\) to the JSON-LD context. [\#366](https://github.com/EMMC-ASBL/tripper/pull/366) ([jesper-friis](https://github.com/jesper-friis))
- Added support for ASK and DESCRIBE queries in the sparqlwrapper backend [\#364](https://github.com/EMMC-ASBL/tripper/pull/364) ([jesper-friis](https://github.com/jesper-friis))
- Improved formatting of keyword documentation table. [\#362](https://github.com/EMMC-ASBL/tripper/pull/362) ([jesper-friis](https://github.com/jesper-friis))
- Test for the datadoc command-line tool [\#361](https://github.com/EMMC-ASBL/tripper/pull/361) ([jesper-friis](https://github.com/jesper-friis))
- Fixed CONTEXT\_URL after branch 294-validator-for-schema was merged to master [\#359](https://github.com/EMMC-ASBL/tripper/pull/359) ([jesper-friis](https://github.com/jesper-friis))
- Fix formatting [\#358](https://github.com/EMMC-ASBL/tripper/pull/358) ([jesper-friis](https://github.com/jesper-friis))
- Added session [\#357](https://github.com/EMMC-ASBL/tripper/pull/357) ([jesper-friis](https://github.com/jesper-friis))
- Added update\(\) method to sparqlwrapper backend [\#356](https://github.com/EMMC-ASBL/tripper/pull/356) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#355](https://github.com/EMMC-ASBL/tripper/pull/355) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#353](https://github.com/EMMC-ASBL/tripper/pull/353) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Corrected sparqlquery for removing triples [\#351](https://github.com/EMMC-ASBL/tripper/pull/351) ([francescalb](https://github.com/francescalb))
- Corrected formatting of example [\#349](https://github.com/EMMC-ASBL/tripper/pull/349) ([francescalb](https://github.com/francescalb))
- Added test for Fuseki and fixed query to return TURTLE which works for both fuseki and graphdb [\#347](https://github.com/EMMC-ASBL/tripper/pull/347) ([francescalb](https://github.com/francescalb))
- \[pre-commit.ci\] pre-commit autoupdate [\#346](https://github.com/EMMC-ASBL/tripper/pull/346) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Correct syntax [\#344](https://github.com/EMMC-ASBL/tripper/pull/344) ([jesper-friis](https://github.com/jesper-friis))
- Correct syntax [\#343](https://github.com/EMMC-ASBL/tripper/pull/343) ([jesper-friis](https://github.com/jesper-friis))
- Flb/expand iri in sparql query [\#340](https://github.com/EMMC-ASBL/tripper/pull/340) ([francescalb](https://github.com/francescalb))
- disable pylint errors on too-many-positional-arguments [\#339](https://github.com/EMMC-ASBL/tripper/pull/339) ([francescalb](https://github.com/francescalb))
- Fixed CONSTRUCT to return s and not o [\#338](https://github.com/EMMC-ASBL/tripper/pull/338) ([francescalb](https://github.com/francescalb))
- Corrected literals in SELECT and CONSTRUCT queries in the sparqlwrapper backend [\#335](https://github.com/EMMC-ASBL/tripper/pull/335) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#332](https://github.com/EMMC-ASBL/tripper/pull/332) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Added CONSTRUCT query to sparqlwrapper,  [\#331](https://github.com/EMMC-ASBL/tripper/pull/331) ([francescalb](https://github.com/francescalb))
- Include context files in installation [\#328](https://github.com/EMMC-ASBL/tripper/pull/328) ([jesper-friis](https://github.com/jesper-friis))
- Added PINK to contributing projects [\#327](https://github.com/EMMC-ASBL/tripper/pull/327) ([jesper-friis](https://github.com/jesper-friis))
- Update dataset.py [\#325](https://github.com/EMMC-ASBL/tripper/pull/325) ([jesper-friis](https://github.com/jesper-friis))
- Added units submodule for working with units and quantities defined in ontologies [\#324](https://github.com/EMMC-ASBL/tripper/pull/324) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#321](https://github.com/EMMC-ASBL/tripper/pull/321) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Schema validator [\#296](https://github.com/EMMC-ASBL/tripper/pull/296) ([jesper-friis](https://github.com/jesper-friis))

## [v0.4.0](https://github.com/EMMC-ASBL/tripper/tree/v0.4.0) (2025-02-10)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.3.4...v0.4.0)

**Closed issues:**

- Clean up documentation [\#302](https://github.com/EMMC-ASBL/tripper/issues/302)
- Make datadoc windows compatible [\#301](https://github.com/EMMC-ASBL/tripper/issues/301)

**Merged pull requests:**

- \[pre-commit.ci\] pre-commit autoupdate [\#317](https://github.com/EMMC-ASBL/tripper/pull/317) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Add updateEndpoint to SPARQLwrapper [\#313](https://github.com/EMMC-ASBL/tripper/pull/313) ([torhaugl](https://github.com/torhaugl))
- Updated the readme file [\#311](https://github.com/EMMC-ASBL/tripper/pull/311) ([jesper-friis](https://github.com/jesper-friis))
- Drop support for Python 3.7 [\#310](https://github.com/EMMC-ASBL/tripper/pull/310) ([jesper-friis](https://github.com/jesper-friis))
- Include prefixes from context when populating a triplestore from a csv file [\#309](https://github.com/EMMC-ASBL/tripper/pull/309) ([jesper-friis](https://github.com/jesper-friis))
- Added support for username/password for sparqlwrapper [\#308](https://github.com/EMMC-ASBL/tripper/pull/308) ([jesper-friis](https://github.com/jesper-friis))
- Implementing regex search [\#307](https://github.com/EMMC-ASBL/tripper/pull/307) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#306](https://github.com/EMMC-ASBL/tripper/pull/306) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Rename dataset [\#304](https://github.com/EMMC-ASBL/tripper/pull/304) ([jesper-friis](https://github.com/jesper-friis))
- Change pathlib to be pathlib and not as uri. This fixes opening in wi… [\#303](https://github.com/EMMC-ASBL/tripper/pull/303) ([francescalb](https://github.com/francescalb))
- Added fixes for the demonstration at the PINK demo [\#299](https://github.com/EMMC-ASBL/tripper/pull/299) ([jesper-friis](https://github.com/jesper-friis))
- Renamed the dataset subpackage to datadoc [\#298](https://github.com/EMMC-ASBL/tripper/pull/298) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#287](https://github.com/EMMC-ASBL/tripper/pull/287) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Make datasets with a datamodel an individual of the datamodel [\#286](https://github.com/EMMC-ASBL/tripper/pull/286) ([jesper-friis](https://github.com/jesper-friis))
- Re-applied fixes from testing datadoc on a use case for PINK. [\#285](https://github.com/EMMC-ASBL/tripper/pull/285) ([jesper-friis](https://github.com/jesper-friis))
- Command-line datadoc script [\#281](https://github.com/EMMC-ASBL/tripper/pull/281) ([jesper-friis](https://github.com/jesper-friis))
- Added documentation for datasets [\#280](https://github.com/EMMC-ASBL/tripper/pull/280) ([jesper-friis](https://github.com/jesper-friis))
- Dataset TODOs [\#279](https://github.com/EMMC-ASBL/tripper/pull/279) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#277](https://github.com/EMMC-ASBL/tripper/pull/277) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Added csv parser to Tabledoc  [\#275](https://github.com/EMMC-ASBL/tripper/pull/275) ([jesper-friis](https://github.com/jesper-friis))
- Updated dataset figures [\#274](https://github.com/EMMC-ASBL/tripper/pull/274) ([jesper-friis](https://github.com/jesper-friis))
- New TableDoc class providing a table interface for data documentation [\#273](https://github.com/EMMC-ASBL/tripper/pull/273) ([jesper-friis](https://github.com/jesper-friis))
- Updated dataset module [\#272](https://github.com/EMMC-ASBL/tripper/pull/272) ([jesper-friis](https://github.com/jesper-friis))
- Corrected dataset module [\#271](https://github.com/EMMC-ASBL/tripper/pull/271) ([jesper-friis](https://github.com/jesper-friis))
- Add query to SPARQLwrapper strategy [\#269](https://github.com/EMMC-ASBL/tripper/pull/269) ([torhaugl](https://github.com/torhaugl))
- \[pre-commit.ci\] pre-commit autoupdate [\#268](https://github.com/EMMC-ASBL/tripper/pull/268) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Add support for Python 3.13 [\#266](https://github.com/EMMC-ASBL/tripper/pull/266) ([jesper-friis](https://github.com/jesper-friis))
- Updated requirements to allow Pint 0.24, which in turn opens for NumPy 2 [\#265](https://github.com/EMMC-ASBL/tripper/pull/265) ([jesper-friis](https://github.com/jesper-friis))
- Updated documentation format for better rendering [\#262](https://github.com/EMMC-ASBL/tripper/pull/262) ([jesper-friis](https://github.com/jesper-friis))
- Predefined EMMO namespace with checking and label lookup [\#261](https://github.com/EMMC-ASBL/tripper/pull/261) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#259](https://github.com/EMMC-ASBL/tripper/pull/259) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#258](https://github.com/EMMC-ASBL/tripper/pull/258) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
-  Dataset [\#256](https://github.com/EMMC-ASBL/tripper/pull/256) ([jesper-friis](https://github.com/jesper-friis))

## [v0.3.4](https://github.com/EMMC-ASBL/tripper/tree/v0.3.4) (2024-10-17)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.3.3...v0.3.4)

**Merged pull requests:**

- Allowing backends to indicate whether they prefer the sparql interface [\#255](https://github.com/EMMC-ASBL/tripper/pull/255) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#254](https://github.com/EMMC-ASBL/tripper/pull/254) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Update n3 format for string with quotes. [\#253](https://github.com/EMMC-ASBL/tripper/pull/253) ([pintr](https://github.com/pintr))
- Added option to Triplestore.value\(\) to return a generator over all matching values [\#252](https://github.com/EMMC-ASBL/tripper/pull/252) ([jesper-friis](https://github.com/jesper-friis))
- Ignore safety vulnerabeility 72715 [\#251](https://github.com/EMMC-ASBL/tripper/pull/251) ([jesper-friis](https://github.com/jesper-friis))
- Fix empty prefix [\#250](https://github.com/EMMC-ASBL/tripper/pull/250) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#249](https://github.com/EMMC-ASBL/tripper/pull/249) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Backend info to triplestore instance [\#248](https://github.com/EMMC-ASBL/tripper/pull/248) ([jesper-friis](https://github.com/jesper-friis))
- Added argument `ignore_unrecognised` to tripper.convert\(\) [\#247](https://github.com/EMMC-ASBL/tripper/pull/247) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#244](https://github.com/EMMC-ASBL/tripper/pull/244) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))

## [v0.3.3](https://github.com/EMMC-ASBL/tripper/tree/v0.3.3) (2024-08-26)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.3.2...v0.3.3)

**Implemented enhancements:**

- Use Trusted Publishers for PyPI [\#242](https://github.com/EMMC-ASBL/tripper/issues/242)

**Closed issues:**

- Add instructions of how to release a new version [\#47](https://github.com/EMMC-ASBL/tripper/issues/47)
- Update Python API references in README [\#22](https://github.com/EMMC-ASBL/tripper/issues/22)

**Merged pull requests:**

- Use Trusted Publishers on PyPI [\#243](https://github.com/EMMC-ASBL/tripper/pull/243) ([CasperWA](https://github.com/CasperWA))

## [v0.3.2](https://github.com/EMMC-ASBL/tripper/tree/v0.3.2) (2024-08-19)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.3.1...v0.3.2)

**Merged pull requests:**

- Minor fix for documentation layout  [\#238](https://github.com/EMMC-ASBL/tripper/pull/238) ([jesper-friis](https://github.com/jesper-friis))
- Updated documentation navigation [\#237](https://github.com/EMMC-ASBL/tripper/pull/237) ([jesper-friis](https://github.com/jesper-friis))
- Updated cd\_release workflow [\#236](https://github.com/EMMC-ASBL/tripper/pull/236) ([jesper-friis](https://github.com/jesper-friis))

## [v0.3.1](https://github.com/EMMC-ASBL/tripper/tree/v0.3.1) (2024-08-16)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.3.0...v0.3.1)

**Merged pull requests:**

- Avoid that tripper.Namespace crashes if the cache directory cannot be accessed [\#235](https://github.com/EMMC-ASBL/tripper/pull/235) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#232](https://github.com/EMMC-ASBL/tripper/pull/232) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- \[pre-commit.ci\] pre-commit autoupdate [\#231](https://github.com/EMMC-ASBL/tripper/pull/231) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Cleaned up backend tests [\#230](https://github.com/EMMC-ASBL/tripper/pull/230) ([jesper-friis](https://github.com/jesper-friis))
- Added a fix for parsing rdflib literals. [\#229](https://github.com/EMMC-ASBL/tripper/pull/229) ([jesper-friis](https://github.com/jesper-friis))
- Add better and more convenient support for rdf:JSON datatype [\#228](https://github.com/EMMC-ASBL/tripper/pull/228) ([jesper-friis](https://github.com/jesper-friis))

## [v0.3.0](https://github.com/EMMC-ASBL/tripper/tree/v0.3.0) (2024-06-24)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.16...v0.3.0)

**Merged pull requests:**

- Tutorial update [\#227](https://github.com/EMMC-ASBL/tripper/pull/227) ([jesper-friis](https://github.com/jesper-friis))
- Get rid of the last warning in the tests [\#226](https://github.com/EMMC-ASBL/tripper/pull/226) ([jesper-friis](https://github.com/jesper-friis))
- Get restrictions as dicts [\#225](https://github.com/EMMC-ASBL/tripper/pull/225) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#224](https://github.com/EMMC-ASBL/tripper/pull/224) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Added an additional test for convert [\#223](https://github.com/EMMC-ASBL/tripper/pull/223) ([jesper-friis](https://github.com/jesper-friis))
- Minor fix in tutorial [\#221](https://github.com/EMMC-ASBL/tripper/pull/221) ([jesper-friis](https://github.com/jesper-friis))
- Updated the tutorial [\#220](https://github.com/EMMC-ASBL/tripper/pull/220) ([jesper-friis](https://github.com/jesper-friis))
- Improved the handling of different return types from the query\(\) method [\#219](https://github.com/EMMC-ASBL/tripper/pull/219) ([jesper-friis](https://github.com/jesper-friis))
- Correct parsing literals from the rdflib backend. [\#217](https://github.com/EMMC-ASBL/tripper/pull/217) ([jesper-friis](https://github.com/jesper-friis))
- Do not save cache while interpreter shotdown. [\#216](https://github.com/EMMC-ASBL/tripper/pull/216) ([jesper-friis](https://github.com/jesper-friis))
- Allow string literal to compare equal to strings. [\#215](https://github.com/EMMC-ASBL/tripper/pull/215) ([jesper-friis](https://github.com/jesper-friis))
- Also test for Python 3.12 [\#213](https://github.com/EMMC-ASBL/tripper/pull/213) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.16](https://github.com/EMMC-ASBL/tripper/tree/v0.2.16) (2024-05-16)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.15...v0.2.16)

**Fixed bugs:**

- cannot release [\#211](https://github.com/EMMC-ASBL/tripper/issues/211)

**Closed issues:**

- Add caching and extension to tripper.Namespace [\#194](https://github.com/EMMC-ASBL/tripper/issues/194)
- Add support for adding and searching for restrictions [\#189](https://github.com/EMMC-ASBL/tripper/issues/189)

**Merged pull requests:**

- In tripper.convert, commented out recognised keys for oteapi strategies [\#212](https://github.com/EMMC-ASBL/tripper/pull/212) ([jesper-friis](https://github.com/jesper-friis))
- Use latest SINTEF/ci-cd version [\#210](https://github.com/EMMC-ASBL/tripper/pull/210) ([CasperWA](https://github.com/CasperWA))
- Allow prefix with digits [\#209](https://github.com/EMMC-ASBL/tripper/pull/209) ([jesper-friis](https://github.com/jesper-friis))
- Added test for SPARQL CONSTRUCT query via tripper [\#207](https://github.com/EMMC-ASBL/tripper/pull/207) ([jesper-friis](https://github.com/jesper-friis))
- Added more recognised keys to tripper.convert [\#206](https://github.com/EMMC-ASBL/tripper/pull/206) ([jesper-friis](https://github.com/jesper-friis))
- \[pre-commit.ci\] pre-commit autoupdate [\#204](https://github.com/EMMC-ASBL/tripper/pull/204) ([pre-commit-ci[bot]](https://github.com/apps/pre-commit-ci))
- Changed EMMO representation of function arguments from datasets to datum [\#203](https://github.com/EMMC-ASBL/tripper/pull/203) ([jesper-friis](https://github.com/jesper-friis))
- Added comment suggested by Francesca [\#201](https://github.com/EMMC-ASBL/tripper/pull/201) ([jesper-friis](https://github.com/jesper-friis))
- Enhanced the use of namespaces [\#195](https://github.com/EMMC-ASBL/tripper/pull/195) ([jesper-friis](https://github.com/jesper-friis))
- Support for restrictions [\#190](https://github.com/EMMC-ASBL/tripper/pull/190) ([jesper-friis](https://github.com/jesper-friis))
- Correctly convert rdflib bnodes back to tripper [\#187](https://github.com/EMMC-ASBL/tripper/pull/187) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.15](https://github.com/EMMC-ASBL/tripper/tree/v0.2.15) (2024-03-12)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.14...v0.2.15)

**Closed issues:**

- Documentation CD \(still\) fails due to old python version [\#193](https://github.com/EMMC-ASBL/tripper/issues/193)
- Publish workflow fails because it uses python 3.7 [\#191](https://github.com/EMMC-ASBL/tripper/issues/191)
- Allow untyped literals [\#182](https://github.com/EMMC-ASBL/tripper/issues/182)
- Search with ts.triples\(\) doesn't recognise literals [\#179](https://github.com/EMMC-ASBL/tripper/issues/179)
- PyBackTrip - external tripper backends available [\#177](https://github.com/EMMC-ASBL/tripper/issues/177)
- Surprising literal comparisons [\#161](https://github.com/EMMC-ASBL/tripper/issues/161)
- Retain literal types in collection backend [\#160](https://github.com/EMMC-ASBL/tripper/issues/160)
- Document implemented backends  [\#157](https://github.com/EMMC-ASBL/tripper/issues/157)

**Merged pull requests:**

- Loosen req on pint to include 0.23 \(newest\) [\#198](https://github.com/EMMC-ASBL/tripper/pull/198) ([francescalb](https://github.com/francescalb))
- Use Python 3.9 in all CI/CD workflows [\#196](https://github.com/EMMC-ASBL/tripper/pull/196) ([CasperWA](https://github.com/CasperWA))
- Bump basic CI tests and CD to python 3.9 [\#192](https://github.com/EMMC-ASBL/tripper/pull/192) ([ajeklund](https://github.com/ajeklund))
- Cleaned up PR template [\#188](https://github.com/EMMC-ASBL/tripper/pull/188) ([jesper-friis](https://github.com/jesper-friis))
- Bump mkdocs-material version for security [\#186](https://github.com/EMMC-ASBL/tripper/pull/186) ([ajeklund](https://github.com/ajeklund))
- Allow untyped literals [\#184](https://github.com/EMMC-ASBL/tripper/pull/184) ([jesper-friis](https://github.com/jesper-friis))
- Added test for finding literal triples [\#183](https://github.com/EMMC-ASBL/tripper/pull/183) ([jesper-friis](https://github.com/jesper-friis))
- Added reference to PyBackTrip [\#180](https://github.com/EMMC-ASBL/tripper/pull/180) ([jesper-friis](https://github.com/jesper-friis))
- Added support for xsd:nonNegativeInteger literals [\#178](https://github.com/EMMC-ASBL/tripper/pull/178) ([jesper-friis](https://github.com/jesper-friis))
- Added acknowledgements to readme file. [\#173](https://github.com/EMMC-ASBL/tripper/pull/173) ([jesper-friis](https://github.com/jesper-friis))
- Retain literal types in collection backend [\#165](https://github.com/EMMC-ASBL/tripper/pull/165) ([jesper-friis](https://github.com/jesper-friis))
- Improved comparing literals [\#164](https://github.com/EMMC-ASBL/tripper/pull/164) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.14](https://github.com/EMMC-ASBL/tripper/tree/v0.2.14) (2024-01-25)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.13...v0.2.14)

**Closed issues:**

- Literals are lost when listing triples with rdflib [\#162](https://github.com/EMMC-ASBL/tripper/issues/162)
- dependencies are too strict, at least for pint [\#149](https://github.com/EMMC-ASBL/tripper/issues/149)
- Function repo plugin system [\#128](https://github.com/EMMC-ASBL/tripper/issues/128)

**Merged pull requests:**

- Retain datatype when listing literals from rdflib [\#163](https://github.com/EMMC-ASBL/tripper/pull/163) ([jesper-friis](https://github.com/jesper-friis))
- Make it possible to expose an existing rdflib graph via tripper [\#156](https://github.com/EMMC-ASBL/tripper/pull/156) ([jesper-friis](https://github.com/jesper-friis))
- Mapping function plugin system [\#152](https://github.com/EMMC-ASBL/tripper/pull/152) ([jesper-friis](https://github.com/jesper-friis))
- Get rid of confusing UnusedArgumentWarning from working code [\#151](https://github.com/EMMC-ASBL/tripper/pull/151) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.13](https://github.com/EMMC-ASBL/tripper/tree/v0.2.13) (2023-11-14)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.12...v0.2.13)

**Merged pull requests:**

- Added UnknownUnitError [\#153](https://github.com/EMMC-ASBL/tripper/pull/153) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.12](https://github.com/EMMC-ASBL/tripper/tree/v0.2.12) (2023-11-07)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.11...v0.2.12)

**Merged pull requests:**

- Expand pint requirements to include more versions [\#150](https://github.com/EMMC-ASBL/tripper/pull/150) ([francescalb](https://github.com/francescalb))

## [v0.2.11](https://github.com/EMMC-ASBL/tripper/tree/v0.2.11) (2023-10-30)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.10...v0.2.11)

**Merged pull requests:**

- Added new section to README file [\#148](https://github.com/EMMC-ASBL/tripper/pull/148) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.10](https://github.com/EMMC-ASBL/tripper/tree/v0.2.10) (2023-10-19)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.9...v0.2.10)

**Merged pull requests:**

- Francescalb/testing dependencies [\#142](https://github.com/EMMC-ASBL/tripper/pull/142) ([francescalb](https://github.com/francescalb))
- Clearified that tripper does not depend on DLite and Pydantic [\#136](https://github.com/EMMC-ASBL/tripper/pull/136) ([jesper-friis](https://github.com/jesper-friis))
- Cleaned up mappings module [\#132](https://github.com/EMMC-ASBL/tripper/pull/132) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.9](https://github.com/EMMC-ASBL/tripper/tree/v0.2.9) (2023-09-29)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.8...v0.2.9)

## [v0.2.8](https://github.com/EMMC-ASBL/tripper/tree/v0.2.8) (2023-09-12)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.7...v0.2.8)

**Merged pull requests:**

- Added support for lists in tripper.convert [\#129](https://github.com/EMMC-ASBL/tripper/pull/129) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.7](https://github.com/EMMC-ASBL/tripper/tree/v0.2.7) (2023-08-29)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.6...v0.2.7)

**Fixed bugs:**

- Fix issues related to renaming of the default branch [\#116](https://github.com/EMMC-ASBL/tripper/issues/116)

**Merged pull requests:**

- Added a module for converting to/from dicts [\#126](https://github.com/EMMC-ASBL/tripper/pull/126) ([jesper-friis](https://github.com/jesper-friis))
- Update dependabot after changing master branch to 'master' [\#121](https://github.com/EMMC-ASBL/tripper/pull/121) ([jesper-friis](https://github.com/jesper-friis))
- Also run CI tests on examples in documentation [\#118](https://github.com/EMMC-ASBL/tripper/pull/118) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.6](https://github.com/EMMC-ASBL/tripper/tree/v0.2.6) (2023-06-23)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.5...v0.2.6)

**Closed issues:**

- Add CI/CD tests for Python 3.11 [\#102](https://github.com/EMMC-ASBL/tripper/issues/102)

**Merged pull requests:**

- One letter words where not allowed in mappings, now they are [\#117](https://github.com/EMMC-ASBL/tripper/pull/117) ([francescalb](https://github.com/francescalb))
- pylint settings [\#115](https://github.com/EMMC-ASBL/tripper/pull/115) ([jesper-friis](https://github.com/jesper-friis))
- Fix issue with entry points for Python 3.6 and 3.7 [\#113](https://github.com/EMMC-ASBL/tripper/pull/113) ([jesper-friis](https://github.com/jesper-friis))
- Added DOI badge [\#109](https://github.com/EMMC-ASBL/tripper/pull/109) ([jesper-friis](https://github.com/jesper-friis))
- Fixed parsing rdf:HTML literals with the rdflib backend [\#106](https://github.com/EMMC-ASBL/tripper/pull/106) ([jesper-friis](https://github.com/jesper-friis))
- Support Python 3.11 [\#103](https://github.com/EMMC-ASBL/tripper/pull/103) ([jesper-friis](https://github.com/jesper-friis))
- 92 new triplestore subclass [\#99](https://github.com/EMMC-ASBL/tripper/pull/99) ([alfredoisg](https://github.com/alfredoisg))

## [v0.2.5](https://github.com/EMMC-ASBL/tripper/tree/v0.2.5) (2023-05-24)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.4...v0.2.5)

## [v0.2.4](https://github.com/EMMC-ASBL/tripper/tree/v0.2.4) (2023-04-30)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.3...v0.2.4)

**Implemented enhancements:**

- Add entrypoint system to link external backend implementation [\#63](https://github.com/EMMC-ASBL/tripper/issues/63)

**Closed issues:**

- Transformations based on data sources [\#90](https://github.com/EMMC-ASBL/tripper/issues/90)
- Add workflow example  [\#79](https://github.com/EMMC-ASBL/tripper/issues/79)

**Merged pull requests:**

- Added argument `lang` to triplestore.value\(\) [\#104](https://github.com/EMMC-ASBL/tripper/pull/104) ([jesper-friis](https://github.com/jesper-friis))
- Run doctest from CI tests [\#101](https://github.com/EMMC-ASBL/tripper/pull/101) ([jesper-friis](https://github.com/jesper-friis))
- Added add\_data\(\), get\_value\(\) and add\_interpolation\_source\(\) methods to Triplestore [\#91](https://github.com/EMMC-ASBL/tripper/pull/91) ([jesper-friis](https://github.com/jesper-friis))
- Added tests for Python 3.11 and 3.6 [\#84](https://github.com/EMMC-ASBL/tripper/pull/84) ([jesper-friis](https://github.com/jesper-friis))
- Remove some deprecation warnings [\#83](https://github.com/EMMC-ASBL/tripper/pull/83) ([jesper-friis](https://github.com/jesper-friis))
- Workflow example [\#81](https://github.com/EMMC-ASBL/tripper/pull/81) ([jesper-friis](https://github.com/jesper-friis))
- Support external backends [\#80](https://github.com/EMMC-ASBL/tripper/pull/80) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.3](https://github.com/EMMC-ASBL/tripper/tree/v0.2.3) (2023-02-05)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.2...v0.2.3)

**Closed issues:**

- Add a to\_yaml\(\) method to MappingStep [\#66](https://github.com/EMMC-ASBL/tripper/issues/66)

**Merged pull requests:**

- Add official support for Python 3.11 [\#82](https://github.com/EMMC-ASBL/tripper/pull/82) ([jesper-friis](https://github.com/jesper-friis))
- added PR template [\#77](https://github.com/EMMC-ASBL/tripper/pull/77) ([alfredoisg](https://github.com/alfredoisg))

## [v0.2.2](https://github.com/EMMC-ASBL/tripper/tree/v0.2.2) (2023-01-30)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.1...v0.2.2)

**Fixed bugs:**

- pre-commit failing hook installation [\#75](https://github.com/EMMC-ASBL/tripper/issues/75)
- ontopy backend failing tests [\#7](https://github.com/EMMC-ASBL/tripper/issues/7)

**Closed issues:**

- Describe functions with EMMO instead of FnO [\#65](https://github.com/EMMC-ASBL/tripper/issues/65)

**Merged pull requests:**

- Using isort 5.12.0 for pre-commit [\#76](https://github.com/EMMC-ASBL/tripper/pull/76) ([CasperWA](https://github.com/CasperWA))
- Visualise [\#74](https://github.com/EMMC-ASBL/tripper/pull/74) ([jesper-friis](https://github.com/jesper-friis))
- Generate mapping routes from subclasses of Value and MappingStep [\#73](https://github.com/EMMC-ASBL/tripper/pull/73) ([jesper-friis](https://github.com/jesper-friis))
- Fix deprecated calls syntax to Triplestore.triples\(\) [\#71](https://github.com/EMMC-ASBL/tripper/pull/71) ([jesper-friis](https://github.com/jesper-friis))
- Made the value optional + added some cleanup [\#70](https://github.com/EMMC-ASBL/tripper/pull/70) ([jesper-friis](https://github.com/jesper-friis))
- Add map\(\) method to Triplestore [\#69](https://github.com/EMMC-ASBL/tripper/pull/69) ([jesper-friis](https://github.com/jesper-friis))
- Proper cost function [\#68](https://github.com/EMMC-ASBL/tripper/pull/68) ([jesper-friis](https://github.com/jesper-friis))
- Updated Triplestore.add\_function\(\) to also support EMMO. [\#67](https://github.com/EMMC-ASBL/tripper/pull/67) ([jesper-friis](https://github.com/jesper-friis))
- Added mappings [\#62](https://github.com/EMMC-ASBL/tripper/pull/62) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.1](https://github.com/EMMC-ASBL/tripper/tree/v0.2.1) (2022-12-18)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.2.0...v0.2.1)

**Closed issues:**

- Simplify use of the Triplestore triples\(\) and remove\(\) methods [\#50](https://github.com/EMMC-ASBL/tripper/issues/50)

**Merged pull requests:**

- Commented out \_\_hash\_\_\(\) and \_\_eq\_\_\(\) methods from Literal. [\#55](https://github.com/EMMC-ASBL/tripper/pull/55) ([jesper-friis](https://github.com/jesper-friis))
- Simplify use of the Triplestore triples\(\) and remove\(\) methods [\#51](https://github.com/EMMC-ASBL/tripper/pull/51) ([jesper-friis](https://github.com/jesper-friis))
- Separated `base_iri` argument from `triplestore_url` in rdflib backend [\#49](https://github.com/EMMC-ASBL/tripper/pull/49) ([jesper-friis](https://github.com/jesper-friis))

## [v0.2.0](https://github.com/EMMC-ASBL/tripper/tree/v0.2.0) (2022-12-13)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.1.2...v0.2.0)

**Fixed bugs:**

- Deploy docs failing due to wrong dependency installation [\#53](https://github.com/EMMC-ASBL/tripper/issues/53)

**Closed issues:**

- Remove backend packages from requirements [\#48](https://github.com/EMMC-ASBL/tripper/issues/48)
- Fix utils.parse\_object\(\)  [\#45](https://github.com/EMMC-ASBL/tripper/issues/45)

**Merged pull requests:**

- Update `docs` extra [\#54](https://github.com/EMMC-ASBL/tripper/pull/54) ([CasperWA](https://github.com/CasperWA))
- Remove backend packages from requirements [\#52](https://github.com/EMMC-ASBL/tripper/pull/52) ([jesper-friis](https://github.com/jesper-friis))
- Fix utils.parse\_object\(\) [\#46](https://github.com/EMMC-ASBL/tripper/pull/46) ([jesper-friis](https://github.com/jesper-friis))

## [v0.1.2](https://github.com/EMMC-ASBL/tripper/tree/v0.1.2) (2022-12-11)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/v0.1.1...v0.1.2)

**Implemented enhancements:**

- The return value of `query()` depends on the query [\#42](https://github.com/EMMC-ASBL/tripper/issues/42)
- Add DLite collection backend [\#41](https://github.com/EMMC-ASBL/tripper/issues/41)
- Implement create\_database\(\) and remove\_database\(\) methods [\#34](https://github.com/EMMC-ASBL/tripper/issues/34)
- SPARQLWrapper backend [\#10](https://github.com/EMMC-ASBL/tripper/issues/10)
- Refactor triplestore.py \(triplestore module API\) [\#3](https://github.com/EMMC-ASBL/tripper/issues/3)

**Closed issues:**

- Revert to using the proper general version for SINTEF/ci-cd [\#35](https://github.com/EMMC-ASBL/tripper/issues/35)
- Write in type annotations [\#33](https://github.com/EMMC-ASBL/tripper/issues/33)
- Improve README file [\#18](https://github.com/EMMC-ASBL/tripper/issues/18)
- Add support for simple persistent storage in the rdflib backend [\#14](https://github.com/EMMC-ASBL/tripper/issues/14)

**Merged pull requests:**

- Added collection backend [\#44](https://github.com/EMMC-ASBL/tripper/pull/44) ([jesper-friis](https://github.com/jesper-friis))
- Fix return types [\#43](https://github.com/EMMC-ASBL/tripper/pull/43) ([CasperWA](https://github.com/CasperWA))
- Updated import statements in the tutorial [\#40](https://github.com/EMMC-ASBL/tripper/pull/40) ([jesper-friis](https://github.com/jesper-friis))
- Added create\_database\(\) and remove\_database\(\) methods. [\#39](https://github.com/EMMC-ASBL/tripper/pull/39) ([jesper-friis](https://github.com/jesper-friis))
- Use the proper version of SINTEF/ci-cd [\#36](https://github.com/EMMC-ASBL/tripper/pull/36) ([CasperWA](https://github.com/CasperWA))
- bumped ci-cd version to remove --strict mkdocs command [\#32](https://github.com/EMMC-ASBL/tripper/pull/32) ([daniel-sintef](https://github.com/daniel-sintef))
- 3 refactor triplestorepy triplestore module api [\#31](https://github.com/EMMC-ASBL/tripper/pull/31) ([daniel-sintef](https://github.com/daniel-sintef))
- 3 refactor triplestore [\#27](https://github.com/EMMC-ASBL/tripper/pull/27) ([jesper-friis](https://github.com/jesper-friis))
- Corrected copyright [\#21](https://github.com/EMMC-ASBL/tripper/pull/21) ([jesper-friis](https://github.com/jesper-friis))
- Add a useful description to README file. [\#19](https://github.com/EMMC-ASBL/tripper/pull/19) ([jesper-friis](https://github.com/jesper-friis))
- Added support for simple persistent storage in the rdflib backend [\#15](https://github.com/EMMC-ASBL/tripper/pull/15) ([jesper-friis](https://github.com/jesper-friis))
- sparqlwrapper backend [\#11](https://github.com/EMMC-ASBL/tripper/pull/11) ([jesper-friis](https://github.com/jesper-friis))
- Documented return value of the Triplestore.query\(\) and added a test for it [\#9](https://github.com/EMMC-ASBL/tripper/pull/9) ([jesper-friis](https://github.com/jesper-friis))

## [v0.1.1](https://github.com/EMMC-ASBL/tripper/tree/v0.1.1) (2022-10-13)

[Full Changelog](https://github.com/EMMC-ASBL/tripper/compare/4753f8b0cc39d54636f5ff7fa39e33364542a5cd...v0.1.1)

**Implemented enhancements:**

- Change package name to `tripper` on PyPI [\#13](https://github.com/EMMC-ASBL/tripper/issues/13)
- Clean up newly initialized Python API [\#1](https://github.com/EMMC-ASBL/tripper/issues/1)

**Fixed bugs:**

- Enable proper release workflow [\#8](https://github.com/EMMC-ASBL/tripper/issues/8)
- Fix workflows so they succeed [\#2](https://github.com/EMMC-ASBL/tripper/issues/2)

**Merged pull requests:**

- Use the package name `tripper` \(not `tripperpy`\) [\#16](https://github.com/EMMC-ASBL/tripper/pull/16) ([CasperWA](https://github.com/CasperWA))
- Clean up repository & fix workflows [\#5](https://github.com/EMMC-ASBL/tripper/pull/5) ([CasperWA](https://github.com/CasperWA))
- Added version number in \_\_init\_\_ to enable local pip install [\#4](https://github.com/EMMC-ASBL/tripper/pull/4) ([quaat](https://github.com/quaat))



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*

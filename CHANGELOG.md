# Changelog

## [v0.2.1](https://github.com/EMMC-ASBL/tripper/tree/v0.2.1) (2022-12-16)

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

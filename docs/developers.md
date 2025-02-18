# For developers

## Adding new backends

See [interface.py], which defines the interface of a backend and may serve as a template for creating new backends.

### Developing the sparqlwrapper

Tripper comes with an inbuilt backend to the SPARQLWrapper. In order
to test this properly a real triplestore is needed. This is not done in the
automatic workflows on github. However, a lcal graphDB can be setup as described below and tested with test_sparqlwrapper_graphdb.py.

To create the local instance of graphdb:
```bash
docker pull ontotext/graphdb:10.8.3 # latest tag 17.02.2025
docker run -d -p 7200:7200 --name graphdb ontotext/graphdb:10.8.3
```

To create a repository in the graphdb isntance:
```bash
curl -X POST \
     -H "Content-Type: application/rdf+xml" \
     --data-binary @tests/backends/graphdb_config.xml \
     http://localhost:7200/rest/repositories
```

Then go to  [http://localhost:7200/](http://localhost:7200/) in your browser.
You can add a new repository by pressing `create new reposotory` in the bottom right corner. Choose `GraphDB Reposotory` choos `test_repo` a id.
Tick off `Enable full-text search` and leave the rest as predefined.

You can now run the test.



## Creating new release

To create a new release, it is good to have a release summary.

To add this, create a milestone that matches the new version and tag, e.g., `v1.0.8`.

Then create a new issue, adding it to the milestone and add the `release-summary` label.

For the issue description, write the actual release summary.
This will be included as part of the changelog as well as the release notes on GitHub.

Then, go to [create a new GitHub releases](https://github.com/EMMC-ASBL/tripper/releases/new) and select the tag that matches the milestone (creating a new one).
Add again the tag as the release title (optionally write something else that defines this release as a title).

Finally, press the "Publish release" button and ensure the release workflow succeeds (check [the release workflow](https://github.com/EMMC-ASBL/tripper/actions/workflows/cd_release.yml)).




[interface.py]: https://github.com/EMMC-ASBL/tripper/blob/master/tripper/interface.py

Test services
=============

This directory contains a [compose.yaml](compose.yaml) file that starts
the external services used by the Tripper tests.  It works with both
`docker compose` and `podman compose`.

| Service   | Port |
|-----------|------|
| `fuseki`  | 3030 |
| `graphdb` | 7200 |


Usage
-----
Start all services from the root of the repository with

    docker compose -f test-services/compose.yaml up -d

or only some of them, e.g.

    docker compose -f test-services/compose.yaml up -d fuseki

Add `--wait` to wait until the services are healthy.  Stop them again with

    docker compose -f test-services/compose.yaml down

The compose project has the fixed name `tripper-test-services`, so the
services can also be managed with `docker compose -p tripper-test-services
...` from any directory.

Tests that need a service which is not running are skipped.

Note that the services publish their ports on localhost.  Stop any
locally running server that uses the same port first.


Credentials
-----------
The credentials are only meant for local testing.  They agree with the
defaults in `TEST_SERVICES` in [tripper/testutils.py](../tripper/testutils.py).
They can be changed by setting environment variables named
`TRIPPER_TEST_<SERVICE>_<KEY>`, both when starting the services and when
running the tests, e.g.

    export TRIPPER_TEST_FUSEKI_PASSWORD=my-secret

- fuseki is started with admin password `admin0` and a `test_repo`
  dataset.
- Starting graphdb also starts the one-shot `graphdb-init` service,
  which creates the `test_repo` repository with full-text search from
  [graphdb-test_repo-config.ttl](graphdb-test_repo-config.ttl), unless
  it already exists.


Continuous integration
----------------------
The [CI tests](../.github/workflows/ci_tests.yml) workflow starts the
services needed by the Tripper tests from the same compose file.

To avoid the rate limit of Docker Hub, the `docker-images` job pulls the
images once and stores them with `actions/cache`.  The pytest jobs load
the images from the cache and start the services without pulling.  The
cache key is a hash of [compose.yaml](compose.yaml), so keep the images
pinned to fixed tags and change the tag to update an image.

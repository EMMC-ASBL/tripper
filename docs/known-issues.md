Known issues
============

  * If you use the rdflib backend and don't have write permissions to
    the cache directory (which e.g. can happen if you run Python in
    docker as a non-root user), you may get a `urllib.error.HTTPError`
    error when accessing an online rdf resource.

    Setting the environment variable `XDG_CACHE_HOME` to a directory
    that you have write access to will solve the problem.

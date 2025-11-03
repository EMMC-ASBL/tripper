Session
=======
Tripper provides simple support for sessions.

First you should configure some triplestores you want to use. This is done in a
YAML where each configured triplestore is identified with a unique name.

The default location of this configuration file depends on the system:

- Linux: `$HOME/.config/tripper/session.yaml`
- Windows: `$HOME/AppData/Local/tripper/Config/session.yaml`
- Darwin: `$HOME/Library/Config/tripper/session.yaml`

The schema of the YAML file is simple.
A session should have a name that identifies it and should be followed by keyword arguments accepted by the `Triplestore` constructor.

Here is an example of a possible session file:

```
---

RdflibTest:
  backend: rdflib

GraphDBTest:
  backend: sparqlwrapper
  base_iri: http://localhost:7200/repositories/test_repo
  update_iri: http://localhost:7200/repositories/test_repo/statements
  check_iri: http://localhost:7200/repositories

FusekiTest:
  backend: sparqlwrapper
  base_iri: http://localhost:3030/test_repo
  update_iri: http://localhost:3030/test_repo/update
  check_iri: http://localhost:3030
  username: admin
  password: admin0

MyKB:
  backend: sparqlwrapper
  base_iri: https://graphdb.myproject.eu/repositories/test_repo
  update_iri: https://graphdb.myproject.eu/repositories/test_repo/statements
  check_iri: https://graphdb.myproject.eu/repositories
  username: myname
  password: KEYRING
```

The first entry is an in-memory rdflib backend.

The second and third entries correspond to GraphDB and Fuseki services,
respectively.
These can be started with docker as described in the [developers] section.

The fourth entry is just a dummy example, showing how to use [keyring].

Each entry starts with the name identifying the configured triplestore.
The keywords following it, correspond to the keyword arguments passed to the
[Triplestore] constructor.

If an entry has a `password` keyword with the special value "KEYRING", the
value is replaced with the password looked up using the [keyring] library.


!!! tip

    To store the password for the "MyKB" backend in the keyring, make sure
    that you have [keyring] installed and run the following command in a
    terminal

        keyring set MyKB myname

    Enter the password in the prompt. That's it, now you can access `MyKB`
    as if the password was hardcoded into the session.yaml file.

    See the [keyring] documentation for improved security by using one of
    the recommended keyring backends for your system.


Example
-------

If you have started the Fuseki service (as described on [developers]),
you can now do:

```python
>>> from tripper import Literal, Session

# Normally you will call Session with no arguments
>>> session = Session()  # doctest: +SKIP

# ...but it is also possible to specify the config file explicitly
>>> session = Session("tests/input/session.yaml")
>>> ts = session.get_triplestore("FusekiTest")
>>> EX = ts.bind("ex", "http://example.com#")

>>> ts.remove()  # clear the triplestore  # doctest: +ELLIPSIS
<SPARQLWrapper.Wrapper.QueryResult object at 0x...>

>>> ts.add_triples([
...     (EX.john, EX.hasName, Literal("John")),
...     (EX.john, EX.hasSon, EX.lars),
... ])
>>> list(ts.triples())  # doctest: +NORMALIZE_WHITESPACE
[('http://example.com#john', 'http://example.com#hasName', Literal('John')),
 ('http://example.com#john', 'http://example.com#hasSon', 'http://example.com#lars')]

```


[developers]: https://emmc-asbl.github.io/tripper/latest/developers/
[keyring]: https://pypi.org/project/keyring/
[Triplestore]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore

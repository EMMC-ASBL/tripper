Session
=======
Tripper provides simple support for sessions.

First you should configure some triplestores you want to use. This is done in a
YAML where each configured triplestore is identified with a unique name.

The default location of this configuration file depends on the system:

- Linux: `$HOME/.config/tripper/session.yaml`
- Windows: `$HOME/AppData/Local/tripper/Config/session.yaml`
- Darwin: `$HOME/Library/Config/tripper/session.yaml`

Add some default

```
GraphDBTest:
  backend: sparqlwrapper
  base_iri: http://localhost:7200/repositories/test_repo
  update_iri: http://localhost:7200/repositories/test_repo/statements

FusekiTest:
  backend: sparqlwrapper
  base_iri: http://localhost:3030/test_repo
  update_iri: http://localhost:3030/test_repo/update
  username: admin
  password: admin0

MyKB:
  backend: sparqlwrapper
  base_iri: https://graphdb.myproject.eu/repositories/test_repo
  update_iri: https://graphdb.myproject.eu/repositories/test_repo/statements
  username: myname
  password: KEYRING
```

The two first entries correspond to the GraphDB and Fuseki services
that can be started with docker as described in the [developers]
section.

The third entry is just a dummy example, showing how to use [keyring].

Each entry starts with the name identifying the configured triplestore.
The keywords following it, correspond to the keyword arguments passed to the
[Triplestore] constructor.

If an entry has a `password` keyword with the special value "KEYRING", the
value is replaced with the password looked up using the [keyring] library.


Example
-------

If you have started the Fuseki service (as described on [developers]),
you can now do:

```python
>>> from tripper import Literal, Session

>>> session = Session()
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

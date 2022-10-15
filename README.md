Tripper
=======
**Tripper** is triplestore wrapper for Python providing a simple and
consistent interface to a range of triplestore backends.

The interface of **Tripper** strives for simplicity and is modelled
after [rdflib] (with a few simplifications).


Basic concepts
--------------
In Tripper are:
- all IRIs are represented by Python strings
- blank nodes are strings starting with "_:"
- literals are constructed with `tripper.Literal`

Tripper offers the `tripper.Namespace` class for simplifying working
with namespaces and writing IRIs.

A triplestore wrapper is created by instantiating `tripper.Triplestore`.


Getting started
---------------
Take a look at the [tutorial](docs/tutorial.md) to get started.


Installation
------------
**Tripper** has by itself no dependencies outside the standard
library, but the triplestore backends may have.


The package can be installed from [PyPI](https://pypi.org/project/tripper) using `pip`:

```shell
pip install tripper
```

License and copyright
---------------------
All files in this repository are licensed under the [MIT license](LICENSE) with copyright &copy; 2022 SINTEF.



[rdflib]: https://rdflib.readthedocs.io/en/stable/

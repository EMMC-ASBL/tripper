Tripper
=======
_Triplestore wrapper for Python providing a simple and consistent interface to a range of triplestore backends._

![CI tests](https://github.com/EMMC-ASBL/tripper/workflows/CI%20-%20Tests/badge.svg)
[![PyPI version](https://badge.fury.io/py/tripper.svg)](https://badge.fury.io/py/tripper)



Basic concepts
--------------
**Tripper** strives for simplicity and is modelled after [rdflib] (with a few simplifications).

In Tripper are:
* All IRIs are represented by Python strings.
  Example: `"http://emmo.info/emmo#Atom"`

* Blank nodes are strings starting with "_:".
  Example: `"_:bnode1"`

* Literals are constructed with `tripper.Literal`.
  Example: `tripper.Literal(3.14, datatype=XSD.float)`

To make it easy to work with IRIs, provide Tripper a set of pre-defined namespaces, like `XSD.float`.
New namespaces can easily be defined with the `tripper.Namespace` class.

A triplestore wrapper is created with the `tripper.Triplestore` class.



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
All files in this repository are licensed under the [MIT license](LICENSE) with copyright &copy; 2022 European Material Modelling Council.



[rdflib]: https://rdflib.readthedocs.io/en/stable/

Tripper
=======
_Triplestore wrapper for Python providing a simple and consistent interface to a range of triplestore backends - the best ride when handling any triplestore._


[![PyPI](https://img.shields.io/pypi/v/tripper?logo=pypi)](https://pypi.org/project/tripper)
[![Documentation](https://img.shields.io/badge/documentation-informational?logo=github)](https://emmc-asbl.github.io/tripper/latest/)
[![CI tests](https://github.com/EMMC-ASBL/tripper/workflows/CI%20-%20Tests/badge.svg)](https://github.com/EMMC-ASBL/tripper/actions/workflows/ci_tests.yml?query=branch%3Amain)


Basic concepts
--------------
**Tripper** strives for simplicity and is modelled after [rdflib] (with a few simplifications).

In Tripper are:
* All IRIs are represented by Python strings.
  Example: `"http://emmo.info/emmo#Atom"`

* Blank nodes are strings starting with "_:".
  Example: `"_:bnode1"`

* Literals are constructed with [`tripper.Literal`][Literal].
  Example: `tripper.Literal(3.14, datatype=XSD.float)`

To make it easy to work with IRIs, provide Tripper a set of pre-defined namespaces, like `XSD.float`.
New namespaces can easily be defined with the [`tripper.Namespace`][Namespace] class.

A triplestore wrapper is created with the [`tripper.Triplestore`][Triplestore] class.



Documentation
-------------
* Getting started: Take a look at the [tutorial](docs/tutorial.md).
* Reference manual: [API Reference]


Installation
------------
**Tripper** has by itself no dependencies outside the standard
library, but the triplestore backends may have.


The package can be installed from [PyPI] using `pip`:

```shell
pip install tripper
```

License and copyright
---------------------
All files in this repository are licensed under the [MIT license](LICENSE).
If not stated otherwise in the top of the file, it has copyright &copy; 2022
SINTEF.




[rdflib]: https://rdflib.readthedocs.io/en/stable/
[PyPI]: https://pypi.org/project/tripper
[API Reference]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/
[Literal]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Literal
[Namespace]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Namespace
[Triplestore]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore

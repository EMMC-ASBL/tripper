Basic tutorial
==============
<!-- markdownlint-disable MD007 -->

Creating a triplestore interface
--------------------------------
Tripper is a Python library providing a common interface to a range of pre-defined triplestores.
To interface a triplestore, you create an instance of [Triplestore] providing the name of the triplestore as the `backend` argument.

For example, to create an interface to an in-memory [rdflib] triplestore, you can use the `rdflib` backend:

```python
>>> from tripper import Triplestore
>>> ts = Triplestore(backend="rdflib")

```


Creating a namespace
--------------------
Tripper provides a set of pre-defined namespaces that simplifies writing IRIs.
For example:

```python
>>> from tripper import RDFS, OWL
>>> RDFS.subClassOf
'http://www.w3.org/2000/01/rdf-schema#subClassOf'

```

New namespaces can be created using the [Namespace] class, but are usually added with the `bind()` method:

```python
>>> ONTO = ts.bind("onto", "http://example.com/onto#")
>>> ONTO.MyConcept
'http://example.com/onto#MyConcept'

```

Namespace also supports access by label and IRI checking.
Both of these features requires loading an ontology.
The following example shows how to create an EMMO namespace with IRI checking.
The keyword argument `label_annotations=True` enables access by `skos:prefLabel`, `rdfs:label` or `skos:altLabel`.
What labels to use can also be specified explicitly.
The `check=True` enables checking for existing IRIs.

```python
>>> EMMO = ts.bind(
...     prefix="emmo",
...     namespace="https://w3id.org/emmo#",
...     label_annotations=True,
...     check=True,
... )

# Access by label
>>> EMMO.Atom
'https://w3id.org/emmo#EMMO_eb77076b_a104_42ac_a065_798b2d2809ad'

# This fails because we set `check=True`
>>> EMMO.invalid_name
Traceback (most recent call last):
    ...
tripper.errors.NoSuchIRIError: https://w3id.org/emmo#invalid_name

```

The above example works, since the `namespace="https://w3id.org/emmo#"` is resolvable.
In the case when the IRI in the `namespace` argument is not resolvable, it is possible to supply a resolvable IRI or a reference to a populated Triplestore instance via the `triplestore` keyword argument.

Access by label makes it much easier to work with ontologies, like EMMO, that uses non-human readable IDs for the IRIs.
More about this below.




Working with an interfaced triplestore
--------------------------------------
The interface provided by Tripper is modelled after [rdflib], so if you know that library, you will find Tripper rather familiar.

There are some differences, though. Most recognisable:
* All IRIs are represented by Python strings.
  Example: `"https://w3id.org/emmo#Metre"`
* Blank nodes are strings starting with "_:".
  Example: `"_:bnode1"`
* Literals are constructed with [`tripper.Literal`][Literal].
  Example: `tripper.Literal(3.14, datatype=XSD.float)`

Lets assume you have created a triplestore as showed in [Creating a triplestore interface].
You can then start to add new triples to it with the `add()` and `add_triples()` methods:

```python
# en(msg) is a convenient function for adding english literals.
# It is equivalent to ``tripper.Literal(msg, lang="en")``.
>>> from tripper.utils import en
>>> ts.add_triples([
...     (ONTO.MyConcept, RDFS.subClassOf, OWL.Thing),
...     (ONTO.MyConcept, RDFS.label, en("My briliant ontological concept.")),
... ])

```

You can also load triples from a source using the `parse()` method:

```python
ts.parse("onto.ttl", format="turtle")
```


You can also serialise the triplestore to a string or a file using `serialize()`:

```python
ts.serialize("onto2.ttl")
```

A set of convenient functions exists for simple queries, including `triples()`, `subjects()`, `predicates()`, `objects()`, `subject_predicates()`, `subject_objects()`, `predicate_objects()` and `value()`.
Except for `value()`, they return the result as generators.
For example:

```python
>>> ts.objects(subject=ONTO.MyConcept, predicate=RDFS.subClassOf)  # doctest: +ELLIPSIS
<generator object Triplestore.objects at 0x...>

>>> list(ts.objects(subject=ONTO.MyConcept, predicate=RDFS.subClassOf))
['http://www.w3.org/2002/07/owl#Thing']

```

The `query()` and `update()` methods can be used to query and update the triplestore using SPARQL.
See the next section.


Writing SPARQL queries using Tripper
------------------------------------
A challenge with ontologies using numerical IRIs is that SPARQL queries become difficult to read and understand.
This challenge is greatly mitigated by using the `label_annotations` feature of Tripper namespaces.
The example below shows how to write and execute a SPARQL query with Tripper that finds the IRI and unit symbol of all length units.
Note:
1. EMMO classes and properties are written as `{EMMO.LengthUnit}`, which would expand to `https://w3id.org/emmo#EMMO_b3600e73_3e05_479d_9714_c041c3acf5cc`.
2. The curly brackets after the `WHERE` clause have to be written `{{`, `}}` because the query is an f-string.

```python
# Load pre-inferred EMMO
>>> ts = Triplestore("rdflib", base_iri="https://w3id.org/emmo#")
>>> ts.parse("https://w3id.org/emmo#inferred")

# Bind "emmo" prefix to base_iri
>>> EMMO = ts.bind("emmo", label_annotations=True, check=True)

# Get IRI and symbol of all length units
>>> query = f"""
... PREFIX owl:  <http://www.w3.org/2002/07/owl#>
... PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
... PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
...
... SELECT ?unit ?symbol
... WHERE {{
...   ?unit rdfs:subClassOf <{EMMO.LengthUnit}> .
...   ?unit rdfs:subClassOf ?r .
...   ?r rdf:type owl:Restriction .
...   ?r owl:onProperty <{EMMO.hasSymbolValue}> .
...   ?r owl:hasValue ?symbol .
... }}
... """
>>> r = ts.query(query)
>>> (EMMO.Metre, "m") in r
True

```


Specialised methods
===================


Working with mappings
---------------------
The [Triplestore] class has two specialised methods `map()` and `add_function()` that simplify working with mappings.

`map()` is convinient for defining new mappings:

```python
from tripper import Namespace
META = Namespace("http://onto-ns.com/meta/0.1/MyEntity#")
ts.map(META.my_property, ONTO.MyConcept)
```

It can also be used with DLite and SOFT7 data models.
Here we repeat the above with DLite:

```python
import dlite
meta = dlite.get_instance("http://onto-ns.com/meta/0.1/MyEntity")
ts.map(meta.my_property, ONTO.MyConcept)
```

The `add_function()` describes a function and adds mappings for its arguments and return value(s).
Currently [EMMO] and the [Function Ontology (FnO)] are supported.

```python
def mean(x, y):
    """Returns the mean value of `x` and `y`."""
    return (x + y)/2

ts.add_function(
    mean,
    expects=(ONTO.RightArmLength, ONTO.LeftArmLength),
    returns=ONTO.AverageArmLength,
)
```

[rdflib]: https://rdflib.readthedocs.io/
[Triplestore]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore
[Namespace]:
https://emmc-asbl.github.io/tripper/latest/api_reference/namespace/#tripper.namespace.Namespace
[Literal]:
https://emmc-asbl.github.io/tripper/latest/api_reference/literal/#tripper.literal.Literal
[Creating a triplestore interface]: #creating-a-triplestore-interface
[EMMO]: https://emmc.eu/emmo/
[Function Ontology (FnO)]: https://fno.io/

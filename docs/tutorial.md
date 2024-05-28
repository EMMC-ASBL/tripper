Basic tutorial
==============
<!-- markdownlint-disable MD007 -->


Introduction
------------
Tripper is a Python library providing a common interface to a range of pre-defined triplestores.
This is done via a plugin system for different triplestore `backends`.
See the README file for a [list of currently supported backends].

To interface a triplestore, you create an instance of [Triplestore] providing the name of the triplestore as the `backend` argument.

The API provided by Tripper is modelled after [rdflib], so if you know that library, you will find Tripper rather familiar.
But there are some differences that you should be aware of.
Most recognisable:
* All IRIs are represented by Python strings.
  Example: `"https://w3id.org/emmo#Metre"`
* Blank nodes are strings starting with "_:".
  Example: `"_:bnode1"`
* Literals are constructed with [`tripper.Literal`][Literal].
  Example: `tripper.Literal(3.14, datatype=XSD.float)`
* Namespace object works similar to namespace objects in rdflib, but its
  attribution access expands to plain Python strings.
  Example: `XSD.float`

  Tripper namespaces has also additional features that make them very
  convinient when working with ontologies, like [EMMO] that uses
  numerical IRIs.


Getting started
---------------

For example, to create an interface to an in-memory [rdflib] triplestore, you can use the `rdflib` backend:

```python
>>> from tripper import Triplestore
>>> ts = Triplestore(backend="rdflib")

```

### Namespace objects
Namespace objects are a very convenient feature that simplifies writing IRIs.
Tripper provides a set of standard pre-defined namespaces that can simply be imported.
For example:

```python
>>> from tripper import OWL, RDFS
>>> RDFS.subClassOf
'http://www.w3.org/2000/01/rdf-schema#subClassOf'

```

New namespaces can be created using the [Namespace] class, but are usually added with the `bind()` method:

```python
>>> ONTO = ts.bind("onto", "http://example.com/onto#")
>>> ONTO.MyConcept
'http://example.com/onto#MyConcept'

```

### Adding triples to the triplestore
We can now start to add triples to the triplestore, using the `add()` and `add_triples()` methods:

```python
>>> from tripper.utils import en
>>> ts.add_triples([
...     (ONTO.MyConcept, RDFS.subClassOf, OWL.Thing),
...     (ONTO.MyConcept, RDFS.label, en("My briliant ontological concept.")),
... ])

```

The function `en(msg)` is just a convenient function for adding english literals.
It is equivalent to `tripper.Literal(msg, lang="en")`.

You can also load triples from a source using the `parse()` method.
For example will

```python
ts.parse("onto.ttl", format="turtle")
```

load all triples in turtle file `onto.ttl` into the triplestore.

Similarly you can serialise the triplestore to a string or a file using the `serialize()` method:

```python
ts.serialize("onto2.ttl")  # serialise to file `onto2.ttl`
s = ts.serialize(format="ntriples")  # serialise to string s in ntriples format
```

### Retrieving triples from and querying a triplestore
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


Slightly more advanced features
-------------------------------

### More advanced use of namespaces
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
>>> EMMO.invalid_name  # doctest: +ELLIPSIS
Traceback (most recent call last):
    ...
tripper.errors.NoSuchIRIError: https://w3id.org/emmo#invalid_name
Maybe you have to remove the cache file: ...

```

The above example works, since the `namespace="https://w3id.org/emmo#"` is resolvable.
In the case when the IRI in the `namespace` argument is not resolvable, it is possible to supply a resolvable IRI or a reference to a populated Triplestore instance via the `triplestore` keyword argument.

Access by label makes it much easier to work with ontologies, like EMMO, that uses non-human readable IDs for the IRIs.
More about this below.



### Writing SPARQL queries using Tripper
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

### Utilities
*Todo: Describe the `tripper.utils` module*



Specialised features
====================


Working with mappings
---------------------
With a *data model*, we here mean an abstract model that describes the structure of a dataset.
To provide a shared semantic meaning of a data model and its *properties* (structural elements), one can create *mappings* between these elements and ontological concepts (typically a class in an OWL ontology).

Mappings can also be used to semantically document the arguments and return values of a function.

The [Triplestore] class has two specialised methods for adding mappings, `map()` and `add_function()`.
The purpose of the `map()` method, is to map a data models and its properties to ontological concepts, while `add_function()` maps the arguments and return value of a function to ontological concepts.

**Note**, the name of the `map()` and `add_function()` methods are not very intuitive and may be changed in the future.


### Adding mappings
Lets assume that you have a data model identified by the IRI `http://onto-ns.com/meta/ex/0.1/MyDataModel`, which has a property (structural element) called *velocity*.
A namespace object for this data model can be created with

```python
from tripper import Namespace
DM = Namespace("http://onto-ns.com/meta/ex/0.1/MyDataModel#")
```

and use to map the data model property `velocity` to the concept `ONTO.Velocity` in the ontology


```python
ts.map(DM.velocity, ONTO.Velocity)
```

One can also work directly with DLite and SOFT7 data models.
Here we repeat the above with DLite:

```python
import dlite
mymodel = dlite.get_instance("http://onto-ns.com/meta/ex/0.1/MyDataModel")
ts.map(mymodel.velocity, ONTO.Velocity)
```

The `add_function()` method documents a Python function semantically and adds mappings for its arguments and return value(s).
Currently, it supports both [EMMO] and the [Function Ontology (FnO)] for the semantic documentation.

For example, to semantically document the general function `mean()` applied to the special context of arm lengths, one can do

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


### Using mappings
*Todo: Describe the `tripper.mappings` subpackage...*



### Representing pydantic data models as RDF
*Todo: Describe the `tripper.convert` subpackage...*




[rdflib]: https://rdflib.readthedocs.io/
[Triplestore]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore
[Namespace]:
https://emmc-asbl.github.io/tripper/latest/api_reference/namespace/#tripper.namespace.Namespace
[Literal]:
https://emmc-asbl.github.io/tripper/latest/api_reference/literal/#tripper.literal.Literal
[Creating a triplestore interface]: #creating-a-triplestore-interface
[EMMO]: https://emmc.eu/emmo/
[Function Ontology (FnO)]: https://fno.io/
[list of currently supported backends]: https://github.com/EMMC-ASBL/tripper?tab=readme-ov-file#available-backends

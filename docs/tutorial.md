Basic tutorial
==============
<!-- markdownlint-disable MD007 -->


Introduction
------------
Tripper is a Python library providing a common interface to a range of pre-defined triplestores.
This is done via a plugin system for different triplestore `backends`.
See the README file for a [list of currently supported backends].

The API provided by Tripper is modelled after [rdflib], so if you know that library, you will find Tripper rather familiar.
But there are some differences to be aware of.
Most important are:

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
To interface a triplestore, you create an instance of [Triplestore] providing the name of the triplestore as the `backend` argument.

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

New namespaces can be created using the [Namespace] class, but are usually added with the [`bind()`] method:

```python
>>> ONTO = ts.bind("onto", "http://example.com/onto#")
>>> ONTO.MyConcept
'http://example.com/onto#MyConcept'

```

### Adding triples to the triplestore
Triples can now be added to the triplestore, using the [`add()`] and [`add_triples()`] methods:

```python
>>> from tripper.utils import en
>>> ts.add_triples([
...     (ONTO.MyConcept, RDFS.subClassOf, OWL.Thing),
...     (ONTO.MyConcept, RDFS.label, en("My briliant ontological concept.")),
... ])

```

The function [`en()`] is just a convenient function for adding English literals.
It is equivalent to `tripper.Literal(msg, lang="en")`.

Triples can also be added from a source using the [`parse()`] method.
For example will

```python
ts.parse("onto.ttl", format="turtle")
```

load all triples in turtle file `onto.ttl` into the triplestore.

Similarly, the triplestore can be serialised to a string or a file using the [`serialize()`] method:

```python
ts.serialize("onto2.ttl")  # serialise to file `onto2.ttl`
s = ts.serialize(format="ntriples")  # serialise to string s in ntriples format
```

### Retrieving triples from and querying a triplestore
A set of convenient functions exist for simple queries, including [`triples()`], [`subjects()`], [`predicates()`], [`objects()`], [`subject_predicates()`], [`subject_objects()`], [`predicate_objects()`] and [`value()`].
Except for [`value()`], they return iterators.
For example:

```python
>>> ts.objects(subject=ONTO.MyConcept, predicate=RDFS.subClassOf)  # doctest: +ELLIPSIS
<generator object Triplestore.objects at 0x...>

>>> list(ts.objects(subject=ONTO.MyConcept, predicate=RDFS.subClassOf))
['http://www.w3.org/2002/07/owl#Thing']

```

The [`query()`] and [`update()`] methods can be used to query and update the triplestore using SPARQL.
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
When the IRI in the `namespace` argument is not resolvable, it is possible to supply a resolvable IRI or a reference to a populated [Triplestore] instance via the `triplestore` keyword argument.

Access by label makes it much easier to work with ontologies, like EMMO, that uses non-human readable IDs for the IRIs.
More about this below.

The utility function [`extend_namespace()`] can be used to add additional known labels to a namespace.
For example:

```python
>>> from tripper import Namespace
>>> from tripper.utils import extend_namespace
>>> FOOD = Namespace(
...     "http://onto-ns.com/ontologies/examples/food#",
...     label_annotations=True,
...     check=True,
...     reload=True,
...     triplestore="https://raw.githubusercontent.com/EMMC-ASBL/tripper/master/tests/ontologies/food.ttl",
...     format="turtle",
... )

# Hamburger is not a known label
>>> FOOD.Hamburger  # doctest: +ELLIPSIS
Traceback (most recent call last):
    ...
tripper.errors.NoSuchIRIError: http://onto-ns.com/ontologies/examples/food#Hamburger
...

# Add Hamburger to known labels
>>> extend_namespace(FOOD, {"Hamburger": FOOD + "Hamburger"})
>>> FOOD.Hamburger == FOOD + "Hamburger"
True

# Fish is not a known label
>>> FOOD.Fish  # doctest: +ELLIPSIS
Traceback (most recent call last):
    ...
tripper.errors.NoSuchIRIError: http://onto-ns.com/ontologies/examples/food#Fish
...

# Extend FOOD from an online turtle file
>>> extend_namespace(
...    FOOD,
...    "https://raw.githubusercontent.com/EMMC-ASBL/tripper/master/tests/ontologies/food-more.ttl",
...    format="turtle",
... )

# Now Fish is in the namespace
>>> FOOD.Fish
'http://onto-ns.com/ontologies/examples/food#FOOD_90f5dd54_9e5c_46c9_824f_e10625a90c26'

```


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

### Class restrictions
When working with OWL ontologies, it is often required to inspect or add class [restriction]s.
The Triplestore class has two convenient methods for this, that do not require knowledge about how restrictions are represented in RDF.
Only support basic restrictions, without any nested logical constructs, are supoprted.
For more advanced restrictions, we recommend to use [EMMOntoPy] or [Owlready2].

A [restriction] restricts a class to only those individuals that satisfy the restriction.
It is described by the following set of parameters.

  * **cls**: IRI of class to which the restriction applies.
  * **property**: IRI of restriction property.
  * **type**: The type of the restriction.  Should be one of:
    - *some*: existential restriction (target is a class IRI)
    - *only*: universal restriction (target is a class IRI)
    - *exactly*: cardinality restriction (target is a class IRI)
    - *min*: minimum cardinality restriction (target is a class IRI)
    - *max*: maximum cardinality restriction (target is a class IRI)
    - *value*: Value restriction (target is an IRI of an individual or a literal)

  * **cardinality**: the cardinality value for cardinality restrictions.
  * **value**: The IRI or literal value of the restriction target.

As an example, the class `onto:Bacteria` can be logically restricted to be unicellular.
In Manchester syntax, this can be stated as `onto:Bacteria emmo:hasPart exactly 1 onto:Cell`.
With Tripper this can be stated as:

```python
>>> iri = ts.add_restriction(
...     cls=ONTO.Bacteria,
...     property=EMMO.hasPart,
...     type="exactly",
...     cardinality=1,
...     value=ONTO.Cell,
... )

```
The returned `iri` is the blank node IRI of the new restriction.

To find the above restriction, the [`restrictions()`] method can be used.
It returns an iterator over all restrictions that matches the provided criteria.
For example:

```python
>>> g = ts.restrictions(cls=ONTO.Bacteria, property=EMMO.hasPart, asdict=True)
>>> list(g)  # doctest: +ELLIPSIS
[{'iri': '_:...', 'cls': 'http://example.com/onto#Bacteria', 'property': 'https://w3id.org/emmo#EMMO_17e27c22_37e1_468c_9dd7_95e137f73e7f', 'type': 'exactly', 'cardinality': 1, 'value': 'http://example.com/onto#Cell'}]

```

With the `asdict` argument set to false, an iterator over the IRIs of all matching restrictions is returned:

```python
>>> g = ts.restrictions(cls=ONTO.Bacteria, property=EMMO.hasPart, asdict=False)
>>> next(g) == iri
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

The [Triplestore] class has two specialised methods for adding mappings, [`map()`] and [`add_function()`].
The purpose of the [`map()`] method, is to map a data models and its properties to ontological concepts, while [`add_function()`] maps the arguments and return value of a function to ontological concepts.

**Note**, the name of the [`map()`] and [`add_function()`] methods are not very intuitive and may be changed in the future.


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





[rdflib]: https://rdflib.readthedocs.io/
[EMMO]: https://emmc.eu/emmo/
[OTEIO]: https://github.com/emmo-repo/domain-oteio/
[Function Ontology (FnO)]: https://fno.io/
[EMMOntoPy]: https://emmo-repo.github.io/EMMOntoPy/
[Owlready2]: https://pypi.org/project/owlready2/
[restriction]: https://www.w3.org/TR/owl-ref/#Restriction
[JSON-LD]: https://json-ld.org/

[Creating a triplestore interface]: #creating-a-triplestore-interface
[list of currently supported backends]: https://github.com/EMMC-ASBL/tripper?tab=readme-ov-file#available-backends

[tripper.convert]: https://emmc-asbl.github.io/tripper/latest/api_reference/convert/convert/

[Triplestore]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore
[Namespace]:
https://emmc-asbl.github.io/tripper/latest/api_reference/namespace/#tripper.namespace.Namespace
[Literal]:
https://emmc-asbl.github.io/tripper/latest/api_reference/literal/#tripper.literal.Literal

[`en()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.utils.en
[`extend_namespace()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.utils.extend_namespace

[`load_container()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/convert/convert/#tripper.convert.convert.load_container
[`save_container()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/convert/convert/#tripper.convert.convert.save_container

[`add()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.add
[`add_function()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.add_function
[`add_restriction()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.add_restriction
[`add_triples()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.add_triples
[`bind()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.bind
[`map()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.map
[`objects()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.objects
[`parse()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.parse
[`predicates()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.predicates
[`predicate_objects()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.predicate_objects
[`query()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.query
[`restrictions()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.restrictions
[`serialize()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.serialize
[`subject_objects()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.subject_objects
[`subject_predicates()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.subject_predicates
[`subjects()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.subjects
[`triples()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.triples
[`update()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.update
[`value()`]: https://emmc-asbl.github.io/tripper/latest/api_reference/triplestore/#tripper.triplestore.Triplestore.value

Units and quantities
====================
The [tripper.units] subpackage provide support for using [Pint] to work with units and quantites defined in ontologies.

Currently, only [EMMO] and EMMO-based ontologies can be used as a source for units and quantities.
However, since [EMMO] include references to the [QUDT] and [OM] ontologies, it is also possible to work with IRIs for these ontologies as well.

> [!NOTE]
> Currently the support for [OM] is weak.  Improvements are planned.


Unit registry
-------------
The [UnitRegistry] in [tripper.units] is a subclass the [Pint] unit registry.
By default it is populated with units from [EMMO].

```python
>>> from tripper.units import UnitRegistry
>>> ureg = UnitRegistry()

```

The registry provide attribute and item access to units based on their [EMMO] prefLabel or symbol.

```python
>>> ureg.Pascal
<Unit('Pascal')>

>>> ureg.Pa
<Unit('Pascal')>

```

By convention are [EMMO] units written in "CamelCase".
However, unit access also work with "snake_case":

```python
>>> ureg.pascal
<Unit('Pascal')>

>>> ureg.newton_square_metre
<Unit('NewtonSquareMetre')>

```

Item access creates a quantity representation (see [Working with quantities]):

```python
>>> ureg["Pa"]
<Quantity(1, 'Pascal')>

>>> ureg["N⋅m²"]
<Quantity(1, 'Newton * Metre ** 2')>

```

### Extra unit registry methods
Tripper adds some extra methods to the unit registry on top of what is already provided by [Pint], including:

- [get_unit()]: Access unit from name, symbol, IRI (supporting [EMMO], [QUDT] and [OM]), or unit code defined in the ontology.
- [get_unit_info()]: Returns a dict with attribute access providing additional information about the unit.
- [load_quantity()]: Loads a quantity from a triplestore.
- [save_quantity()]: Saves a quantity to a triplestore.
- [clear_cache()]: Clear caches.
- [set_as_default()]: Set the current unit registry as the default. This allows to access the registry with the [get_ureg()] method.

Here we will only discuss [get_unit()] and [get_unit_info()] methods.
See [Accessing quantities in a triplestore] and [Setting up custom unit registry] for the rest.

For example:

```python
>>> ureg.get_unit(name="Metre")  # name
<Quantity(1, 'Metre')>

>>> ureg.get_unit(symbol="H/Ω")  # EMMO symbol
<Quantity(1, 'HenryPerOhm')>

>>> ureg.get_unit(symbol="H.Ohm-1")  # UCUM symbol
<Quantity(1, 'HenryPerOhm')>

>>> ureg.get_unit(iri="https://w3id.org/emmo#Metre")  # EMMO IRI
<Quantity(1, 'Metre')>

>>> ureg.get_unit(iri="http://qudt.org/vocab/unit/HR")  # QUDT IRI
<Quantity(1, 'Hour')>

>>> ureg.get_unit(iri="http://www.ontology-of-units-of-measure.org/resource/om-2/cubicMetre")  # OM IRI
<Quantity(1, 'CubicMetre')>

>>> ureg.get_unit(unitCode="HUR")
<Quantity(1, 'Hour')>

```

When you have a unit, you can also ask it for its IRI using its `emmoIRI`, `qudtIRI` and `omIRI` properties:

```python
>>> ureg.CubicMetre.emmoIRI
'https://w3id.org/emmo#CubicMetre'

>>> ureg.CubicMetre.qudtIRI
'http://qudt.org/vocab/unit/M3'

>>> ureg.CubicMetre.omIRI
'http://www.ontology-of-units-of-measure.org/resource/om-2/cubicMetre'

```

Units have an [info] property providing a dict with attribute access with description of the unit provided by the ontology.
It contains the following fields:

  - **name**: Preferred label.
  - **description**: Unit description.
  - **aliases**: List of alternative labels.
  - **symbols**: List with unit symbols.
  - **dimension**: Named tuple with quantity dimension.
  - **emmoIRI**: IRI of the unit in the EMMO ontology.
  - **qudtIRI**: IRI of the unit in the QUDT ontology.
  - **omIRI**: IRI of the unit in the OM ontology.
  - **ucumCodes**: List of UCUM codes for the unit.
  - **unitCode**: UNECE common code for the unit.
  - **multiplier**: Unit multiplier.
  - **offset**: Unit offset.

This dict can also be accessed with the [get_unit()] method.

For example:

```python
>>> info = ureg.CubicMetre.info
>>> info.name
'CubicMetre'

>>> info.dimension
Dimension(T=0, L=3, M=0, I=0, H=0, N=0, J=0)

```

The same dict can also be accessed from the unit registry with the `get_unit_info()` method.

```python
>>> info = ureg.get_unit_info("CubicMetre")
>>> info.name
'CubicMetre'

```

Working with quantities
-----------------------
Physical quantities consisting of a numerical value and a unit, can be constructed in several ways.

For example by using [ureg.Quantity()] with two arguments

```python
>>> length = ureg.Quantity(6, "km")
>>> length
<Quantity(6, 'KiloMetre')>

```

or with a single string argument

```python
>>> time = ureg.Quantity("1.2 h")
>>> time
<Quantity(1.2, 'Hour')>

```

or by multiplying a numerical value with a unit

```python
>>> pressure = 101325 * ureg.Pa
>>> pressure
<Quantity(101325, 'Pascal')>

```

The magnitude and unit of a quantity can be accessed individually with the properties `m` and `u`:

```python
>>> pressure.m
101325

>>> pressure.u
<Unit('Pascal')>

```

By default, [EMMO] does not include prefixed units (with a few exceptions).
It is therefore not uncommon to have a quantity with a unit not in the ontology.
For example:

```python
>>> duration = 1.2 * ureg.kh
>>> duration
<Quantity(1.2, 'KiloHour')>

# This raises an exception since KiloHour is not in the ontology
>>> duration.u.info
Traceback (most recent call last):
...
tripper.units.units.MissingUnitError: name=KiloHour

```

You can use to [to_ontology_units()] method (or its in-place variant [ito_ontology_units()]) to rescale the quantity to a unit that exists in the ontology:

```python
>>> duration.ito_ontology_units()
>>> f"{duration:.1f}"  # avoid rounding errors
'50.0 Day'

# The unit now has a `info` property
>>> duration.u.info.qudtIRI
'http://qudt.org/vocab/unit/DAY'

```


### Quantities as literals
Quantities are also understood by the [Literal] constructor

```python
>>> from tripper import Literal
>>> literal = Literal(pressure)
>>> literal
Literal('101325 Pa', datatype='https://w3id.org/emmo#EMMO_799c067b_083f_4365_9452_1f1433b03676')

# Check the label of the datatype
>>> from tripper import EMMO
>>> EMMO._get_labels(literal.datatype)
['SIQuantityDatatype']

```

which uses the `emmo:SIQuantityDatatype` datatype.
The [Literal.value] property and [Literal.n3()] method can be used to convert back to a quantity or represent it in N3 notation:

```python
>>> literal = Literal(pressure)
>>> literal.value
<Quantity(101325, 'Pascal')>

>>> literal.n3()
'"101325 Pa"^^<https://w3id.org/emmo#EMMO_799c067b_083f_4365_9452_1f1433b03676>'

```

### Accessing quantities in a triplestore
Lets do a small calculation using the quantities constructed above:

```python
>>> mean_speed = length / time
>>> mean_speed
<Quantity(5.0, 'KiloMetre / Hour')>

```

and store our calculated `mean_speed` to a triplestore:

```python
>>> from tripper import EMMO, Triplestore
>>> ts = Triplestore(backend="rdflib")
>>> NS = ts.bind("", "http://example.com#")
>>> ureg.save_quantity(ts, mean_speed, iri=NS.MeanSpeed, type=EMMO.Speed)

```

Above we have created a new triplestore, bound empty prefix to the namespace
`http://example.com#` and saved the calculated `mean_speed` to a new individual
with IRI `http://example.com#MeanSpeed`.
The final `type` argument to [ureg.save_quantity()] states that our new individual
will be an individual of the class `emmo:Speed`.

The content of the triplestore is now

```python
>>> print(ts.serialize())
@prefix : <http://example.com#> .
@prefix emmo: <https://w3id.org/emmo#> .
<BLANKLINE>
:MeanSpeed a emmo:EMMO_81369540_1b0e_471b_9bae_6801af22800e ;
    emmo:EMMO_42806efc_581b_4ff8_81b0_b4d62153458b "5.0 km/h"^^emmo:EMMO_799c067b_083f_4365_9452_1f1433b03676 .
<BLANKLINE>
<BLANKLINE>

```

By default [ureg.save_quantity()] saves the quantity as an individual using the `emmo:SIQuantityDatatype` datatype.
But, the [ureg.save_quantity()] method has also options for saving the quantity as a class (argument `tbox=True`) or to represent the quantity using the `emmo:hasNumericalPart` and `emmo:hasReferencePart` properties (argument `si_datatype=False`).

Loading a quantity from the triplestore can be with [ureg.load_quantity()]:


```python
>>> q = ureg.load_quantity(ts, iri=NS.MeanSpeed)
>>> q
<Quantity(5.0, 'KiloMetre / Hour')>

```


Setting up custom unit registry
-------------------------------
You can extend the default set of units by creating a domain or application ontology with additional custom units.
It should import EMMO to get the default units.

Use the `url` and `name` options when instantiating the unit registry

```python
>>> ureg = UnitRegistry(url="http://custom.org/myunits.ttl", name="myunits-0.3.2")  # doctest: +SKIP

```

where `url` is the URL or file path to the ontology and `name` is a, preferred versioned, name for the custom ontology used for caching.

Typically you create the unit registry when initialising your application.
After creating it, you can call the [set_as_default()] method.


```python
>>> ureg.set_as_default()  # doctest: +ELLIPSIS
<tripper.units.units.UnitRegistry object at 0x...>

```

This will allow to retrieve the custom unit register from anywhere in your application using the [get_ureg()] function

```python
>>> from tripper.units import get_ureg
>>> ureg = get_ureg()

```


Tips & tricks
-------------
Tripper caches the ontology and [Pint] units definition file for performance reasons.
If the ontology has been updated, you may need to clear the cache.
That can either be done manually or by calling the [ureg.clear_cache()] method.

For manual deletion of the cache files, the cache directory can be found using the `ureg._tripper_cachedir` attribute.


[Working with quantities]: #working-with-quantities
[Accessing quantities in a triplestore]: #accessing-quantities-in-a-triplestore
[Setting up custom unit registry]: #setting-up-custom-unit-registry

[tripper.units]: ../api_reference/units/units.md
[UnitRegistry]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry
[get_unit()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.get_unit
[get_unit_info()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.get_unit_info
[load_quantity()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.load_quantity
[save_quantity()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.save_quantity
[clear_cache()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.clear_cache
[set_as_default()]:
../api_reference/units/units.md#tripper.units.units.UnitRegistry.set_as_default
[to_ontology_units()]:
../api_reference/units/units.md#tripper.units.units.UnitRegistry.Quantity.to_ontology_units
[ito_ontology_units()]:
../api_reference/units/units.md#tripper.units.units.UnitRegistry.Quantity.ito_ontology_units
[ureg.Unit()]:
../api_reference/units/units.md#tripper.units.units.UnitRegistry.Unit
[ureg.Quantity()]:
../api_reference/units/units.md#tripper.units.units.UnitRegistry.Quantity
[ureg.save_quantity()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.save_quantity
[ureg.load_quantity()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.load_quantity
[ureg.clear_cache()]: ../api_reference/units/units.md#tripper.units.units.UnitRegistry.clear_cache

[get_ureg()]: ../api_reference/units/units.md#tripper.units.units.get_ureg

[info]:
../api_reference/units/units.md#tripper.units.units.UnitRegistry.Unit.info

[Literal]: ../api_reference/literal.md#tripper.literal.Literal
[Literal.value]: ../api_reference/literal.md#tripper.literal.Literal.value
[Literal.n3()]: ../api_reference/literal.md#tripper.literal.Literal.n3

[Pint]: https://pint.readthedocs.io/en/
[EMMO]: https://github.com/emmo-repo/EMMO
[QUDT]: https://qudt.org/
[OM]: https://github.com/HajoRijgersberg/OM
[UCUM]: https://ucum.org/
[UNECE]: https://docs.peppol.eu/poacc/billing/3.0/2024-Q2/codelist/UNECERec20/

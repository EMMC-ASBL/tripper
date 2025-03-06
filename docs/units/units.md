Units and quantities
====================

The `tripper.units` subpackage provide support for using [Pint] to work with units and quantites defined in ontologies.

Currently, only [EMMO] and EMMO-based ontologies can be used as a source for units and quantities.
However, since [EMMO] include references to the [QUDT] and [OM] ontologies, it is also possible to work with IRIs for these ontologies as well.

!!! note

    Currently the support for [OM] is weak.  Improvements are planned.


Unit access
-----------
Create a [Pint] unit registry using [EMMO]:

```python
>>> from tripper.units import UnitRegistry
>>> ureg = UnitRegistry()
```

The registry provide attribute access to units based on their [EMMO] prefLabel or symbol.

```python
>>> ureg.Pascal
<Unit(Pascal')>

>>> ureg.Pa
<Unit(Pascal')>

```

By convention are [EMMO] units written in "CamelCase".
However, unit access also work with "snake_case":

```python
>>> ureg.pascal
<Unit(Pascal')>

>>> ureg.newton_square_metre
<Unit('NewtonSquareMetre')>

```

Item access creates a quantity representation:

```python
>>> ureg["Pa"]
<Quantity(1, 'Pascal')>

>>> ureg["N⋅m²"]
<Quantity(1, 'Newton * Metre ** 2')>

```

Tripper adds some extra functionality on top of [Pint].

The `ureg.get_unit()` method allows you to access units by name, symbol (by EMMO labels or [UCUM] symbol), IRI or unitCode ([UNECE] common code). their IRI (supporting [EMMO], [QUDT] and [OM]).

For example:

```python
>>> ureg.get_unit(name="Metre"):  # name
<Quantity(1, 'Metre')>

>>> ureg.get_unit(symbol="H/Ω"):  # EMMO symbol
<Quantity(1, 'HenryPerOhm')>

>>> ureg.get_unit(symbol="H.Ohm-1"):  # UCUM symbol
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

The `get_unit_info()` returns a dict with attribute access with description of the unit provided by the ontology.
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

For example:

```python
>>> info = ureg.CubicMetre.get_unit_info()
>>> info.name
'CubicMetre'

>>> info.dimensions
Dimension(T=0, L=3, M=0, I=0, H=0, N=0, J=0)

```


Working with quantities
-----------------------
Lets do a small calculation:

```python
>>> length = ureg.Quantity(6, "km")
>>> time = ureg.Quantity(1.2, "h")
>>> mean_velocity = length / time
>>> mean_velocity
<Quantity(5.0, 'kiloMetre / Hour')>

```


Tips & tricks
-------------
Tripper caches the ontology and [Pint] units definition file for performance reasons.
If the ontology has been updated, you may need to clear the cache.
That can either be done manually or by calling the `ureg.clear_cache()` method.

For manual deletion of the cache files, the cache directory can be found using the `ureg._tripper_cachedir` attribute.


[Pint]: https://pint.readthedocs.io/en/
[EMMO]: https://github.com/emmo-repo/EMMO
[QUDT]: https://qudt.org/
[OM]: https://github.com/HajoRijgersberg/OM
[UCUM]: https://ucum.org/
[UNECE]: https://docs.peppol.eu/poacc/billing/3.0/2024-Q2/codelist/UNECERec20/

# Validation
Below is a list of cases that can validate.

1. The object of an object property must be an IRI.

   > Validated by `tripper.store()`.

2. The object of a data property must be of the correct datatype.

   >

3. Conformance (or data constraints) specifying that individuals of a
   given class must (at least) have a given set of properties.

4. Consistency - that a reasoner would not infer any inconsistencies.

5. The type of the subject of object and data properties. This can not
   be done with JSON-LD, since the context lacks information about the
   domain. I think this is best done with SHACL (although the keywords
   file might be used as well).

6. The type of the object of object properties. Like for case 5, I
   think this is best done with SHACL.



```turtle
dcat:Dataset pink:mandatoryProperty (
    dcterms:title ,
    dcterms:license ,
    dcat:distribution
) .

```


Vihicle (hasWheel exactly 4 Wheel) or (hasWheel exactly 2 Wheel)

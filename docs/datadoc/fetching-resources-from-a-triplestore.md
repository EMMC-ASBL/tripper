Working with already documented resources
=========================================

The [tripper.datadoc] module also includes functionality for easy searching of the documented resources.

For these examples there must be a triplestore instance available, poplated with some data.
```python
>>> from tripper import Triplestore
>>> from tripper.datadoc import save_datadoc
>>> ts = Triplestore(backend="rdflib")
>>> save_datadoc(ts,"https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tests/input/semdata.yaml") # doctest: +ELLIPSIS
{'@graph': [...], ...}

```

Searching the knowledge base
----------------------------

### Get all IRIs of all datasets in the kb

```python
>>> from tripper.datadoc import search
>>> search(ts) # doctest: +ELLIPSIS
[...]

```

This will return a list of all datasets in the knowledge base.


### Search with filtering criteria

Before adding specific filtering criteria it is important to bind non-standard prefixes to corresponding namespaces (standard prefixes defined in the keywords file, like dcterms, dcat, etc do not need to be defined again):

```python
>>> DATA = ts.bind("data", "http://example.com/data#")
>>> MAT = ts.bind("mat", "http://example.com/materials#")

```

It is possible to search for instances of type `dcat:Dataset` in two ways:

```python
>>> search(ts, type="Dataset")  # doctest: +ELLIPSIS
[...]

>>> search(ts, type="dcat:Dataset")  # doctest: +ELLIPSIS
[...]

```
The first shortened version is only possible for [predefined keywords] that are specifically added in tripper.

Note that full iris (e.g. `http://www.w3.org/ns/dcat#Dataset`) are currently not supported.


You can also search for documented resources of other types or include more than one type in the search.
```python
>>> SEM = ts.bind("sem", "https://w3id.com/emmo/domain/sem/0.1#")
>>> search(ts, type="sem:SEMImage")  # doctest: +ELLIPSIS
[...]

>>> search(ts, type=["sem:SEMImage", "dcat:Dataset"])  # doctest: +ELLIPSIS
[...]

```


It is also possible to filter through other criteria:
```python
>>> search(ts, criteria={"creator.name": "Sigurd Wenner"})  # doctest: +ELLIPSIS
[...]

>>> search(ts, criteria={"creator.name": ["Sigurd Wenner", "Named Lab Assistant"]})  # doctest: +ELLIPSIS
[...]

>>> KB = ts.bind('kb', 'http://example.com/kb/' )
>>> search(ts, criteria={"@id": KB.image1}) # doctest: +ELLIPSIS
[...]

```

Note that here the object created when binding the `kb` prefix is a tripper.Namespace, and can be used directly as the second example above.

Fetching metadata and data
--------------------------

The `acquire` function can be used to fetch metadata from the triplestore.
```python
>>> from tripper.datadoc import acquire
>>> acquire(ts, 'https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001')  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
AttrDict({
    '@id': 'https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001',
    ...
})


```

Similarly the load function can be used to fetch the data using the information about the dowload URL in the metadata.
The syntax is the same as above. Note though that for this specific example you would need access to a server that
is not available to the general public.


Removing instances in the knowledge base
----------------------------------------

Be very careful when using this, as there is a high risk that you delete data from others if you have access to delete on a shared knowledge base.

The same criteria as shown above can be used e.g.:

```python
>>> from tripper.datadoc import delete
>>> delete(ts, criteria={"@id": KB.image1})
>>> delete(ts, criteria={"creator.name": "Sigurd Wenner"})

```
It is also possible to remove everything in the triplestore with `delete(ts)`, but this is strongly discouraged.



[predefined keywords]: keywords.md
[tripper.datadoc]: https://emmc-asbl.github.io/tripper/latest/datadoc/introduction

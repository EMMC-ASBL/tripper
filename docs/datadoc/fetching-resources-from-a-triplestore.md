Working with already documented resources
=========================================

The [tripper.datadoc] module also includes functionality for easy searching of the documented reseources.

For these examples there must be a triplestore instance available, poplated with some data.
```python
>>> from tripper import Triplestore
>>> from tripper.datadoc import save_datadoc
>>> ts = Triplestore(backend="rdflib")
>>> save_datadoc(ts,"https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tests/input/semdata.yaml")
```

Searching the knowledge base
----------------------------

### Get all IRIs of all datasets in the kb

```python
>>> from tripper.datadoc import search
>>> search(ts) # doctest: +SKIP
```

This will return a list of all datasets in the knowledge base.


### Search with filtering criteria

Before adding specific filtering criteria it is importa to bind prefixes to the triplestore instance:

```python
>>> ts.bind("dcat", "http://www.w3.org/ns/dcat#")
>>> ts.bind("dcterms", "http://purl.org/dc/terms/")  
```

It is possible to search for instances of type `dcat:Dataset` in two ways:

```python
>>> search(ts, type="Dataset") # doctest: +SKIP
>>> search(ts, type="dcat:Dataset") # doctest: +SKIP
```
The first shortened version is only possible for [predefined keywords] that are specifically added in tripper.
The binding of the `dcat` namespace is required first for both cases.

Note that full iris (e.g. `http://www.w3.org/ns/dcat#Dataset`) cannot be used currently.


You can then search for documented resources of other types or include more than one type in the search.
```python
>>> ts.bind("sem", "https://w3id.com/emmo/domain/sem/0.1#")
>>> search(ts, type="sem:SEMImage") # doctest: +SKIP
>>> search(ts, type=["sem:SEMImage", "dcat:Dataset"]) # doctest: +SKIP
```


It is also possible to filter through other criteria:
```python
>>> search(ts, criteria={"creator.name": "Sigurd Wenner"}) # doctest: +SKIP
>>> search(ts, criteria={"creator.name": ["Sigurd Wenner", "Named Lab Assistant"]}) # doctest: +SKIP
>>> KB = ts.bind('kb', 'http://example.com/kb/')
>>> search(ts, criteria={"@id": KB.image1}) # doctest: +SKIP
```

Note that here the object created when binding the `kb` prefixs is a tripper.namespace.Namespace, and can be used directly as the second example above.

Removing instances in the knowledge base
----------------------------------------

Be very careful when using this, as there is a high risk that you delete data from others if you have access to delete a shared knowledge base.

The same criteria as shown above can be used e.g.:

```python
>>> from tripper.datadoc import delete
>>> delete(ts, criteria={"@id": KB.image1})
>>> delete(ts, criteria={"creator.name": "Sigurd Wenner"})
```
It is also possible to remove everything in the triplestore with `delete(ts)`, but this is strongly discouraged.



[predefined keywords]: keywords.md
[tripper.datadoc]: https://emmc-asbl.github.io/tripper/latest/datadoc/introduction

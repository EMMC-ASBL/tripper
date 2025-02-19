# pylint: disable=line-too-long, too-many-lines
"""Module for documenting datasets with Tripper.

The dataset documentation follows the [DCAT] structure and is exposed
as Python dicts with attribute access in this module.  The semantic
meaning of the keywords in this dict are defined by a [JSON-LD context].

High-level function for populating the triplestore from YAML documentation:

  - `save_datadoc()`: Save documentation from YAML file to the triplestore.

Functions for searching the triplestore:

  - `search_iris()`: Get IRIs of matching entries in the triplestore.

Functions for working with the dict-representation:

  - `read_datadoc()`: Read documentation from YAML file and return it as dict.
  - `save_dict()`: Save dict documentation to the triplestore.
  - `load_dict()`: Load dict documentation from the triplestore.
  - `as_jsonld()`: Return the dict as JSON-LD (represented as a Python dict)

Functions for interaction with OTEAPI:

  - `get_partial_pipeline()`: Returns a OTELib partial pipeline.

---

[DCAT]: https://www.w3.org/TR/vocab-dcat-3/
[JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.2/context.json

"""

from __future__ import annotations

# pylint: disable=invalid-name,redefined-builtin,import-outside-toplevel
import io
import json
import re
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from tripper import DCAT, EMMO, OTEIO, OWL, RDF, Namespace, Triplestore
from tripper.utils import AttrDict, as_python, openfile

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Iterable, List, Mapping, Optional, Sequence, Union

    from tripper.utils import Triple

# Local path (for fast loading) and URL to the JSON-LD context
CONTEXT_PATH = (
    Path(__file__).parent.parent / "context" / "0.2" / "context.json"
)
CONTEXT_URL = (
    "https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/"
    "master/tripper/context/0.2/context.json"
)

MATCH_PREFIXED_IRI = re.compile(
    r"^([a-z0-9]*):([a-zA-Z_]([a-zA-Z0-9_/+-]*[a-zA-Z0-9_+-])?)$"
)

# Resource types
dicttypes = {
    "parser": {
        "datadoc_label": "parsers",
        "@type": OTEIO.Parser,
    },
    "generator": {
        "datadoc_label": "generators",
        "@type": OTEIO.Generator,
    },
    "accessService": {
        "datadoc_label": "dataServices",
        "@type": DCAT.DataService,
    },
    "distribution": {
        "datadoc_label": "distributions",
        "@type": DCAT.Distribution,
    },
    "dataset": {
        "datadoc_label": "datasets",
        "@type": [DCAT.Dataset, EMMO.Dataset],
    },
    "resource": {
        # General data resource
        # Ex: samples, instruments, models, people, projects, ...
        "datadoc_label": "resources",
        "@type": OWL.NamedIndividual,
    },
}


class InvalidKeywordError(KeyError):
    """Keyword is not defined."""


def save_dict(
    ts: Triplestore,
    dct: dict,
    type: "Optional[str]" = "dataset",
    prefixes: "Optional[dict]" = None,
    **kwargs,
) -> dict:
    # pylint: disable=line-too-long,too-many-branches
    """Save a dict representation of given type of data to a triplestore.

    Arguments:
        ts: Triplestore to save to.
        dct: Dict with data to save.
        type: Type of data to save.  Should either be one of the
            pre-defined names: "dataset", "distribution", "accessService",
            "parser" and "generator" or an IRI to a class in an ontology.
            Defaults to "dataset".
        prefixes: Dict with prefixes in addition to those included in the
            JSON-LD context.  Should map namespace prefixes to IRIs.
        kwargs: Additional keyword arguments to add to the returned dict.
            A leading underscore in a key will be translated to a
            leading "@"-sign.  For example, "@id=..." may be provided
            as "_id=...".

    Returns:
        An updated copy of `dct`.

    Notes:
        The keys in `dct` and `kwargs` may be either properties defined in the
        [JSON-LD context] or one of the following special keywords:

          - "@id": Dataset IRI.  Must always be given.
          - "@type": IRI of the ontology class for this type of data.
            For datasets, it is typically used to refer to a specific subclass
            of `emmo:Dataset` that provides a semantic description of this
            dataset.

    References:
    [JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/oteapi-dlite/refs/heads/rdf-serialisation/oteapi_dlite/context/0.2/context.json
    """
    if "@id" not in dct:
        raise ValueError("`dct` must have an '@id' key")

    all_prefixes = get_prefixes()
    all_prefixes.update(ts.namespaces)
    if prefixes:
        all_prefixes.update(prefixes)

    d = as_jsonld(dct=dct, type=type, prefixes=all_prefixes, **kwargs)

    # Bind prefixes
    for prefix, ns in all_prefixes.items():
        ts.bind(prefix, ns)

    # Write json-ld data to triplestore (using temporary rdflib triplestore)
    f = io.StringIO(json.dumps(d))
    with Triplestore(backend="rdflib") as ts2:
        ts2.parse(f, format="json-ld")
        ts.add_triples(ts2.triples())

    # Add statements and data models to triplestore
    save_extra_content(ts, d)

    return d


def save_extra_content(ts: Triplestore, dct: dict) -> None:
    """Save extra content in `dct` to the triplestore.

    Currently, this includes:
    - statements and mappings
    - data models (require that DLite is installed)

    Arguments:
        ts: Triplestore to load data from.
        dct: Dict in multi-resource format.

    """
    import requests

    # Save statements and mappings
    statements = get_values(dct, "statements")
    statements.extend(get_values(dct, "mappings"))
    if statements:
        ts.add_triples(statements)

    # Save data models
    datamodels = {
        d["@id"]: d["datamodel"]
        for d in dct.get("datasets", ())
        if "datamodel" in d
    }
    try:
        # pylint: disable=import-outside-toplevel
        import dlite
        from dlite.dataset import add_dataset
    except ModuleNotFoundError:
        if datamodels:
            warnings.warn(
                "dlite is not installed - data models will not be added to "
                "the triplestore"
            )
    else:
        for url in get_values(dct, "datamodelStorage"):
            dlite.storage_path.append(url)

        for iri, uri in datamodels.items():
            ok = False
            r = requests.get(uri, timeout=3)
            if r.ok:
                content = (
                    r.content.decode()
                    if isinstance(r.content, bytes)
                    else str(r.content)
                )
                dm = dlite.Instance.from_json(content)
                add_dataset(ts, dm)
                ok = True
            else:
                try:
                    dm = dlite.get_instance(uri)
                except (
                    dlite.DLiteMissingInstanceError  # pylint: disable=no-member
                ):
                    # __FIXME__: check session whether to warn or re-raise
                    warnings.warn(f"cannot load datamodel: {uri}")
                else:
                    add_dataset(ts, dm)
                    ok = True

            if ok:
                # Make our dataset an individual of the new dataset subclass
                # that we have created by serialising the datamodel
                ts.add((iri, RDF.type, uri))


def load_dict(
    ts: Triplestore, iri: str, use_sparql: "Optional[bool]" = None
) -> dict:
    """Load dict representation of data with given IRI from the triplestore.

    Arguments:
        ts: Triplestore to load data from.
        iri: IRI of the data to load.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to `ts.prefer_sparql`.

    Returns:
        Dict-representation of the loaded data.
    """
    if use_sparql is None:
        use_sparql = ts.prefer_sparql
    if use_sparql:
        return _load_sparql(ts, iri)

    nested = dicttypes.keys()
    d = AttrDict()
    dct = _load_triples(ts, iri)

    for k, v in dct.items():
        if k in nested:
            if not isinstance(v, list):
                v = [v]
            for vv in v:
                d[k] = load_dict(ts, iri=vv, use_sparql=use_sparql)
                add(d[k], "@type", dicttypes[k]["@type"])
        else:
            d[k] = v
    return d


def _load_triples(ts: Triplestore, iri: str) -> dict:
    """Load `iri` from triplestore by calling `ts.triples()`."""
    shortnames = get_shortnames()
    dct: dict = {}
    for p, o in ts.predicate_objects(ts.expand_iri(iri)):
        add(dct, shortnames.get(p, p), as_python(o))
    if dct:
        d = {"@id": iri}
        d.update(dct)
        return d
    return dct


def _load_sparql(ts: Triplestore, iri: str) -> dict:
    """Load `iri` from triplestore by calling `ts.query()`."""
    # The match-all pattern `(:|!:)*` in the query string below
    # ensures that the returned triples include nested structures,
    # like distributions in a dataset. However, it does not include
    # references to named resources, like parsers and generators.
    # This choice was made because it limits the number of returned triples.
    # The `recur()` function will load such named resources recursively.
    #
    # Note that this implementation completely avoids querying for
    # blank nodes.
    subj = iri if iri.startswith("_:") else f"<{iri}>"
    query = f"""
    PREFIX : <http://example.com#>
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
      {subj} (:|!:)* ?s .
      ?s ?p ?o .
    }}
    """
    nested = dicttypes.keys()

    def recur(d):
        """Recursively load and insert referred resources into dict `d`."""
        if isinstance(d, dict):
            for k, v in d.items():
                if k in nested:
                    val = v.get("@id")
                    if isinstance(val, str):
                        d[k] = load_dict(ts, val, use_sparql=True)
                    elif isinstance(v, (dict, list)):
                        recur(v)
        elif isinstance(d, list):
            for e in d:
                recur(e)

    triples = ts.query(query)
    with Triplestore(backend="rdflib") as ts2:
        ts2.add_triples(triples)  # type: ignore
        dct = load_dict(ts2, iri, use_sparql=False)
    recur(dct)
    return dct


def get_values(
    data: "Union[dict, list]", key: str, extend: bool = True
) -> list:
    """Parse `data` recursively and return a list with the values
    corresponding to the given key.

    If `extend` is true, the returned list will be extended with
    values that themselves are list, instead of appending them in a
    nested manner.

    """
    values = []
    if isinstance(data, dict):
        val = data.get(key)
        if extend and isinstance(val, list):
            values.extend(val)
        elif val:
            values.append(val)
        for k, v in data.items():
            if k != "@context" and isinstance(v, (dict, list)):
                values.extend(get_values(v, key))
    elif isinstance(data, list):
        for ele in data:
            if isinstance(ele, (dict, list)):
                values.extend(get_values(ele, key))
    return values


def get_jsonld_context(
    context: "Optional[Union[str, dict, Sequence[Union[str, dict]]]]" = None,
    timeout: float = 5,
    fromfile: bool = True,
) -> dict:
    """Returns the JSON-LD context as a dict.

    The JSON-LD context maps all the keywords that can be used as keys
    in the dict-representation of a dataset to properties defined in
    common vocabularies and ontologies.

    Arguments:
        context: Additional user-defined context that should be returned
            on top of the default context.  It may be a string with an URL
            to the user-defined context, a dict with the user-defined context
            or a sequence of strings and dicts.
        timeout: Number of seconds before timing out.
        fromfile: Whether to load the context from local file.

    """
    import requests

    if fromfile:
        with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
            ctx = json.load(f)["@context"]
    else:
        r = requests.get(CONTEXT_URL, allow_redirects=True, timeout=timeout)
        ctx = json.loads(r.content)["@context"]

    if isinstance(context, (str, dict)):
        context = [context]

    if context:
        for token in context:
            if isinstance(token, str):
                with openfile(token, timeout=timeout, mode="rt") as f:
                    content = f.read()
                ctx.update(json.loads(content)["@context"])
            elif isinstance(token, dict):
                ctx.update(token)
            else:
                raise TypeError(
                    "`context` must be a string (URL), dict or a sequence of "
                    f"strings and dicts.  Not '{type(token)}'"
                )

    return ctx


def get_prefixes(
    context: "Optional[Union[str, dict, Sequence[Union[str, dict]]]]" = None,
    timeout: float = 5,
    fromfile: bool = True,
) -> dict:
    """Loads the JSON-LD context and returns a dict mapping prefixes to
    their namespace URL.

    Arguments are passed to `get_jsonld_context()`.
    """
    ctx = get_jsonld_context(
        context=context, timeout=timeout, fromfile=fromfile
    )
    prefixes = {
        k: str(v)
        for k, v in ctx.items()
        if isinstance(v, (str, Namespace)) and str(v).endswith(("#", "/"))
    }
    return prefixes


def get_shortnames(
    context: "Optional[Union[str, dict, Sequence[Union[str, dict]]]]" = None,
    timeout: float = 5,
    fromfile: bool = True,
) -> dict:
    """Loads the JSON-LD context and returns a dict mapping IRIs to their
    short names defined in the context.

    Arguments are passed to `get_jsonld_context()`.
    """
    ctx = get_jsonld_context(
        context=context, timeout=timeout, fromfile=fromfile
    )
    prefixes = get_prefixes(context=ctx)
    shortnames = {
        expand_iri(v["@id"] if isinstance(v, dict) else v, prefixes): k
        for k, v in ctx.items()
        if (
            (isinstance(v, str) and not v.endswith(("#", "/")))
            or isinstance(v, dict)
        )
    }
    shortnames.setdefault(RDF.type, "@type")
    return shortnames


def load_list(ts: Triplestore, iri: str):
    """Load and return RDF list whose first node is `iri`."""
    lst = []
    for p, o in ts.predicate_objects(iri):
        if p == RDF.first:
            lst.append(o)
        elif p == RDF.rest:
            lst.extend(load_list(ts, o))
    return lst


def add(d: dict, key: str, value: "Any") -> None:
    """Append key-value pair to dict `d`.

    If `key` already exists in `d`, its value is converted to a list
    and `value` is appended to it.  `value` may also be a list. Values
    are not duplicated.

    """
    if key not in d:
        d[key] = value
    else:
        klst = d[key] if isinstance(d[key], list) else [d[key]]
        if isinstance(value, dict):
            v = klst if value in klst else klst + [value]
        else:
            vlst = value if isinstance(value, list) else [value]
            try:
                v = list(set(klst).union(vlst))
            except TypeError:  # klst contains unhashable dicts
                v = klst + [x for x in vlst if x not in klst]
        d[key] = (
            v[0]
            if len(v) == 1
            else sorted(
                # Sort dicts at end, by representing them with a huge
                # unicode character
                v,
                key=lambda x: "\uffff" if isinstance(x, dict) else x,
            )
        )


def addnested(
    d: "Union[dict, list]", key: str, value: "Any"
) -> "Union[dict, list]":
    """Like add(), but allows `key` to be a dot-separated list of sub-keys.
    Returns the updated `d`.

    Each sub-key will be added to `d` as a corresponding sub-dict.

    Example:

        >>> d = {}
        >>> addnested(d, "a.b.c", "val") == {'a': {'b': {'c': 'val'}}}
        True

    """
    if "." in key:
        first, rest = key.split(".", 1)
        if isinstance(d, list):
            for ele in d:
                if isinstance(ele, dict):
                    addnested(ele, key, value)
                    break
            else:
                d.append(addnested({}, key, value))
        elif first in d and isinstance(d[first], (dict, list)):
            addnested(d[first], rest, value)
        else:
            addnested(d, first, addnested(AttrDict(), rest, value))
    elif isinstance(d, list):
        for ele in d:
            if isinstance(ele, dict):
                add(ele, key, value)
                break
        else:
            d.append({key: value})
    else:
        add(d, key, value)
    return d


def get(
    d: dict, key: str, default: "Any" = None, aslist: bool = True
) -> "Any":
    """Like `d.get(key, default)` but returns the value as a list if
    `aslist` is True and value is not already a list.

    An empty list is returned in the special case that `key` is not in
    `d` and `default` is None.

    """
    value = d.get(key, default)
    if aslist:
        return (
            value
            if isinstance(value, list)
            else [] if value is None else [value]
        )
    return value


def expand_iri(iri: str, prefixes: dict) -> str:
    """Return the full IRI if `iri` is prefixed.  Otherwise `iri` is
    returned."""
    match = re.match(MATCH_PREFIXED_IRI, iri)
    if match:
        prefix, name, _ = match.groups()
        if prefix in prefixes:
            return f"{prefixes[prefix]}{name}"
        warnings.warn(f'Undefined prefix "{prefix}" in IRI: {iri}')
    return iri


def read_datadoc(filename: "Union[str, Path]") -> dict:
    """Read YAML data documentation and return it as a dict.

    The filename may also be an URL to a file accessible with HTTP GET.
    """
    import yaml  # type: ignore

    with openfile(filename, mode="rt", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return prepare_datadoc(d)


def save_datadoc(
    ts: Triplestore, file_or_dict: "Union[str, Path, dict]"
) -> dict:
    """Populate triplestore with data documentation.

    Arguments:
        ts: Triplestore to save dataset documentation to.
        file_or_dict: Data documentation dict or name of a YAML file to read
            the data documentation from.  It may also be an URL to a file
            accessible with HTTP GET.

    Returns:
        Dict-representation of the loaded dataset.
    """
    if isinstance(file_or_dict, dict):
        d = prepare_datadoc(file_or_dict)
    else:
        d = read_datadoc(file_or_dict)

    # Bind prefixes
    context = d.get("@context")
    prefixes = get_prefixes(context=context)
    prefixes.update(d.get("prefixes", {}))
    for prefix, ns in prefixes.items():  # type: ignore
        ts.bind(prefix, ns)

    # Maps datadoc_labels to type
    types = {v["datadoc_label"]: k for k, v in dicttypes.items()}

    # Write json-ld data to triplestore (using temporary rdflib triplestore)
    for spec in dicttypes.values():
        label = spec["datadoc_label"]
        for dct in get(d, label):
            dct = as_jsonld(
                dct=dct, type=types[label], prefixes=prefixes, _context=context
            )
            f = io.StringIO(json.dumps(dct))
            with Triplestore(backend="rdflib") as ts2:
                ts2.parse(f, format="json-ld")
                ts.add_triples(ts2.triples())

    # Add statements and datamodels to triplestore
    save_extra_content(ts, d)
    return d


def prepare_datadoc(datadoc: dict) -> dict:
    """Return an updated version of dict `datadoc` that is prepared with
    additional key-value pairs needed for creating valid JSON-LD that
    can be serialised to RDF.

    """
    d = AttrDict({"@context": CONTEXT_URL})
    d.update(datadoc)

    context = datadoc.get("@context")
    prefixes = get_prefixes(context=context)
    if "prefixes" in d:
        d.prefixes.update(prefixes)
    else:
        d.prefixes = prefixes.copy()

    for type, spec in dicttypes.items():
        label = spec["datadoc_label"]
        for i, dct in enumerate(get(d, label)):
            d[label][i] = as_jsonld(
                dct=dct, type=type, prefixes=d.prefixes, _context=context
            )

    return d


def as_jsonld(
    dct: dict,
    type: "Optional[str]" = "dataset",
    prefixes: "Optional[dict]" = None,
    **kwargs,
) -> dict:
    """Return an updated copy of dict `dct` as valid JSON-LD.

    Arguments:
        dct: Dict documenting a resource to be represented as JSON-LD.
        type: Type of data to document.  Should either be one of the
            pre-defined names: "dataset", "distribution", "accessService",
            "parser" and "generator" or an IRI to a class in an ontology.
            Defaults to "dataset".
        prefixes: Dict with prefixes in addition to those included in the
            JSON-LD context.  Should map namespace prefixes to IRIs.
        kwargs: Additional keyword arguments to add to the returned
            dict.  A leading underscore in a key will be translated to
            a leading "@"-sign.  For example, "@id", "@type" or
            "@context" may be provided as "_id" "_type" or "_context",
            respectively.

    Returns:
        An updated copy of `dct` as valid JSON-LD.

    """
    # pylint: disable=too-many-branches

    # Id of base entry that is documented
    _entryid = kwargs.pop("_entryid", None)

    context = kwargs.pop("_context", None)

    d = AttrDict()
    if not _entryid:
        d["@context"] = CONTEXT_URL
        if context:
            add(d, "@context", context)

    if type:
        t = dicttypes[type]["@type"] if type in dicttypes else type
        add(d, "@type", t)  # get type at top
        d.update(dct)
        add(d, "@type", t)  # readd type if overwritten
    else:
        d.update(dct)

    for k, v in kwargs.items():
        key = f"@{k[1:]}" if re.match("^_([^_]|([^_].*[^_]))$", k) else k
        add(d, key, v)

    if "@id" not in d and not _entryid:
        raise ValueError("Missing '@id' in dict to document")

    if not _entryid:
        _entryid = d["@id"]

    if "@type" not in d:
        warnings.warn(f"Missing '@type' in dict to document: {_entryid}")

    all_prefixes = get_prefixes(context=context)
    if prefixes:
        all_prefixes.update(prefixes)

    # Recursively expand IRIs and prepare sub-directories
    # Nested lists are not supported
    nested = dicttypes.keys()
    for k, v in d.items():
        if k == "mappingURL":
            for url in get(d, k):
                with Triplestore("rdflib") as ts2:
                    ts2.parse(url, format=d.get("mappingFormat"))
                    if "statements" in d:
                        d.statements.extend(ts2.triples())
                    else:
                        d["statements"] = list(ts2.triples())
        if k in ("statements", "mappings"):
            for i, spo in enumerate(d[k]):
                d[k][i] = [
                    (
                        get(d, e, e)[0]
                        if e.startswith("@")
                        else expand_iri(e, prefixes=all_prefixes)
                    )
                    for e in spo
                ]
        elif isinstance(v, str):
            d[k] = expand_iri(v, all_prefixes)
        elif isinstance(v, list):
            for i, e in enumerate(v):
                if isinstance(e, str):
                    v[i] = expand_iri(e, all_prefixes)
                elif isinstance(e, dict) and k in nested:
                    v[i] = as_jsonld(
                        e, k, _entryid=_entryid, prefixes=all_prefixes
                    )
        elif isinstance(v, dict) and k in nested:
            d[k] = as_jsonld(v, k, _entryid=_entryid, prefixes=all_prefixes)

    return d


def get_partial_pipeline(  # pylint: disable=too-many-positional-arguments
    ts: Triplestore,
    client,
    iri: str,
    parser: "Optional[Union[bool, str]]" = None,
    generator: "Optional[Union[bool, str]]" = None,
    distribution: "Optional[str]" = None,
    use_sparql: "Optional[bool]" = None,
) -> bytes:
    """Returns a OTELib partial pipeline.

    Arguments:
        ts: Triplestore to load data from.
        client: OTELib client to create pipeline with.
        iri: IRI of the dataset to load.
        parser: Whether to return a datasource partial pipeline.
            Should be True or an IRI of parser to use in case the
            distribution has multiple parsers.  By default the first
            parser will be selected.
        generator: Whether to return a datasink partial pipeline.
            Should be True or an IRI of generator to use in case the
            distribution has multiple generators.  By default the first
            generator will be selected.
        distribution: IRI of distribution to use in case the dataset
            dataset has multiple distributions.  By default any of
            the distributions will be picked.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to `ts.prefer_sparql`.

    Returns:
        OTELib partial pipeline.
    """
    # pylint: disable=too-many-branches
    dct = load_dict(ts, iri, use_sparql=use_sparql)

    if isinstance(distribution, str):
        for distr in get(dct, "distribution"):
            if distr["@id"] == distribution:
                break
        else:
            raise ValueError(
                f"dataset '{iri}' has no such distribution: {distribution}"
            )
    else:
        distr = get(dct, "distribution")[0]

    accessService = (
        distr.accessService.get("endpointURL")
        if "accessService" in distr
        else None
    )

    # OTEAPI still puts the parse configurations into the dataresource
    # instead of a in a separate parse strategy...
    if parser:
        if parser is True:
            par = get(distr, "parser")[0]
        elif isinstance(parser, str):
            for par in get(distr, "parser"):
                if par.get("@id") == parser:
                    break
            else:
                raise ValueError(
                    f"dataset '{iri}' has no such parser: {parser}"
                )
        configuration = par.get("configuration")
    else:
        configuration = None

    dataresource = client.create_dataresource(
        downloadUrl=distr.get("downloadURL"),
        mediaType=distr.get("mediaType"),
        accessUrl=distr.get("accessURL"),
        accessService=accessService,
        configuration=dict(configuration) if configuration else {},
    )

    statements = dct.get("statements", [])
    statements.extend(dct.get("mappings", []))
    if statements:
        mapping = client.create_mapping(
            mappingType="triples",
            # The OTEAPI datamodels stupidly strict, requireing us
            # to cast the data ts.namespaces and statements
            prefixes={k: str(v) for k, v in ts.namespaces.items()},
            triples=[tuple(t) for t in statements],
        )

    if parser:
        pipeline = dataresource
        if statements:
            pipeline = pipeline >> mapping
    elif generator:
        if generator is True:
            gen = get(distr, "generator")[0]
        elif isinstance(generator, str):
            for gen in get(distr, "generator"):
                if gen.get("@id") == generator:
                    break
            else:
                raise ValueError(
                    f"dataset '{iri}' has no such generator: {generator}"
                )

        conf = gen.get("configuration")
        if gen.generatorType == "application/vnd.dlite-generate":
            conf.setdefault("datamodel", dct.get("datamodel"))

        function = client.create_function(
            functionType=gen.generatorType,
            configuration=conf,
        )
        if statements:
            pipeline = mapping >> function >> dataresource
        else:
            pipeline = function >> dataresource

    return pipeline


def search_iris(
    ts: Triplestore,
    type=None,
    criterias: "Optional[dict]" = None,
    regex: "Optional[dict]" = None,
) -> "List[str]":
    """Return a list of IRIs for all matching resources.
    Additional matching criterias can be specified by `kwargs`.

    Arguments:
        ts: Triplestore to search.
        type: Either a [resource type] (ex: "dataset", "distribution", ...)
            or the IRI of a class to limit the search to.
        criterias: Exact match criterias. A dict of IRI, value pairs, where the
            IRIs refer to data properties on the resource match. The IRIs
            may use any prefix defined in `ts`. E.g. if the prefix `dcterms`
            is in `ts`, it is expanded and the match criteria `dcterms:title`
            is correctly parsed.
        regex: Like `criterias` but the values in the provided dict are regular
            expressions used for the matching.

    Returns:
        List of IRIs for matching resources.

    Examples:
        List all data resources IRIs:

            search_iris(ts)

        List IRIs of all resources with John Doe as `contactPoint`:

            search_iris(ts, criteria={"contactPoint": "John Doe"})

        List IRIs of all samples:

            search_iris(ts, type=CHAMEO.Sample)

        List IRIs of all datasets with John Doe as `contactPoint` AND are
        measured on a given sample:

            search_iris(
                ts,
                type=DCAT.Dataset,
                criteria={
                    "contactPoint": "John Doe",
                    "fromSample": SAMPLE.batch2/sample3,
                },
            )

        List IRIs of all datasets who's title matches the regular expression
        "[Mm]agnesium":

            search_iris(
                ts, type=DCAT.Dataset, regex={"title": "[Mm]agnesium"},
            )

    SeeAlso:
    [resource type]: https://emmc-asbl.github.io/tripper/latest/datadoc/introduction/#resource-types
    """
    if criterias is None:
        criterias = {}

    # Special handling of @id
    id = (
        criterias.pop("@id")
        if "@id" in criterias
        else criterias.pop("_id", None)
    )

    crit = []
    filters = []
    if type:
        if ":" in type:
            expanded = ts.expand_iri(type)
            crit.append(f"  ?iri rdf:type <{expanded}> .")
        elif type in dicttypes:
            types = dicttypes[type]["@type"]
            if isinstance(types, str):
                types = [types]
            for t in types:
                crit.append(f"  ?iri rdf:type <{t}> .")
        else:
            raise ValueError(
                "`type` must either be an IRI or the name of one the "
                f"resource types. Got: {type}"
            )

    else:
        crit.append("  ?iri rdf:type ?o .")

    n = 0  # variable no
    expanded = {v: k for k, v in get_shortnames().items()}

    def get_predicate_value(k, v):
        """Get value to match."""
        key = f"@{k[1:]}" if k.startswith("_") else k
        predicate = ts.expand_iri(key)
        if v in expanded:
            value = f"<{expanded[v]}>"
        elif isinstance(v, str):
            value = (
                f"<{v}>" if re.match("^[a-z][a-z0-9.+-]*://", v) else f'"{v}"'
            )
        else:
            value = v
        return predicate, value

    for k, v in criterias.items():
        predicate, value = get_predicate_value(k, v)
        crit.append(f"      ?iri <{predicate}> {value} .")

    if regex:
        for k, v in regex.items():
            n += 1
            var = f"v{n}"
            predicate, value = get_predicate_value(k, v)
            crit.append(f"      ?iri <{predicate}> ?{var} .")
            filters.append(f"      FILTER REGEX(str(?{var}), {value})")

    where_statements = "\n".join(crit + filters)
    query = f"""
    PREFIX rdf: <{RDF}>
    SELECT DISTINCT ?iri
    WHERE {{
    {where_statements}
    }}
    """
    return [r[0] for r in ts.query(query) if not id or r[0] == ts.expand_iri(id)]  # type: ignore

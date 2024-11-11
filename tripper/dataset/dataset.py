# pylint: disable=line-too-long
"""Module for documenting datasets with Tripper.

The dataset documentation follows the [DCAT] structure and is exposed
as Python dicts with attribute access in this module.  The semantic
meaning of the keywords in this dict are defined by a [JSON-LD context].

High-level functions for accessing and storing actual data:
  - `load()`: Load documented dataset from its source.
  - `save()`: Save documented dataset to a data resource.

High-level function for populating the triplestore from YAML documentation:
  - `save_datadoc()`: Save documentation from YAML file to the triplestore.

Functions for searching the triplestore:
  - `list_dataset_iris()`: Get IRIs of matching datasets.

Functions for working with the dict-representation:
  - `read_datadoc()`: Read documentation from YAML file and return it as dict.
  - `save_dict()`: Save dict documentation to the triplestore.
  - `load_dict()`: Load dict documentation from the triplestore.

Functions for interaction with OTEAPI:
  - `get_partial_pipeline()`: Returns a OTELib partial pipeline.

---

__TODO__: Update the URL to the JSON-LD context when merged to master

[DCAT]: https://www.w3.org/TR/vocab-dcat-3/
[JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/dataset/tripper/context/0.2/context.json

"""

# pylint: enable=line-too-long
# pylint: disable=invalid-name,redefined-builtin,import-outside-toplevel
import functools
import io
import json
import re
import secrets  # From Python 3.9 we could use random.randbytes(16).hex()
import warnings
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
import yaml  # type: ignore

from tripper import DCAT, OTEIO, RDF, Triplestore
from tripper.utils import AttrDict, as_python

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Iterable, List, Mapping, Optional, Sequence, Union

    from tripper.utils import Triple

# Cache decorator
cache = (
    functools.cache  # new in Python 3.9, smaller and faster than lru_cache()
    if hasattr(functools, "cache")
    else functools.lru_cache(maxsize=1)
)


# Pytest can't cope with this
# EMMO = Namespace(
#     iri="https://w3id.org/emmo#",
#     label_annotations=True,
#     check=True,
# )

CONTEXT_PATH = (
    Path(__file__).parent.parent / "context" / "0.2" / "context.json"
).as_uri()

# __TODO__: Update URI when merged to master
CONTEXT_URL = (
    "https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/"
    "dataset/tripper/context/0.2/context.json"
)

MATCH_PREFIXED_IRI = re.compile(
    r"^([a-z0-9]*):([a-zA-Z_]([a-zA-Z0-9_/+-]*[a-zA-Z0-9_+-])?)$"
)

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
        "@type": DCAT.Dataset,
        # "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    },
}


def save(
    ts: Triplestore,
    data: bytes,
    class_iri: "Optional[str]" = None,
    dataset: "Optional[Union[str, dict]]" = None,
    distribution: "Optional[Union[str, dict]]" = None,
    generator: "Optional[str]" = None,
    prefixes: "Optional[dict]" = None,
    use_sparql: "Optional[bool]" = None,
) -> str:
    """Saves data to a dataresource and document it in the triplestore.

    Arguments:
        ts: Triplestore to load data from.
        data: Bytes representation of the data to save.
        class_iri: IRI of a class in the ontology (e.g. an `emmo:DataSet`
            subclass) that describes the dataset that is saved.
            Is used to select the `distribution` if that is not given.
            If `distribution` is also given, a
            `dcat:distribution value <distribution>` restriction will be
            added to `class_iri`
        dataset: Either the IRI of the dataset individual standing for
            the data to be saved or or a dict with additional
            documentation of the dataset.
            If the dataset already exists, a new distribution will be added
            to it. Otherwise a new random blank node IRI will be created.
        distribution: IRI of distribution for the data to be saved.
            Or a dict additional documentation of the distribution,
            like media type, parsers, generators etc...
        generator: Name of generator to use in case the distribution has
            several generators.
        prefixes: Dict with prefixes in addition to those included in the
            context.  Should map namespace prefixes to IRIs.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to `ts.prefer_sparql`.

    Returns:
        IRI of the dataset.

    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    # Use the Protocol plugin system from DLite.  Should we move it to tripper?
    from dlite.protocol import Protocol

    triples = []
    save_dataset = save_distribution = False

    if dataset is None:
        # __TODO__: Infer dataset from value restriction on `class_iri`
        # This require that we make a SPARQL-version of ts.restriction().
        newiri = f"_:N{secrets.token_hex(16)}"
        typeiri = [DCAT.Dataset, class_iri] if class_iri else DCAT.Dataset
        dataset = AttrDict({"@id": newiri, "@type": typeiri})
        save_dataset = True
    elif isinstance(dataset, str):
        dset = load_dict(ts, iri=dataset, use_sparql=use_sparql)
        if dset:
            dataset = dset
        else:
            typeiri = [DCAT.Dataset, class_iri] if class_iri else DCAT.Dataset
            dataset = AttrDict({"@id": dataset, "@type": typeiri})
            save_dataset = True
    elif isinstance(dataset, dict):
        save_dataset = True
    else:
        raise TypeError(
            "if given, `dataset` should be either a string or dict"
        )
    dataset: dict  # Tell mypy that this now is a dict

    if distribution is None:
        if "distribution" in dataset:
            distribution = get(dataset, "distribution")[0]
        else:
            newiri = f"_:N{secrets.token_hex(16)}"
            distribution = AttrDict(
                {"@id": newiri, "@type": DCAT.Distribution}
            )
            add(dataset, "distribution", distribution)
            triples.append((dataset["@id"], DCAT.distribution, newiri))
            save_distribution = True
    if isinstance(distribution, str):
        distr = load_dict(ts, iri=distribution, use_sparql=use_sparql)
        if distr:
            distribution = distr
        else:
            distribution = AttrDict(
                {"@id": distribution, "@type": DCAT.Distribution}
            )
            add(dataset, "distribution", distribution)
            triples.append((dataset["@id"], DCAT.distribution, newiri))
            save_distribution = True
    elif isinstance(distribution, dict):
        add(dataset, DCAT.distribution, distribution)
        if "@id" in distribution:
            triples.append(
                (dataset["@id"], DCAT.distribution, distribution["@id"])
            )
        save_distribution = True
    else:
        raise TypeError(
            "if given, `distribution` should be either a string or dict"
        )
    distribution: dict  # Tell mypy that this now is a dict

    if isinstance(generator, str):
        for gen in get(distribution, "generator"):
            if gen.get("@id") == generator:
                break
        else:
            raise ValueError(
                f"dataset '{dataset}' has no such generator: {generator}"
            )
    elif "generator" in distribution:
        gen = get(distribution, "generator")[0]
    else:
        gen = None

    # __TODO__: Check if `class_iri` already has the value restriction.
    # If not, add it to triples

    # __TODO__: Move this mapping of supported schemes into the protocol
    # module.
    schemes = {
        "https": "http",
    }

    # Save data
    url = distribution.get("downloadURL", distribution.get("accessURL"))
    p = urlparse(url)
    scheme = schemes.get(p.scheme, p.scheme) if p.scheme else "file"
    location = (
        f"{scheme}://{p.netloc}{p.path}" if p.netloc else f"{scheme}:{p.path}"
    )
    options = [p.query] if p.query else []
    if gen and "configuration" in gen and "options" in gen.configuration:
        # __TODO__: allow options to also be a dict
        options.append(gen.configuration["options"])
    id = (
        distribution["accessService"].get("identifier")
        if "accessService" in distribution
        else None
    )
    with Protocol(scheme, location, options=";".join(options)) as pr:
        pr.save(data, id)

    # Update triplestore
    ts.add_triples(triples)
    if save_dataset:
        save_dict(ts, "dataset", dataset, prefixes=prefixes)
    elif save_distribution:
        save_dict(ts, "distribution", distribution, prefixes=prefixes)

    return dataset["@id"]


def load(
    ts: Triplestore,
    iri: str,
    distributions: "Optional[Union[str, Sequence[str]]]" = None,
    use_sparql: "Optional[bool]" = None,
) -> bytes:
    """Load dataset with given IRI from its source.

    Arguments:
        ts: Triplestore to load data from.
        iri: IRI of the data to load.
        distributions: Name or sequence of names of distribution(s) to
            try in case the dataset has multiple distributions.  The
            default is to try all documented distributions.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to `ts.prefer_sparql`.

    Returns:
        Bytes object with the underlying data.

    Note:
        For now this requires DLite.
    """
    # Use the Protocol plugin system from DLite.  Should we move it to tripper?
    import dlite
    from dlite.protocol import Protocol

    dct = load_dict(ts, iri=iri, use_sparql=use_sparql)
    if DCAT.Dataset not in get(dct, "@type"):
        raise TypeError(
            f"expected IRI '{iri}' to be a dataset, but got: "
            f"{', '.join(get(dct, '@type'))}"
        )

    if distributions is None:
        distributions = get(dct, "distribution")

    for dist in distributions:
        url = dist.get("downloadURL", dist.get("accessURL"))  # type: ignore
        if url:
            p = urlparse(url)
            # Mapping of supported schemes - should be moved into the protocol
            # module.
            schemes = {
                "https": "http",
            }
            scheme = schemes.get(p.scheme, p.scheme) if p.scheme else "file"
            location = (
                f"{scheme}://{p.netloc}{p.path}"
                if p.netloc
                else f"{scheme}:{p.path}"
            )
            id = (
                dist.accessService.get("identifier")  # type: ignore
                if "accessService" in dist
                else None
            )
            try:
                with Protocol(scheme, location, options=p.query) as pr:
                    return pr.load(id)
                # pylint: disable=no-member
            except (dlite.DLiteProtocolError, dlite.DLiteIOError):
                pass

    raise IOError(f"Cannot access dataset: {iri}")


def save_dict(
    ts: Triplestore,
    type: str,
    dct: dict,
    prefixes: "Optional[dict]" = None,
    **kwargs,
) -> dict:
    # pylint: disable=line-too-long,too-many-branches
    """Save a dict representation of given type of data to a triplestore.

    Arguments:
        ts: Triplestore to save to.
        type: Type of dict to save.  Should be one of: "dataset",
            "distribution", "parser" or "generator".
        dct: Dict with data to save.
        prefixes: Dict with prefixes in addition to those included in the
            context.  Should map namespace prefixes to IRIs.
        kwargs: Additional keyword arguments to add to the returned dict.
            A leading underscore in a key will be translated to a
            leading "@"-sign.  For example, "@id=..." may be provided
            as "_id=...".

    Returns:
        An updated copy of `dct`.

    Notes:
        The keys in `dct` and `kwargs` may be either properties defined in the
        [JSON-LD context](https://raw.githubusercontent.com/EMMC-ASBL/oteapi-dlite/refs/heads/rdf-serialisation/oteapi_dlite/context/0.2/context.json)
        or one of the following special keywords:
          - "@id": Dataset IRI.  Must always be given.
          - "@type": IRI of the ontology class for this type of data.
            For datasets, it is typically used to refer to a specific subclass
            of `emmo:DataSet` that provides a semantic description of this
            dataset.

    """
    if "@id" not in dct:
        raise ValueError("`dct` must have an '@id' key")

    all_prefixes = get_prefixes()
    if prefixes:
        all_prefixes.update(prefixes)

    d = prepare(type=type, dct=dct, prefixes=all_prefixes, kwargs=kwargs)

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

    Currently, this include:
    - statements and mappings
    - data models (require that DLite is installed)

    """
    # Save statements and mappings
    statements = get_values(dct, "statements")
    statements.extend(get_values(dct, "mappings"))
    ts.add_triples(statements)

    # Save data models
    datamodels = get_values(dct, "datamodel")
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

        for uri in datamodels:
            r = requests.get(uri, timeout=3)
            if r.ok:
                dm = dlite.Instance.from_json(r.content)
                add_dataset(ts, dm)
            else:
                try:
                    dm = dlite.get_instance(uri)
                except (
                    dlite.DLiteMissingInstanceError  # pylint: disable=no-member
                ):
                    # __FIXME__: check session whether want to warn or re-reise
                    # in this case
                    warnings.warn(f"cannot load datamodel: {uri}")
                else:
                    add_dataset(ts, dm)


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
            d[k] = load_dict(ts, iri=v, use_sparql=use_sparql)
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
    # ensures that the returned triples includes nested structures,
    # like distributions in a dataset. However, it does not include
    # references to named resources, like parsers and generators.
    # This is good, because it limits the number of returned triples.
    # The `recur()` function will load such named resources recursively.
    #
    # Note that this implementation completely avoid querying for
    # blank nodes, which avoids problems with backends that renames
    # blank nodes.
    subj = iri if iri.startswith("_:") else f"<{iri}>"
    query = f"""
    PREFIX : <http://example.com#>
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
      {subj} (:|!:)* ?o .
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
        for v in data.values():
            if isinstance(v, (dict, list)):
                values.extend(get_values(v, key))
    elif isinstance(data, list):
        for ele in data:
            if isinstance(ele, (dict, list)):
                values.extend(get_values(ele, key))
    return values


@cache  # type: ignore
def get_context(timeout: float = 5, fromfile: bool = True) -> dict:
    """Return context as a dict.

    Arguments:
        timeout: Number of seconds before timing out.
        fromfile: Whether to load the context from local file.

    Whether to read the context from file."""
    if fromfile:
        with open(CONTEXT_PATH[7:], "r", encoding="utf-8") as f:
            context = json.load(f)["@context"]
    else:
        r = requests.get(CONTEXT_URL, allow_redirects=True, timeout=timeout)
        context = json.loads(r.content)["@context"]
    return context


def get_prefixes(timeout: float = 5) -> dict:
    """Loads the context and returns a dict mapping prefixes to
    their namespace URL."""
    context = get_context(timeout=timeout)
    prefixes = {
        k: v
        for k, v in context.items()
        if isinstance(v, str) and v.endswith(("#", "/"))
    }
    return prefixes


def get_shortnames(timeout: float = 5) -> dict:
    """Loads the context and returns a dict mapping IRIs to their
    short names defined in the context."""
    context = get_context(timeout=timeout)
    prefixes = get_prefixes()
    shortnames = {
        expand_iri(v["@id"] if isinstance(v, dict) else v, prefixes): k
        for k, v in context.items()
        if (
            (isinstance(v, str) and not v.endswith(("#", "/")))
            or isinstance(v, dict)
        )
    }
    shortnames.setdefault(RDF.type, "@type")
    return shortnames


def load_list(ts: Triplestore, iri: str):
    """Load and return RDF list whos first node is `iri`."""
    lst = []
    for p, o in ts.predicate_objects(iri):
        if p == RDF.first:
            lst.append(o)
        elif p == RDF.rest:
            lst.extend(load_list(ts, o))
    return lst


def add(d: dict, key: str, value: "Any") -> None:
    """Append key-value pair to dict `d`.

    If `key` already exists in `d`, its value is converted to a list and
    `value` is appended to it.  Values are not duplicated.
    """
    if key not in d:
        d[key] = value
    else:
        klst = d[key] if isinstance(d[key], list) else [d[key]]
        vlst = value if isinstance(value, list) else [value]
        v = list(set(klst).union(vlst))
        d[key] = v[0] if len(v) == 1 else sorted(v)


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
    """Read YAML data documentation and return it as a dict."""
    with open(filename, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return prepare_datadoc(d)


def save_datadoc(
    ts: Triplestore, file_or_dict: "Union[str, Path, dict]"
) -> dict:
    """Populate triplestore with data documentation.

    Arguments:
        ts: Triplestore to load dataset from.
        file_or_dict: Data documentation dict or name of a YAML file to read
            the data documentation from.

    Returns:
        Dict-representation of the loaded dataset.
    """
    if isinstance(file_or_dict, dict):
        d = prepare_datadoc(file_or_dict)
    else:
        d = read_datadoc(file_or_dict)

    # Bind prefixes
    prefixes = get_prefixes()
    prefixes.update(d.get("prefixes", {}))
    for prefix, ns in prefixes.items():  # type: ignore
        ts.bind(prefix, ns)

    # Maps datadoc_labels to type
    types = {v["datadoc_label"]: k for k, v in dicttypes.items()}

    # Write json-ld data to triplestore (using temporary rdflib triplestore)
    for spec in dicttypes.values():
        label = spec["datadoc_label"]
        for dct in get(d, label):
            dct = prepare(types[label], dct, prefixes=prefixes)
            f = io.StringIO(json.dumps(dct))
            with Triplestore(backend="rdflib") as ts2:
                ts2.parse(f, format="json-ld")
                ts.add_triples(ts2.triples())

    # Add statements and datamodels to triplestore
    save_extra_content(ts, d)
    return d


def prepare_datadoc(datadoc: dict) -> dict:
    """Return an updated version of dict `datadoc` that is prepared for
    serialisation to RDF."""
    d = AttrDict({"@context": CONTEXT_URL})
    d.update(datadoc)

    prefixes = get_prefixes()
    if "prefixes" in d:
        d.prefixes.update(prefixes)
    else:
        d.prefixes = prefixes.copy()

    for type, spec in dicttypes.items():
        label = spec["datadoc_label"]
        for i, dct in enumerate(get(d, label)):
            d[label][i] = prepare(type, dct, prefixes=d.prefixes)

    return d


def prepare(type: str, dct: dict, prefixes: dict, **kwargs) -> dict:
    """Return an updated copy of dict `dct` with additional key-value
    pairs needed for serialisation to RDF.

    Arguments:
        type: Type of dict to prepare.  Should be one of: "dataset",
            "distribution", "parser" or "generator".
        dct: Dict to return an updated copy of.
        prefixes: Dict with prefixes in addition to those included in the
            context.  Should map namespace prefixes to IRIs.
        kwargs: Additional keyword arguments to add to the returned dict.
            A leading underscore in a key will be translated to a
            leading "@"-sign.  For example, "@id=..." may be provided
            as "_id=...".

    Returns:
        An updated copy of `dct`.
    """
    # pylint: disable=too-many-branches
    if type not in dicttypes:
        raise ValueError(
            f"`type` must be one of: {', '.join(dicttypes.keys())}. "
            f"Got: '{type}'"
        )
    spec = dicttypes[type]

    d = AttrDict({"@context": CONTEXT_URL})
    add(d, "@type", spec["@type"])  # get type at top
    d.update(dct)
    add(d, "@type", spec["@type"])  # readd type if overwritten

    for k, v in kwargs.items():
        key = f"@{k[1:]}" if re.match("^_([^_]|([^_].*[^_]))$", k) else k
        add(d, key, v)

    all_prefixes = get_prefixes()
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
                    v[i] = prepare(k, e, prefixes=prefixes)
        elif isinstance(v, dict) and k in nested:
            d[k] = prepare(k, v, prefixes=prefixes)

    return d


def get_partial_pipeline(
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


def list_dataset_iris(ts: Triplestore, **kwargs):
    """Return a list of IRIs for all datasets matching a set of criterias
    specified by `kwargs`.

    Arguments:
        ts: Triplestore to search.
        kwargs: Match criterias.
    """
    crit = []
    expanded = {v: k for k, v in get_shortnames().items()}
    for k, v in kwargs.items():
        key = f"@{k[1:]}" if k.startswith("_") else k
        predicate = expanded[key]
        if v in expanded:
            value = f"<{expanded[v]}>"
        elif isinstance(v, str):
            value = (
                f"<{v}>" if re.match("^[a-z][a-z0-9.+-]*://", v) else f'"{v}"'
            )
        else:
            value = v
        crit.append(f"  ?dataset <{predicate}> {value} .")
    criterias = "\n".join(crit)
    query = f"""
    PREFIX rdf: <{RDF}>
    PREFIX dcat: <{DCAT}>
    SELECT ?dataset
    WHERE {{
      ?dataset rdf:type dcat:Dataset .
    {criterias}
    }}
    """
    return [r[0] for r in ts.query(query)]  # type: ignore

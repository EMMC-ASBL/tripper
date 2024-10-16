"""Module for documenting datasets with Tripper."""

# pylint: disable=invalid-name,redefined-builtin
import functools
import io
import json
import re
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

import requests
import yaml  # type: ignore

from tripper import DCAT, OTEIO, RDF, Triplestore
from tripper.utils import AttrDict, as_python

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Iterable, List, Mapping, Optional, Union

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
    "dataset": {
        "datadoc_label": "datasets",
        "@type": DCAT.Dataset,
        # "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    },
    "distribution": {
        "datadoc_label": "distributions",
        "@type": DCAT.Distribution,
    },
    "parser": {
        "datadoc_label": "parsers",
        "@type": OTEIO.Parser,
    },
    "generator": {
        "datadoc_label": "generators",
        "@type": OTEIO.Generator,
    },
}


def save(
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

    return d


def load(
    ts: Triplestore, iri: str, use_sparql: "Optional[bool]" = None
) -> dict:
    """Load data from triplestore.

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
    dct = _load_sparql(ts, iri) if use_sparql else _load_triples(ts, iri)

    nested = ("distribution", "parser", "generator", "mapping")
    d = AttrDict()
    dct = _load_sparql(ts, iri) if use_sparql else _load_triples(ts, iri)
    for k, v in dct.items():
        if k in nested:
            d[k] = load(ts, iri=v, use_sparql=use_sparql)
        else:
            d[k] = v
    return d


def _load_triples(ts: Triplestore, iri: str) -> dict:
    """Load `iri` from triplestore by calling `ts.triples()`."""
    shortnames = get_shortnames()
    d = {} if iri.startswith("_:") else {"@id": iri}
    for p, o in ts.predicate_objects(ts.expand_iri(iri)):
        add(d, shortnames.get(p, p), as_python(o))
    return d


def _load_sparql(ts: Triplestore, iri: str) -> dict:
    """Load `iri` from triplestore by calling `ts.query()`."""
    subj = iri if iri.startswith("_:") else f"<{iri}>"
    query = f"""
    PREFIX : <http://example.com#>
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
      {subj} (:|!:)* ?o .
      ?s ?p ?o .
    }}
    """
    triples = ts.query(query)
    with Triplestore(backend="rdflib") as ts2:
        ts2.add_triples(triples)  # type: ignore
        return _load_triples(ts2, iri)


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
        expand_iri(v, prefixes): k
        for k, v in context.items()
        if isinstance(v, str) and not v.endswith(("#", "/"))
    }
    shortnames.setdefault(RDF.type, "@type")
    shortnames.setdefault(OTEIO.prefix, "prefixes")
    shortnames.setdefault(OTEIO.hasConfiguration, "configuration")
    shortnames.setdefault(OTEIO.statement, "statements")
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


def expand_prefixes(obj: "Union[dict, list]", prefixes: dict) -> None:
    """Recursively expand IRI prefixes in the values of dict `d`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                obj[k] = expand_iri(v, prefixes)
            elif isinstance(v, (dict, list)):
                expand_prefixes(v, prefixes)
    elif isinstance(obj, list):
        for i, e in enumerate(obj):
            if isinstance(e, str):
                obj[i] = expand_iri(e, prefixes)
            elif isinstance(e, (dict, list)):
                expand_prefixes(e, prefixes)


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
    for prefix, ns in d.prefixes.items():  # type: ignore
        ts.bind(prefix, ns)

    # Write json-ld data to triplestore (using temporary rdflib triplestore)
    for spec in dicttypes.values():
        label = spec["datadoc_label"]
        for dct in get(d, label):
            f = io.StringIO(json.dumps(dct))
            with Triplestore(backend="rdflib") as ts2:
                ts2.parse(f, format="json-ld")
                ts.add_triples(ts2.triples())

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
    if type not in dicttypes:
        raise ValueError(
            f"`type` must be one of: {', '.join(dicttypes.keys())}"
        )
    spec = dicttypes[type]

    d = AttrDict({"@context": CONTEXT_URL})
    d.update(dct)
    add(d, "@type", spec["@type"])
    for k, v in kwargs.items():
        key = f"@{k[1:]}" if re.match("^_([^_]|([^_].*[^_]))$", k) else k
        add(d, key, v)

    all_prefixes = get_prefixes()
    if prefixes:
        all_prefixes.update(prefixes)
    expand_prefixes(d, all_prefixes)

    return d

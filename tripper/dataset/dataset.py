"""Module for documenting datasets with Tripper."""

# pylint: disable=invalid-name
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
from tripper.utils import as_python

# from tripper.errors import NamespaceError
# from tripper.utils import parse_literal

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
    "https://raw.githubusercontent.com/EMMC-ASBL/oteapi-dlite/refs/heads/"
    "rdf-serialisation/oteapi_dlite/context/0.2/context.json"
)
# CONTEXT_URL = "file:tripper/context/0.2/context.json"


_MATCH_PREFIXED_IRI = re.compile(r"^([a-z0-9]*):([a-zA-Z_][a-zA-Z0-9_+-]*)$")

DataSet = "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a"


def save_dataset(
    ts: Triplestore,
    dataset: "Union[dict, str]",
    distribution: "Optional[Union[dict, List[dict]]]" = None,
    datasink: "Optional[Union[dict, List[dict]]]" = None,
    prefixes: "Optional[dict]" = None,
) -> dict:
    # pylint: disable=line-too-long,too-many-branches
    """Save a dict representation of dataset documentation to a triplestore.

    Arguments:
        ts: Triplestore to save to.
        dataset: A dict documenting a new dataset or an IRI referring to an
            existing dataset.

            If this is a dict, the keys may be either properties of
            [dcat:Dataset](https://www.w3.org/TR/vocab-dcat-3/#Class:Dataset)
            (without the prefix) or one of the following keywords:
              - "@id": Dataset IRI.  Must always be given.
              - "@type": IRI of a specific dataset subclass. Typically is used
                to refer to a specific subclass of `emmo:DataSet`, providing a
                semantic description of this dataset.
        distribution: A dict or a list of dicts documenting specific
            realisations of the dataset.  The keys may be either properties of
            [dcat:Distribution](https://www.w3.org/TR/vocab-dcat-3/#Class:Distribution)
            (not prefixed with a namespace) or any of the following keys:
               - "@id": Distribution IRI. Must always be given.
               - "parser": Sub-dict documenting an OTEAPI parser.
               - "mapping": Sub-dict documenting OTEAPI mappings.
        datasink: A dict or a list of dicts documenting specific  sink for this
            dataset.
        prefixes: Namespace prefixes that should be recognised as values.

    Returns:
        Updated copy of `dataset`.

    SeeAlso:
        __TODO__: add URL to further documentation and examples.
    """
    if isinstance(dataset, str):
        dataset = load_dataset(ts, dataset)
    else:
        dataset = dataset.copy()

    if "@id" not in dataset:
        raise ValueError("dataset must have an '@id' key")

    add(dataset, "@context", CONTEXT_URL)

    # Add distribution and datasink
    for k, v, type_ in [
        ("distribution", distribution, DCAT.Distribution),
        ("datasink", datasink, OTEIO.DataSink),
    ]:
        if v:
            add(dataset, k, v)
        if k in dataset:
            if isinstance(dataset[k], list):
                for d in dataset[k]:
                    add(d, "@type", type_)
            else:
                add(dataset[k], "@type", type_)

    # Expand prefixes
    _expand_prefixes(dataset, prefixes if prefixes else {})

    # Append dcat:Dataset to @type
    add(dataset, "@type", DCAT.Dataset)

    # Bind prefixes
    default_prefixes = get_prefixes()
    if prefixes:
        default_prefixes.update(prefixes)
    for prefix, ns in default_prefixes.items():
        ts.bind(prefix, ns)

    # Write json-ld data to temporary rdflib triplestore
    f = io.StringIO(json.dumps(dataset))
    ts2 = Triplestore(backend="rdflib")
    ts2.parse(f, format="json-ld")

    # Add triples from temporary triplestore
    ts.add_triples(ts2.triples())
    ts2.close()  # explicit close ts2

    return dataset


def load_dataset(ts: Triplestore, iri: str) -> dict:
    """Load dataset from triplestore.

    Arguments:
        ts: Triplestore to load dataset from.
        iri: IRI of the dataset to load.

    Returns:
        Dict-representation of the loaded dataset.
    """
    context = get_context()
    shortnames = get_shortnames()

    dataset: dict = {}
    for p, o in ts.predicate_objects(ts.expand_iri(iri)):
        add(dataset, shortnames.get(p, p), as_python(o))
    _update_dataset(ts, iri, dataset, context, shortnames)
    add(dataset, "@id", iri)

    return dataset


def load_dataset_sparql(ts: Triplestore, iri: str) -> dict:
    """Like load_dataset(), but queries the triplestore with SPARQL.

    Arguments:
        ts: Triplestore to load dataset from.
        iri: IRI of the dataset to load.

    Returns:
        Dict-representation of the loaded dataset.
    """
    query = f"""
    PREFIX : <http://example.com#>
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
      <{iri}> (:|!:)* ?o .
      ?s ?p ?o .
    }}
    """
    triples = ts.query(query)
    ts2 = Triplestore(backend="rdflib")
    ts2.add_triples(triples)  # type: ignore
    dataset = load_dataset(ts2, iri)
    ts2.close()
    return dataset


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
        _expand_prefix(v, prefixes): k
        for k, v in context.items()
        if isinstance(v, str) and not v.endswith(("#", "/"))
    }
    shortnames.setdefault(RDF.type, "@type")
    shortnames.setdefault(OTEIO.prefix, "prefixes")
    shortnames.setdefault(OTEIO.hasConfiguration, "configuration")
    shortnames.setdefault(OTEIO.statement, "statements")
    return shortnames


def _expand_prefix(s: str, prefixes: dict) -> str:
    """Replace prefix in s."""
    for prefix, ns in prefixes.items():
        s = re.sub(f"^{prefix}:", ns, s, count=1)
    return s


def _update_dataset(
    ts: Triplestore, iri: str, dct: dict, context: dict, shortnames: dict
) -> None:
    """Recursively update dict-representation of dataset."""
    nested = ("distribution", "datasink", "parser", "generator", "mapping")

    for name in nested:
        if name in dct:
            v = dct[name] if isinstance(dct[name], list) else [dct[name]]
            for i, node in enumerate(v):
                d: dict = {}
                for p, o in ts.predicate_objects(ts.expand_iri(node)):
                    add(d, shortnames.get(p, p), as_python(o))
                if isinstance(dct[name], list):
                    dct[name][i] = d
                else:
                    dct[name] = d
                _update_dataset(ts, node, d, context, shortnames)

    # Special handling of statements
    if "statements" in dct:
        (iri,) = ts.objects(predicate=OTEIO.statement)
        dct["statements"] = load_statements(ts, iri)


def load_list(ts: Triplestore, iri: str):
    """Load and return RDF list whos first node is `iri`."""
    lst = []
    for p, o in ts.predicate_objects(iri):
        if p == RDF.first:
            lst.append(o)
        elif p == RDF.rest:
            lst.extend(load_list(ts, o))
    return lst


def load_statements(ts: Triplestore, iri: str):
    """Load and return list of spo statements from triplestore, with `iri`
    being the first node in the list of statements.
    """
    statements = []
    for node in load_list(ts, iri):
        d = {}
        for p, o in ts.predicate_objects(node):
            if p == RDF.subject:
                d["subject"] = as_python(o)
            elif p == RDF.predicate:
                d["predicate"] = as_python(o)
            elif p == RDF.object:
                d["object"] = as_python(o)
        statements.append(d)
    return sorted(statements, key=lambda d: sorted(d.items()))


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


def _expand_prefixes(d: dict, prefixes: dict) -> None:
    """Recursively expand IRI prefixes in the values of dict `d`."""
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = expand_iri(v, prefixes)
        elif isinstance(v, list):
            _expand_elements(v, prefixes)
        elif isinstance(v, dict):
            _expand_prefixes(v, prefixes)


def _expand_elements(lst: list, prefixes: dict) -> None:
    """Recursively expand IRI prefixes in the elements of list `lst`."""
    for i, e in enumerate(lst):
        if isinstance(e, str):
            lst[i] = expand_iri(e, prefixes)
        elif isinstance(e, list):
            _expand_elements(e, prefixes)
        elif isinstance(e, dict):
            _expand_prefixes(e, prefixes)


def expand_iri(iri: str, prefixes: dict) -> str:
    """Return the full IRI if `iri` is prefixed.  Otherwise `iri` is
    returned."""
    match = re.match(_MATCH_PREFIXED_IRI, iri)
    if match:
        prefix, name = match.groups()
        if prefix in prefixes:
            return f"{prefixes[prefix]}{name}"
        warnings.warn(f'Undefined prefix "{prefix}" in IRI: {iri}')
    return iri


def load_datadoc(filename: "Union[str,Path]"):
    """Populate triplestore with data documentation in YAML."""
    # pylint: disable=unused-argument
    with open(filename, "r", encoding="utf-8") as f:
        d = yaml.safe_load(f)

    # context
    # prefixes = d["prefixes"]
    # for dataset in d["datasets"]

    return prepare_datadoc(d)


def prepare_datadoc(datadoc: dict) -> dict:
    """Return an updated version of dict `datadoc` that is prepared for
    serialisation to RDF."""
    d = {
        "@context": (
            "https://raw.githubusercontent.com/EMMC-ASBL/oteapi-dlite/refs/"
            "heads/rdf-serialisation/oteapi_dlite/context/0.2/context.json"
        ),
    }
    d.update(datadoc)
    for dataset in get(datadoc, "datasets"):
        update_dataset(dataset)
    return d


def update_dataset(dataset: dict) -> None:  # pylint: disable=unused-argument
    """Update dict `dataset` with additional key-value pairs needed
    for serialisation to RDF.
    """

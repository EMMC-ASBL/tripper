# pylint: disable=line-too-long, too-many-lines
"""Module for documenting datasets with Tripper.

The dataset documentation follows the [DCAT] structure and is exposed
as Python dicts with attribute access in this module.  The semantic
meaning of the keywords in this dict are defined by a [JSON-LD context].

High-level function for populating the triplestore from YAML documentation:

  - `save_datadoc()`: Save documentation from YAML file to the triplestore.

Functions for searching the triplestore:

  - `search()`: Get IRIs of matching entries in the triplestore.

Functions for working with the dict-representation:

  - `read_datadoc()`: Read documentation from YAML file and return it as dict.
  - `store()`: Store documentation to the triplestore.
  - `acquire()`: Load documentation from the triplestore.
  - `told()`: Extend documention to valid JSON-LD (represented as a Python dict)
  - `delete_iri()`: Remove documentation of resource with given IRI.
  - `delete()`: Remove documentation of matching resources.

---

[DCAT]: https://www.w3.org/TR/vocab-dcat-3/
[JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.2/context.json

"""

from __future__ import annotations

# pylint: disable=invalid-name,redefined-builtin,import-outside-toplevel
# pylint: disable=too-many-branches
import json
import logging
import re
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from tripper import (
    OWL,
    RDF,
    Literal,
    Namespace,
    Triplestore,
)
from tripper.datadoc.context import Context, get_context
from tripper.datadoc.errors import (  # MissingKeywordsClassWarning,; UnknownKeywordWarning,
    InvalidDatadocError,
    IRIExistsError,
    IRIExistsWarning,
    NoSuchTypeError,
    ValidateError,
)
from tripper.datadoc.keywords import Keywords, get_keywords
from tripper.utils import (
    AttrDict,
    as_python,
    expand_iri,
    openfile,
    parse_literal,
    prefix_iri,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import (
        Any,
        Collection,
        Iterable,
        List,
        Mapping,
        Optional,
        Sequence,
        Union,
    )

    from tripper.datadoc.keywords import FileLoc
    from tripper.utils import Triple


# Local path (for fast loading) and URL to the JSON-LD context
CONTEXT_PATH = (
    Path(__file__).parent.parent / "context" / "0.3" / "context.json"
)
# TODO: fix IRI when merged to master
CONTEXT_URL = (
    "https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/"
    "master/tripper/context/0.3/context.json"
)

MATCH_IRI = re.compile(
    r"^(([a-z0-9]*):([a-zA-Z_]([a-zA-Z0-9_/+-]*[a-zA-Z0-9_+-])?))|"
    r"([a-zA-Z0-9]*://[a-zA-Z_]([a-zA-Z0-9_/.?#=+-]*))$"
)

logger = logging.getLogger(__name__)


def _get_range(keyword: str, keywords: "Optional[Keywords]" = None):
    """Return the range of `keyword`.

    If `keywords` is None, the keywords for the default domain are used.
    """
    keywords = get_keywords(keywords)
    return keywords[keyword].range


def show(obj, indent=2) -> None:
    """Print object to screen as pretty json."""
    if isinstance(obj, (bytes, str)):
        d = json.loads(obj)
    elif isinstance(obj, Keywords):
        d = obj.get_context()
    elif isinstance(obj, Context):
        d = obj.get_context_dict()
    else:
        d = obj
    print(json.dumps(d, indent=indent))


def told(
    descr: "Union[dict, list]",
    type: "Optional[str]" = None,
    keywords: "Optional[Keywords]" = None,
    prefixes: "Optional[dict]" = None,
    context: "Optional[Context]" = None,
) -> "AttrDict":
    """Return an updated copy of data description `descr` as valid JSON-LD.

    The following transformations are performed:

    - insert @type keywords
    - expand IRIs and substitute @id and @type in `statements` keyword
    - expand IRIs and substitute @id and @type in `mappings` keyword
    - insert mappings from `mappingURL` keyword (uses `mappingFormat`)

    Arguments:
        descr: Documenting of one or several resources to be represented as
            JSON-LD.  Supports both single- and multi-resource dicts.
        type: Type of data to save.  Should be one of the resource types
            defined in `keywords`.
        keywords: Keywords object with keywords definitions.  If not provided,
            only default keywords are considered.
        prefixes: Dict with prefixes in addition to those known in keywords
            or included in the JSON-LD context.
        context: Optional context object. It will be updated from the input
            data documentation `descr`.

    Returns:
        Dict with an updated copy of `descr` as valid JSON-LD.

    """
    single = "@id", "@type", "@graph"
    multi = "domain", "keywordfile", "prefixes", "base"
    singlerepr = any(s in descr for s in single) or isinstance(descr, list)
    multirepr = any(s in descr for s in multi)
    if singlerepr and multirepr:
        raise InvalidDatadocError(
            "invalid mixture of single- and multi-resource dict"
        )
    if not singlerepr:
        keywords = get_keywords(
            keywords=keywords,
            domain=descr.get("domain", "default"),  # type: ignore
            yamlfile=descr.get("keywordfile"),  # type: ignore
        )
    else:
        keywords = get_keywords(keywords=keywords)

    context = get_context(
        context=context, keywords=keywords, prefixes=prefixes
    )
    resources = keywords.data.resources

    if singlerepr:  # single-resource representation
        d = descr
    else:  # multi-resource representation
        d = {}
        graph = []
        for k, v in descr.items():  # type: ignore
            if k == "domain":
                pass
            elif k == "@context":
                context.add_context(v)
                d[k] = v
            elif k == "prefixes":
                context.add_context(v)
            elif k == "base":
                context.base = v
            elif k in resources:
                if isinstance(v, list):
                    for dct in v:
                        add(dct, "@type", resources[k].iri)
                        graph.append(dct)
                else:
                    graph.append(v)
            else:
                raise InvalidDatadocError(
                    f"Invalid keyword in root of multi-resource dict: {k}"
                )
        d["@graph"] = graph

    return _told(
        d,
        type=type,
        keywords=keywords,
        prefixes=context.get_prefixes(),
        root=True,
        hasid=False,
    )


def _told(
    descr: "Union[dict, list, str]",
    type: "Optional[str]",
    keywords: "Keywords",
    prefixes: "dict",
    root: bool = False,  # true at first recursive call
    hasid: bool = True,  # whether description has an @id
):
    """Recursive help function for told()."""
    # pylint: disable=too-many-statements

    def expand(iri):
        return expand_iri(iri, prefixes)

    def torange(kw):
        return keywords[kw].range if kw in keywords else None

    def addsuperclasses(d, cls):
        """Add `cls` and its superclasses to key "@type" in dict `d`."""
        classes = cls if isinstance(cls, list) else [cls]
        missing = []
        for c in classes:
            try:
                add(d, "@type", keywords.superclasses(c))
            except NoSuchTypeError:
                missing.append(prefix_iri(c, keywords.get_prefixes()))
                add(d, "@type", c)
            if missing:
                # Using logging.info() here, since warnings is too verbose
                # pylint: disable=logging-fstring-interpolation
                logging.info(
                    f"Class not in keywords: {', '.join(missing)}",
                )

    if isinstance(descr, str):
        return descr

    if isinstance(descr, list):
        lst = [_told(token, type, keywords, prefixes) for token in descr]
        return {"@graph": lst} if root else lst

    if not isinstance(descr, dict):
        raise InvalidDatadocError(
            "Malformed data documentation. Expected dict, list or string. "
            f"Got: {descr:!}"
        )

    # From hereon `descr` must be a dict.
    # Check that it has an "@id" or "@graph" key
    if not hasid and "@id" not in descr and "@graph" not in descr:
        raise InvalidDatadocError("Missing '@id' key in data documentation.")

    # Create returned dict with @context, @id and @type as the first items
    d = {}
    for k in "@context", "@id":
        if k in descr:
            d[k] = descr[k]
    if "@type" in descr:
        addsuperclasses(d, descr["@type"])
    if type:
        addsuperclasses(d, type)
    elif not "@type" in descr and not "@graph" in descr:
        d["@type"] = "owl:NamedIndividual"

    for k, v in descr.items():
        if not k.startswith("@") and k not in keywords:
            # pylint: disable=logging-fstring-interpolation
            logging.info(f"Property not in keywords: {k}")
        if k in ("@context", "@id", "@type"):
            pass
        elif k == "@graph":
            d[k] = _told(v, type, keywords, prefixes)
        elif k == "mappingURL":
            for url in get(descr, k):
                with Triplestore("rdflib") as ts:
                    ts.parse(url, format=descr.get("mappingFormat"))
                    add(d, "mappings", list(ts.triples()))
        elif k in ("statements", "mappings"):
            lst = [
                [
                    expand(get(descr, e, e)[0] if e[0] == "@" else e)
                    for e in spo
                ]
                for i, spo in enumerate(descr[k])
            ]
            add(d, k, [tuple(t) for t in lst])
        elif k == "datamodel":
            add(d, "@type", v)
            d[k] = v
        elif isinstance(v, (str, int, float, bool, None.__class__)):
            d[k] = v
        elif isinstance(v, list):
            d[k] = _told(v, torange(k), keywords, prefixes)
        elif isinstance(v, dict):
            if k in keywords and "datatype" in keywords[k]:
                d[k] = v
            else:
                d[k] = _told(v, torange(k), keywords, prefixes)

    return d


def store(
    ts: Triplestore,
    source: "Union[dict, list]",
    type: "Optional[str]" = None,
    context: "Optional[Context]" = None,
    keywords: "Optional[Keywords]" = None,
    prefixes: "Optional[dict]" = None,
    method: str = "raise",
    restrictions: "Collection" = (),
) -> dict:
    # pylint: disable=line-too-long,too-many-branches
    """Store documentation of a resource to a triplestore.

    Arguments:
        ts: Triplestore to store to.
        source: Dict or list with the resource documentation to store.
        type: Type of documented resource.  Should be one of the resource types
            defined in `keywords`.
        context: Context object defining keywords in addition to those defined
            in the default [JSON-LD context].
            Complementing the `keywords` argument.
        keywords: Keywords object with additional keywords definitions.
            If not provided, only default keywords are considered.
        prefixes: Dict with prefixes in addition to those included in the
            JSON-LD context.  Should map namespace prefixes to IRIs.
        method: How to handle the case where `ts` already contains a document
            with the same id as `source`. Possible values are:
            - "overwrite": Remove existing documentation before storing.
            - "raise": Raise an `IRIExistsError` if the IRI of `source`
              already exits in the triplestore (default).
            - "merge": Merge `source` with existing documentation. This will
              duplicate non-literal properties with no explicit `@id`. If this
              is unwanted, merge manually and use "overwrite".
            - "ignore": If the IRI of `source` already exists, do nothing but
              issueing an `IRIExistsWarning`.
        restrictions: Collection of additional keywords that shuld be
            converted to value restrictions.

    Returns:
        A copy of `source` updated to valid JSON-LD.

    Notes:
        The keywords should either be one of the [default keywords] or defined
        by the `context` or `keywords` arguments.

    References:
    [default keywords]: https://emmc-asbl.github.io/tripper/latest/datadoc/keywords/
    [JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/oteapi-dlite/refs/heads/rdf-serialisation/oteapi_dlite/context/0.3/context.json
    """
    keywords = get_keywords(keywords)
    context = get_context(
        keywords=keywords, context=context, prefixes=prefixes
    )

    doc = told(
        source,
        type=type,
        keywords=keywords,
        prefixes=prefixes,
        context=context,
    )
    docs = doc if isinstance(doc, list) else doc.get("@graph", [doc])
    for d in docs:
        iri = d["@id"]
        if ts.has(iri):
            if method == "overwrite":
                delete_iri(ts, iri)
            elif method == "raise":
                raise IRIExistsError(f"Cannot overwrite existing IRI: {iri}")
            elif method == "merge":
                pass
            elif method == "ignore":
                warnings.warn(iri, category=IRIExistsWarning)
                return doc
            else:
                raise ValueError(
                    f"Invalid storage method: '{method}'. "
                    "Should be one of: 'overwrite', 'raise', 'ignore' or "
                    "'merge'"
                )

    context.sync_prefixes(ts)
    update_classes(doc, context=context, restrictions=restrictions)
    # add(doc, "@context", context.get_context_dict())

    # Validate
    # TODO: reenable validation
    # validate(doc, type=type, keywords=keywords)

    context.to_triplestore(ts, doc)

    # Add statements and data models to triplestore
    save_extra_content(ts, doc)  # FIXME: SLOW!!

    return doc


def save_dict(
    ts: Triplestore,
    source: "Union[dict, list]",
    type: "Optional[str]" = None,
    context: "Optional[Context]" = None,
    keywords: "Optional[Keywords]" = None,
    prefixes: "Optional[dict]" = None,
    method: str = "merge",
    # The unnecessary strictness of the "build documentation" CI enforces us
    # to add a `restrictions` argument to save_dict(), although this argument
    # came after that save_dict() was renamed.
    restrictions: "Collection" = (),
) -> dict:
    """This function is deprecated. Use store() instead."""
    warnings.warn(
        "tripper.datadoc.save_dict() is deprecated. "
        "Please use tripper.datadoc.store() instead.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return store(
        ts=ts,
        source=source,
        type=type,
        context=context,
        keywords=keywords,
        prefixes=prefixes,
        method=method,
        restrictions=restrictions,
    )


def update_classes(
    source: "Union[dict, list]",
    context: "Optional[Context]" = None,
    restrictions: "Collection" = (),
) -> "Union[dict, list]":
    """Update documentation of classes, ensuring that they will be
    correctly represented in RDF.

    Only resources of type `owl:Class` will be updated.

    If a resource has type `owl:Class`, all other types it has will be
    moved to the `subClassOf` keyword.

    By default, only object properties who's value is either a class
    or has a `restrictionType` key are converted to restrictions. Use
    the `restrictions` argument to convert other keywords as well to
    restrictions.

    Arguments:
        source: Input documentation of one or more resources. This dict
            will be updated in-place. It is typically a dict returned by
            `told()`.
        context: Context object defining the keywords.
        restrictions: Collection of additional keywords that shuld be
            converted to value restrictions.

    Returns:
        The updated version of `source`.

    """

    def addrestriction(source, prop, value):
        """Add restriction to `source`."""
        # pylint: disable=no-else-return
        if value is None or prop.startswith("@"):
            return
        elif restrictions and context.expand(prop) in restrictions:
            restrictionType = "value"
        elif isinstance(value, dict) and (
            "restrictionType" in value
            or any(context.expand(s) == OWL.Class for s in get(value, "@type"))
        ):
            restrictionType = value.pop("restrictionType", "some")
            update_classes(value, context=context, restrictions=restrictions)
        elif isinstance(value, list):
            for val in value:
                addrestriction(source, prop, val)
            return
        else:
            return

        d = {
            "rdf:type": "owl:Restriction",
            # We expand here, since JSON-LD doesn't expand values.
            "owl:onProperty": context.expand(prop, strict=True),
        }
        if restrictionType == "value":
            d["owl:hasValue"] = value
        elif restrictionType == "some":
            d["owl:someValuesFrom"] = value
        elif restrictionType == "only":
            d["owl:allValuesFrom"] = value
        else:
            d["owl:onClass"] = value
            ctype, n = restrictionType.split()
            ctypes = {
                "exactly": "owl:qualifiedCardinality",
                "min": "owl:minQualifiedCardinality",
                "max": "owl:maxQualifiedCardinality",
            }
            d[ctypes[ctype]] = int(n)

        add(source, "subClassOf", d)
        if prop in source:  # Avoid removing prop more than once
            del source[prop]

        if restrictionType != "value":  # Recursively update related calsses
            update_classes(value, context, restrictions)

    # Local context
    context = get_context(context=context, copy=True)
    restrictions = {context.expand(s, strict=True) for s in restrictions}

    # Handle lists and graphs
    if isinstance(source, list) or "@graph" in source:
        sources = source if isinstance(source, list) else source["@graph"]
        if isinstance(sources, dict):
            sources = [sources]
        for src in sources:
            update_classes(src, context)
        return source

    # Update local context
    if "@context" in source:
        context.add_context(source["@context"])

    # Ensure that source is only of type owl:Class
    # Move all other types to subClassOf
    types = {context.expand(t): t for t in get(source, "@type")}
    if OWL.Class in types:
        for e, t in types.items():
            if e == OWL.Class:
                source["@type"] = t
            else:
                add(source, "subClassOf", e)

    # Convert relations to restrictions
    for k, v in source.copy().items():
        if k.startswith("@") or k in ("subClassOf",):
            continue
        addrestriction(source, k, v)

    return source


def save_extra_content(ts: Triplestore, source: dict) -> None:
    """Save extra content in `source` to the triplestore.

    Currently, this includes:
    - statements and mappings
    - data models (require that DLite is installed)

    Arguments:
        ts: Triplestore to load data from.
        source: Dict in multi-resource format.

    """
    import requests

    # Save statements and mappings
    statements = get_values(source, "statements")
    statements.extend(get_values(source, "mappings"))
    if statements:
        ts.add_triples(statements)

    # Save data models
    datamodels = {
        d["@id"]: d["datamodel"]
        for d in source.get("Dataset", ())
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
        for url in get_values(source, "datamodelStorage"):
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


def acquire(
    ts: Triplestore,
    iri: str,
    use_sparql: "Optional[bool]" = None,
    context: "Optional[Context]" = None,
) -> dict:
    """Load description of a resource from the triplestore.

    Arguments:
        ts: Triplestore to load description from.
        iri: IRI of the to resource.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to the value of `ts.prefer_sparql`.
        context: Context object defining keywords in addition to those defined
            in the default [JSON-LD context].

    Returns:
        Dict describing the resource identified by `iri`.
    """
    if use_sparql is None:
        use_sparql = ts.prefer_sparql
    if use_sparql:
        return _load_sparql(ts, iri)

    d = AttrDict()
    dct = _load_triples(ts, iri, context=context)
    for key, val in dct.items():
        if key in ("mappings", "statements"):
            add(d, key, val)
        else:
            if not isinstance(val, list):
                val = [val]
            for v in val:
                if key != "@id" and isinstance(v, str) and v.startswith("_:"):
                    add(d, key, acquire(ts, iri=v, use_sparql=use_sparql))
                else:
                    add(d, key, v)

    return d


def load_dict(
    ts: Triplestore,
    iri: str,
    use_sparql: "Optional[bool]" = None,
) -> dict:
    """This function is deprecated. Use acquire() instead."""
    warnings.warn(
        "tripper.datadoc.load_dict() is deprecated. "
        "Please use tripper.datadoc.acquire() instead.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return acquire(ts=ts, iri=iri, use_sparql=use_sparql)


def _load_triples(
    ts: Triplestore,
    iri: str,
    context: "Optional[Context]" = None,
) -> dict:
    """Load `iri` from triplestore by calling `ts.triples()`."""
    if context is None:
        context = get_context()
    dct: dict = {}
    for p, o in ts.predicate_objects(ts.expand_iri(iri)):
        add(dct, context.shortname(p, strict=False), as_python(o))
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
    # blank nodes, which avoids problems with backends that renames
    # blank nodes.
    subj = iri if iri.startswith("_:") else f"<{ts.expand_iri(iri)}>"
    query = f"""
    # Some backends requires the prefix to be defined...
    PREFIX : <http://example.com#>
    CONSTRUCT {{ ?s ?p ?o }}
    WHERE {{
      {subj} (:|!:)* ?s .
      ?s ?p ?o .
    }}
    """
    triples = ts.query(query)
    with Triplestore(backend="rdflib") as ts2:
        for prefix, namespace in ts.namespaces.items():
            ts2.bind(prefix, str(namespace))
        ts2.add_triples(triples)  # type: ignore
        dct = acquire(ts2, iri, use_sparql=False)
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

    warnings.warn(
        "`dataset.get_jsonld_context()` is deprecated, use `get_context()` "
        "instead",
        category=DeprecationWarning,
        stacklevel=2,
    )

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
    warnings.warn(
        "`dataset.get_prefixes()` is deprecated, use `Context.prefixes()` "
        "instead",
        category=DeprecationWarning,
        stacklevel=2,
    )

    if isinstance(context, Context):
        return context.get_prefixes()

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
    warnings.warn(
        "`dataset.get_shortnames()` is deprecated, use `Context.shortname()` "
        "instead",
        category=DeprecationWarning,
        stacklevel=2,
    )

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
                key=lambda x: "\uffff" if isinstance(x, dict) else str(x),
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


def read_datadoc(filename: "Union[str, Path]") -> dict:
    """Read YAML data documentation and return it as a dict.

    The filename may also be an URL to a file accessible with HTTP GET.
    """
    import yaml  # type: ignore

    with openfile(filename, mode="rt", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    return told(d)
    # return prepare_datadoc(d)


def save_datadoc(
    ts: Triplestore,
    file_or_dict: "Union[str, Path, dict]",
    keywords: "Optional[Keywords]" = None,
    context: "Optional[Context]" = None,
) -> dict:
    """Populate triplestore with data documentation.

    Arguments:
        ts: Triplestore to save dataset documentation to.
        file_or_dict: Data documentation dict or name of a YAML file to read
            the data documentation from.  It may also be an URL to a file
            accessible with HTTP GET.
        keywords: Optional Keywords object with keywords definitions.
            The default is to infer the keywords from the `domain` or
            `keywordfile` keys in the YAML file.
        context: Optional Context object with mappings. By default it is
            inferred from `keywords`.

    Returns:
        Dict-representation of the loaded dataset.
    """
    import yaml  # type: ignore

    if isinstance(file_or_dict, dict):
        d = file_or_dict
    else:
        with openfile(file_or_dict, mode="rt", encoding="utf-8") as f:
            d = yaml.safe_load(f)

    return store(ts, d, keywords=keywords, context=context)


def validate(
    dct: dict,
    type: "Optional[str]" = None,
    context: "Optional[Context]" = None,
    keywords: "Optional[Keywords]" = None,
) -> None:
    """Validates single-resource dict `dct`.

    Arguments
        dct: Single-resource dict to validate.
        type: The type of resource to validate. Ex: "Dataset", "Agent", ...
        keywords: Keywords object defining the keywords used in `dct`.

    Raises:
        ValidateError: If the validation fails.
    """
    if keywords is None:
        keywords = Keywords()

    if context is None:
        context = Context(keywords=keywords)

    if type is None and "@type" in dct:
        try:
            type = keywords.typename(dct["@type"])
        except NoSuchTypeError:
            pass

    resources = keywords.data.resources

    def check_keyword(keyword, type):
        """Check that the resource type `type` has keyword `keyword`."""
        typename = keywords.typename(type)
        name = keywords.keywordname(keyword)
        if name in resources[typename].keywords:
            return True
        if "subClassOf" in resources[typename]:
            subclass = resources[typename].subClassOf
            return check_keyword(name, subclass)
        return False

    def _check_keywords(k, v):
        if k in keywords:
            r = keywords[k]
            if "datatype" in r:
                datatype = expand_iri(r.datatype, keywords.data.prefixes)
                literal = parse_literal(v)
                tr = {}
                for t, seq in Literal.datatypes.items():
                    for dt in seq:
                        tr[dt] = t
                if tr.get(literal.datatype) != tr.get(datatype):
                    raise ValidateError(
                        f"invalid datatype for '{v}'. "
                        f"Got '{literal.datatype}', expected '{datatype}'"
                    )
            elif isinstance(v, dict):
                validate(v, type=r.get("range"), keywords=keywords)
            elif isinstance(v, list):
                for it in v:
                    _check_keywords(k, it)
            elif r.range != "rdfs:Literal" and not re.match(MATCH_IRI, v):
                raise ValidateError(f"value of '{k}' is an invalid IRI: '{v}'")
        elif k not in context:
            raise ValidateError(f"unknown keyword: '{k}'")

    # Check the keyword-value pairs in `dct`
    for k, v in dct.items():
        if k.startswith("@"):
            continue
        _check_keywords(k, v)

    if type:
        typename = keywords.typename(type)

        for k in dct:
            if not k.startswith("@"):
                if not check_keyword(k, typename):
                    warnings.warn(
                        f"unexpected keyword '{k}' provided for type: '{type}'"
                    )

        for kr, vr in resources[typename].items():
            if "conformance" in vr and vr.conformance == "mandatory":
                if kr not in dct:
                    raise ValidateError(
                        f"missing mandatory keyword '{kr}' for type: '{type}'"
                    )


def get_partial_pipeline(
    ts: Triplestore,
    client,
    iri: str,
    context: "Optional[Context]" = None,
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
        context: Context object.
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
    # pylint: disable=too-many-branches,too-many-locals
    context = get_context(context=context, domain="default")

    dct = acquire(ts, iri, use_sparql=use_sparql)

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
        if isinstance(par, str):
            par = acquire(ts, par)
        configuration = par.get("configuration")
    else:
        configuration = None

    mediaType = distr.get("mediaType")
    mediaTypeShort = (
        mediaType[44:]
        if mediaType.startswith("http://www.iana.org/assignments/media-types/")
        else mediaType
    )
    dataresource = client.create_dataresource(
        downloadUrl=distr.get("downloadURL"),
        mediaType=mediaTypeShort,
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


def delete_iri(ts: Triplestore, iri: str) -> None:
    """Delete `iri` from triplestore using SPARQL."""
    subj = iri if iri.startswith("_:") else f"<{ts.expand_iri(iri)}>"
    query = f"""
    # Some backends requires the prefix to be defined...
    PREFIX : <http://example.com#>
    DELETE {{ ?s ?p ?o }}
    WHERE {{
      {subj} (:|!:)* ?s .
      ?s ?p ?o .
    }}
    """
    ts.update(query)


def make_query(
    ts: Triplestore,
    type=None,
    criterias: "Optional[dict]" = None,  # deprecated
    criteria: "Optional[dict]" = None,  # new preferred name
    regex: "Optional[dict]" = None,
    flags: "Optional[str]" = None,
    keywords: "Optional[Keywords]" = None,
    query_type: "Optional[str]" = "SELECT DISTINCT",
) -> "str":
    """Help function for creating a SPARQL query.

    See search() for description of arguments.

    The `query_type` argument is typically one of "SELECT DISTINCT"
    "SELECT", or "DELETE".
    """
    # pylint: disable=too-many-statements,too-many-branches,too-many-locals

    if criterias is not None:
        warnings.warn(
            "`criterias` is deprecated, use `criteria` instead",
            category=DeprecationWarning,
            stacklevel=2,
        )
        # if caller didn’t supply the new name, adopt the old one
        if criteria is None:
            criteria = criterias

    keywords = get_keywords(keywords=keywords)
    context = get_context(keywords=keywords)
    context._create_caches()  # pylint: disable=protected-access
    expanded = context._expanded  # pylint: disable=protected-access

    # Add prefixes to triplestore
    ts.namespaces.update(keywords.get_prefixes())

    # Initiate variables
    criteria = criteria or {}
    regex = regex or {}
    crit = []
    filters = []
    n = 0  # counter for creating new unique sparql variables
    flags_arg = f", {flags}" if flags else ""

    # Special handling of @id
    cid = criteria.pop("@id", criteria.pop("_id", None))
    rid = regex.pop("@id", regex.pop("_id", None))
    if cid:
        filters.append(f'FILTER(STR(?iri) = "{ts.expand_iri(cid)}") .')
    elif rid:
        filters.append(
            f'FILTER REGEX(STR(?iri), "{ts.expand_iri(rid)}"{flags_arg}) .'
        )

    if type:
        types = [type] if not isinstance(type, list) else type
        for t in types:
            if ":" in t:
                expanded_iri = ts.expand_iri(t)
                crit.append(f"?iri rdf:type <{expanded_iri}> .")
            else:
                if keywords is None:
                    keywords = Keywords()
                typ = keywords.superclasses(t)
                if not isinstance(typ, str):
                    typ = typ[0]
                crit.append(f"?iri rdf:type <{ts.expand_iri(typ)}> .")  # type: ignore

    def add_crit(k, v, regex=False, s="iri"):
        """Add criteria to SPARQL query."""
        nonlocal n
        key = f"@{k[1:]}" if k.startswith("_") else k
        if isinstance(v, list):
            for ele in v:
                add_crit(key, ele, regex=regex, s=s)
            return
        if re.match(r"^[_a-zA-Z0.9]+\.", key):
            newkey, restkey = key.split(".", 1)
            if newkey in expanded:
                newkey = expanded[newkey]
            n += 1
            var = f"v{n}"
            crit.append(f"?{s} <{ts.expand_iri(newkey)}> ?{var} .")
            add_crit(restkey, v, s=var)
        else:
            if key in expanded:
                key = expanded[key]
            if v in expanded:
                value = f"<{expanded[v]}>"
            elif isinstance(v, str):
                value = (
                    f"<{v}>"
                    if re.match("^[a-z][a-z0-9.+-]*://", v)
                    else f'"{v}"'
                )
            else:
                value = v
            n += 1
            var = f"v{n}"
            crit.append(f"?{s} <{ts.expand_iri(key)}> ?{var} .")
            if regex:
                filters.append(
                    f"FILTER REGEX(STR(?{var}), {value}{flags_arg}) ."
                )
            else:
                filters.append(f"FILTER(STR(?{var}) = {value}) .")

    for k, v in criteria.items():
        add_crit(k, v)

    if not crit:
        crit.append("?iri ?p ?o .")

    for k, v in regex.items():
        add_crit(k, v, regex=True)

    where_statements = "\n      ".join(crit + filters)
    query = f"""
    PREFIX rdf: <{RDF}>
    {query_type} ?iri
    WHERE {{
      {where_statements}
    }}
    """
    return query


def search(
    ts: Triplestore,
    type=None,
    criterias: "Optional[dict]" = None,  # deprecated
    criteria: "Optional[dict]" = None,  # new preferred name
    regex: "Optional[dict]" = None,
    flags: "Optional[str]" = None,
    keywords: "Optional[Keywords]" = None,
    skipblanks: "bool" = True,
) -> "List[str]":
    """Return a list of IRIs for all matching resources.

    Arguments:
        ts: Triplestore to search.
        type: Either a [resource type] (ex: "Dataset", "Distribution", ...)
            or the IRI of a class to limit the search to.
        criteria: Exact match criteria. A dict of IRI, value pairs, where the
            IRIs refer to data properties on the resource match. The IRIs
            may use any prefix defined in `ts`. E.g. if the prefix `dcterms`
            is in `ts`, it is expanded and the match criteria `dcterms:title`
            is correctly parsed.
        regex: Like `criteria` but the values in the provided dict are regular
            expressions used for the matching.
        flags: Flags passed to regular expressions.
            - `s`: Dot-all mode. The . matches any character.  The default
              doesn't match newline or carriage return.
            - `m`: Multi-line mode. The ^ and $ characters matches beginning
              or end of line instead of beginning or end of string.
            - `i`: Case-insensitive mode.
            - `q`: Special characters representing themselves.
        keywords: Keywords instance defining the resource types used with
            the `type` argument.
        skipblanks: Whether to skip blank nodes.

    Returns:
        List of IRIs for matching resources.

    Examples:
        List all data resources IRIs:

            search(ts)

        List IRIs of all resources with John Doe as `contactPoint`:

            search(ts, criteria={"contactPoint.hasName": "John Doe"})

        List IRIs of all samples:

            search(ts, type=CHAMEO.Sample)

        List IRIs of all datasets with John Doe as `contactPoint` AND are
        measured on a given sample:

            search(
                ts,
                type=DCAT.Dataset,
                criteria={
                    "contactPoint.hasName": "John Doe",
                    "fromSample": SAMPLE.batch2/sample3,
                },
            )

        List IRIs of all datasets who's title matches the regular expression
        "[Mm]agnesium":

            search(
                ts, type=DCAT.Dataset, regex={"title": "[Mm]agnesium"},
            )

    SeeAlso:
        [resource type]: https://emmc-asbl.github.io/tripper/latest/datadoc/introduction/#resource-types
    """

    if criterias is not None:
        warnings.warn(
            "`criterias` is deprecated, use `criteria` instead",
            category=DeprecationWarning,
            stacklevel=2,
        )
        # if caller didn’t supply the new name, adopt the old one
        if criteria is None:
            criteria = criterias

    # normalize defaults
    criteria = criteria or {}
    regex = regex or {}

    query = make_query(
        ts=ts,
        type=type,
        criteria=criteria,
        regex=regex,
        flags=flags,
        keywords=keywords,
        query_type="SELECT DISTINCT",
    )
    if skipblanks:
        return [
            r[0] for r in ts.query(query) if not r[0].startswith("_:")  # type: ignore
        ]
    return [r[0] for r in ts.query(query)]  # type: ignore


def search_iris(
    ts: Triplestore,
    type=None,
    criterias: "Optional[dict]" = None,
    regex: "Optional[dict]" = None,
    flags: "Optional[str]" = None,
    keywords: "Optional[Keywords]" = None,
    skipblanks: "bool" = True,
) -> "List[str]":
    """This function is deprecated. Use search() instead."""
    warnings.warn(
        "tripper.datadoc.search_iris() is deprecated. "
        "Please use tripper.datadoc.search() instead.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    return search(
        ts=ts,
        type=type,
        criterias=criterias,
        regex=regex,
        flags=flags,
        keywords=keywords,
        skipblanks=skipblanks,
    )


def delete(
    ts: Triplestore,
    type=None,
    criterias: "Optional[dict]" = None,  # deprecated
    criteria: "Optional[dict]" = None,  # new preferred name
    regex: "Optional[dict]" = None,
    flags: "Optional[str]" = None,
    keywords: "Optional[Keywords]" = None,
) -> None:
    """Delete matching resources. See `search()` for a description of arguments."""

    if criterias is not None:
        warnings.warn(
            "`criterias` is deprecated, use `criteria` instead",
            category=DeprecationWarning,
            stacklevel=2,
        )
        # if caller didn’t supply the new name, adopt the old one
        if criteria is None:
            criteria = criterias

    # normalize defaults
    criteria = criteria or {}
    regex = regex or {}

    iris = search(
        ts=ts,
        type=type,
        criteria=criteria,
        regex=regex,
        flags=flags,
        keywords=keywords,
    )
    for iri in iris:
        delete_iri(ts, iri)

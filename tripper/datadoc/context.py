"""Parse and work with JSON-LD context."""

# pylint: disable=too-many-branches,redefined-builtin

import json
import os
import re
import warnings
from typing import TYPE_CHECKING, Sequence

from pyld import jsonld
from rdflib import Graph

from tripper import OWL, RDF, RDFS, Triplestore
from tripper.datadoc.errors import InvalidContextError, PrefixMismatchError
from tripper.errors import NamespaceError, NamespaceWarning
from tripper.utils import MATCH_IRI, MATCH_PREFIXED_IRI, openfile, prefix_iri

if TYPE_CHECKING:  # pragma: no cover
    from typing import IO, Optional, Union

    from tripper.datadoc.keywords import Keywords

    # Possible types for a JSON-LD context
    ContextType = Union[str, dict, Sequence[Union[str, dict]], "Context"]


def get_context(
    context: "Optional[ContextType]" = None,
    theme: "Optional[Union[str, Sequence[str]]]" = None,
    default_theme: "Optional[Union[str, Sequence[str]]]" = "ddoc:datadoc",
    keywords: "Optional[Keywords]" = None,
    prefixes: "Optional[dict]" = None,
    processingMode: str = "json-ld-1.1",
    copy: bool = False,
    timeout: float = 3,
) -> "Context":
    """A convinient function that returns an Context instance.

    Arguments:
        context: Input context.  Several types are supported:
            - Context: The Context instance will be updated and returned,
              unless `copy` is true.
            - dict: Dict-representation of a valid JSON-LD context.
            - str: If a valid URI, the context is loaded from this URI,
              otherwise it is assumed to be a file path to load.
            - sequence: A sequence of the above.
        theme: Load initial context for this theme.
        default_theme: Initialise context for this theme if neither
            `context` nor `theme` are provided.
        keywords: Initialise from this keywords instance.
        prefixes: Optional dict with additional prefixes.
        processingMode: Either "json-ld-1.0" or "json-ld-1.1".
        copy: If true, always return a new Context object.
        timeout: Timeout when accessing remote files.

    Returns:
        Context object.
    """
    # pylint: disable=import-outside-toplevel
    from tripper.datadoc.keywords import get_keywords

    if isinstance(context, Context):
        if copy:
            context = context.copy()
        if keywords or theme:
            kw = get_keywords(keywords=keywords, theme=theme)
            context.add_context(kw.get_context())
    else:
        context = Context(
            context=context,
            theme=theme if context or theme or keywords else default_theme,
            keywords=keywords,
            processingMode=processingMode,
            timeout=timeout,
        )
    if prefixes:
        context.add_context({k: str(v) for k, v in prefixes.items()})
    return context


class Context:
    """A class representing a context."""

    def __init__(
        self,
        context: "Optional[ContextType]" = None,
        theme: "Optional[Union[str, Sequence[str]]]" = "ddoc:datadoc",
        keywords: "Optional[Keywords]" = None,
        processingMode: str = "json-ld-1.1",
        timeout: float = 3,
    ) -> None:
        """Initialises context object.

        Arguments:
            context: Optional context to load. Supported types:
                - Context: The Context instance will be updated and returned,
                  unless `copy` is true.
                - dict: Dict-representation of a valid JSON-LD context.
                - str: If a valid URI, the context is loaded from this URI,
                  otherwise it is assumed to be a file path to load.
                - sequence: A sequence of the above.
            theme: Load initial context for this theme.
            keywords: Initialise from this keywords instance.
            processingMode: Either "json-ld-1.0" or "json-ld-1.1".
            timeout: Timeout when accessing remote files.

        """
        # pylint: disable=import-outside-toplevel
        from tripper.datadoc.keywords import Keywords

        self.ld = jsonld.JsonLdProcessor()
        self.ctx = self.ld._get_initial_context(
            options={"processingMode": processingMode}
        )
        self.timeout = timeout
        self._expanded: dict = {}
        self._prefixed: dict = {}
        self._shortnamed: dict = {}

        if keywords is not None:
            if theme:
                keywords.add_theme(theme)
            self.add_context(keywords.get_context())
        elif theme:
            keywords = Keywords(theme=theme)
            self.add_context(keywords.get_context())

        if context:
            self.add_context(context)

    def __contains__(self, item):
        self._create_caches()
        return item in self._expanded

    def __getitem__(self, key):
        self._create_caches()
        return self._expanded[key]

    def __iter__(self):
        self._create_caches()
        return iter(set(self._shortnamed.values()))

    def __dir__(self):
        self._create_caches()
        return dir(Context) + ["ld", "ctx"]

    ## def __repr__(self):
    ##     js = json.dumps(self.get_context_dict(), indent=4)
    ##     return f"Context(context={js})"

    def __str__(self):
        return json.dumps({"@context": self.get_context_dict()}, indent=2)

    def copy(self) -> "Context":
        """Return a copy of this context."""
        copy = Context(theme=None)
        copy.ctx = self.ctx  # frozendict - no need to copy
        return copy

    def add_context(self, context: "ContextType") -> None:
        """Add a context to this object."""
        if isinstance(context, Context):
            context = context.get_context_dict()
        elif isinstance(context, str):
            with openfile(context, "rt", timeout=self.timeout) as f:
                context = json.load(f)
        elif isinstance(context, Sequence):
            for c in context:
                self.add_context(c)
            return
        elif isinstance(context, dict):
            pass
        else:
            raise TypeError(
                "`context` should be a dict, str, Context or a sequence of "
                f"these.  Got: {type(context)}"
            )

        if "@id" in context:
            if "@context" in context:
                context = context["@context"]  # type: ignore
            else:
                r = repr(context)
                c = f"{r}..." if len(r) > 100 else r
                raise InvalidContextError(
                    f"context cannot have an @id key: {c}"
                )

        def rec(dct):
            """Return a copy of `dct` with all empty key names replaced
            with "@base"."""
            if not isinstance(dct, dict):
                return dct

            d = dct.copy()
            for k, v in dct.items():
                if k == "":
                    if isinstance(v, str):
                        d["@base"] = d.pop("")
                    else:
                        raise InvalidContextError(
                            f"empty key with non-string value: {v}"
                        )
                if isinstance(v, dict):
                    d[k] = rec(v)
            return d

        self.ctx = self.ld.process_context(self.ctx, rec(context), options={})

        # Clear caches
        self._expanded.clear()
        self._prefixed.clear()
        self._shortnamed.clear()

    def get_context_dict(self) -> dict:
        """Return a context dict."""
        context = {}
        if "@base" in self.ctx and self.ctx["@base"]:
            context["@base"] = self.ctx["@base"]
        if "@vocab" in self.ctx and self.ctx["@vocab"]:
            context["@vocab"] = self.ctx["@vocab"]
        for name, info in self.ctx["mappings"].items():
            if "@type" in info:
                context[name] = {
                    "@id": info["@id"],
                    "@type": info["@type"],
                }
            else:
                context[name] = info["@id"]
        return context

    # def get_context(self) -> dict:
    #     """Return a context dict."""
    #     return {k: v.get("@id") for k, v in self.ctx["mappings"].items()}

    def get_mappings(self) -> dict:
        """Return a dict mapping keywords to IRIs."""
        return {
            k: v["@id"]
            for k, v in self.ctx["mappings"].items()
            if v.get("_prefix") is False and "@id" in v
        }

    def get_prefixes(self) -> dict:
        """Return a dict mapping prefixes to IRIs."""

        prefixes = {"": self.base} if self.base else {}
        for k, v in self.ctx["mappings"].items():
            if v.get("_prefix") and "@id" in v:
                prefixes[k] = v["@id"]
        return prefixes

    def sync_prefixes(
        self, ts: Triplestore, update: "Optional[bool]" = None
    ) -> None:
        """Syncronise prefixes between context and triplestore.

        The `update` option controls how prefix inconsistencies are handeled.
        If `update` is:

        - True:  Prefixes in the context will be updated.
        - False: Prefixes in the triplestore will be updated.
        - None:  A PrefixMismatchError is raised.

        """
        ns1 = self.get_prefixes().copy()
        ns2 = {pf: str(ns) for pf, ns in ts.namespaces.items()}
        if update is None:
            mismatch = [
                p for p in set(ns1).intersection(ns2) if ns1[p] != ns2[p]
            ]
            if mismatch:
                msg = ["Mismatch in definition of prefix(es): "]
                for mis in mismatch:
                    msg.extend(
                        [
                            f"* Prefix '{mis}' is defined as",
                            f"  - {ns1[mis]} in context",
                            f"  - {ns2[mis]} in triplestore",
                        ]
                    )
                raise PrefixMismatchError(os.linesep.join(msg))

        if update:
            ns1.update(ns2)
            ns2 = ns1
        else:
            ns2.update(ns1)
            ns1 = ns2

        self.add_context(ns2)

        for prefix, ns in ns1.items():
            if prefix not in ts.namespaces:
                ts.bind(prefix, ns)

    def expand(self, name: str, strict: bool = False) -> str:
        """Return `name` expanded to a full IRI.

        If `name` is not defined in the context, a `NameSpaceError` will
        be raised if `strict` is true. Otherwise `name` will be returned
        unchanged.

        Example:

        >>> context = Context()
        >>> context.expand("Dataset")
        'http://www.w3.org/ns/dcat#Dataset'

        """
        # Check cache
        if self._expanded and name in self._expanded:
            return self._expanded[name]
        # Check ctx
        if name in self.ctx["mappings"]:
            return self.ctx["mappings"][name]["@id"]
        # Check if name is already expanded
        if re.match(MATCH_IRI, name):
            return name
        # Check if prefixed
        if re.match(MATCH_PREFIXED_IRI, name):
            prefix, shortname = name.split(":", 1)
            prefixes = self.get_prefixes()
            if prefix in prefixes:
                return f"{prefixes[prefix]}{shortname}"
        # Name not defined in context
        if strict:
            raise NamespaceError(f"cannot expand: {name}")
        return name

    def prefixed(self, name: str, strict: bool = True) -> str:
        """Return `name` as a prefixed IRI.

        If `name` is not defined in the context, a `NameSpaceError` will
        be raised if `strict` is true. Otherwise `name` will be returned
        unchanged.

        Example:

        >>> context = Context()
        >>> context.prefixed("Dataset")
        'dcat:Dataset'

        """
        if not self._prefixed:
            self._create_caches()
        if name in self._prefixed:
            return self._prefixed[name]
        if strict:
            raise NamespaceError(f"cannot prefix: {name}")
        return name

    def shortname(self, name: str, strict: bool = True) -> str:
        """Return the short name (keyword) corresponding to `name`.

        If `name` is not defined in the context, a `NameSpaceError` will
        be raised if `strict` is true. Otherwise `name` will be returned
        unchanged.

        Example:

        >>> context = Context()
        >>> context.shortname("dcat:Dataset")
        'Dataset'

        """
        if not self._shortnamed:
            self._create_caches()
        if name in self._shortnamed:
            return self._shortnamed[name]
        if strict:
            raise NamespaceError(f"no short name for: {name}")
        return name

    def getdef(self, name: str) -> dict:
        """Return JSON-LD definition of `name`."""
        shortname = self.shortname(name)
        return self.ctx["mappings"][shortname]

    def isref(self, name: str) -> bool:
        """Return wheter `name` is an object property that refers to a node."""
        return self.getdef(name).get("@type") == "@id"

    def is_object_property(self, name: str) -> bool:
        """Whether `name` appears to be an object property or not."""
        if (
            name
            in (
                "type",
                "rdf:type",
                RDF.type,
                "subClassOf",
                "rdfs:subClassOf",
                RDFS.subClassOf,
                "subPropertyOf",
                "rdfs:subPropertyOf",
                RDFS.subPropertyOf,
            )
            or name not in self
        ):
            return False
        return self.getdef(name).get("@type") == "@id"

    def is_data_property(self, name: str) -> bool:
        """Returns whether `name` appears to be a data property."""
        if name not in self or (
            self.is_object_property(name)
            or self.is_annotation_property(name)
            or self.is_class(name)
        ):
            return False
        type = self.getdef(name).get("@type")
        return bool(type) and type not in ("@id", RDFS.Class, OWL.Class)

    def is_annotation_property(self, name: str) -> bool:
        """Returns whether `name` appears to be an annotation property."""
        if name not in self:
            return False
        d = self.getdef(name)
        return "@type" not in d or "@language" in d

    def is_class(self, name: str) -> bool:
        """Returns whether `name` appears to be a class."""
        return name in self and self.getdef(name).get("@type") in (
            RDFS.Class,
            OWL.Class,
        )

    def expanddoc(self, doc: "Union[dict, list]") -> list:
        """Return expanded JSON-LD document `doc`."""
        return self.ld.expand(self._todict(doc), options={})

    def compactdoc(self, doc: dict) -> dict:
        """Return compacted JSON-LD document `doc`."""
        return self.ld.compact(doc, self.get_context_dict(), options={})

    def to_triplestore(
        self,
        ts,
        doc: "Union[dict, list]",
        force: "bool" = False,
        baseiri: "Optional[str]" = None,
    ) -> Graph:
        """Store JSON-LD document `doc` to triplestore `ts`.

        Arguments:
            ts: Triplestore to store to.
            doc: JSON-LD document to store, as a dict or list of dicts.
            force: If True, store document even if it contains invalid terms.
                Incomplete IRIs will be stored with namespace
                "http://falseiri/", unless baseiri is given.
            baseiri: If given, it will be used as a base iri to
                resolve relative IRIs. (I.e. Not valid URLs).

        Returns:
            The store RDFLIB Graph created from the document.

        """
        base = baseiri if baseiri else "https://falseiri/"

        g = Graph()

        g.parse(data=self._todict(doc), format="json-ld", base=base)

        # Check that no IRIs are in namespace "https://falseiri/".
        # If Force is True, issue a warning
        # If Force is False, raise an error
        for s, p, o in g:
            for term in (s, p, o):
                if isinstance(term, str) and term.startswith(
                    "https://falseiri/"
                ):
                    msg = (
                        f"Missing base iri for term: "
                        f"'{term.lstrip('https://falseiri/')}'"
                    )
                    if force:
                        warnings.warn(msg, NamespaceWarning)
                    else:
                        raise NamespaceError(msg)

        ts.parse(data=g.serialize(format="ntriples"), format="ntriples")

        if isinstance(doc, dict) and "@context" in doc:
            ctx = self.copy()
            ctx.add_context(doc)
        else:
            ctx = self
        for prefix, ns in ctx.get_prefixes().items():
            if prefix not in ts.namespaces:
                ts.bind(prefix, ns)
        return g

    def _todict(self, doc: "Union[dict, list]") -> dict:
        """Returns a shallow copy of doc as a dict with current
        context added."""
        if isinstance(doc, list):
            return {
                "@context": self.get_context_dict(),
                "@graph": doc,
            }

        if "@context" in doc:
            ctx = self.copy()
            ctx.add_context(doc["@context"])
            new = doc.copy()
            new["@context"] = ctx.get_context_dict()
        else:
            new = {"@context": self.get_context_dict()}
            new.update(doc)
        return new

    def _create_caches(self) -> None:
        """Create _expanded dict cached."""
        if self._expanded:
            return
        prefixes = self.get_prefixes()
        mappings = self.get_mappings()
        self._expanded["@type"] = RDF.type
        self._expanded["rdf:type"] = RDF.type
        self._expanded[RDF.type] = RDF.type
        self._prefixed[RDF.type] = "rdf:type"
        self._prefixed["rdf:type"] = "rdf:type"
        self._prefixed["@type"] = "rdf:type"
        self._shortnamed[RDF.type] = "@type"
        self._shortnamed["rdf:type"] = "@type"
        self._shortnamed["@type"] = "@type"
        for key, expanded in mappings.items():
            prefixed = prefix_iri(expanded, prefixes)
            self._update_caches(key, prefixed, expanded)

    def _update_caches(self, shortname, prefixed, expanded):
        self._expanded[shortname] = expanded
        self._expanded[prefixed] = expanded
        self._expanded[expanded] = expanded
        self._prefixed[shortname] = prefixed
        self._prefixed[prefixed] = prefixed
        self._prefixed[expanded] = prefixed
        self._shortnamed[shortname] = shortname
        self._shortnamed[prefixed] = shortname
        self._shortnamed[expanded] = shortname

    base = property(
        fget=lambda self: self.ctx.get("@base"),
        fset=lambda self, ns: self.add_context({"@base": ns}),
        doc="Base IRI against which to resolve those relative IRIs.",
    )
    processingMode = property(
        lambda self: self.ctx.get("processingMode"),
        doc="Tag for JSON-LD version that this context is processed against.",
    )

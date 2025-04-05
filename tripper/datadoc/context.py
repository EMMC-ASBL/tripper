"""Parse and work with JSON-LD context."""

# pylint: disable=too-many-branches,redefined-builtin

import re
import warnings
from typing import TYPE_CHECKING

from pyld import jsonld

from tripper.datadoc.keywords import Keywords
from tripper.errors import NamespaceError
from tripper.utils import MATCH_PREFIXED_IRI

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Sequence, Union

    # Possible types for a JSON-LD context
    ContextType = Union[str, dict, Sequence[Union[str, dict]], "Context"]


def get_context(
    keywords: "Optional[Keywords]" = None,
    domain: "Optional[Union[str, Sequence[str]]]" = None,
    context: "Optional[ContextType]" = None,
    processingMode: str = "json-ld-1.1",
) -> "Context":
    """A convinient function that returns an Context instance.

    Arguments:
        keywords: Initialise from this keywords instance.
        domain: Load initial context for this domain.
        context: Optional context to load.
        processingMode: Either "json-ld-1.0" or "json-ld-1.1".

    """
    if isinstance(context, Context):
        if keywords or domain:
            if not keywords:
                keywords = Keywords()
            if domain:
                keywords.add_field(domain)
            context.add_context(keywords.get_context())
    else:
        context = Context(
            keywords=keywords,
            domain=domain,  # type: ignore
            context=context,
            processingMode=processingMode,
        )
    return context


class Context:
    """A class representing a context."""

    def __init__(
        self,
        keywords: "Optional[Keywords]" = None,
        domain: "Union[str, Sequence[str]]" = "default",
        context: "Optional[ContextType]" = None,
        processingMode: str = "json-ld-1.1",
    ) -> None:
        """Initialises context object.

        Arguments:
            keywords: Initialise from this keywords instance.
            domain: Load initial context for this domain.
            context: Optional context to load.
            processingMode: Either "json-ld-1.0" or "json-ld-1.1".

        """
        self.ld = jsonld.JsonLdProcessor()
        self.ctx = self.ld._get_initial_context(
            options={"processingMode": processingMode}
        )
        self._expanded: dict = {}
        self._prefixed: dict = {}
        self._shortnamed: dict = {}

        if keywords:
            if domain:
                keywords.add_field(domain)
            self.add_context(keywords.get_context())
        elif domain:
            keywords = Keywords(field=domain)
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

    def copy(self) -> "Context":
        """Return a copy of this context."""
        copy = Context()
        copy.ctx = self.ctx  # frozendict - no need to copy
        return copy

    def add_context(self, context: "ContextType") -> None:
        """Add a context to this object."""
        if isinstance(context, Context):
            context = context.get_context_dict()
        elif "@context" in context:
            context = context["@context"]  # type: ignore

        if "@id" in context:
            warnings.warn(
                f"skip adding context with @id keyword: {repr(context)[:100]}"
            )
            return

        self.ctx = self.ld.process_context(self.ctx, context, options={})
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

    def get_prefixes(self) -> dict:
        """Return a dict mapping prefixes to IRIs."""
        return {
            k: v["@id"]
            for k, v in self.ctx["mappings"].items()
            if v.get("_prefix") and "@id" in v
        }

    def get_mappings(self) -> dict:
        """Return a dict mapping prefixes to IRIs."""
        return {
            k: v["@id"]
            for k, v in self.ctx["mappings"].items()
            if v.get("_prefix") is False and "@id" in v
        }

    def expand(self, name, strict=False) -> str:
        """Return `name` expanded to a full IRI.

        Example:

        >>> context = Context()
        >>> context.expand("Dataset")
        'http://www.w3.org/ns/dcat#Dataset'

        """
        # Check cache: _expanded
        if self._expanded:
            if name in self._expanded:
                return self._expanded[name]
            if re.match(MATCH_PREFIXED_IRI, name):
                prefix, shortname = name.split(":", 1)
                prefixes = self.get_prefixes()
                if prefix in prefixes:
                    expanded = f"{prefixes[prefix]}{shortname}"
                    # Save to cache for later use
                    self._expanded[shortname] = expanded
                    self._expanded[name] = expanded
                    self._expanded[expanded] = expanded
                    self._prefixed[shortname] = name
                    self._prefixed[name] = name
                    self._prefixed[expanded] = name
                    self._shortnamed[shortname] = shortname
                    self._shortnamed[name] = shortname
                    self._shortnamed[expanded] = shortname
                    return expanded
            if strict:
                raise NamespaceError(f"cannot expand: {name}")
            return name
        # Check ctx
        if name in self.ctx["mappings"]:
            return self.ctx["mappings"][name]["@id"]
        # Create cache: _expanded
        self._create_caches()
        return self.expand(name, strict=strict)

    def prefixed(self, name) -> str:
        """Return `name` as a prefixed IRI.

        Example:

        >>> context = Context()
        >>> context.prefixed("Dataset")
        'dcat:Dataset'

        """
        if not self._prefixed:
            self._create_caches()
        if name in self._prefixed:
            return self._prefixed[name]
        raise NamespaceError(f"cannot prefix: {name}")

    def shortname(self, name) -> str:
        """Return the short name (keyword) corresponding to `name`.

        Example:

        >>> context = Context()
        >>> context.shortname("dcat:Dataset")
        'Dataset'

        """
        if not self._shortnamed:
            self._create_caches()
        if name in self._shortnamed:
            return self._shortnamed[name]
        raise NamespaceError(f"no short name for: {name}")

    def expanddoc(self, doc: dict) -> list:
        """Return expanded JSON-LD document `doc`."""
        return self.ld.expand(doc, options={})

    def compactdoc(self, doc: dict) -> dict:
        """Return compacted JSON-LD document `doc`."""
        return self.ld.compact(doc, self.get_context_dict(), options={})

    def _create_caches(self) -> None:
        """Create _expanded dict cached."""
        if self._expanded:
            return
        prefixes = self.get_prefixes()
        mappings = self.get_mappings()
        self._expanded.update(mappings)
        self._expanded.update((v, v) for v in mappings.values())
        for key, expanded in mappings.items():
            for prefix, ns in prefixes.items():
                if expanded.startswith(ns):
                    prefixed = f"{prefix}:{key}"
                    self._expanded[prefixed] = expanded
                    self._prefixed[key] = prefixed
                    self._prefixed[prefixed] = prefixed
                    self._prefixed[expanded] = prefixed
                    self._shortnamed[key] = key
                    self._shortnamed[prefixed] = key
                    self._shortnamed[expanded] = key
                    break

"""Parse and work with JSON-LD context."""

# pylint: disable=too-many-branches,redefined-builtin

from typing import TYPE_CHECKING

from pyld import jsonld

from tripper.datadoc.keywords import Keywords
from tripper.errors import NamespaceError

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Sequence, Union

    # Possible types for a JSON-LD context
    ContextType = Union[str, dict, Sequence[Union[str, dict]]]


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

    def copy(self) -> "Context":
        """Return a copy of this context."""
        copy = Context()
        copy.ctx = self.ctx  # frozendict - no need to copy
        return copy

    def add_context(self, context: "ContextType") -> None:
        """Add a context to this object."""
        self.ctx = self.ld.process_context(self.ctx, context, options={})
        # Clear caches
        self._expanded.clear()
        self._prefixed.clear()
        self._shortnamed.clear()

    def get_context_dict(self) -> dict:
        """Return a context dict."""
        return {k: v.get("@id") for k, v in self.ctx["mappings"].items()}

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

    def expand(self, name) -> str:
        """Return `name` expanded to a full IRI."""
        # Check cache: _expanded
        if self._expanded:
            if name in self._expanded:
                return self._expanded[name]
            raise NamespaceError(f"cannot expand: {name}")
        # Check ctx
        if name in self.ctx["mappings"]:
            return self.ctx["mappings"][name]["@id"]
        # Create cache: _expanded
        self._create_caches()
        return self.expand(name)

    def prefixed(self, name) -> str:
        """Return `name` as a prefixed IRI."""
        if not self._prefixed:
            self._create_caches()
        if name in self._prefixed:
            return self._prefixed[name]
        raise NamespaceError(f"cannot prefix: {name}")

    def shortname(self, name) -> str:
        """Return the short name (keyword) corresponding to `name`."""
        if not self._shortnamed:
            self._create_caches()
        if name in self._shortnamed:
            return self._shortnamed[name]
        raise NamespaceError(f"no short name for: {name}")

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

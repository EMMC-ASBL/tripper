"""Parse keywords definition and generate context."""

# pylint: disable=too-many-branches,redefined-builtin,too-many-lines
# pylint: disable=logging-not-lazy,logging-fstring-interpolation

import json
import logging
import os
import warnings
from copy import deepcopy
from importlib import import_module
from io import IOBase

# from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import yaml
from rdflib.util import SUFFIX_FORMAT_MAP as RDFLIB_SUFFIX_FORMAT_MAP
from rdflib.util import guess_format as guess_rdf_format

import tripper
from tripper import DDOC, OWL, RDF, RDFS, XSD, Triplestore
from tripper.datadoc.errors import (
    DatadocValueError,
    InvalidDatadocError,
    InvalidKeywordError,
    MissingKeyError,
    NoSuchTypeError,
    ParseError,
    PrefixMismatchError,
    RedefineError,
    RedefineKeywordWarning,
    SkipRedefineKeywordWarning,
)
from tripper.datadoc.utils import add, asseq, iriname, merge
from tripper.utils import (
    AttrDict,
    expand_iri,
    get_entry_points,
    is_curie,
    is_uri,
    openfile,
    prefix_iri,
    recursive_update,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import IO, Any, Iterable, List, Optional, Set, Tuple, Union

    FileLoc = Union[Path, str]
    KeywordsType = Union["Keywords", dict, IO, Path, str, Sequence]


# Module-level logger
logger = logging.getLogger(__name__)


# Pre-defined conformance levels
CONFORMANCE_MAPS = {
    "mandatory": "mandatory",
    DDOC.mandatory: "mandatory",
    "ddoc:mandatory": "mandatory",
    "recommended": "recommended",
    DDOC.recommended: "recommended",
    "ddoc:recommended": "recommended",
    "optional": "optional",
    DDOC.optional: "optional",
    "ddoc:optional": "optional",
}


# Todo: If enabling caching, ensure that the returned keywords object
# is immutable.
# @lru_cache(maxsize=32)
def get_keywords(
    keywords: "Optional[KeywordsType]" = None,
    format: "Optional[str]" = None,
    theme: "Optional[Union[str, Sequence[str]]]" = "ddoc:datadoc",
    yamlfile: "Optional[FileLoc]" = None,
    timeout: float = 3,
    strict: bool = False,
    redefine: str = "raise",
) -> "Keywords":
    """A convenient function that returns a Context instance.

    Arguments:
        keywords: Optional existing keywords object.
        format: Format of input if `keywords` refer to a file that can be
            loaded.
        theme: IRI of one of more themes to load keywords for.
        yamlfile: YAML file with keyword definitions to parse.  May also
            be an URI in which case it will be accessed via HTTP GET.
            Deprecated. Use the `add_yaml()` or `add()` methods instead.
        timeout: Timeout in case `yamlfile` is a URI.
        strict: Whether to raise an `InvalidKeywordError` exception if `d`
            contains an unknown key.
        redefine: Determine how to handle redefinition of existing
            keywords.  Should be one of the following strings:
              - "allow": Allow redefining a keyword. Emits a
                `RedefineKeywordWarning`.
              - "skip": Don't redefine existing keyword. Emits a
                `RedefineKeywordWarning`.
              - "raise": Raise an RedefineError (default).
    """
    if isinstance(keywords, Keywords):
        kw = keywords
        if theme:
            kw.add_theme(
                theme, timeout=timeout, strict=strict, redefine=redefine
            )
    else:
        kw = Keywords(theme=theme)
        if keywords:
            kw.add(
                keywords,
                format=format,
                timeout=timeout,
                strict=strict,
                redefine=redefine,
            )

    if yamlfile:
        warnings.warn(
            "The `yamlfile` argument is deprecated. Use the `add_yaml()` or "
            "`add()` methods instead.",
            DeprecationWarning,
        )
        kw.load_yaml(
            yamlfile, timeout=timeout, strict=strict, redefine=redefine
        )

    return kw


def load_datadoc_schema(ts: "Triplestore") -> None:
    """Load schema for data documentation to triplestore `ts`.

    It is safe to call this function more than once.
    """
    if not ts.query(f"ASK WHERE {{ <{-DDOC}> a <{OWL.Ontology}> }}"):
        ts.bind("ddoc", DDOC)
        path = Path(tripper.__file__).parent / "context" / "datadoc.ttl"
        ts.parse(path)


class Keywords:
    """A class representing all keywords within a theme."""

    # pylint: disable=too-many-public-methods

    rootdir = Path(__file__).absolute().parent.parent.parent.resolve()

    def __init__(
        self,
        theme: "Optional[Union[str, Sequence[str]]]" = "ddoc:datadoc",
        yamlfile: "Optional[FileLoc]" = None,
        timeout: float = 3,
    ) -> None:
        """Initialises keywords object.

        Arguments:
            theme: IRI of one of more themes to load keywords for.
            yamlfile: A YAML file with keyword definitions to parse.  May also
                be an URI in which case it will be accessed via HTTP GET.
                Deprecated. Use the `add_yaml()` or `add()` methods instead.
            timeout: Timeout in case `yamlfile` is a URI.

        Attributes:
            data: The dict loaded from the keyword yamlfile.
            keywords: A dict mapping keywords (name/prefixed/iri) to dicts
                describing the keywords.
            theme: IRI of a theme or scientic domain that the keywords
                belong to.
        """
        default_prefixes = AttrDict(ddoc=str(DDOC))
        self.theme = None  # theme for this object
        self.data = AttrDict(prefixes=default_prefixes, resources=AttrDict())

        # A "view" into `self.data`. A dict mapping short, prefixed
        # and expanded keyword names to corresponding value dicts in
        # self.data.
        self.keywords = AttrDict()

        # Themes and files that has been parsed
        self.parsed: "set" = set()

        if theme:
            self.add_theme(theme)

        if yamlfile:
            warnings.warn(
                "The `yamlfile` argument is deprecated. Use the `add_yaml()` "
                "or `add()` methods instead.",
                DeprecationWarning,
            )
            if isinstance(yamlfile, (str, Path)):
                self.load_yaml(yamlfile, timeout=timeout)
            else:
                for path in yamlfile:
                    self.load_yaml(path, timeout=timeout)

    def __contains__(self, item):
        return item in self.keywords

    def __getitem__(self, key):
        return self.keywords[key]

    def __iter__(self):
        return iter(k for k in self.keywords if is_curie(k))

    def __len__(self):
        return len(list(self.__iter__()))

    def __dir__(self):
        return dir(Keywords) + ["data", "keywords", "theme"]

    def __eq__(self, other):
        return self.data == other.data and self.theme == other.theme

    def _set_keyword(self, keywords, keyword, value, redefine=False):
        """Add new keyword-value pair to `keywords` dict."""
        # value = AttrDict(value)
        expanded = expand_iri(value.iri, self.get_prefixes())
        prefixed = prefix_iri(expanded, self.get_prefixes())
        if redefine or keyword not in keywords:
            keywords[keyword] = value
        if redefine or prefixed not in keywords:
            keywords[prefixed] = value
        if redefine or expanded not in keywords:
            keywords[expanded] = value

    def _set_keywords(self, clear=True, redefine=False):
        """Update internal keywords attribute to data attribute.

        Arguments:
            clear: If false, only new keywords will be added, but nothing
                removed.
            redefine: Wheter to redefine existing keyword.
        """
        if clear:
            self.keywords.clear()
        for clsvalue in self.data.get("resources", AttrDict()).values():
            for keyword, value in clsvalue.get("keywords", AttrDict()).items():
                self._set_keyword(
                    self.keywords, keyword, value, redefine=redefine
                )

    def copy(self):
        """Returns a copy of self."""
        new = Keywords(theme=None)
        new.theme = self.theme
        new.data = deepcopy(self.data)
        new.keywords = deepcopy(self.keywords)
        new.parsed = self.parsed.copy()
        return new

    def add(
        self,
        keywords: "Optional[KeywordsType]",
        format: "Optional[Union[str, Sequence]]" = None,
        timeout: float = 3,
        strict: bool = False,
        redefine: str = "raise",
    ) -> None:
        """Add `keywords` to this Keywords object.

        Arguments:
            keywords: Keywords definitions to add to this Keyword object.
                May be another Keyword object, path to a file, theme or a
                sequence of these.
            format: Format if `keywords`. Recognised formats include:
                yaml, csv, tsv, turtle, xml, json-ld, rdfa, ...
            timeout: Timeout when accessing remote files.
            strict: Whether to raise an `InvalidKeywordError` exception if `d`
                contains an unknown key.
            redefine: Determine how to handle redefinition of existing
                keywords.  Should be one of the following strings:
                  - "allow": Allow redefining a keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "skip": Don't redefine existing keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "raise": Raise an RedefineError (default).

        """
        if not isinstance(keywords, str) and isinstance(keywords, Sequence):
            if isinstance(format, str):
                format = [format] * len(keywords)
            elif format and len(format) != len(keywords):
                raise TypeError(
                    "If given, `format` must have the same length as "
                    "`keywords`"
                )

        def _add(kw, fmt):
            if kw is None:
                pass
            elif isinstance(kw, Keywords):
                self.theme = merge(self.theme, kw.theme)
                recursive_update(self.data, kw.data, cls=AttrDict)
                self._set_keywords(clear=False)
            elif isinstance(kw, dict):
                self._load_yaml(kw, strict=strict, redefine=redefine)
            elif not isinstance(kw, str) and isinstance(kw, Sequence):
                for i, e in enumerate(kw):
                    _add(e, fmt[i] if fmt else None)
            elif isinstance(kw, (str, Path, IOBase)):
                if (
                    isinstance(kw, str)
                    and ":" in kw
                    and not (
                        kw.startswith("/") or kw.startswith("./") or is_uri(kw)
                    )
                ):
                    self.add_theme(
                        kw,
                        timeout=timeout,
                        strict=strict,
                        redefine=redefine,
                    )
                else:
                    if not fmt:
                        name = kw.name if hasattr(kw, "name") else kw
                        fmt = Path(name).suffix
                    fmt = fmt.lstrip(".").lower()
                    # pylint:disable=consider-using-get
                    if fmt in RDFLIB_SUFFIX_FORMAT_MAP:
                        fmt = RDFLIB_SUFFIX_FORMAT_MAP[fmt]

                    if fmt in ("yaml", "yml"):
                        self.load_yaml(
                            kw,
                            timeout=timeout,
                            strict=strict,
                            redefine=redefine,
                        )
                    elif fmt in ("csv", "tsv", "xlsx", "excel"):
                        self.load_table(kw, format=fmt)
                    else:
                        self.load_rdffile(
                            kw,
                            format=fmt,
                            timeout=timeout,
                            strict=strict,
                            redefine=redefine,
                        )
            else:
                raise TypeError(
                    "`keywords` must be a KeywordsType object (Keywords "
                    "instance, dict, IO, Path, string or sequence). "
                    f"Got: {type(kw)}"
                )

        _add(keywords, format)

    def add_theme(
        self,
        theme: "Union[str, Sequence[str]]",
        timeout: float = 3,
        strict: bool = False,
        redefine: str = "raise",
    ) -> None:
        """Add keywords for `theme`, where `theme` is the IRI of a
        theme or scientific domain or a list of such IRIs.

        Arguments:
            theme: IRI (or list of IRIs) of a theme/scientific domain to load.
            timeout: Timeout when accessing remote files.
            strict: Whether to raise an `InvalidKeywordError` exception if the
                theme contains an unknown key.
            redefine: Determine how to handle redefinition of existing
                keywords.  Should be one of the following strings:
                  - "allow": Allow redefining a keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "skip": Don't redefine existing keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "raise": Raise an RedefineError (default).

        """
        if isinstance(theme, str):
            theme = [theme]

        parsedkey = (tuple(theme), strict, redefine)
        if parsedkey in self.parsed:
            return

        for name in theme:  # type: ignore
            expanded = expand_iri(name, self.get_prefixes())
            prefixed = prefix_iri(name, self.get_prefixes())
            add(
                self.data,
                "theme",
                prefixed,
            )
            for ep in get_entry_points("tripper.keywords"):
                if expand_iri(ep.value, self.get_prefixes()) == expanded:
                    package_name, path = ep.name.split("/", 1)
                    package = import_module(package_name)
                    fullpath = (
                        Path(package.__file__).parent / path  # type: ignore
                    )
                    self.add(
                        fullpath,
                        timeout=timeout,
                        strict=strict,
                        redefine=redefine,
                    )
                    break
            else:
                # Fallback in case the entry point is not installed
                if expanded == DDOC.datadoc:
                    self.load_yaml(
                        self.rootdir
                        / "tripper"
                        / "context"
                        / "0.3"
                        / "keywords.yaml",
                        timeout=timeout,
                        strict=strict,
                        redefine=redefine,
                    )
                else:
                    raise TypeError(f"Unknown theme: {name}")

        self.parsed.add(parsedkey)

    def load_yaml(
        self,
        yamlfile: "Union[Path, str]",
        timeout: float = 3,
        strict: bool = True,
        redefine: str = "raise",
    ) -> None:
        """Load YAML file with keyword definitions.

        Arguments:
            yamlfile: Path of URL to a YAML file to load.
            timeout: Timeout when accessing remote files.
            strict: Whether to raise an `InvalidKeywordError` exception if `d`
                contains an unknown key.
            redefine: Determine how to handle redefinition of existing
                keywords.  Should be one of the following strings:
                  - "allow": Allow redefining a keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "skip": Don't redefine existing keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "raise": Raise an RedefineError (default).

        """
        parsedkey = (yamlfile, strict, redefine)
        if parsedkey in self.parsed:
            return

        with openfile(yamlfile, timeout=timeout, mode="rt") as f:
            d = yaml.safe_load(f)
        try:
            self._load_yaml(d, strict=strict, redefine=redefine)
        except Exception as exc:
            raise ParseError(f"error parsing '{yamlfile}'") from exc

        self.parsed.add(parsedkey)

    def _load_yaml(
        self,
        d: dict,
        strict: bool = True,
        redefine: str = "raise",
    ) -> None:
        """Parse a dict with keyword definitions following the format of
        the YAML file.

        Arguments:
            d: Dict defining a keyword following the YAML file format.
            strict: Whether to raise an `InvalidKeywordError` exception if `d`
                contains an unknown key.
            redefine: Determine how to handle redefinition of existing
                keywords.  Should be one of the following strings:
                  - "allow": Allow redefining a keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "skip": Don't redefine existing keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "raise": Raise an RedefineError (default).

        """
        # pylint: disable=too-many-nested-blocks,too-many-statements
        # pylint: disable=too-many-locals
        self.add(d.get("basedOn"))

        required_resource_keys = {"iri"}
        valid_resource_keys = {
            "iri",
            "subClassOf",
            "description",
            "usageNote",
            "keywords",
        }
        required_keywords = {"iri"}
        valid_keywords = {
            "name",
            "iri",
            "type",
            "subPropertyOf",
            "inverseOf",  # XXX - to be implemented
            "domain",
            "range",
            "datatype",
            "inverse",  # XXX - to be implemented (remove?)
            "unit",  # XXX - to be implemented
            "conformance",
            "description",
            "usageNote",
            "theme",
            "default",
        }
        iri_keywords = {
            "iri",
            "type",
            "subPropertyOf",
            "inverseOf",
            "domain",
            "range",
            "datatype",
        }
        valid_conformances = ["mandatory", "recommended", "optional"]

        def to_prefixed(x):
            """Help function that converts an IRI or list of IRIs to
            prefixed IRIs."""
            if isinstance(x, str):
                return self.prefixed(x, strict=False)
            return [to_prefixed(e) for e in x]

        # Create a deep copies that we are updating
        prefixes = deepcopy(self.data.prefixes)
        resources = deepcopy(self.data.resources)
        keywords = deepcopy(self.keywords)

        # Prefixes
        for prefix, ns in d.get("prefixes", AttrDict()).items():
            if prefix in prefixes and ns != prefixes[prefix]:
                raise PrefixMismatchError(
                    f"prefix '{prefix}' is already mapped to "
                    f"'{prefixes[prefix]}'. Cannot redefine it to '{ns}'"
                )
            prefixes[prefix] = ns

        # Map keywords IRIs to keyword definitions
        iridefs = {}
        for defs in d.get("resources", {}).values():
            for kw, val in defs.get("keywords", {}).items():
                # Check that value has all the required keywords
                for k in required_keywords:
                    if k not in val:
                        raise MissingKeyError(f"no '{k}' in keyword '{kw}'")
                key = prefix_iri(val["iri"], prefixes)
                if len(val) > 1 or key not in iridefs:
                    iridefs[key] = val

        # Resources
        for cls, defs in d.get("resources", AttrDict()).items():
            resval = resources.get(cls, AttrDict())

            defs = AttrDict(defs).copy()
            for key in required_resource_keys:
                if key not in defs:
                    raise MissingKeyError(
                        f"missing required key '{key}' for resource '{cls}'"
                    )
            for key in defs:
                if strict and key not in valid_resource_keys:
                    raise InvalidDatadocError(f"invalid resource key: '{key}'")
            # TODO: Check for redefinition of existing class

            resval.iri = prefix_iri(defs.iri, prefixes)
            if "subClassOf" in defs:
                resval.subClassOf = to_prefixed(defs.subClassOf)
            if "description" in defs:
                resval.description = defs.description
            if "usageNote" in defs:
                resval.usageNote = defs.usageNote
            resval.setdefault("keywords", AttrDict())

            for keyword, value in defs.get("keywords", AttrDict()).items():

                # If a value only contain an IRI, replace it with a more
                # elaborate definition (if it exists)
                if len(value) == 1:
                    value = AttrDict(iridefs[value["iri"]])

                # Check conformance values
                if "conformance" in value:
                    c = value["conformance"]
                    if c not in valid_conformances:
                        raise DatadocValueError(f"invalid conformance: {c}")

                # If strict, check that all keys are known
                if strict:
                    for k in value.keys():
                        if k not in valid_keywords:
                            raise InvalidKeywordError(
                                f"keyword '{keyword}' has invalid key: {k}"
                            )

                # Normalise IRIs in values to prefixed IRIs
                value = AttrDict(value).copy()
                for k in iri_keywords:
                    if k in value:
                        value[k] = to_prefixed(value[k])

                # Add extra annotations to value
                if "name" not in value or ":" in value.name:
                    value.name = keyword
                if "theme" in d:
                    add(value, "theme", d["theme"])
                add(value, "domain", prefix_iri(defs.iri, prefixes))

                # Check whether we try to redefine an existing keyword
                skip = False
                if keyword in keywords:
                    for k, v in value.items():
                        oldval = keywords[keyword].get(k)
                        if k in ("iri", "domain") or v == oldval:
                            continue
                        oldiri = keywords[keyword].iri
                        if value.iri == oldiri:
                            if redefine != "allow":
                                raise RedefineError(
                                    "Cannot redefine existing concept "
                                    f"'{value.iri}'. Trying to change "
                                    f"property '{k}' from '{oldval}' to "
                                    f"'{v}'."
                                )
                            warnings.warn(
                                "Redefining existing concept "
                                f"'{value.iri}'. Change property "
                                f"'{k}' from '{oldval}' to '{v}'.",
                                RedefineKeywordWarning,
                            )
                        if redefine == "raise":
                            raise RedefineError(
                                f"Trying to redefine keyword "
                                f"'{keyword}' from '{oldiri}' "
                                f"to '{value.iri}'."
                            )
                        if redefine == "skip":
                            skip = True
                            warnings.warn(
                                f"Skip redefinition of keyword: {keyword}",
                                SkipRedefineKeywordWarning,
                            )
                        elif redefine == "allow":
                            warnings.warn(
                                f"Redefining keyword '{keyword}' from "
                                f"'{oldiri}' to '{value.iri}'.",
                                RedefineKeywordWarning,
                            )
                        else:
                            raise ValueError(
                                "Invalid value of `redefine` "
                                f'argument: "{redefine}".  Should be '
                                'one of "allow", "keep" or "raise".'
                            )
                        break
                if skip:
                    continue

                kw = resval.keywords
                if keyword in kw:
                    kw[keyword].update(value)
                else:
                    kw[keyword] = value

                self._set_keyword(keywords, keyword, value, redefine=True)

            if cls in resources:
                resources[cls].update(resval)
            else:
                resources[cls] = resval

        # Everything succeeded, update instance
        self.data.prefixes.update(prefixes)
        self.data.resources.update(resources)
        self.keywords.update(keywords)

        # Run an extra round and add keywords we have missed.
        self._set_keywords(clear=False, redefine=False)

    def save_yaml(
        self,
        yamlfile: "Union[Path, str]",
        keywords: "Optional[Sequence[str]]" = None,
        classes: "Optional[Union[str, Sequence[str]]]" = None,
        themes: "Optional[Union[str, Sequence[str]]]" = None,
        namespace_filter: "Optional[Union[str, Sequence[str]]]" = None,
    ) -> None:
        """Save YAML file with keyword definitions.

        Arguments:
            yamlfile: File to save keyword definitions to.
            keywords: Sequence of keywords to include.
            classes: Include keywords that have these classes in their domain.
            themes: Include keywords for these themes.
            namespace_filter: A prefix, namespace or a sequence of these.
                If given, keep only keywords and classes from the returned
                `keywordset` and `classet` with IRIs in one of
                these namespaces.

        """
        keywords, classes, themes = self._keywords_list(
            keywords, classes, themes, namespace_filter=namespace_filter
        )
        resources = {}
        for cls, clsval in self.data.resources.items():
            if self.prefixed(cls) in classes:
                resources[cls] = dict(clsval.copy())
                resources[cls]["keywords"] = {}
                for k, v in self.data.resources[cls].keywords.items():
                    if self.prefixed(k) in keywords:
                        resources[cls]["keywords"][k] = dict(v)
        data = dict(self.data.copy())
        del data["resources"]
        recursive_update(data, {}, cls=dict)
        data["resources"] = resources

        with open(yamlfile, "wt", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)

    def load_table(
        self,
        filename: "FileLoc",
        format: "Optional[str]" = None,  # pylint: disable=unused-argument
        prefixes: "Optional[dict]" = None,
        theme: "Optional[str]" = None,
        basedOn: "Optional[Union[str, List[str]]]" = None,
        **kwargs,
    ) -> None:
        """Load keywords from a csv file.

        Arguments:
            filename: File to load.
            format: File format. Unused.  Only csv is currently supported.
            prefixes: Dict with additional prefixes used in the table.
            theme: Theme defined by the table.
            basedOn: Theme(s) that the table is based on.
            kwargs: Keyword arguments passed on to TableDoc.parse_csv().
        """
        # pylint: disable=import-outside-toplevel
        from tripper.datadoc.tabledoc import TableDoc

        td = TableDoc.parse_csv(
            filename, type=None, prefixes=prefixes, **kwargs
        )
        dicts = td.asdicts()
        self.fromdicts(dicts, prefixes=prefixes, theme=theme, basedOn=basedOn)

    def save_table(
        self,
        filename: "FileLoc",
        format: "Optional[str]" = None,  # pylint: disable=unused-argument
        names: "Optional[Sequence]" = None,
        strip: bool = True,
        keymode: str = "name",
        **kwargs,
    ) -> None:
        # pylint: disable=line-too-long
        """Load keywords from a csv file.

        Arguments:
            filename: File to load.
            format: File format. Unused.  Only csv is currently supported.
            names: A sequence of keyword or class names to save.  The
                default is to save all keywords.
            strip: Whether to strip leading and trailing whitespaces
                from cells.
            keymode: How to represent column headers.  Should be either
                "name", "prefixed" (CURIE) or "expanded" (full IRI).
            kwargs: Additional keyword arguments passed to the writer.
                For more details, see [write_csv()].

        References:
        [write_csv()]: https://emmc-asbl.github.io/tripper/latest/api_reference/datadoc/tabledoc/#tripper.datadoc.tabledoc.TableDoc.write_csv
        """
        # pylint: disable=import-outside-toplevel
        from tripper.datadoc.tabledoc import TableDoc

        dicts = self.asdicts(names, keymode=keymode)
        td = TableDoc.fromdicts(dicts, type=None, keywords=self, strip=strip)
        td.write_csv(filename, **kwargs)

    def keywordnames(self) -> "list":
        """Return a list with all keyword names defined in this instance."""
        return [k for k in self.keywords.keys() if ":" not in k]

    def classnames(self) -> "list":
        """Return a list with all class names defined in this instance."""
        return list(self.data.resources.keys())

    def asdicts(
        self,
        names: "Optional[Sequence]" = None,
        keymode: str = "prefixed",
    ) -> "List[dict]":
        """Return the content of this Keywords object as a list of JSON-LD
        dicts.

        Arguments:
            names: A sequence of keyword or class names.  The
                default is to return all keywords.
            keymode: How to represent keys.  Should be either "name",
                "prefixed" (CURIE) or "expanded" (full IRI).

        Returns:
            List of JSON-LD dicts corresponding to `names`.
        """
        keymodes = {
            "name": iriname,
            "prefixed": None,
            "expanded": self.expanded,
        }
        maps = {
            "subPropertyOf": "rdfs:subPropertyOf",
            "unit": "ddoc:unitSymbol",
            "description": "dcterms:description",
            "usageNote": "vann:usageNote",
            "theme": "dcat:theme",
        }

        def key(k):
            """Return key `k` accordig to `keymode`."""
            return keymodes[keymode](k) if keymodes[keymode] else k

        conformance_indv = {v: k for k, v in CONFORMANCE_MAPS.items()}
        if names is None:
            names = self.keywordnames()

        classes = []
        dicts = []
        for name in names:
            if name not in self.keywords:
                classes.append(name)
                continue
            d = self.keywords[name]
            if "range" in d and self.expanded(d.range) != RDFS.Literal:
                proptype = "owl:ObjectProperty"
                range = d.range
            elif (
                "datatype" in d and self.expanded(d.datatype) != RDF.langString
            ):
                proptype = "owl:DatatypeProperty"
                range = d.get("datatype")
            else:
                proptype = "owl:AnnotationProperty"
                range = d.get("datatype")

            dct = {
                "@id": d.iri,
                "@type": proptype,
                key("rdfs:label"): d.name,
            }
            if "domain" in d:
                dct[key("rdfs:domain")] = d.domain
            if range:
                dct[key("rdfs:range")] = range
            if "conformance" in d:
                dct[key("ddoc:conformance")] = conformance_indv.get(
                    d.conformance, d.conformance
                )
            for k, v in d.items():
                if k in maps:
                    dct[key(maps[k])] = v
            dicts.append(dct)

        if classes:
            classmaps = {}
            for k, v in self.data.resources.items():
                classmaps[k] = k
                classmaps[self.expanded(k)] = k
                classmaps[self.prefixed(k)] = k

            for name in classes:
                d = self.data.resources[classmaps[name]]
                dct = {"@id": d.iri, "@type": OWL.Class}
                if "subClassOf" in d:
                    dct[key("rdfs:subClassOf")] = d.subClassOf
                if "description" in d:
                    dct[key("dcterms:description")] = d.description
                if "usageNote" in d:
                    dct[key("vann:usageNote")] = d.usageNote
                dicts.append(dct)

        return dicts

    def fromdicts(
        self,
        dicts: "Sequence[dict]",
        prefixes: "Optional[dict]" = None,
        theme: "Optional[str]" = None,
        basedOn: "Optional[Union[str, List[str]]]" = None,
        strict: bool = False,
        redefine: str = "raise",
    ) -> None:
        """Populate this Keywords object from a sequence of dicts.

        Arguments:
            dicts: A sequence of JSON-LD dicts to populate this keywords object
                from.  Their format should follow what is returned by
                tripper.datadoc.acquire().
            prefixes: Dict with additional prefixes used by `dicts`.
            theme: Theme defined by `dicts`.
            basedOn: Theme(s) that `dicts` are based on.
            strict: Whether to raise an `InvalidKeywordError` exception if `d`
                contains an unknown key.
            redefine: Determine how to handle redefinition of existing
                keywords.  Should be one of the following strings:
                  - "allow": Allow redefining a keyword.
                  - "skip": Don't redefine existing keyword.
                  - "raise": Raise an RedefineError (default).

        """
        data = self._fromdicts(
            dicts,
            prefixes=prefixes,
            theme=theme,
            basedOn=basedOn,
        )
        self._load_yaml(data, strict=strict, redefine=redefine)

    def _fromdicts(
        self,
        dicts: "Sequence[dict]",
        prefixes: "Optional[dict]" = None,
        theme: "Optional[str]" = None,
        basedOn: "Optional[Union[str, List[str]]]" = None,
    ) -> dict:
        """Help method for `fromdicts()` that returns a dict with
        keyword definitions following the format of the YAML file.
        """
        # pylint: disable=too-many-locals,too-many-statements

        def to_prefixed(x, prefixes, strict=True):
            """Help function that converts an IRI or list of IRIs to
            prefixed IRIs."""
            if isinstance(x, str):
                return prefix_iri(x, prefixes, strict=strict)
            return [to_prefixed(e, prefixes, strict=strict) for e in x]

        # Prefixes (merged with self.data.prefixes)
        p = self.get_prefixes().copy()
        if prefixes:
            for prefix, ns in prefixes.items():
                if prefix in p and p[prefix] != ns:
                    raise PrefixMismatchError(
                        f"adding prefix `{prefix}: {ns}` but it is already "
                        f"defined to '{p[prefix]}'"
                    )
            p.update({k: str(v) for k, v in prefixes.items()})

        def isproperty(v):
            if "@type" not in v:
                return False
            types = [v["@type"]] if isinstance(v["@type"], str) else v["@type"]
            for t in types:
                exp = expand_iri(t, p, strict=True)
                if exp in (
                    OWL.AnnotationProperty,
                    OWL.ObjectProperty,
                    OWL.DatatypeProperty,
                    RDF.Property,
                ):
                    return True
            return False

        entities = {expand_iri(d["@id"], p): d for d in dicts}
        properties = {k: v for k, v in entities.items() if isproperty(v)}
        classes = {k: v for k, v in entities.items() if k not in properties}

        data = AttrDict()
        if theme:
            data.theme = theme
        if basedOn:
            data.basedOn = basedOn
        data.prefixes = p
        data.resources = AttrDict()
        resources = data.resources

        # Add classes
        clslabels = {}
        for k, v in classes.items():
            d = AttrDict(iri=prefix_iri(k, p))
            for kk, vv in v.items():
                if kk in ("description", "usageNote"):
                    d[kk] = vv
                if kk == "subClassOf":
                    if isinstance(vv, str):
                        d[kk] = to_prefixed(vv, p, strict=True)
            d.setdefault("keywords", AttrDict())
            label = v["label"] if "label" in v else iriname(k)
            resources[label] = d
            clslabels[d.iri] = label

        # Add properties
        for propname, value in properties.items():
            name = iriname(propname)
            label = value["label"] if "label" in value else name
            d = AttrDict(iri=value["@id"])
            if "@type" in value:
                d.type = to_prefixed(value["@type"], p)
            d.domain = value.get("domain", RDFS.Resource)

            for domain in asseq(d.domain):
                dlabel = prefix_iri(domain, p, strict=True)
                domainname = clslabels.get(dlabel, iriname(domain))
                if domainname not in resources:
                    if domainname not in self.data.resources:
                        if domainname not in ("Resource",):
                            logger.info(
                                f"Adding undefined domain '{domain}' for "
                                f"keyword '{label}'"
                            )
                        r = AttrDict(
                            iri=prefix_iri(domain, p),
                            keywords=AttrDict(),
                        )
                    else:
                        r = self.data.resources[domainname].copy()
                    resources[domainname] = r
                    r.keywords[label] = d
                else:
                    resources[domainname].keywords[label] = d
            if "range" in value:
                _types = asseq(d.get("type", OWL.AnnotationProperty))
                types = [expand_iri(t, p) for t in _types]
                if OWL.ObjectProperty in types:
                    d.range = value["range"]
                else:
                    d.range = "rdfs:Literal"
                    if "range" in value:
                        d.datatype = value["range"]
            else:
                d.range = "rdfs:Literal"
                # TODO: Define if we accept missing datatype for literals
            if "conformance" in value:
                d.conformance = CONFORMANCE_MAPS[value["conformance"]]
            if "unitSymbol" in value:
                d.unit = value["unitSymbol"]
            for k, v in value.items():
                if (
                    k not in ("@id", "@type", "domain", "label", "name")
                    and k not in d
                ):
                    d[k] = v

        return data

    def missing_keywords(
        self,
        ts: "Triplestore",
        include_classes: bool = False,
        return_existing: bool = False,
    ) -> "Union[list, Tuple[list, list]]":
        """List keywords not defined in triplestore `ts`.

        Arguments:
            ts: Triplestore object to check.
            include_classes: Also return missing classes.
            return_existing: If true, two lists are returned:
                - list of keywords missing in `ts`
                - list of keywords existing in `ts`

        Returns:
            List with the names of keywords in this instance that are
            not defined in triplestore `ts`.
        """
        expanded = {k for k in self.keywords.keys() if "://" in k}
        if include_classes:
            expanded.update(self.expanded(c) for c in self.classnames())

        if not expanded:
            return []

        query = f"""
        SELECT ?s WHERE {{
          VALUES ?s {{ { ' '.join(f'<{iri}>' for iri in expanded) } }}
          ?s a ?o
        }}
        """
        existing = {r[0] for r in ts.query(query)}
        missing = expanded.difference(existing)
        missing_names = [self.shortname(k) for k in missing]

        if return_existing:
            existing_names = [self.keywords[k].name for k in existing]
            return missing_names, existing_names
        return missing_names

    def _load_rdf(
        self, ts: "Triplestore", iris: "Optional[Sequence[str]]" = None
    ) -> "Sequence[dict]":
        """Help method for load_rdf(). Returns dicts loaded from triplestore
        `ts`.

        If `iris` is not given, all OWL properties in `ts` will be loaded.
        """
        # pylint: disable=import-outside-toplevel,too-many-nested-blocks
        # pylint: disable=too-many-locals
        from tripper.datadoc.context import Context
        from tripper.datadoc.dataset import acquire

        context = Context(self.get_context())

        if iris is None:
            query = """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?s WHERE {
              VALUES ?o {
                owl:DatatypeProperty owl:ObjectProperty owl:AnnotationProperty
                rdf:Property
              }
              ?s a ?o .
            }
            """
            iris = [iri[0] for iri in ts.query(query)]

        prefixes = self.data.prefixes
        for prefix, ns in ts.namespaces.items():
            self.add_prefix(prefix, ns)

        # Maps JSON-LD key name to keyword
        names = {
            DDOC.unitSymbol: "unit",
            "ddoc:unitSymbol": "unit",
        }

        dicts = []
        for iri in iris:
            d = AttrDict()
            for k, v in acquire(ts, iri, context=context).items():
                d[names.get(k, k)] = v
            dicts.append(d)

        dct = {expand_iri(d["@id"], prefixes): d for d in dicts}

        # FIXME: Add domain and range to returned dicts
        # Add domain and range to dicts
        seen = set()
        for d in list(dct.values()):
            for ref in ("domain", "range"):
                if ref in d:
                    for domain in asseq(d[ref]):
                        expanded = expand_iri(domain, prefixes)
                        if expanded.startswith(str(XSD)):
                            continue
                        if expanded not in seen:
                            seen.add(expanded)
                            acquired = acquire(ts, expanded, context=context)
                            if acquired:
                                dct[expanded] = acquired  # type: ignore

        newdicts = list(dct.values())
        return newdicts

    def save_rdf(self, ts: "Triplestore") -> dict:
        """Save to triplestore."""
        # pylint: disable=import-outside-toplevel,cyclic-import
        from tripper.datadoc.dataset import store

        for prefix, ns in self.get_prefixes().items():
            ts.bind(prefix, ns)

        # Ensure that the schema for properties is stored
        load_datadoc_schema(ts)

        # Store all keywords that are not already in the triplestore
        missing = self.missing_keywords(ts, include_classes=True)
        dicts = self.asdicts(missing)
        return store(ts, dicts)

    def load_rdf(
        self,
        ts: "Triplestore",
        iris: "Optional[Sequence[str]]" = None,
        strict: bool = False,
        redefine: str = "raise",
    ) -> None:
        """Populate this Keyword object from a triplestore.

        Arguments:
            ts: Triplestore to load keywords from.
            iris: IRIs to load. The default is to load IRIs corresponding to all
                properties an classes.
            strict: Whether to raise an `InvalidKeywordError` exception if `d`
                contains an unknown key.
            redefine: Determine how to handle redefinition of existing
                keywords.  Should be one of the following strings:
                  - "allow": Allow redefining a keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "skip": Don't redefine existing keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "raise": Raise an RedefineError (default).

        """
        dicts = self._load_rdf(ts, iris)
        self.fromdicts(
            dicts,
            prefixes=ts.namespaces,
            strict=strict,
            redefine=redefine,
        )

    def load_rdffile(
        self,
        rdffile: "FileLoc",
        format: "Optional[str]" = None,
        timeout: float = 3,
        iris: "Optional[Sequence[str]]" = None,
        strict: bool = False,
        redefine: str = "raise",
    ) -> None:
        """Load RDF from file or URL.

        Arguments:
            rdffile: File to load.
            format: Any format supported by rdflib.Graph.parse().
            timeout: Timeout in case `yamlfile` is a URI.
            iris: IRIs to load. The default is to load IRIs corresponding to
                all properties an classes.
            strict: Whether to raise an `InvalidKeywordError` exception if `d`
                contains an unknown key.
            redefine: Determine how to handle redefinition of existing
                keywords.  Should be one of the following strings:
                  - "allow": Allow redefining a keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "skip": Don't redefine existing keyword. Emits a
                    `RedefineKeywordWarning`.
                  - "raise": Raise an RedefineError (default).

        """
        if format is None:
            format = guess_rdf_format(rdffile)

        ts = Triplestore("rdflib")
        with openfile(rdffile, timeout=timeout, mode="rt") as f:
            ts.parse(f, format=format)
        self.load_rdf(ts, iris=iris, strict=strict, redefine=redefine)

    def isnested(self, keyword: str) -> bool:
        """Returns whether the keyword corresponds to an object property."""
        d = self.keywords[keyword]
        if "datatype" in d or d.range == "rdfs:Literal":
            return False
        return True

    def expanded(self, keyword: str, strict: bool = True) -> str:
        """Return the keyword expanded to its full IRI."""
        if keyword in self.keywords:
            iri = self.keywords[keyword].iri
        elif "resources" in self.data and keyword in self.data.resources:
            iri = self.data.resources[keyword].iri
        elif ":" in keyword or not strict:
            iri = keyword
        else:
            raise InvalidKeywordError(keyword)
        return expand_iri(iri, self.get_prefixes(), strict=strict)

    def range(self, keyword: str) -> str:
        """Return the range of the keyword."""
        return self.keywords[keyword].range

    def superclasses(self, cls: str) -> "Union[str, list]":
        """Return a list with `cls` and it superclasses prefixed.

        Example:

        >>> keywords = Keywords()
        >>> keywords.superclasses("Dataset")
        ... # doctest: +NORMALIZE_WHITESPACE
        ['dcat:Dataset',
         'dcat:Resource',
         'emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a']

        >>> keywords.superclasses("dcat:Dataset")
        ... # doctest: +NORMALIZE_WHITESPACE
        ['dcat:Dataset',
         'dcat:Resource',
         'emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a']

        """
        if cls in self.data.resources:
            r = self.data.resources[cls]
        else:
            cls = prefix_iri(cls, self.get_prefixes())
            rlst = [r for r in self.data.resources.values() if cls == r.iri]
            if not rlst:
                raise NoSuchTypeError(cls)
            if len(rlst) > 1:
                raise RuntimeError(
                    f"{cls} matches more than one resource: "
                    f"{', '.join(r.iri for r in rlst)}"
                )
            r = rlst[0]

        if "subClassOf" in r:
            if isinstance(r.subClassOf, str):
                return [r.iri, r.subClassOf]
            return [r.iri] + r.subClassOf
        return r.iri

    def keywordname(self, keyword: str) -> str:
        """Return the short name of `keyword`."""
        warnings.warn(
            "Keywords.keywordname() is deprecated. Use Keywords.shortname() "
            "instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if keyword not in self.keywords:
            raise InvalidKeywordError(keyword)
        return self.keywords[keyword].name

    def shortname(self, iri: str) -> str:
        """Return the short name of `iri`.

        Example:

        >>> keywords = Keywords()
        >>> keywords.shortname("dcterms:title")
        'title'

        """
        if iri in self.keywords:
            return self.keywords[iri].name
        if iri in self.data.resources.keys():
            return iri
        expanded = self.expanded(iri)
        for k, v in self.data.resources.items():
            if expanded == self.expanded(v.iri):
                return k
        raise InvalidKeywordError(iri)

    def prefixed(self, name: str, strict: bool = True) -> str:
        """Return prefixed name or `name`.

        Example:

        >>> keywords = Keywords()
        >>> keywords.prefixed("title")
        'dcterms:title'
        """
        if name in self.keywords:
            return prefix_iri(self.keywords[name].iri, self.get_prefixes())
        if name in self.data.resources:
            return prefix_iri(
                self.data.resources[name].iri,
                self.get_prefixes(),
                strict=strict,
            )
        if is_curie(name):
            return name
        print(name)
        return prefix_iri(name, self.get_prefixes(), strict=strict)

    def typename(self, type) -> str:
        """Return the short name of `type`.

        Example:

        >>> keywords = Keywords()
        >>> keywords.typename("dcat:Dataset")
        'Dataset'

        """
        if type in self.data.resources:
            return type
        prefixed = prefix_iri(type, self.get_prefixes())
        for name, r in self.data.resources.items():
            if prefixed == r.iri:
                return name
        raise NoSuchTypeError(type)

    def get_prefixes(self) -> dict:
        """Return prefixes dict."""
        return self.data.get("prefixes", {})

    def add_prefix(self, prefix, namespace, replace=False):
        """Bind `prefix` to `namespace`.

        If `namespace` is None, is the prefix removed.

        If `replace` is true, will existing namespace will be overridden.
        """
        if namespace is None:
            del self.data.prefixes[str(prefix)]
        elif replace:
            self.data.prefixes[str(prefix)] = str(namespace)
        else:
            self.data.prefixes.setdefault(str(prefix), str(namespace))

    def get_context(self) -> dict:
        """Return JSON-LD context as a dict.

        Note: The returned dict corresponds to the value of the "@context"
        keyword in a JSON-LD document.
        """
        ctx = {}
        ctx["@version"] = 1.1

        # Add prefixes to context
        prefixes = self.data.get("prefixes", {})
        for prefix, ns in prefixes.items():
            ctx[prefix] = ns

        resources = self.data.get("resources", {})

        # Translate datatypes
        translate = {"rdf:JSON": "@json"}

        # Add keywords (properties) to context
        for resource in resources.values():
            for k, v in resource.get("keywords", {}).items():
                iri = v["iri"]
                if "datatype" in v:
                    dt = v["datatype"]
                    if isinstance(dt, str):
                        dt = translate.get(dt, dt)
                    else:
                        dt = [translate.get(t, t) for t in dt]

                    d = {}
                    if v.get("reverse", "").lower() == "true":
                        d["@reverse"] = iri
                    else:
                        d["@id"] = iri

                    if dt == "rdf:langString" or "language" in v:
                        d["@language"] = v.get("language", "en")
                    else:
                        d["@type"] = dt

                    ctx[k] = d  # type: ignore
                elif v.get("range", "rdfs:Literal") == "rdfs:Literal":
                    ctx[k] = iri
                else:
                    ctx[k] = {  # type: ignore
                        "@id": iri,
                        "@type": "@id",
                    }

        # Add resources (classes) to context
        for k, v in resources.items():
            ctx.setdefault(
                k,
                {  # type:ignore
                    "@id": v.iri,
                    "@type": OWL.Class,
                },
            )

        return ctx

    def save_context(self, outfile: "FileLoc", indent: int = 2) -> None:
        """Save JSON-LD context file.

        Arguments:
            outfile: File to save the JSON-LD context to.
            indent: Indentation level. Defaults to two.
        """
        context = {"@context": self.get_context()}
        with open(outfile, "wt", encoding="utf-8") as f:
            json.dump(context, f, indent=indent)
            f.write(os.linesep)

    def _keywords_list(
        self,
        keywords: "Optional[Sequence[str]]" = None,
        classes: "Optional[Union[str, Sequence[str]]]" = None,
        themes: "Optional[Union[str, Sequence[str]]]" = None,
        namespace_filter: "Optional[Union[str, Sequence[str]]]" = None,
    ) -> "Tuple[Set[str], Set[str], Set[str]]":
        """Help function returning a list of keywords corresponding to
        arguments `keywords`, `classes` and `themes`.

        Arguments:
            keywords: Sequence of keywords to include.
            classes: Include keywords that have these classes in their domain.
            themes: Include keywords for these themes.
            namespace_filter: A prefix, namespace or a sequence of these.
                If given, keep only keywords and classes from the returned
                `keywordset` and `classet` with IRIs in one of
                these namespaces.

        Returns:
            keywordset: Set with all included keywords.
            classet: Set with all included classes.
            themeset: Set with all included themes.

        SeeAlso:
            save_markdown_table()

        """
        keywords = (
            set(self.prefixed(k) for k in asseq(keywords))
            if keywords
            else set()
        )
        classes = (
            set(self.prefixed(d) for d in asseq(classes)) if classes else set()
        )
        themes = (
            set(self.prefixed(t) for t in asseq(themes)) if themes else set()
        )
        orig_classes = classes.copy()
        orig_themes = themes.copy()

        prefixtuple = ()
        if namespace_filter:
            nf = (
                [namespace_filter]
                if isinstance(namespace_filter, str)
                else list(namespace_filter)
            )
            for i, value in enumerate(nf):
                if value not in self.data.prefixes:
                    nf[i] = self.prefixed(value).rstrip(":")
            prefixtuple = tuple(f"{v}:" for v in nf)  # type: ignore

        if not keywords and not classes and not themes:
            keywords.update(
                p
                for p in (self.prefixed(k) for k in self.keywordnames())
                if not namespace_filter or p.startswith(prefixtuple)
            )

        for value in self.data.resources.values():
            for k, v in value.get("keywords", {}).items():
                if not self.prefixed(k).startswith(prefixtuple):
                    continue
                vdomain = [
                    self.prefixed(d) for d in asseq(v.get("domain", ()))
                ]
                vtheme = [self.prefixed(t) for t in asseq(v.get("theme", ()))]
                if orig_classes:
                    for domain in vdomain:
                        prefixed = self.prefixed(domain)
                        if prefixed in orig_classes:
                            keywords.add(k)
                if orig_themes:
                    for theme in vtheme:
                        prefixed = self.prefixed(theme)
                        if prefixed in orig_themes:
                            keywords.add(k)

        for k in keywords:
            v = self.keywords[k]
            vdomain = [self.prefixed(d) for d in asseq(v.get("domain", ()))]
            vtheme = [self.prefixed(t) for t in asseq(v.get("theme", ()))]
            if vdomain and not classes.intersection(vdomain):
                classes.add(vdomain[0])
            if vtheme and not themes.intersection(vtheme):
                themes.add(vtheme[0])

        return keywords, classes, themes

    def _keywords_table(
        self,
        keywords: "Sequence[str]",
    ) -> "List[str]":
        """Help function for save_markdown_table().

        Returns a list with Markdown table documenting the provided
        sequence of keywords.
        """
        # pylint: disable=too-many-locals,too-many-branches
        header = [
            "Keyword",
            "Range",
            "Conformance",
            "Definition",
            "Usage note",
        ]
        order = {"mandatory": 1, "recommended": 2, "optional": 3}
        refs = []
        table = []
        for keyword in keywords:
            d = self.keywords[keyword]
            rangestr = f"[{d.range}]" if "range" in d else ""
            if "datatype" in d:
                rangestr += (
                    ", " + ", ".join(d.datatype)
                    if isinstance(d.datatype, list)
                    else f"<br>({d.datatype})"
                )
            table.append(
                [
                    f"[{d.name}]",
                    rangestr,
                    f"{d.conformance}" if "conformance" in d else "",
                    f"{d.description}" if "description" in d else "",
                    f"{d.usageNote}" if "usageNote" in d else "",
                ]
            )
            refs.append(f"[{d.name}]: {self.expanded(d.iri)}")
            if "range" in d:
                refs.append(f"[{d.range}]: {self.expanded(d.range)}")
        table.sort(key=lambda row: order.get(row[2], 10))

        out = self._to_table(header, table)
        out.append("")
        out.extend(refs)
        out.append("")
        out.append("")
        return out

    def save_markdown_table(
        self, outfile: "FileLoc", keywords: "Sequence[str]"
    ) -> None:
        """Save markdown file with documentation of the keywords."""
        table = self._keywords_table(keywords)
        with open(outfile, "wt", encoding="utf-8") as f:
            f.write(os.linesep.join(table) + os.linesep)

    def save_markdown(
        self,
        outfile: "FileLoc",
        keywords: "Optional[Sequence[str]]" = None,
        classes: "Optional[Union[str, Sequence[str]]]" = None,
        themes: "Optional[Union[str, Sequence[str]]]" = None,
        namespace_filter: "Optional[Union[str, Sequence[str]]]" = None,
        explanation: bool = False,
        special: bool = False,
    ) -> None:
        """Save markdown file with documentation of the keywords.

        Arguments:
            outfile: File to save the markdown documentation to.
            keywords: Sequence of keywords to include.
            classes: Include keywords that have these classes in their domain.
            themes: Include keywords for these themes.
            namespace_filter: A prefix, namespace or a sequence of these.
                Keep only keywords within this namespace.
                It is important that the namespace(s) are defined with
                prefixes in the Keywords object.
            explanation: Whether to include explanation of columns labels.
            special: Whether to generate documentation of special
                JSON-LD keywords.

        """
        # pylint: disable=too-many-locals,too-many-branches
        keywords, classes, themes = self._keywords_list(
            keywords, classes, themes, namespace_filter=namespace_filter
        )
        ts = Triplestore("rdflib")
        for prefix, ns in self.data.get("prefixes", {}).items():
            ts.bind(prefix, ns)

        if namespace_filter:
            header = "Keywords for namespaces:" + ", ".join(namespace_filter)
        elif themes:
            header = "Keywords for theme: " + ", ".join(themes)
        else:
            header = "Keywords"
        out = [
            "<!-- Do not edit! This file is generated with Tripper. -->",
            "",
            header,
            "",
        ]
        column_explanations = [
            "The meaning of the columns are as follows:",
            "",
            "- **Keyword**: The keyword referring to a property used for "
            "the data documentation.",
            "- **Range**: Refer to the class for the values of the keyword.",
            "- **Conformance**: Whether the keyword is mandatory, recommended "
            "or optional when documenting the given type of resources.",
            "- **Definition**: The definition of the keyword.",
            "- **Usage note**: Notes about how to use the keyword.",
            "",
        ]
        special_keywords = [
            "## Special keywords (from JSON-LD)",
            "See the [JSON-LD specification] for more details.",
            "",
            # pylint: disable=line-too-long
            "| Keyword    | Range         | Conformance | Definition                                                              | Usage note |",
            "|------------|---------------|-------------|-------------------------------------------------------------------------|------------|",
            "| [@id]      | IRI           | mandatory   | IRI identifying the resource to document.                               |            |",
            "| [@type]    | IRI           | recommended | Ontological class defining the class of a node.                         |            |",
            "| [@context] | dict&#124list | optional    | Context defining namespace prefixes and additional keywords.            |            |",
            "| [@base]    | namespace     | optional    | Base IRI against which relative IRIs are resolved.                      |            |",
            "| [@vocab]   | namespace     | optional    | Used to expand properties and values in @type with a common prefix IRI. |            |",
            "| [@graph]   | list          | optional    | Used for documenting multiple resources.                                |            |",
            "",
        ]
        if explanation:
            out.extend(column_explanations)
        if special:
            out.extend(special_keywords)
        refs = []

        for cls in sorted(classes):
            name = self.prefixed(cls)
            shortname = iriname(name)
            if shortname in self.data.resources:
                resource = self.data.resources[shortname]
            else:
                for rname, resource in self.data.resources.items():
                    if self.prefixed(resource.iri) == name:
                        shortname = rname
                        break
                else:
                    raise MissingKeyError(cls)

            out.append("")
            out.append(f"## Properties on [{shortname}]")
            if "description" in resource:
                out.append(resource.description)
            if "subClassOf" in resource:
                out.append("")
                subcl = (
                    [resource.subClassOf]
                    if isinstance(resource.subClassOf, str)
                    else resource.subClassOf
                )
                out.append(
                    f"- subClassOf: {', '.join(f'[{sc}]' for sc in subcl)}"
                )
                for sc in subcl:
                    refs.append(f"[{sc}]: {ts.expand_iri(sc)}")
            if "iri" in resource:
                refs.append(f"[{shortname}]: {ts.expand_iri(resource.iri)}")
            included_keywords = [
                k
                for k, v in self.keywords.items()
                if name in v.domain and is_curie(k)
            ]
            out.extend(
                self._keywords_table(keywords=sorted(included_keywords))
            )
            out.append("")

        # References
        extra_refs = [
            # pylint: disable=line-too-long
            "[@id]: https://www.w3.org/TR/json-ld11/#syntax-tokens-and-keywords",
            "[@type]: https://www.w3.org/TR/json-ld11/#syntax-tokens-and-keywords",
            "[@context]: https://www.w3.org/TR/json-ld11/#syntax-tokens-and-keywords",
            "[@base]: https://www.w3.org/TR/json-ld11/#syntax-tokens-and-keywords",
            "[@vocab]: https://www.w3.org/TR/json-ld11/#syntax-tokens-and-keywords",
            "[@graph]: https://www.w3.org/TR/json-ld11/#syntax-tokens-and-keywords",
        ]
        refs.extend(extra_refs)
        out.append("")
        out.append("")
        out.append("")
        out.extend(refs)
        with open(outfile, "wt", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")

    def save_markdown_prefixes(self, outfile: "FileLoc") -> None:
        """Save markdown file with documentation of the prefixes."""
        out = [
            "# Predefined prefixes",
            (
                "All namespace prefixes listed on this page are defined in "
                "the [default JSON-LD context]."
            ),
            (
                "See [User-defined prefixes] for how to extend this list "
                "with additional namespace prefixes."
            ),
        ]
        rows = [
            [prefix, ns]
            for prefix, ns in self.data.get("prefixes", {}).items()
        ]
        out.extend(self._to_table(["Prefix", "Namespace"], rows))
        out.append("")
        out.append("")
        out.extend(
            [
                # pylint: disable=line-too-long
                "[default JSON-LD context]: https://raw.githubusercontent.com/EMMC-ASBL/tripper/refs/heads/master/tripper/context/0.3/context.json",
                "[User-defined prefixes]: customisation.md/#user-defined-prefixes",
            ]
        )
        with open(outfile, "wt", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")

    def _to_table(self, header: "Sequence", rows: "Iterable") -> list:
        """Return header and rows as a ."""

        widths = [len(h) for h in header]
        for row in rows:
            for i, col in enumerate(row):
                n = len(col)
                if n > widths[i]:
                    widths[i] = n

        lines = []
        empty = ""
        if rows:
            lines.append("")
            lines.append(
                "| "
                + " | ".join(
                    f"{head:{widths[i]}}" for i, head in enumerate(header)
                )
                + " |"
            )
            lines.append(
                "| "
                + " | ".join(
                    f"{empty:-<{widths[i]}}" for i in range(len(header))
                )
                + " |"
            )
            for row in rows:
                lines.append(
                    "| "
                    + " | ".join(
                        f"{col:{widths[i]}}" for i, col in enumerate(row)
                    )
                    + " |"
                )

        return lines


def main(argv=None):
    """Main function providing CLI access to keywords."""
    import argparse  # pylint: disable=import-outside-toplevel

    parser = argparse.ArgumentParser(
        description=(
            "Tool for generation of JSON-LD context and documentation from "
            "keyword definitions."
        )
    )
    parser.add_argument(
        "--input",
        "-i",
        metavar="FILENAME",
        default=[],
        action="append",
        help="Load keywords from this file. May be given multiple times.",
    )
    parser.add_argument(
        "--format",
        "-f",
        metavar="FORMAT",
        nargs="?",
        action="append",
        help=(
            "Formats of --input. Default format is inferred from the file "
            "name extension.  If given, this option must be provided the "
            "same number of times as --input."
        ),
    )
    parser.add_argument(
        "--theme",
        "-t",
        metavar="NAME",
        nargs="?",
        default=[],
        action="append",
        help="Load keywords from this theme.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Whether to raise an exception of input contains an unknown key.",
    )
    parser.add_argument(  # pylint: disable=duplicate-code
        "--redefine",
        default="raise",
        choices=["raise", "allow", "skip"],
        help="How to handle redifinition of existing keywords.",
    )
    parser.add_argument(
        "--write-context",
        "--write-json",
        "-c",
        metavar="FILENAME",
        help="Generate JSON-LD context file.",
    )
    parser.add_argument(
        "--write-kw-md",
        "-k",
        metavar="FILENAME",
        help="Generate keywords Markdown documentation.",
    )
    parser.add_argument(
        "--write-kw-yaml",
        "-y",
        metavar="FILENAME",
        help="Generate keywords YAML file.",
    )
    parser.add_argument(
        "--explanation",
        "-e",
        action="store_true",
        help="Whether to include explanation in generated documentation.",
    )
    parser.add_argument(
        "--special-keywords",
        "-s",
        action="store_true",
        help="Whether to include special keywords in generated documentation.",
    )
    parser.add_argument(
        "--namespace-filter",
        "--nf",
        metavar="NAMESPACE",
        action="append",
        help=(
            "Keep only keywords with IRIs in "
            "the namespace "
            "provided by this option.  Can be provided more that once. "
            "To be used with the --write-kw-md option. "
            "A namespace can be specified by its full IRI or by a pre-defined "
            "prefix."
            "Note that the namespace must be defined with a prefix. "
            "If missing,"
            "it can be added with --prefix."
        ),
    )
    parser.add_argument(
        "--kw",
        metavar="KW1,KW2,...",
        help=(
            "Comma-separated list of keywords to include in generated table. "
            "Implies --write-markdown."
        ),
    )
    parser.add_argument(
        "--classes",
        metavar="C1,C2,...",
        help=(
            "Generate keywords Markdown documentation for any keywords who's "
            "domain is in the comma-separated list CLASSES. "
            "Implies --write-markdown."
        ),
    )
    parser.add_argument(
        "--themes",
        metavar="T1,T2,...",
        help=(
            "Generate keywords Markdown documentation for any keywords that "
            "belong to one of the themes in the comma-separated list THEMES. "
            "Implies --write-kw-md, --write-kw-json or --write-kw-yaml."
        ),
    )
    parser.add_argument(
        "--write-prefixes",
        "-w",
        metavar="FILENAME",
        help="Write prefixes Markdown file.",
    )
    parser.add_argument(
        "--prefix",
        "-p",
        metavar="PREFIX:NAMESPACE",
        default=[],
        action="append",
        help="Add the prefix given as tuple PREFIX=NAMESPACE, "
        "can be used multiple times.",
    )

    parser.add_argument(
        "--list-themes",
        action="store_true",
        help="List installed themes and exit.",
    )

    args = parser.parse_args(argv)

    if args.list_themes:
        themes = [ep.value for ep in get_entry_points("tripper.keywords")]
        parser.exit(message=os.linesep.join(themes) + os.linesep)

    if args.format and len(args.format) != len(args.input):
        parser.error(
            "The number of --format options must match the number "
            "of --input options."
        )

    if args.theme:
        default_theme = None if None in args.theme else args.theme[0]
    else:
        default_theme = "ddoc:datadoc"

    kw = Keywords(theme=default_theme)

    if args.prefix:
        for p in asseq(args.prefix):
            if ":" not in p:
                parser.error(
                    f"Invalid prefix definition '{p}'. Must be of the "
                    "form PREFIX:NAMESPACE."
                )
            prefix, namespace = p.split(":", 1)
            kw.add_prefix(prefix, namespace, replace=True)

    for theme in args.theme[1:]:
        if theme:
            kw.add_theme(theme, strict=args.strict, redefine=args.redefine)

    kw.add(args.input, args.format, strict=args.strict, redefine=args.redefine)

    if args.write_context:
        kw.save_context(args.write_context)

    if args.write_kw_md or args.kw or args.classes or args.themes:
        kw.save_markdown(
            args.write_kw_md,
            keywords=args.kw.split(",") if args.kw else None,
            classes=args.classes.split(",") if args.classes else None,
            themes=args.themes.split(",") if args.themes else None,
            explanation=args.explanation,
            special=args.special_keywords,
            namespace_filter=args.namespace_filter,
        )

    if args.write_prefixes:
        kw.save_markdown_prefixes(args.write_prefixes)

    if args.write_kw_yaml:
        kw.save_yaml(
            args.write_kw_yaml, namespace_filter=args.namespace_filter
        )


if __name__ == "__main__":
    main()

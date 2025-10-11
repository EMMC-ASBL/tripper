"""Parse keywords definition and generate context."""

# pylint: disable=too-many-branches,redefined-builtin

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import yaml

from tripper import DDOC, Triplestore
from tripper.datadoc.dictutils import add, merge
from tripper.datadoc.errors import (
    InvalidKeywordError,
    NoSuchTypeError,
    RedefineKeywordError,
)
from tripper.utils import (
    AttrDict,
    expand_iri,
    get_entry_points,
    is_uri,
    openfile,
    prefix_iri,
    recursive_update,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Union

    FileLoc = Union[Path, str]
    KeywordsType = Union["Keywords", Path, str, Sequence]


@lru_cache(maxsize=32)
def get_keywords(
    keywords: "Optional[KeywordsType]" = None,
    theme: "Optional[Union[str, Sequence[str]]]" = "ddoc:default",
    yamlfile: "Optional[Union[FileLoc, Sequence[FileLoc]]]" = None,
    timeout: float = 3,
) -> "Keywords":
    """A convinient function that returns an Context instance.

    Arguments:
        keywords: Optional existing keywords object.
        theme: IRI of one of more themes to load keywords for.
        yamlfile: YAML file with keyword definitions to parse.  May also
            be an URI in which case it will be accessed via HTTP GET.
        timeout: Timeout in case `yamlfile` is a URI.
    """
    kw = Keywords(theme=theme, yamlfile=yamlfile, timeout=timeout)
    if keywords:
        kw.add(keywords, timeout=timeout)
    return kw


class Keywords:
    """A class representing all keywords within a theme."""

    rootdir = Path(__file__).absolute().parent.parent.parent.resolve()

    def __init__(
        self,
        theme: "Optional[Union[str, Sequence[str]]]" = "ddoc:default",
        yamlfile: "Optional[Union[FileLoc, Sequence[FileLoc]]]" = None,
        timeout: float = 3,
    ) -> None:
        """Initialises keywords object.

        Arguments:
            theme: IRI of one of more themes to load keywords for.
            yamlfile: YAML file with keyword definitions to parse.  May also
                be an URI in which case it will be accessed via HTTP GET.
            timeout: Timeout in case `yamlfile` is a URI.

        Attributes:
            data: The dict loaded from the keyword yamlfile.
            keywords: A dict mapping keywords (name/prefixed/iri) to dicts
                describing the keywords.
            theme: IRI of a theme or scientic domain that the keywords
                belong to.
        """
        default_prefixes = AttrDict(ddoc=str(DDOC))
        self.data = AttrDict(prefixes=default_prefixes)
        self.keywords = AttrDict()
        self.theme = None

        if theme:
            self.add_theme(theme)

        if yamlfile:
            if isinstance(yamlfile, (str, Path)):
                self.parse(yamlfile, timeout=timeout)
            else:
                for path in yamlfile:
                    self.parse(path, timeout=timeout)

    def __contains__(self, item):
        return item in self.keywords

    def __getitem__(self, key):
        return self.keywords[key]

    def __iter__(self):
        return iter(self.keywords)

    def __dir__(self):
        return dir(Keywords) + ["data", "keywords", "theme"]

    def copy(self):
        """Returns a copy of self."""
        new = Keywords(theme=None)
        new.data.update(self.data)
        new.keywords.update(self.keywords)
        new.theme = self.theme
        return new

    def add(self, keywords: "KeywordsType", timeout: float = 3) -> None:
        """Add `keywords` to current keyword object."""

        def _add(kw):
            if kw is None:
                pass
            elif isinstance(kw, Keywords):
                self.data.update(kw.data)
                self.keywords.update(kw.keywords)
                self.theme = merge(self.theme, kw.theme)
            elif isinstance(kw, Path):
                self.parse(kw, timeout=timeout)
            elif isinstance(kw, str):
                if kw.startswith("/") or kw.startswith("./") or is_uri(kw):
                    self.parse(kw, timeout=timeout)
                else:
                    self.add_theme(kw, timeout=timeout)
            elif isinstance(kw, Sequence):
                for e in kw:
                    _add(e)
            else:
                raise TypeError(
                    "`keywords` must be a Keywords object, a Path object, "
                    f"a string or a sequence of these.  Got: {type(kw)}"
                )

        _add(keywords)

    def add_theme(
        self, theme: "Union[str, Sequence[str]]", timeout: float = 3
    ) -> None:
        """Add keywords for `theme`, where `theme` is the IRI of a
        theme or scientific domain or a list of such IRIs."""
        if isinstance(theme, str):
            theme = [theme]

        for name in theme:  # type: ignore
            expanded = expand_iri(name, self.get_prefixes())
            if self.theme is None:
                self.theme = name  # type: ignore
            for ep in get_entry_points("tripper.keywords"):
                if expand_iri(ep.value, self.get_prefixes()) == expanded:
                    self.parse(
                        self.rootdir / ep.name / "keywords.yaml",
                        timeout=timeout,
                    )
                    break
            else:
                # Fallback in case the entry point is not installed
                if expanded == DDOC.default:
                    self.parse(
                        self.rootdir
                        / "tripper"
                        / "context"
                        / "0.3"
                        / "keywords.yaml",
                        timeout=timeout,
                    )
                else:
                    raise TypeError(f"Unknown theme: {name}")

    def parse(
        self,
        yamlfile: "Union[Path, str]",
        timeout: float = 3,
    ) -> None:
        """Parse YAML file with keyword definitions."""
        # pylint: disable=too-many-nested-blocks
        with openfile(yamlfile, timeout=timeout, mode="rt") as f:
            d = yaml.safe_load(f)

        dm = self.theme[-1] if isinstance(self.theme, list) else self.theme
        theme = self.expanded(d.get("theme", dm))
        self.add(d.get("basedOn"))

        recursive_update(self.data, d)

        resources = self.data.get("resources", {})
        for resource_name, resource in resources.items():
            for keyword, value in resource.get("keywords", {}).items():

                # Simple validation
                valid_keys = [
                    "name",
                    "iri",
                    "subPropertyOf",  # XXX - to be implemented
                    "domain",
                    "range",
                    "datatype",
                    "inverse",  # XXX - to be implemented
                    "unit",  # XXX - to be implemented
                    "conformance",
                    "description",
                    "usageNote",
                    "characteristics",  # XXX - to be implemented
                    "theme",
                    "default",
                ]
                for k in value.keys():
                    if k not in valid_keys:
                        raise InvalidKeywordError(
                            f"keyword '{keyword}' has invalid key: {k}"
                        )
                valid_conformances = ["mandatory", "recommended", "optional"]
                if "conformance" in value:
                    if value["conformance"] not in valid_conformances:
                        raise InvalidKeywordError(
                            f"keyword '{keyword}' has invalid conformance: "
                            f"'{value['conformance']}'. Valid values are "
                            f"{', '.join(valid_conformances)} "
                            f"when parsing '{yamlfile}'"
                        )

                if keyword in self.keywords:
                    # Only allowed changes to existing keywords:
                    #   - make conformance more strict
                    #   - extend: domain, theme
                    #   - change default value
                    for k, v in self.keywords[keyword].items():
                        if k == "conformance":
                            if "conformance" in value and (
                                valid_conformances.index(value.conformance)
                                > valid_conformances.index(v)
                            ):
                                raise InvalidKeywordError(
                                    f"keyword '{keyword}' reduces strictness "
                                    "of existing conformance: "
                                    f"{value.conformance} when parsing "
                                    f"'{yamlfile}'"
                                )
                            value.setdefault(k, v)
                        elif k == "domain":
                            add(value, "domain", resource_name)
                        elif k == "theme":
                            add(value, "theme", theme)
                        elif k == "default":
                            value.setdefault(k, v)
                        elif k in value and value[k] != v:
                            raise RedefineKeywordError(
                                f"Cannot redefine '{k}' in keyword '{keyword}' "
                                f"when parsing '{yamlfile}'"
                            )
                else:
                    value["name"] = keyword
                    add(value, "domain", resource_name)
                    add(value, "theme", theme)
                    recursive_update(
                        self.keywords,
                        {
                            keyword: value,
                            value["iri"]: value,
                            expand_iri(
                                value["iri"], self.get_prefixes()
                            ): value,
                        },
                        append=False,
                    )

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
        """Return the short name of `keyword`.

        Example:

        >>> keywords = Keywords()
        >>> keywords.keywordname("dcterms:title")
        'title'

        """
        if keyword not in self.keywords:
            raise InvalidKeywordError(keyword)
        return self.keywords[keyword].name

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
                elif v["range"] == "rdfs:Literal":
                    ctx[k] = iri
                else:
                    ctx[k] = {  # type: ignore
                        "@id": iri,
                        "@type": "@id",
                    }

        # Add resources (classes) to context
        for k, v in resources.items():
            ctx.setdefault(k, v.iri)

        return ctx

    def write_context(self, outfile: "FileLoc") -> None:
        """Write JSON-LD context file."""
        context = {"@context": self.get_context()}
        with open(outfile, "wt", encoding="utf-8") as f:
            json.dump(context, f, indent=2)
            f.write(os.linesep)

    def write_doc_keywords(self, outfile: "FileLoc") -> None:
        """Write Markdown file with documentation of the keywords."""
        # pylint: disable=too-many-locals,too-many-branches
        ts = Triplestore("rdflib")
        for prefix, ns in self.data.get("prefixes", {}).items():
            ts.bind(prefix, ns)

        theme = f" for theme: {self.theme}" if self.theme else ""
        out = [
            "<!-- Do not edit! This file is generated with Tripper. "
            "Edit the keywords.yaml file instead. -->",
            "",
            f"# Keywords{theme}",
            f"The tables below lists the keywords the theme {self.theme}.",
            "",
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
        order = {"mandatory": 1, "recommended": 2, "optional": 3}
        refs = []

        resources = self.data.get("resources", {})
        for resource_name, resource in resources.items():
            out.append("")
            out.append(f"## Properties on [{resource_name}]")
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
                refs.append(
                    f"[{resource_name}]: {ts.expand_iri(resource.iri)}"
                )
            header = [
                "Keyword",
                "Range",
                "Conformance",
                "Definition",
                "Usage note",
            ]
            table = []
            for keyword, d in resource.get("keywords", {}).items():
                rangestr = f"[{d.range}]" if "range" in d else ""
                if "datatype" in d:
                    rangestr += (
                        ", " + ", ".join(d.datatype)
                        if isinstance(d.datatype, list)
                        else f"<br>({d.datatype})"
                    )
                table.append(
                    [
                        f"[{keyword}]",
                        rangestr,
                        f"{d.conformance}" if "conformance" in d else "",
                        f"{d.description}" if "description" in d else "",
                        f"{d.usageNote}" if "usageNote" in d else "",
                    ]
                )
                refs.append(f"[{keyword}]: {ts.expand_iri(d.iri)}")
                if "range" in d:
                    refs.append(f"[{d.range}]: {ts.expand_iri(d.range)}")
            table.sort(key=lambda row: order.get(row[2], 10))
            out.extend(self._to_table(header, table))
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

    def write_doc_prefixes(self, outfile: "FileLoc") -> None:
        """Write Markdown file with documentation of the prefixes."""
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

    def _to_table(self, header, rows):
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
        "--yamlfile",
        "-i",
        metavar="YAMLFILE",
        action="append",
        help="Load keywords from this YAML file.",
    )
    parser.add_argument(
        "--theme",
        "-f",
        metavar="NAME",
        action="append",
        help="Load keywords from this theme.",
    )
    parser.add_argument(
        "--context",
        "-c",
        metavar="FILENAME",
        help="Generate JSON-LD context file.",
    )
    parser.add_argument(
        "--keywords",
        "-k",
        metavar="FILENAME",
        help="Generate keywords Markdown documentation.",
    )
    parser.add_argument(
        "--prefixes",
        "-p",
        metavar="FILENAME",
        help="Generate prefixes Markdown documentation.",
    )
    args = parser.parse_args(argv)

    if not args.theme and not args.yamlfile:
        args.theme = "ddoc:default"

    keywords = Keywords(theme=args.theme, yamlfile=args.yamlfile)

    if args.context:
        keywords.write_context(args.context)

    if args.keywords:
        keywords.write_doc_keywords(args.keywords)

    if args.prefixes:
        keywords.write_doc_prefixes(args.prefixes)


if __name__ == "__main__":
    main()

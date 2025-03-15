"""Parse and generate context."""

# pylint: disable=too-many-branches

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from tripper import Triplestore
from tripper.utils import (
    AttrDict,
    get_entry_points,
    openfile,
    recursive_update,
)

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Sequence, Union

    FileLoc = Union[Path, str]


class Keywords:
    """A class representing all keywords within a domain."""

    rootdir = Path(__file__).absolute().parent.parent.parent.resolve()

    def __init__(
        self,
        field: "Optional[Union[str, Sequence[str]]]" = None,
        yamlfile: "Optional[Union[FileLoc, Sequence[FileLoc]]]" = None,
        timeout: float = 3,
    ) -> None:
        """Initialises keywords object.

        Arguments:
            field: Name of field to load keywords for.
            yamlfile: YAML file with keyword definitions to parse.  May also
                be an URI in which case it will be accessed via HTTP GET.
            timeout: Timeout in case `yamlfile` is a URI.
        """
        self.keywords = AttrDict()
        self.field = None

        if yamlfile:
            if isinstance(yamlfile, (str, Path)):
                self.parse(yamlfile, timeout=timeout)
            else:
                for path in yamlfile:
                    self.parse(path, timeout=timeout)
        elif not field:
            field = "default"

        if isinstance(field, str):
            field = [field]

        for fieldname in field:  # type: ignore
            if self.field is None:
                self.field = fieldname
            for ep in get_entry_points("tripper.keywords"):
                if ep.value == fieldname:
                    self.parse(self.rootdir / ep.name / "keywords.yaml")
                    break
            else:
                if fieldname == "default":
                    # Fallback in case the entry point is not installed
                    self.parse(
                        self.rootdir
                        / "tripper"
                        / "context"
                        / "0.3"
                        / "keywords.yaml"
                    )
                else:
                    raise TypeError(f"Unknown field name: {fieldname}")

    def parse(self, yamlfile: "Union[Path, str]", timeout: float = 3) -> None:
        """Parse YAML file with keyword definitions."""
        with openfile(yamlfile, timeout=timeout, mode="rt") as f:
            d = yaml.safe_load(f)

        if "basedOn" in d:
            if isinstance(d["basedOn"], str):
                self.parse(d["basedOn"], timeout=timeout)
            elif isinstance(d["basedOn"], list):
                for dct in d["basedOn"]:
                    self.parse(dct, timeout=timeout)

        recursive_update(self.keywords, d)

    def write_context(self, outfile: "FileLoc") -> None:
        """Write JSON-LD context file."""
        c = {}
        c["@version"] = 1.1

        prefixes = self.keywords.get("prefixes", {})
        for prefix, ns in prefixes.items():
            c[prefix] = ns

        for resource_name, resource in self.keywords.items():
            if resource_name in ("basedOn", "prefixes"):
                continue
            for k, v in resource.get("keywords", {}).items():
                iri = v["iri"]
                if v["range"] == "rdfs:Literal":
                    if "datatype" in v:
                        c[k] = {  # type: ignore
                            "@id": iri,
                            "@type": v["datatype"],
                        }
                    else:
                        c[k] = iri
                else:
                    c[k] = {  # type: ignore
                        "@id": iri,
                        "@type": "@id",
                    }

        dct = {"@context": c}
        with open(outfile, "wt", encoding="utf-8") as f:
            json.dump(dct, f, indent=2)
            f.write(os.linesep)

    def write_doc_keywords(self, outfile: "FileLoc") -> None:
        """Write Markdown file with documentation of the keywords."""
        # pylint: disable=too-many-locals,too-many-branches
        ts = Triplestore("rdflib")
        for prefix, ns in self.keywords.get("prefixes", {}).items():
            ts.bind(prefix, ns)

        field = f" for {self.field}" if self.field else ""
        out = [f"# Keywords{field}"]
        order = {"mandatory": 1, "recommended": 2, "optional": 3}
        refs = []

        for resource_name, resource in self.keywords.items():
            if resource_name in ("basedOn", "prefixes"):
                continue

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
                        else f", {d.datatype}"
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
            for prefix, ns in self.keywords.get("prefixes", {}).items()
        ]
        out.extend(self._to_table(["Prefix", "Namespace"], rows))
        out.append("")
        out.append("")
        out.append(
            "[default JSON-LD context]: https://raw.githubuser"
            "content.com/EMMC-ASBL/tripper/refs/heads/master/"
            "tripper/context/0.2/context.json"
        )
        out.append(
            "[User-defined prefixes]: customisation.md/#user-defined-prefixes"
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
        "--field",
        "-f",
        metavar="NAME",
        action="append",
        help="Load keywords from this field.",
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

    keywords = Keywords(field=args.field, yamlfile=args.yamlfile)

    if args.context:
        keywords.write_context(args.context)

    if args.keywords:
        keywords.write_doc_keywords(args.keywords)

    if args.prefixes:
        keywords.write_doc_prefixes(args.prefixes)


if __name__ == "__main__":
    main()

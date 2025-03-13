"""Parse and generate context."""

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

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

        for name in field:  # type: ignore
            if self.field is None:
                self.field = name
            for ep in get_entry_points("tripper.keywords"):
                if ep.name == name:
                    dirname = re.sub(r"(?<!\d)\.", "/", ep.value)
                    self.parse(self.rootdir / dirname / "keywords.yaml")
                    break
            else:
                raise TypeError(f"Unknown field: {name}")

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

    def write_doc_keywords(self, outfile: "FileLoc") -> None:
        """Write Markdown file with documentation of the keywords."""
        field = f" for {self.field}" if self.field else ""
        out = [f"# Keywords{field}", ""]
        refs = []

        for resource_name, resource in self.keywords.items():
            if resource_name in ("basedOn", "prefixes"):
                continue

            out.append(f"## Properties on {resource_name}")
            if "description" in resource:
                out.append(resource.description)
            if "iri" in resource:
                refs.append(f"[{resource_name}]: {resource.iri}")
            header = ["IRI"]
            table = []

            for k, v in resource.get("keywords", {}).items():

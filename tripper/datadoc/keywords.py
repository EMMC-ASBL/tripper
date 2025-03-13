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

        if yamlfile:
            if isinstance(yamlfile, (str, Path)):
                self.parse(yamlfile)
            else:
                for path in yamlfile:
                    self.parse(path)
        elif not field:
            field = "default"

        if isinstance(field, str):
            field = [field]

        for fld in field:
            for ep in get_entry_points("tripper.keywords"):
                if ep.name == fld:
                    dirname = re.sub(r"(?<!\d)\.", "/", ep.value)
                    self.parse(self.rootdir / dirname / "keywords.yaml")
                    break
            else:
                raise TypeError(f"fld")

    def parse(self, yamlfile: "Union[Path, str]", timeout: float = 3):
        """Parse YAML file with keyword definitions."""
        with openfile(yamlfile, timeout=timeout, mode="rt") as f:
            d = yaml.safe_load(f)

        recursive_update(self.keywords, d)


def generate_context(
    infile: "Union[str, Path]", outfile: Path, timeout: float = 5
):
    """Generate context.json file based on YAML input."""

    with openfile(infile, timeout=timeout, mode="rt") as f:
        d = yaml.safe_load(f)

    c = {}
    c["@version"] = 1.1

    prefixes = d.pop("prefixes")
    for prefix, ns in prefixes.items():
        c[prefix] = ns

    for name in d.keys():
        r = d[name]
        for k, v in r.get("keywords", {}).items():
            iri = v["iri"]
            if v["range"] == "rdfs:Literal":
                if "datatype" in v:
                    c[k] = {
                        "@id": iri,
                        "@type": v["datatype"],
                    }
                else:
                    c[k] = iri
            else:
                c[k] = {
                    "@id": iri,
                    "@type": "@id",
                }

    dct = {"@context": c}

    with open(outfile, "wt") as f:
        json.dump(dct, f, indent=2)

    return dct

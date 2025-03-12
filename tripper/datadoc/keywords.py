"""Parse and generate context."""

import json
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from tripper.utils import AttrDict, get_entry_points, openfile

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Union


class Keywords:
    """A class representing all keywords within a domain."""

    def __init__(
        self,
        field: "Optional[str]" = None,
        yamlfile: "Optional[Union[Path, str]]" = None,
    ) -> None:
        """ """
        if field:
            for ep in get_entry_points("tripper.keywords"):
                pass

        with openfile(infile, timeout=timeout, mode="rt") as f:
            d = yaml.safe_load(f)

        self.keywords = yaml.save_load()


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

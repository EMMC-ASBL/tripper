"""Basic interface for tabular documentation of datasets."""

from typing import TYPE_CHECKING

from tripper import Triplestore
from tripper.dataset.dataset import addnested, as_jsonld, save_dict
from tripper.utils import AttrDict

if TYPE_CHECKING:  # pragma: no cover
    from typing import List, Optional, Sequence, Union


class TableDoc:
    """Representation of tabular documentation of datasets.

    Arguments:
        header: Sequence of column header labels.  Nested data can
            be represented by dot-separated label strings (e.g.
            "distribution.downloadURL")
        data: Sequence of rows of data. Each row documents an entry.
        type: Type of data to save (applies to all rows).  Should
            either be one of the pre-defined names: "dataset",
            "distribution", "accessService", "parser" and "generator"
            or an IRI to a class in an ontology.  Defaults to
            "dataset".
        prefixes: Dict with prefixes in addition to those included in the
            JSON-LD context.  Should map namespace prefixes to IRIs.
        context: Dict with user-defined JSON-LD context.

    """

    # pylint: disable=redefined-builtin,too-few-public-methods

    def __init__(
        self,
        header: "Sequence[str]",
        data: "Sequence[Sequence[str]]",
        type: "Optional[str]" = "dataset",
        prefixes: "Optional[dict]" = None,
        context: "Optional[Union[dict, list]]" = None,
    ):
        self.header = header
        self.data = data
        self.type = type
        self.prefixes = prefixes
        self.context = context

    def asdicts(self) -> "List[dict]":
        """Return the table as a list of dicts."""
        kw = {"@context": self.context} if self.context else {}

        results = []
        for row in self.data:
            d = AttrDict()
            for i, colname in enumerate(self.header):
                cell = row[i]
                if cell:
                    addnested(d, colname, cell)
            jsonld = as_jsonld(
                d, type=self.type, prefixes=self.prefixes, **kw  # type: ignore
            )
            results.append(jsonld)
        return results

    def save(self, ts: Triplestore) -> None:
        """Save tabular datadocumentation to triplestore."""
        for d in self.asdicts():
            save_dict(ts, d)

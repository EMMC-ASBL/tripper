"""Basic interface for tabular documentation of datasets."""

import csv
from pathlib import Path
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
        strip: Whether to strip leading and trailing whitespaces from cells.

    """

    # pylint: disable=redefined-builtin,too-few-public-methods

    def __init__(
        self,
        header: "Sequence[str]",
        data: "Sequence[Sequence[str]]",
        type: "Optional[str]" = "dataset",
        prefixes: "Optional[dict]" = None,
        context: "Optional[Union[dict, list]]" = None,
        strip: bool = True,
    ):
        self.header = header
        self.data = data
        self.type = type
        self.prefixes = prefixes
        self.context = context
        self.strip = strip

    def asdicts(self) -> "List[dict]":
        """Return the table as a list of dicts."""
        kw = {"@context": self.context} if self.context else {}

        results = []
        for row in self.data:
            d = AttrDict()
            for i, colname in enumerate(self.header):
                cell = row[i].strip() if self.strip else row[i]
                if cell:
                    addnested(
                        d, colname.strip() if self.strip else colname, cell
                    )
            jsonld = as_jsonld(
                d, type=self.type, prefixes=self.prefixes, **kw  # type: ignore
            )
            results.append(jsonld)
        return results

    def save(self, ts: Triplestore) -> None:
        """Save tabular datadocumentation to triplestore."""
        for d in self.asdicts():
            save_dict(ts, d)

    @staticmethod
    def parse_csv(
        csvfile: "Union[Path, str]",
        type: "Optional[str]" = "dataset",
        prefixes: "Optional[dict]" = None,
        context: "Optional[Union[dict, list]]" = None,
        encoding: str = "utf-8",
        dialect: "Union[csv.Dialect, str]" = "excel",
        **kwargs,
    ) -> "TableDoc":
        # pylint: disable=line-too-long
        """Parse a csv file using the standard library csv module.

        Arguments:
            csvfile: CSV file to parse.
            type: Type of data to save (applies to all rows).  Should
                either be one of the pre-defined names: "dataset",
                "distribution", "accessService", "parser" and "generator"
                or an IRI to a class in an ontology.  Defaults to
                "dataset".
            prefixes: Dict with prefixes in addition to those included in the
                JSON-LD context.  Should map namespace prefixes to IRIs.
            context: Dict with user-defined JSON-LD context.
            encoding: The encoding of the csv file.  Note that Excel may
                encode as "ISO-8859" (commonly used in 1990th).
            dialect: A subclass of csv.Dialect, or the name of the dialect,
                specifying how the `csvfile` is formatted.  For more details,
                see [Dialects and Formatting Parameters].
            kwargs: Additional keyword arguments overriding individual
                formatting parameters.  For more details, see
                [Dialects and Formatting Parameters].

        References:
        [Dialects and Formatting Parameters]: https://docs.python.org/3/library/csv.html#dialects-and-formatting-parameters
        """
        with open(csvfile, mode="rt", encoding=encoding) as f:
            reader = csv.reader(f, dialect=dialect, **kwargs)
            header = next(reader)
            data = list(reader)

        return TableDoc(
            header=header,
            data=data,
            type=type,
            prefixes=prefixes,
            context=context,
        )

    def write_csv(
        self,
        csvfile: "Union[Path, str]",
        encoding: str = "utf-8",
        dialect: "Union[csv.Dialect, str]" = "excel",
        **kwargs,
    ) -> None:
        # pylint: disable=line-too-long
        """Write the table to a csv file using the standard library csv module.

        Arguments:
            csvfile: CSV file to parse.
            encoding: The encoding of the csv file.
            dialect: A subclass of csv.Dialect, or the name of the dialect,
                specifying how the `csvfile` is formatted.  For more details,
                see [Dialects and Formatting Parameters].
            kwargs: Additional keyword arguments overriding individual
                formatting parameters.  For more details, see
                [Dialects and Formatting Parameters].

        References:
        [Dialects and Formatting Parameters]: https://docs.python.org/3/library/csv.html#dialects-and-formatting-parameters
        """
        with open(csvfile, mode="wt", encoding=encoding) as f:
            writer = csv.writer(f, dialect=dialect, **kwargs)
            writer.writerow(self.header)
            for row in self.data:
                writer.writerow(row)

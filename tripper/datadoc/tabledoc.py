"""Basic interface for tabular documentation of datasets."""

# pylint: disable=too-many-locals

import csv
import re
from pathlib import Path
from typing import TYPE_CHECKING

from tripper import Triplestore
from tripper.datadoc.context import Context
from tripper.datadoc.dataset import (
    addnested,
    save_dict,
    told,
)
from tripper.utils import AttrDict, openfile

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterable, List, Optional, Protocol, Sequence, Union

    from tripper.datadoc.context import ContextType

    class Writer(Protocol):
        """Prototype for a class with a write() method."""

        # pylint: disable=too-few-public-methods,missing-function-docstring

        def write(self, data: str) -> None: ...


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
        context: Additional user-defined context that should be
            returned on top of the default context.  It may be a
            string with an URL to the user-defined context, a dict
            with the user-defined context or a sequence of strings and
            dicts.
        strip: Whether to strip leading and trailing whitespaces from cells.

    """

    # pylint: disable=redefined-builtin,too-few-public-methods

    def __init__(
        self,
        header: "Sequence[str]",
        data: "Sequence[Sequence[str]]",
        type: "Optional[str]" = "Dataset",
        context: "Optional[ContextType]" = None,
        prefixes: "Optional[dict]" = None,
        strip: bool = True,
    ):
        self.header = list(header)
        self.data = [list(row) for row in data]
        self.type = type
        self.context: Context = Context(context=context)
        ## self.prefixes = get_prefixes(context=context)
        if prefixes:
            ## self.prefixes.update(prefixes)
            self.context.add_context(prefixes)
        ## self.context = context if context else {}
        self.strip = strip

    def save(self, ts: Triplestore) -> None:
        """Save tabular datadocumentation to triplestore."""
        ## self.prefixes.update(ts.namespaces)

        self.context.add_context(
            {prefix: str(ns) for prefix, ns in ts.namespaces.items()}
        )

        for prefix, ns in self.context.get_prefixes().items():
            ts.bind(prefix, ns)

        save_dict(ts, self.asdicts(), type=self.type, context=self.context)

    def asdicts(self) -> "List[dict]":
        """Return the table as a list of dicts."""
        results = []
        for row in self.data:
            d = AttrDict()
            for i, colname in enumerate(self.header):
                cell = row[i].strip() if row[i] and self.strip else row[i]
                if cell:
                    addnested(
                        d, colname.strip() if self.strip else colname, cell
                    )
            results.append(d)
        ld = told(
            results,
            type=self.type,
            prefixes=self.context.get_prefixes(),
            context=self.context,
        )
        dicts = ld["@graph"]
        return dicts

    @staticmethod
    def fromdicts(
        dicts: "Sequence[dict]",
        type: "Optional[str]" = "Dataset",
        prefixes: "Optional[dict]" = None,
        context: "Optional[Union[str, dict, list]]" = None,
        strip: bool = True,
    ) -> "TableDoc":
        """Create new TableDoc instance from a sequence of dicts.

        Arguments:
            dicts: Sequence of single-resource dicts.
            type: Type of data to save (applies to all rows).  Should
                either be one of the pre-defined names: "Dataset",
                "Distribution", "AccessService", "Parser" and
                "Generator" or an IRI to a class in an ontology.
                Defaults to "Dataset".
            prefixes: Dict with prefixes in addition to those included
                in the JSON-LD context.  Should map namespace prefixes
                to IRIs.
            context: Additional user-defined context that should be
                returned on top of the default context.  It may be a
                string with an URL to the user-defined context, a dict
                with the user-defined context or a sequence of strings
                and dicts.
            strip: Whether to strip leading and trailing whitespaces
                from cells.

        Returns:
            New TableDoc instance.

        """
        # Store the header as keys in a dict to keep ordering
        headdict = {"@id": True}

        def addheaddict(d, prefix=""):
            """Add keys in `d` to headdict.

            Nested dicts will result in dot-separated keys.
            """
            for k, v in d.items():
                if k == "@context":
                    pass
                elif isinstance(v, dict):
                    d = v.copy()
                    d.pop("@type", None)
                    addheaddict(d, k + ".")
                else:
                    headdict[prefix + k] = True

        # Assign the headdict
        for d in dicts:
            addheaddict(d)

        header = list(headdict)

        # Column multiplicity
        mult = [1] * len(header)

        # Assign table data. Nested dicts are accounted for
        data = []
        for dct in dicts:
            row = []
            for i, head in enumerate(header):
                if head in dct:
                    row.append(dct[head])
                else:
                    d = dct
                    for key in head.split("."):
                        d = d.get(key, {})
                    row.append(d if d != {} else None)
                if isinstance(row[-1], list):  # added value is a list
                    mult[i] = len(row[-1])  # update column multiplicity
            data.append(row)

        # Expand table with multiplicated columns
        if max(mult) > 1:
            exp_header = []
            for h, m in zip(header, mult):
                exp_header.extend([h] * m)

            exp_data = []
            for row in data:
                r = []
                for h, v in zip(header, row):
                    r.extend(v if isinstance(v, list) else [v])
                exp_data.append(r)
            header, data = exp_header, exp_data

        return TableDoc(
            header=header,
            data=data,
            type=type,
            prefixes=prefixes,
            context=context,
            strip=strip,
        )

    @staticmethod
    def parse_csv(
        csvfile: "Union[Iterable[str], Path, str]",
        type: "Optional[str]" = "Dataset",
        prefixes: "Optional[dict]" = None,
        context: "Optional[Union[dict, list]]" = None,
        encoding: str = "utf-8",
        dialect: "Optional[Union[csv.Dialect, str]]" = None,
        **kwargs,
    ) -> "TableDoc":
        # pylint: disable=line-too-long
        """Parse a csv file using the standard library csv module.

        Arguments:
            csvfile: Name of CSV file to parse or an iterable of strings.
            type: Type of data to save (applies to all rows).  Should
                either be one of the pre-defined names: "Dataset",
                "Distribution", "AccessService", "Parser" and "Generator"
                or an IRI to a class in an ontology.  Defaults to
                "Dataset".
            prefixes: Dict with prefixes in addition to those included in the
                JSON-LD context.  Should map namespace prefixes to IRIs.
            context: Dict with user-defined JSON-LD context.
            encoding: The encoding of the csv file.  Note that Excel may
                encode as "ISO-8859" (which was commonly used in the 1990th).
            dialect: A subclass of csv.Dialect, or the name of the dialect,
                specifying how the `csvfile` is formatted.  For more details,
                see [Dialects and Formatting Parameters].
            kwargs: Additional keyword arguments overriding individual
                formatting parameters.  For more details, see
                [Dialects and Formatting Parameters].

        Returns:
            New TableDoc instance.

        References:
        [Dialects and Formatting Parameters]: https://docs.python.org/3/library/csv.html#dialects-and-formatting-parameters
        """

        def read(f, dialect):
            """Return csv reader from file-like object `f`."""
            if dialect is None and not kwargs:
                sample = f.read(1024)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t ")
                except csv.Error:
                    # The build-in sniffer not always work well with
                    # non-numerical csv files. Try our simple sniffer
                    dialect = csvsniff(sample)
                finally:
                    f.seek(0)
            reader = csv.reader(f, dialect=dialect, **kwargs)
            header = next(reader)
            data = list(reader)
            return header, data

        if isinstance(csvfile, (str, Path)):
            with openfile(csvfile, mode="rt", encoding=encoding) as f:
                header, data = read(f, dialect)
        else:
            header, data = read(csvfile, dialect)

        return TableDoc(
            header=header,
            data=data,
            type=type,
            prefixes=prefixes,
            context=context,
        )

    def write_csv(
        self,
        csvfile: "Union[Path, str, Writer]",
        encoding: str = "utf-8",
        dialect: "Union[csv.Dialect, str]" = "excel",
        prefixes: "Optional[dict]" = None,
        **kwargs,
    ) -> None:
        # pylint: disable=line-too-long
        """Write the table to a csv file using the standard library csv module.

        Arguments:
            csvfile: File-like object or name of CSV file to write.
            encoding: The encoding of the csv file.
            dialect: A subclass of csv.Dialect, or the name of the dialect,
                specifying how the `csvfile` is formatted.  For more details,
                see [Dialects and Formatting Parameters].
            prefixes: Prefixes used to compact the header.
            kwargs: Additional keyword arguments overriding individual
                formatting parameters.  For more details, see
                [Dialects and Formatting Parameters].

        References:
        [Dialects and Formatting Parameters]: https://docs.python.org/3/library/csv.html#dialects-and-formatting-parameters
        """

        def write(f):
            writer = csv.writer(f, dialect=dialect, **kwargs)

            # TODO: use self.context and compact to shortnames
            if prefixes:
                header = []
                for h in self.header:
                    for prefix, ns in prefixes.items():
                        if h.startswith(str(ns)):
                            header.append(f"{prefix}:{h[len(str(ns)):]}")
                            break
                    else:
                        header.append(h)
                writer.writerow(header)
            else:
                writer.writerow(self.header)

            for row in self.data:
                writer.writerow(row)

        if isinstance(csvfile, (str, Path)):
            with open(csvfile, mode="wt", encoding=encoding) as f:
                write(f)
        else:
            write(csvfile)


def csvsniff(sample):
    """Custom csv sniffer.

    Analyse csv sample and returns a csv.Dialect instance.
    """
    # Determine line terminator
    if "\r\n" in sample:
        linesep = "\r\n"
    else:
        counts = {s: sample.count(s) for s in "\n\r"}
        linesep = max(counts, key=lambda k: counts[k])

    lines = sample.split(linesep)
    del lines[-1]  # skip last line since it might be truncated
    if not lines:
        raise csv.Error(
            "too long csv header. No line terminator within sample"
        )
    header = lines[0]

    # Possible delimiters and quote chars to check
    delims = [d for d in ",;\t :" if header.count(d)]
    quotes = [q for q in "\"'" if sample.count(q)]
    if not quotes:
        quotes = ['"']

    # For each (quote, delim)-pair, count the number of tokens per line
    # Only pairs for which all lines has the same number of tokens are added
    # to ntokens
    ntokens = {}  # map (quote, delim) to number of tokens per line
    for q in quotes:
        for d in delims:
            ntok = []
            for ln in lines:
                # Remove quoted tokens
                ln = re.sub(f"(^{q}[^{q}]*{q}{d})|({d}{q}[^{q}]*{q}$)", d, ln)
                ln = re.sub(f"{d}{q}[^{q}]*{q}{d}", d * 2, ln)
                ntok.append(len(ln.split(d)))

            if ntok and max(ntok) == min(ntok):
                ntokens[(q, d)] = ntok[0]

    # From ntokens, select (quote, delim) pair that results in the highest
    # number of tokens per line
    if not ntokens:
        raise csv.Error("not able to determine delimiter")
    quote, delim = max(ntokens, key=lambda k: ntokens[k])

    class dialect(csv.Dialect):
        """Custom dialect."""

        # pylint: disable=too-few-public-methods
        _name = "sniffed"
        delimiter = delim
        doublequote = True  # quote chars inside quotes are duplicated
        # escapechar = "\\"  # unused
        lineterminator = linesep
        quotechar = quote
        quoting = csv.QUOTE_MINIMAL
        skipinitialspace = False  # don't ignore spaces before a delimiter
        strict = False  # be permissive on malformed csv input

    return dialect

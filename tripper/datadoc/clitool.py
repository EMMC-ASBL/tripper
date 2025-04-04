"""A script for data documentation."""

# pylint: disable=too-many-branches

import argparse
import io
import json
import os
from pathlib import Path

from tripper import Session, Triplestore
from tripper.datadoc import (
    TableDoc,
    delete,
    get_jsonld_context,
    load,
    load_dict,
    save_datadoc,
    save_dict,
    search_iris,
)


def subcommand_add(ts, args):
    """Subcommand for populating the triplestore"""
    infile = Path(args.input)
    extension = args.input_format if args.input_format else infile.suffix
    fmt = extension.lower().lstrip(".")

    if fmt in ("yml", "yaml"):
        save_datadoc(ts, infile)
    elif fmt in ("csv",):
        kw = {}
        if args.csv_option:
            for token in args.csv_option:
                option, value = token.split("=", 1)
                kw[option] = value
        td = TableDoc.parse_csv(
            infile, context=get_jsonld_context(args.context), **kw
        )
        td.save(ts)
    else:
        raise ValueError(f"Unknown input format: {fmt}")

    if args.dump:
        ts.serialize(args.dump, format=args.format)


def subcommand_delete(ts, args):
    """Subcommand for removing matching entries in the triplestore."""
    criterias = {}
    regex = {}
    if args.criteria:
        for crit in args.criteria:
            if "=~" in crit:
                key, value = crit.split("=~", 1)
                regex[key] = value
            else:
                key, value = crit.split("=", 1)
                criterias[key] = value
    delete(ts, type=args.type, criterias=criterias, regex=regex)


def subcommand_find(ts, args):
    """Subcommand for finding IRIs in the triplestore."""
    criterias = {}
    regex = {}
    if args.criteria:
        for crit in args.criteria:
            if "=~" in crit:
                key, value = crit.split("=~", 1)
                regex[key] = value
            else:
                key, value = crit.split("=", 1)
                criterias[key] = value

    iris = search_iris(ts, type=args.type, criterias=criterias, regex=regex)

    # Infer format
    if args.format:
        fmt = args.format.lower()
    elif args.output:
        fmt = Path(args.output).suffix.lower().lstrip(".")
    else:
        fmt = "iris"

    # Create output
    if fmt in ("iris", "txt"):
        s = "\n".join(iris)
    elif fmt == "json":
        s = json.dumps(
            [load_dict(ts, iri) for iri in iris if not iri.startswith("_:")],
            indent=2,
        )
    elif fmt in ("turtle", "ttl"):
        ts2 = Triplestore("rdflib")
        for iri in iris:
            d = load_dict(ts, iri)
            save_dict(ts2, d)
        s = ts2.serialize()
    elif fmt == "csv":
        dicts = [load_dict(ts, iri) for iri in iris]
        td = TableDoc.fromdicts(dicts)
        with io.StringIO() as f:
            td.write_csv(f, prefixes=ts.namespaces)
            s = f.getvalue()
    else:
        raise ValueError(f"Unknown format: {fmt}")

    if args.output:
        with open(args.output, "wt", encoding="utf-8") as f:
            f.write(s + os.linesep)
    else:
        print(s)

    return s


def subcommand_fetch(ts, args):
    """Subcommand for fetching a documented dataset from a storage."""
    data = load(ts, args.iri)

    if args.output:
        with open(args.output, "wb") as f:
            f.write(data)
    else:
        print(data)

    return data


def maincommand(argv=None):
    """Main command."""
    # pylint: disable=too-many-statements

    parser = argparse.ArgumentParser(
        description=(
            "Tool for data documentation.\n\n"
            "It allows populating and searching a triplestore for existing "
            "documentation."
        ),
    )

    subparsers = parser.add_subparsers(required=True, help="Subcommands:")

    # Subcommand: add
    parser_add = subparsers.add_parser(
        "add",
        help="Populate the triplestore with data documentation.",
    )
    parser_add.set_defaults(func=subcommand_add)
    parser_add.add_argument(
        "input",
        help=(
            "Path or URL to the input the triplestore should be populated "
            "from."
        ),
    )
    parser_add.add_argument(
        "--input-format",
        "-i",
        choices=["yaml", "csv"],
        help=(
            "Input format. By default it is inferred from the file "
            "extension of the `input` argument."
        ),
    )
    parser_add.add_argument(
        "--csv-option",
        action="append",
        metavar="OPTION=VALUE",
        help=(
            "Options describing the CSV dialect for --input-format=csv. "
            "Common options are 'dialect', 'delimiter' and 'quotechar'. "
            "This option may be provided multiple times."
        ),
    )
    parser_add.add_argument(
        "--context",
        help="Path or URL to custom JSON-LD context for the input.",
    )
    parser_add.add_argument(
        "--dump",
        "-d",
        metavar="FILENAME",
        help="File to dump the populated triplestore to.",
    )
    parser_add.add_argument(
        "--format",
        "-f",
        default="turtle",
        help='Format to use with `--dump`.  Default is "turtle".',
    )

    # Subcommand: delete
    parser_delete = subparsers.add_parser(
        "delete", help="Delete matching resources in the triplestore."
    )
    parser_delete.set_defaults(func=subcommand_delete)
    parser_delete.add_argument(
        "--type",
        "-t",
        help=(
            'Either a resource type (ex: "dataset", "distribution", ...) '
            "or the IRI of a class to limit the search to."
        ),
    )
    parser_delete.add_argument(
        "--criteria",
        "-c",
        action="append",
        metavar="IRI=VALUE",
        help=(
            "Matching criteria for resources to delete. The IRI may be "
            'written with namespace prefix, like `dcterms:title="My title"`. '
            'Writing the criteria with the "=" operator, corresponds to '
            "exact match. "
            'If the operator is written "=~", regular expression matching '
            "will be used instead. This option can be given multiple times."
        ),
    )

    # Subcommand: find
    parser_find = subparsers.add_parser(
        "find", help="Find documented resources in the triplestore."
    )
    parser_find.set_defaults(func=subcommand_find)
    parser_find.add_argument(
        "--type",
        "-t",
        help=(
            'Either a resource type (ex: "dataset", "distribution", ...) '
            "or the IRI of a class to limit the search to."
        ),
    )
    parser_find.add_argument(
        "--criteria",
        "-c",
        action="append",
        metavar="IRI=VALUE",
        help=(
            "Matching criteria for resources to find. The IRI may be written "
            'using a namespace prefix, like `dcterms:title="My title"`. '
            'Writing the criteria with the "=" operator, corresponds to '
            "exact match. "
            'If the operator is written "=~", regular expression matching '
            "will be used instead. This option can be given multiple times."
        ),
    )
    parser_find.add_argument(
        "--output",
        "-o",
        metavar="FILENAME",
        help=(
            "Write matching output to the given file. The default is to "
            "write to standard output."
        ),
    )
    parser_find.add_argument(
        "--format",
        "-f",
        default="iris",
        choices=["iris", "json", "turtle", "csv"],
        help=(
            "Output format to list the matched resources. The default is "
            "to infer from the file extension if --output is given. "
            'Otherwise it defaults to "iris".'
        ),
    )

    # Subcommand: fetch
    parser_fetch = subparsers.add_parser(
        "fetch", help="Fetch documented dataset from a storage."
    )
    parser_fetch.set_defaults(func=subcommand_fetch)
    parser_fetch.add_argument(
        "iri",
        help="IRI of dataset to fetch.",
    )
    parser_fetch.add_argument(
        "--output",
        "-o",
        metavar="FILENAME",
        help=(
            "Write the dataset to the given file. The default is to write "
            "to standard output."
        ),
    )

    # General: options
    parser.add_argument(
        "--config",
        "-c",
        help="Session configuration file.",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Show Python traceback on error."
    )
    parser.add_argument(
        "--triplestore",
        "-t",
        help=(
            "Name of triplestore to connect to. The name should be defined "
            "in the session configuration file."
        ),
    )
    parser.add_argument(
        "--backend",
        "-b",
        default="rdflib",
        help=(
            'Triplestore backend to use. Defaults to "rdflib" - an '
            "in-memory rdflib triplestore, that can be pre-loaded with "
            "--parse."
        ),
    )
    parser.add_argument(
        "--base-iri",
        "-B",
        help="Base IRI of the triplestore.",
    )
    parser.add_argument(
        "--database",
        "-d",
        help="Name of database to connect to (for backends supporting it).",
    )
    parser.add_argument(
        "--package",
        help="Only needed when `backend` is a relative module.",
    )
    parser.add_argument(
        "--parse",
        "-p",
        metavar="LOCATION",
        help="Load triplestore from this location.",
    )
    parser.add_argument(
        "--parse-format",
        "-F",
        help="Used with `--parse`. Format to use when parsing triplestore.",
    )
    parser.add_argument(
        "--prefix",
        "-P",
        action="append",
        metavar="PREFIX=URL",
        help=(
            "Namespace prefix to bind to the triplestore. "
            "This option can be given multiple times."
        ),
    )

    args = parser.parse_args(argv)

    if args.triplestore:
        session = Session(config=args.config)
        ts = session.get_triplestore(args.triplestore)
    else:
        ts = Triplestore(
            backend=args.backend,
            base_iri=args.base_iri,
            database=args.database,
            package=args.package,
        )

    if args.parse:
        ts.parse(args.parse, format=args.parse_format)

    if args.prefix:
        for token in args.prefix:
            prefix, ns = token.split("=", 1)
            ts.bind(prefix, ns)

    # Call subcommand handler
    try:
        return args.func(ts, args)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        if args.debug:
            raise
        print(f"{exc.__class__.__name__}: {exc}")
        return exc


def main(argv=None):
    """Main function."""
    retval = maincommand(argv)
    return 1 if isinstance(retval, Exception) else 0


if __name__ == "__main__":
    main()

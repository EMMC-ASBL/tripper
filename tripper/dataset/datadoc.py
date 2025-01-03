"""A script for data documentation."""

import argparse
import io
import json

from tripper import Triplestore
from tripper.dataset import (
    TableDoc,
    get_jsonld_context,
    load_dict,
    save_datadoc,
    save_dict,
    search_iris,
)


def subcommand_add(ts, args):
    """Subcommand for populating the triplestore"""
    if args.yamlfile:
        save_datadoc(ts, args.yamlfile)

    if args.table:
        td = TableDoc.parse_csv(
            args.table, context=get_jsonld_context(args.context)
        )
        td.save(ts)

        save_datadoc(ts, args.yamlfile)

    if args.serialize:
        ts.serialize(args.serialize, format=args.sformat)


def subcommand_find(ts, args):
    """Subcommand for finding IRIs in the triplestore."""
    if args.criteria:
        kwargs = dict(crit.split("=", 1) for crit in args.criteria)
    else:
        kwargs = {}
    iris = search_iris(ts, type=args.type, **kwargs)

    # Create output
    if args.format == "iris":
        s = "\n".join(iris)
    elif args.format == "json":
        s = json.dumps([load_dict(ts, iri) for iri in iris], indent=2)
    elif args.format == "turtle":
        ts2 = Triplestore("rdflib")
        for iri in iris:
            d = load_dict(ts, iri)
            save_dict(ts2, d)
        s = ts2.serialize()
    elif args.format == "csv":
        dicts = [load_dict(ts, iri) for iri in iris]
        td = TableDoc.fromdicts(dicts)
        with io.StringIO() as f:
            td.write_csv(f)
            s = f.getvalue()
    else:
        raise ValueError(args.format)

    print(s)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description=(
            "Tool for data documentation.\n\n"
            "It allows populating and searching a triplestore for existing "
            "documentation."
        ),
    )

    subparsers = parser.add_subparsers(required=True, help="subcommand help")

    # Subcommand: add
    parser_add = subparsers.add_parser("add", help="add help")
    parser_add.set_defaults(func=subcommand_add)
    parser_add.add_argument(
        "--context",
        help="Path or URL to custom JSON-LD context.  Used with `--table`.",
    )
    parser_add.add_argument(
        "--yamlfile",
        help="Path or URL to YAML file to add to the triplestore.",
    )
    parser_add.add_argument(
        "--table", help="Path to table to populate the triplestore from."
    )
    parser_add.add_argument(
        "--tformat",
        help=(
            "Used with `--table`. Format of the table to load. "
            "Only csv is currently supported."
        ),
    )
    parser_add.add_argument(
        "--serialize",
        metavar="FILENAME",
        help="File to serialise the populated triplestore to.",
    )
    parser_add.add_argument(
        "--sformat",
        default="turtle",
        help='Format to use with `--serialize`.  Default is "turtle".',
    )

    # Subcommand: find
    parser_find = subparsers.add_parser(
        "find", help="Find IRIs of resources in the triplestore."
    )
    parser_find.set_defaults(func=subcommand_find)
    parser_find.add_argument(
        "--type",
        "-t",
        help="The type of resources to find.",
    )
    parser_find.add_argument(
        "--criteria",
        "-c",
        action="extend",
        nargs="+",
        metavar="KEY=VALUE",
        help=("Matching criteria for resources to find.  "),
    )
    parser_find.add_argument(
        "--format",
        "-f",
        default="iris",
        choices=["iris", "json", "turtle", "csv"],
        help="Output format to list the matched resources.",
    )

    # General: options
    parser.add_argument(
        "--backend",
        "-b",
        default="rdflib",
        help="Triplestore backend to use.",
    )
    parser.add_argument(
        "--base_iri",
        help="Base IRI of the triplestore (seldom needed).",
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
        "--pformat",
        "-f",
        help="Used with `--parse`. Format to use when parsing triplestore.",
    )

    args = parser.parse_args()

    ts = Triplestore(
        backend=args.backend,
        base_iri=args.base_iri,
        database=args.database,
        package=args.package,
    )
    if args.parse:
        ts.parse(args.parse, format=args.pformat)

    # Call subcommand handler
    args.func(ts, args)


if __name__ == "__main__":
    main()

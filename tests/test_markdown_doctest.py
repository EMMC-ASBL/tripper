"""Run doctest on all markdown files in the docs/ folder."""

import sys

import pytest

pytest.importorskip("rdflib")
pytest.importorskip("yaml")
pytest.importorskip("pint")


@pytest.mark.skipif(sys.version_info < (3, 9), reason="pint needs Python 3.9")
def test_markdown_doctest():
    """Runs doctest on all markdown files in the docs/ folder."""
    import doctest
    import os
    from pathlib import Path

    rootdir = Path(__file__).resolve().parent.parent
    skipfiles = {"CHANGELOG.md", "LICENSE.md"}

    for dirpath, _, filenames in os.walk(rootdir / "docs"):
        for filename in filenames:
            if (
                filename in skipfiles
                or filename.startswith(".")
                or not filename.endswith(".md")
            ):
                continue
            path = os.path.join(dirpath, filename)
            relpath = os.path.relpath(dirpath, str(rootdir))
            print(f"-- doctest {relpath}/{filename}")
            doctest.testfile(str(path), module_relative=False)

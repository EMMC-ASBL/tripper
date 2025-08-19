"""Run doctest on all markdown files in the docs/ folder."""

import sys
import warnings

import pytest

pytest.importorskip("rdflib")
pytest.importorskip("yaml")
pytest.importorskip("pint")
pytest.importorskip("pyld")


@pytest.mark.skipif(sys.version_info < (3, 9), reason="pint needs Python 3.9")
def test_markdown_doctest():
    """Runs doctest on all markdown files in the docs/ folder."""
    import doctest
    import os
    from pathlib import Path

    from tripper.utils import check_service_availability

    rootdir = Path(__file__).resolve().parent.parent
    skipfiles = {"CHANGELOG.md", "LICENSE.md"}

    # Skip doctests conditionally
    if not check_service_availability("http://localhost:3030", timeout=1):
        skipfiles.add("session.md")
        warnings.warn("Fuseki is down, skipping running doctest on session.md")

    # Run doctest on all modules
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
            result = doctest.testfile(str(path), module_relative=False)
            if result.failed:
                raise RuntimeError(
                    f"failing doctest: {relpath}/{filename}\n"
                    "To debug, please run:\n\n"
                    f"    python -m doctest {relpath}/{filename}\n"
                )

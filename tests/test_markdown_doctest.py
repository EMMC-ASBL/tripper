"""Run doctest on all markdown files in the docs/ folder."""

import sys
from pathlib import Path

import pytest

pytest.importorskip("rdflib")
pytest.importorskip("yaml")
pytest.importorskip("pint")
pytest.importorskip("pyld")

rootdir = Path(__file__).resolve().parent.parent
docsdir = rootdir / "docs"

skipfiles = {"CHANGELOG.md", "LICENSE.md"}

# Markdown files with doctests that need a running Fuseki service
fuseki_files = {"session.md"}

# Markdown files (relative to docs/) with doctests that need internet access
network_files = {
    "datadoc/customisation.md",
    "datadoc/documenting-a-resource.md",
    "datadoc/fetching-resources-from-a-triplestore.md",
    "tutorial.md",
}

markdown_files = sorted(
    path.relative_to(docsdir).as_posix()
    for path in docsdir.rglob("*.md")
    if path.name not in skipfiles
    and not any(p.startswith(".") for p in path.relative_to(docsdir).parts)
)


def _marks(relpath: str) -> list:
    """Return pytest marks for markdown file `relpath`."""
    marks = []
    if relpath in network_files:
        marks.append(pytest.mark.network)
    if Path(relpath).name in fuseki_files:
        # Uses the shared Fuseki "test_repo" dataset, see
        # test_backends_sparql.py
        marks.append(pytest.mark.xdist_group("triplestore"))
    return marks


@pytest.mark.skipif(sys.version_info < (3, 9), reason="pint needs Python 3.9")
@pytest.mark.parametrize(
    "relpath",
    [pytest.param(f, id=f, marks=_marks(f)) for f in markdown_files],
)
def test_markdown_doctest(relpath):
    """Runs doctest on a markdown file in the docs/ folder."""
    import doctest

    from tripper.utils import service_responds

    path = docsdir / relpath

    if path.name in fuseki_files and not service_responds(
        "http://localhost:3030"
    ):
        pytest.skip("Fuseki is down, skipping doctest")

    result = doctest.testfile(str(path), module_relative=False)
    if result.failed:
        relpath = path.relative_to(rootdir)
        raise RuntimeError(
            f"failing doctest: {relpath}\n"
            "To debug, please run:\n\n"
            f"    python -m doctest {relpath}\n"
        )

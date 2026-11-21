#!/usr/bin/env python
"""Generate the API reference and the landing page of the documentation.

- docs/api_reference/ gets one markdown file per module in tripper/
  (rendered by mkdocstrings) and a `.pages` file per package (used by
  the mkdocs-awesome-pages plugin).

- docs/index.md is a copy of README.md, with links relative to docs/.

Exits with code 1 if any file was changed, such that pre-commit
reports that the hook modified files.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = "tripper"
APIDIR = ROOT / "docs" / "api_reference"
UNWANTED = {"__pycache__", "context", "old"}

changed: list[Path] = []


def write(path: Path, content: str) -> None:
    """Write `content` to `path` if it differs from its current content."""
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        changed.append(path)


def api_reference() -> None:
    """Generate the API reference."""
    pkgdir = ROOT / PACKAGE
    expected = set()
    for pyfile in sorted(pkgdir.rglob("*.py")):
        relpath = pyfile.relative_to(pkgdir)
        if UNWANTED.intersection(relpath.parts) or pyfile.stem.startswith("_"):
            continue
        module = ".".join((PACKAGE, *relpath.with_suffix("").parts))
        mdfile = APIDIR / relpath.with_suffix(".md")
        write(mdfile, f"# {pyfile.stem}\n\n::: {module}\n")
        expected.add(mdfile)

        # Add a .pages file for each (sub)package directory
        for parent in [mdfile.parent, *mdfile.parent.parents]:
            if parent == APIDIR.parent:
                break
            title = "API Reference" if parent == APIDIR else parent.name
            pages = parent / ".pages"
            write(pages, f'title: "{title}"\n')
            expected.add(pages)

    # Remove files for modules that no longer exist
    for path in sorted(APIDIR.rglob("*"), reverse=True):
        if path.is_file() and path not in expected:
            path.unlink()
            changed.append(path)
        elif path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def landing_page() -> None:
    """Generate docs/index.md from README.md."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    write(
        ROOT / "docs" / "index.md",
        readme.replace("(docs/", "(").replace('"docs/', '"'),
    )


if __name__ == "__main__":
    api_reference()
    landing_page()
    for path in changed:
        print(f"Updated {path.relative_to(ROOT)}")  # noqa: T201
    sys.exit(1 if changed else 0)

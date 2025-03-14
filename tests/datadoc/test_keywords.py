"""Test the Keywords class."""


# if True:
def test_parse_default():
    """Test parse keywords."""
    import json

    import pytest

    pytest.importorskip("rdflib")

    from dataset_paths import outdir, rootdir

    from tripper.datadoc.keywords import Keywords

    keywords = Keywords()

    keywords.write_context(outdir / "context.json")
    with open(
        rootdir / "tripper" / "context" / "0.3" / "context.json",
        mode="rt",
        encoding="utf-8",
    ) as f:
        d1 = json.load(f)
    with open(outdir / "context.json", "rt", encoding="utf-8") as f:
        d2 = json.load(f)
    assert d2 == d1

    keywords.write_doc_keywords(outdir / "keywords.md")
    keywords.write_doc_prefixes(outdir / "prefixes.md")

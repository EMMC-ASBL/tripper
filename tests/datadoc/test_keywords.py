"""Test the Keywords class."""

import pytest

pytest.importorskip("yaml")

# pylint: disable=wrong-import-position
from tripper.datadoc.keywords import Keywords

# A fixture used by all the tests
keywords = Keywords()


def test_write():
    """Test write JSON-LD context and documentation."""
    import json

    from dataset_paths import outdir, rootdir  # pylint: disable=import-error

    pytest.importorskip("rdflib")

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


def test_isnested():
    """Test isnested() method."""
    assert keywords.isnested("distribution")
    assert keywords.isnested("creator")
    assert not keywords.isnested("description")
    with pytest.raises(KeyError):
        keywords.isnested("Dataset")


def test_expanded():
    """Test expanded() method."""
    from tripper import DCAT
    from tripper.datadoc.errors import InvalidKeywordError

    assert keywords.expanded("distribution") == DCAT.distribution
    assert keywords.expanded("dcat:distribution") == DCAT.distribution
    assert keywords.expanded("Dataset") == DCAT.Dataset
    assert keywords.expanded("dcat:xxx") == DCAT.xxx
    with pytest.raises(InvalidKeywordError):
        keywords.expanded("xxx")


def test_range():
    """Test range() method."""
    assert keywords.range("distribution") == "dcat:Distribution"
    assert keywords.range("creator") == "foaf:Agent"
    assert keywords.range("description") == "rdfs:Literal"
    with pytest.raises(KeyError):
        keywords.range("Dataset")


def test_normtype():
    """Test normtype() method."""
    from tripper import DCAT
    from tripper.datadoc.errors import NoSuchTypeError

    assert keywords.normtype("Dataset") == [
        "dcat:Dataset",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    ]
    assert keywords.normtype("dcat:Dataset") == [
        "dcat:Dataset",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    ]
    assert keywords.normtype(DCAT.Dataset) == [
        "dcat:Dataset",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    ]
    assert keywords.normtype("Distribution") == "dcat:Distribution"
    with pytest.raises(NoSuchTypeError):
        keywords.normtype("distribution")


def test_keywordname():
    """Test keywordname() method."""
    from tripper import DCTERMS
    from tripper.datadoc.errors import InvalidKeywordError

    assert keywords.keywordname("title") == "title"
    assert keywords.keywordname("dcterms:title") == "title"
    assert keywords.keywordname(DCTERMS.title) == "title"
    with pytest.raises(InvalidKeywordError):
        keywords.keywordname("xxx")


def test_typename():
    """Test typename() method."""
    from tripper import DCAT
    from tripper.datadoc.errors import NoSuchTypeError

    assert keywords.typename("Dataset") == "Dataset"
    assert keywords.typename("dcat:Dataset") == "Dataset"
    assert keywords.typename(DCAT.Dataset) == "Dataset"
    with pytest.raises(NoSuchTypeError):
        keywords.typename("xxx")

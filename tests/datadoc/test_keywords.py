"""Test the Keywords class."""

import pytest

pytest.importorskip("yaml")

# pylint: disable=wrong-import-position
from tripper.datadoc import Keywords

# A fixture used by all the tests
keywords = Keywords()


def test_get_keywords():
    """Test get_keywords() function."""
    from tripper.datadoc import get_keywords

    kw1 = get_keywords()
    assert kw1.data == keywords.data
    assert kw1.keywords == keywords.keywords
    assert kw1.domain == keywords.domain
    assert kw1.data.__class__.__name__ == "AttrDict"
    assert kw1.keywords.__class__.__name__ == "AttrDict"

    kw2 = get_keywords(keywords, domain=None)
    assert kw2.data == keywords.data
    assert kw2.keywords == keywords.keywords
    assert kw2.domain == keywords.domain
    assert kw2.data.__class__.__name__ == "AttrDict"
    assert kw2.keywords.__class__.__name__ == "AttrDict"

    kw3 = get_keywords(keywords)
    assert kw3.data == keywords.data
    assert kw3.keywords == keywords.keywords
    assert kw3.domain == keywords.domain
    assert kw3.data.__class__.__name__ == "AttrDict"
    assert kw3.keywords.__class__.__name__ == "AttrDict"


def test_dir():
    """Test `dir(keywords)`."""
    dirlist = set(dir(keywords))
    assert "write_context" in dirlist
    assert "__dir__" in dirlist
    assert "data" in dirlist
    assert "keywords" in dirlist
    assert "domain" in dirlist


def test_copy():
    """Test copy()."""
    copy = keywords.copy()
    assert copy.data == keywords.data
    assert copy.keywords == keywords.keywords
    assert copy.domain == keywords.domain


def test_get_prefixes():
    """Test get_prefixes()."""
    prefixes = keywords.get_prefixes()
    assert prefixes["dcat"] == "http://www.w3.org/ns/dcat#"


def test_get_context():
    """Test get_context()."""
    ctx = keywords.get_context()
    assert ctx["dcat"] == "http://www.w3.org/ns/dcat#"
    assert ctx["creator"] == {"@id": "dcterms:creator", "@type": "@id"}
    assert ctx["title"] == {"@id": "dcterms:title", "@language": "en"}
    assert ctx["version"] == "dcat:version"


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


def test_superclasses():
    """Test superclasses() method."""
    from tripper import DCAT
    from tripper.datadoc.errors import NoSuchTypeError

    assert keywords.superclasses("Dataset") == [
        "dcat:Dataset",
        "dcat:Resource",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    ]
    assert keywords.superclasses("dcat:Dataset") == [
        "dcat:Dataset",
        "dcat:Resource",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    ]
    assert keywords.superclasses(DCAT.Dataset) == [
        "dcat:Dataset",
        "dcat:Resource",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    ]
    assert keywords.superclasses("Distribution") == [
        "dcat:Distribution",
        "dcat:Resource",
    ]
    with pytest.raises(NoSuchTypeError):
        keywords.superclasses("distribution")


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

"""Test context module."""

import pytest

pytest.importorskip("pyld")

# pylint: disable=wrong-import-position
from tripper.datadoc.context import Context, get_context

# A fixture used by all the tests
ctx = Context()


def test_copy():
    """Test copy() method."""
    copy = ctx.copy()
    assert id(copy) != id(ctx)
    assert copy.ctx == ctx.ctx


def test_add_context():
    """Test add_context() method."""
    context = {
        "fam": "http://example.com/family#",
        "hasSon": {"@id": "fam:hasSon", "@type": "@id"},
        "hasDaughter": {"@id": "fam:hasDaughter", "@type": "@id"},
        "Son": "fam:Son",
        "Daughter": "fam:Daughter",
    }
    copy = ctx.copy()
    copy.add_context(context)
    assert "fam" in copy.ctx["mappings"]
    assert copy.ctx["mappings"]["fam"]["@id"] == "http://example.com/family#"
    assert copy.ctx["mappings"]["fam"]["_prefix"] is True

    assert "hasSon" in copy.ctx["mappings"]
    assert copy.ctx["mappings"]["hasSon"]["@id"] == (
        "http://example.com/family#hasSon"
    )
    assert copy.ctx["mappings"]["hasSon"]["_prefix"] is False


def test_get_context_dict():
    """Test get_context() method."""
    context = ctx.get_context_dict()
    assert context["adms"] == "http://www.w3.org/ns/adms#"
    assert context["mediaType"] == {
        "@id": "http://www.w3.org/ns/dcat#mediaType",
        "@type": "@id",
    }


def test_get_mappings():
    """Test get_mappings() method."""
    mappings = ctx.get_mappings()
    assert "adms" not in mappings
    assert mappings["mediaType"] == "http://www.w3.org/ns/dcat#mediaType"


def test_get_prefixes():
    """Test get_prefixes() method."""
    prefixes = ctx.get_prefixes()
    assert prefixes["adms"] == "http://www.w3.org/ns/adms#"
    assert "mediaType" not in prefixes


def test_sync_prefixes():
    """Test sync_prefixes() method."""
    from tripper import Triplestore

    ts = Triplestore("rdflib")
    ns1 = ts.namespaces.copy()
    pf1 = ctx.get_prefixes().copy()
    ctx.sync_prefixes(ts)
    ns2 = ts.namespaces.copy()
    pf2 = ctx.get_prefixes().copy()
    assert len(ns2) > len(ns1)
    assert len(pf2) >= len(pf1)
    # xml cannot be added to `ctx` since it doesn't end with a slash or hash
    # assert pf2 == ns2


def test_expand():
    """Test expand() method."""
    from tripper import DCAT, DCTERMS
    from tripper.errors import NamespaceError

    assert ctx.expand("mediaType") == DCAT.mediaType
    assert ctx.expand("dcat:mediaType") == DCAT.mediaType
    assert ctx.expand("dcterms:title") == DCTERMS.title
    assert ctx.expand(DCAT.mediaType) == DCAT.mediaType
    assert ctx.expand(DCAT.distribution) == DCAT.distribution
    assert ctx.expand("non-existing") == "non-existing"

    with pytest.raises(NamespaceError):
        ctx.expand("non-existing", strict=True)


def test_prefixed():
    """Test prefixed() method."""
    from tripper.errors import NamespaceError

    prefixed = "dcat:mediaType"
    assert ctx.prefixed("mediaType") == prefixed
    assert ctx.prefixed(prefixed) == prefixed
    assert ctx.prefixed("http://www.w3.org/ns/dcat#mediaType") == prefixed
    assert ctx.prefixed("non-existing", strict=False) == "non-existing"

    with pytest.raises(NamespaceError):
        ctx.prefixed("non-existing")


def test_shortname():
    """Test shortname() method."""
    from tripper.errors import NamespaceError

    assert ctx.shortname("mediaType") == "mediaType"
    assert ctx.shortname("dcat:mediaType") == "mediaType"
    assert ctx.shortname("http://www.w3.org/ns/dcat#mediaType") == "mediaType"
    assert ctx.prefixed("non-existing", strict=False) == "non-existing"

    with pytest.raises(NamespaceError):
        ctx.prefixed("non-existing")


def test_expanddoc_compactdoc():
    """Test expanddoc() method."""
    doc = {
        "@context": {
            "@base": "http://example1.com/",
            "@vocab": "http://example2.com/",
            "knows": {"@id": "http://example2.com/knows", "@type": "@vocab"},
        },
        "@id": "fred",
        "knows": [{"@id": "barney", "mnemonic": "the sidekick"}, "barney"],
    }

    context = get_context(context=doc)
    exp = context.expanddoc(doc)
    assert exp == [
        {
            "@id": "fred",
            "http://example2.com/knows": [
                {
                    "@id": "barney",
                    "http://example2.com/mnemonic": [
                        {"@value": "the sidekick"}
                    ],
                },
                {"@id": "http://example2.com/barney"},
            ],
        }
    ]
    compact = context.compactdoc(exp)
    assert compact == doc


def test_isref():
    """Test isref() method."""
    assert ctx.isref("dcat:distribution") is True
    assert ctx.isref("dcterms:title") is False


def test_to_triplestore():
    """Test to_triplestore() method."""
    from tripper import Namespace, Triplestore

    PERS = Namespace("http://example.com/person#")
    FAM = Namespace("http://example.com/family#")
    context = {
        "pers": str(PERS),
        "fam": str(FAM),
        "son": {"@id": "fam:son", "@type": "@id"},
        "daughter": {"@id": "fam:daughter", "@type": "@id"},
        "Son": "fam:Son",
        "Daughter": "fam:Daughter",
    }
    ctx = get_context(context=context)

    doc1 = {
        "@id": "pers:ada",
        "daughter": "pers:britt",
        "son": "pers:cyril",
    }
    ts1 = Triplestore("rdflib")
    ctx.to_triplestore(ts1, doc1)
    assert set(ts1.triples()) == {
        (PERS.ada, FAM.daughter, PERS.britt),
        (PERS.ada, FAM.son, PERS.cyril),
    }

    doc2 = {
        "@context": {"father": {"@id": "fam:father", "@type": "@id"}},
        "@id": "pers:ada",
        "daughter": "pers:britt",
        "son": "pers:cyril",
        "father": "pers:daniel",
    }
    ts2 = Triplestore("rdflib")
    ctx.to_triplestore(ts2, doc2)
    assert set(ts2.triples()) == {
        (PERS.ada, FAM.daughter, PERS.britt),
        (PERS.ada, FAM.son, PERS.cyril),
        (PERS.ada, FAM.father, PERS.daniel),
    }

    doc3 = [
        {
            "@context": {"father": {"@id": "fam:father", "@type": "@id"}},
            "@id": "pers:ada",
            "daughter": "pers:britt",
            "son": "pers:cyril",
            "father": "pers:daniel",
        },
        {
            "@id": "pers:cyril",
            "daughter": "pers:ewa",
            "son": "pers:fredrik",
        },
    ]
    ts3 = Triplestore("rdflib")
    ctx.to_triplestore(ts3, doc3)
    assert set(ts3.triples()) == {
        (PERS.ada, FAM.daughter, PERS.britt),
        (PERS.ada, FAM.son, PERS.cyril),
        (PERS.ada, FAM.father, PERS.daniel),
        (PERS.cyril, FAM.daughter, PERS.ewa),
        (PERS.cyril, FAM.son, PERS.fredrik),
    }


def test_base():
    """Test base property."""
    assert ctx.base is None
    ctx.base = "http://base.org/"
    assert ctx.base == "http://base.org/"


def test_processingmode():
    """Test processingMode property."""
    assert ctx.processingMode == "json-ld-1.1"

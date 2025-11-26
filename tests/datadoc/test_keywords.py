"""Test the Keywords class."""

import pytest

pytest.importorskip("yaml")
pytest.importorskip("pyld")

# pylint: disable=wrong-import-position
from tripper.datadoc import Keywords

# A fixture used by all the tests
keywords = Keywords()


def test_get_keywords():
    """Test get_keywords() function."""
    from dataset_paths import testdir  # pylint: disable=import-error

    from tripper import DDOC
    from tripper.datadoc import get_keywords

    kw1 = get_keywords()
    assert kw1.data == keywords.data
    assert set(kw1.data.keys()) == {"prefixes", "theme", "resources"}
    assert kw1.keywords == keywords.keywords
    assert kw1.theme == keywords.theme
    assert kw1.data.__class__.__name__ == "AttrDict"
    assert kw1.keywords.__class__.__name__ == "AttrDict"

    kw2 = get_keywords(keywords, theme=None)
    assert kw2.data == keywords.data
    assert kw2.keywords == keywords.keywords
    assert kw2.theme == keywords.theme
    assert kw2.data.__class__.__name__ == "AttrDict"
    assert kw2.keywords.__class__.__name__ == "AttrDict"

    kw3 = get_keywords(keywords)
    assert kw3.data == keywords.data
    assert kw3.keywords == keywords.keywords
    assert kw3.theme == keywords.theme
    assert kw3.data.__class__.__name__ == "AttrDict"
    assert kw3.keywords.__class__.__name__ == "AttrDict"

    kw4 = get_keywords(theme=DDOC.process)
    assert set(kw4.data.keys()) == {
        "prefixes",
        "theme",
        "resources",
    }
    assert kw4.data.theme == ["ddoc:datadoc", "ddoc:prefixes", "ddoc:process"]
    assert len(kw4.keywords) > len(kw1.keywords)

    kw5 = get_keywords(yamlfile=testdir / "input" / "custom_keywords.yaml")
    assert set(kw5.data.keys()) == {
        "prefixes",
        "theme",
        "resources",
    }
    assert kw5.data.theme == ["ddoc:datadoc", "ddoc:prefixes", "ddoc:process"]
    assert len(kw5.keywords) > len(kw1.keywords)

    kw6 = get_keywords(
        kw4, yamlfile=testdir / "input" / "custom_keywords.yaml"
    )
    assert kw4.data.theme == ["ddoc:datadoc", "ddoc:prefixes", "ddoc:process"]
    assert "batchNumber" in kw6


def test_iter():
    """Test __iter__() method."""
    n = 0
    for k in keywords:
        if k:
            n += 1
    assert n == len(keywords)

    it = iter(keywords)
    assert next(it) in keywords


def test_len():
    """Test __iter__() method."""
    assert len(keywords) == 127


def test_dir():
    """Test __dir__() method."""
    dirlist = set(dir(keywords))
    assert "save_context" in dirlist
    assert "__dir__" in dirlist
    assert "data" in dirlist
    assert "keywords" in dirlist
    assert "theme" in dirlist


def test_copy():
    """Test copy() method."""
    copy = keywords.copy()
    assert copy.data == keywords.data
    assert copy.keywords == keywords.keywords
    assert copy.theme == keywords.theme


def test_add():
    """Test add() method."""
    from dataset_paths import indir, ontodir  # pylint: disable=import-error

    from tripper.datadoc import get_keywords

    kw = get_keywords(theme=None)
    kw1 = kw.copy()
    kw1.add("ddoc:datadoc")
    assert kw1 == keywords

    kw2 = kw.copy()
    kw2.add(indir / "custom_keywords.yaml")
    assert "distribution" in kw2
    assert "batchNumber" in kw2

    # Works, but requires that the tests are run from the root directory
    # kw3 = kw.copy()
    # kw3.add("./tests/input/custom_keywords.yaml")
    # assert kw3 == kw2

    kw4 = get_keywords(theme=None)
    kw4.add(kw2)
    assert len(kw4) == len(kw2)

    kw5 = get_keywords(theme=None)
    kw5.add([indir / "custom_keywords.yaml"], format="yaml")
    assert len(kw5) == len(kw2)

    with pytest.raises(TypeError):
        # Length of input and format must equal
        kw5.add([indir / "custom_keywords.yaml"], format=["yaml", "yml"])

    kw6 = get_keywords(theme="ddoc:prefixes")
    kw6.add_prefix("ex", "http://example.com/kw/")
    kw6.add([indir / "new_keywords.csv"])
    assert list(kw6.data.resources.DeviceX.keywords.keys()) == [
        "voltage",
        "owner",
    ]

    kw7 = get_keywords(theme=None)
    kw7.add(ontodir / "family.ttl")

    with pytest.raises(TypeError):
        kw7.add(True)


def test_load_yaml():
    """Test load_yaml() method. Most of it is already tested via get_keywords().
    Only a few additional tests are added here.
    """
    from dataset_paths import indir  # pylint: disable=import-error

    from tripper.datadoc.errors import ParseError

    kw = keywords.copy()

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords0.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords1.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords2.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords3.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords4.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords5.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords6.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords7.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords8.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords9.yaml")

    with pytest.raises(ParseError):
        kw.load_yaml(indir / "invalid_keywords9.yaml", redefine="xxx")

    # keywords are unchanged by failures
    # assert kw == keywords

    kw.load_yaml(indir / "invalid_keywords9.yaml", redefine="skip")
    assert kw["title"].iri == "dcterms:title"

    kw.load_yaml(indir / "invalid_keywords9.yaml", redefine="allow")
    assert kw["title"].iri == "myonto:a"

    kw.load_yaml(indir / "valid_keywords.yaml")


def test_save_yaml():
    """Test save_yaml() method."""
    from dataset_paths import outdir  # pylint: disable=import-error

    from tripper.datadoc import get_keywords

    kw = get_keywords()
    kw.save_yaml(outdir / "keywords.yaml")


def test_load_table():
    """Test load_table() method."""
    from dataset_paths import indir  # pylint: disable=import-error

    from tripper.datadoc import get_keywords

    kw = get_keywords()
    kw.load_table(
        indir / "keywords.csv", prefixes={"ex": "http://example.com/ex#"}
    )
    assert kw.keywords.hasColor == {
        "iri": "ex:hasColor",
        "type": "owl:DatatypeProperty",
        "domain": "prov:Entity",
        "range": "rdfs:Literal",
        "datatype": "xsd:string",
        "conformance": "optional",
        "description": "A colour name.",
        "name": "hasColor",
    }
    assert kw.keywords.ref == {
        "iri": "ex:ref",
        "type": "owl:AnnotationProperty",
        "domain": ["dcat:Resource", "rdfs:Resource"],
        "range": "rdfs:Literal",
        "datatype": "rdf:langString",
        "conformance": "optional",
        "description": "A bibliographic reference.",
        "name": "ref",
    }
    assert kw.keywords.neighbor == {
        "iri": "ex:neighbor",
        "type": "owl:ObjectProperty",
        "domain": ["dcat:Resource", "rdfs:Resource"],
        "range": "foaf:Agent",
        "description": "A neighboring object.",
        "usageNote": "Ref. to neighboring object.",
        "name": "neighbor",
    }


def test_save_table():
    """Test save_table() method."""
    import csv

    from dataset_paths import outdir  # pylint: disable=import-error

    from tripper.datadoc import get_keywords

    kw = get_keywords()
    kw.save_table(outdir / "keywords.csv")

    with open(outdir / "keywords.csv", "rt", encoding="utf-8") as f:
        cr = csv.reader(f)
        header = next(cr)
        row1 = next(cr)

    assert len(header) == 9
    facit = [
        ("@id", "dcterms:accessRights"),
        ("@type", "owl:ObjectProperty"),
        ("label", "accessRights"),
        ("domain", "dcat:Resource"),
        ("range", "dcterms:RightsStatement"),
        ("conformance", "ddoc:optional"),
        (
            "description",
            "Information about who can access the resource or an indication "
            "of its security status.",
        ),
        (
            "usageNote",
            "Access Rights may include information regarding access or "
            "restrictions based on privacy, security, or other policies. "
            "The following preferred Rights Statement individuals are "
            "defined: `accr:PUBLIC`, `accr:NON_PUBLIC`, `accr:CONFIDENTIAL`, "
            "`accr:RESTRICTED`, `accr:SENSITIVE`",
        ),
        ("theme", "ddoc:datadoc"),
    ]
    assert list(zip(header, row1)) == facit


def test_unit():
    """Test keyword definition with default."""
    from tripper import Triplestore
    from tripper.datadoc import get_keywords, store

    kw = get_keywords(theme=None)
    d = {
        "prefixes": {
            "ex": "http://example.com/ex#",
        },
        "resources": {
            "Resource": {
                "iri": "dcat:Resource",
                "keywords": {
                    "voltage": {
                        "iri": "ex:voltage",
                        "range": "rdfs:Literal",
                        "datatype": "xsd:double",
                        "unit": "Volt",
                    }
                },
            }
        },
    }
    kw.add(d)

    ts = Triplestore(backend="rdflib")
    data = {
        "@id": "ex:equipment",
        "@type": "dcat:Resource",
        "voltage": 3.2,
    }
    store(ts, data, keywords=kw)
    print(ts.serialize())
    # TODO: complete the test...


def test_keywordnames():
    """Test keywordnames() method."""
    keywordnames = keywords.keywordnames()
    assert "distribution" in keywordnames
    assert len(keywordnames) == len(keywords)


def test_classnames():
    """Test keywordnames() method."""
    classnames = keywords.classnames()
    assert "Dataset" in classnames
    assert len(classnames) == 27


def test_fromdicts():
    """Test fromdicts() method."""
    from tripper.datadoc import get_context

    kw = Keywords(theme=None)
    prefixes = get_context().get_prefixes()
    dicts1 = [
        {
            "@id": "dcterms:description",
            "@type": "http://www.w3.org/2002/07/owl#AnnotationProperty",
            "label": "description",
            "description": "A free-text account of the resource.",
            "usageNote": (
                "This property can be repeated for parallel language versions "
                "of the description."
            ),
            "domain": "dcat:Resource",
            "range": "rdf:langString",
            "conformance": "ddoc:mandatory",
        },
        {
            "@id": "dcterms:modified",
            "@type": "owl:DatatypeProperty",
            "label": "modificationDate",
            "description": (
                "The most recent date on which the resource was changed or "
                "modified."
            ),
            "domain": "dcat:Resource",
            "range": "xsd:date",
            "conformance": "ddoc:optional",
        },
        {
            "@id": "oteio:curator",
            "@type": "owl:ObjectProperty",
            "domain": "dcat:Resource",
            "range": "foaf:Agent",
            "description": "The agent that curated the resource.",
            "usageNote": "Use `issued` to refer to the date of curation.",
        },
        {
            "@id": "oteio:minimal",
        },
    ]
    kw.fromdicts(dicts1, prefixes=prefixes)
    assert kw.data.prefixes == prefixes
    assert "description" in kw.keywords
    assert "modificationDate" in kw.keywords
    assert kw.keywords.modificationDate.iri == "dcterms:modified"
    assert kw.keywords.curator.iri == "oteio:curator"
    assert kw.keywords.curator.range == "foaf:Agent"


def test_save_rdf():
    """Test missing_keywords() method.  VERY SLOW!"""
    from dataset_paths import outdir  # pylint: disable=import-error

    from tripper import Triplestore

    pytest.importorskip("rdflib")

    ts = Triplestore(backend="rdflib")
    d = keywords.save_rdf(ts)

    graph = d["@graph"]
    # assert len(graph) == len(existing2) - 1  # conformance already exists
    (descr,) = [d for d in graph if d["@id"] == "dcterms:description"]
    assert descr["@type"] == "owl:AnnotationProperty"
    assert descr["rdfs:range"] == "rdf:langString"

    # Create input to test_load_rdf()
    ts.serialize(outdir / "default-keywords.ttl")


def test_missing_keywords():
    """Test missing_keywords() method."""
    from dataset_paths import outdir  # pylint: disable=import-error

    from tripper import Triplestore

    pytest.importorskip("rdflib")

    ts = Triplestore(backend="rdflib")
    missing = keywords.missing_keywords(ts)
    assert len(missing) == len(keywords.keywordnames())

    missing2 = keywords.missing_keywords(ts, include_classes=True)
    assert len(missing2) == (
        len(keywords.keywordnames()) + len(keywords.classnames())
    )

    ts.parse(outdir / "default-keywords.ttl")

    missing3 = keywords.missing_keywords(ts, include_classes=True)
    assert len(missing3) == 0

    missing4, existing4 = keywords.missing_keywords(ts, return_existing=True)
    assert len(missing4) == 0
    assert len(existing4) == len(keywords.keywordnames())


def test_load_rdf():
    """Test load_rdf() method."""
    from dataset_paths import outdir  # pylint: disable=import-error

    from tripper import Triplestore

    # from tripper.datadoc import acquire
    from tripper.datadoc.keywords import load_datadoc_schema

    ts = Triplestore(backend="rdflib")
    load_datadoc_schema(ts)
    ts.parse(outdir / "default-keywords.ttl")
    ts.bind("eli", "http://data.europa.eu/eli/ontology#")

    kw = Keywords(theme=None)
    kw.load_rdf(ts)

    # Check that loaded Keywords object matches the global global
    # keywords object
    for name in keywords.keywordnames():
        for k, v in keywords[name].items():
            if k in ("range", "theme") and k not in kw[name]:
                continue
            if isinstance(kw[name][k], list):
                continue
            assert kw.expanded(kw[name][k], False) == keywords.expanded(
                v, False
            )


def test_load2():
    """Test load_rdf() on an ontology."""
    from dataset_paths import ontodir  # pylint: disable=import-error

    from tripper import Triplestore
    from tripper.datadoc import get_keywords
    from tripper.utils import AttrDict

    ts = Triplestore("rdflib")
    ts.parse(ontodir / "family.ttl")

    # Create an empty Keywords object and load the ontology
    kw = get_keywords(theme=None)
    assert kw.keywords == AttrDict()
    kw.load_rdf(ts, strict=False, redefine="allow")

    assert set(kw.keywordnames()) == {
        "hasAge",
        "hasWeight",
        "hasSkill",
        "hasChild",
        "hasName",
    }
    assert set(kw.classnames()) == {
        "Person",
        "Parent",
        "Child",
        "Skill",
        "Resource",
    }
    d = kw["hasAge"]
    assert d.iri == "fam:hasAge"
    assert d.range == "rdfs:Literal"
    assert d.datatype == "xsd:double"
    assert d.unit == "year"
    assert kw["hasName"] == {
        "iri": "fam:hasName",
        "type": "owl:AnnotationProperty",
        "domain": "rdfs:Resource",
        "range": "rdfs:Literal",
        "comment": "Name.",
        "name": "hasName",
    }

    ts = Triplestore("rdflib")
    ts.parse(ontodir / "family.ttl")

    # Create a new Keywords object with
    # default keywords and load from the triplestore
    kw2 = get_keywords()
    kw2.load_rdf(ts, redefine="allow")

    # Ensure that the specified keywords are in kw2
    assert not {
        "hasAge",
        "hasWeight",
        "hasSkill",
        "hasChild",
        "hasName",
    }.difference(kw2.keywordnames())
    assert not {
        "Person",
        "Parent",
        "Child",
        "Skill",
        "Resource",
    }.difference(kw2.classnames())
    d = kw2["hasAge"]
    assert d.iri == "fam:hasAge"
    assert d.range == "rdfs:Literal"
    assert d.datatype == "xsd:double"
    assert d.unit == "year"
    assert kw2["hasName"] == {  # vcard:hasName is overwritten
        "iri": "fam:hasName",
        "type": "owl:AnnotationProperty",
        "domain": ["dcat:Resource", "rdfs:Resource"],
        "range": "rdfs:Literal",
        "comment": "Name.",
        "name": "hasName",
    }


def test_get_prefixes():
    """Test get_prefixes() method."""
    prefixes = keywords.get_prefixes()
    assert prefixes["dcat"] == "http://www.w3.org/ns/dcat#"


def test_add_prefix():
    """Test add_prefix()."""
    prefixes = keywords.get_prefixes()
    assert "xxx" not in prefixes
    keywords.add_prefix("xxx", "https://w3id.org/ns/xxx")
    assert "xxx" in prefixes
    assert prefixes["xxx"] == "https://w3id.org/ns/xxx"
    keywords.add_prefix("xxx", "https://w3id.org/ns/xxx2")
    assert prefixes["xxx"] == "https://w3id.org/ns/xxx"
    keywords.add_prefix("xxx", "https://w3id.org/ns/xxx2", replace=True)
    assert prefixes["xxx"] == "https://w3id.org/ns/xxx2"
    keywords.add_prefix("xxx", None)
    assert "xxx" not in prefixes


def test_get_context():
    """Test get_context() method."""
    ctx = keywords.get_context()
    assert ctx["dcat"] == "http://www.w3.org/ns/dcat#"
    assert ctx["creator"] == {"@id": "dcterms:creator", "@type": "@id"}
    assert ctx["title"] == {"@id": "dcterms:title", "@language": "en"}
    assert ctx["version"] == "dcat:version"


def test_save_context():
    """Test save JSON-LD context and documentation."""
    import json

    from dataset_paths import outdir, rootdir  # pylint: disable=import-error

    # from tripper.datadoc import get_keywords

    pytest.importorskip("rdflib")

    kw = Keywords()
    kw.save_context(outdir / "context.json")
    with open(
        rootdir / "tripper" / "context" / "0.3" / "context.json",
        mode="rt",
        encoding="utf-8",
    ) as f:
        d1 = json.load(f)
    with open(outdir / "context.json", "rt", encoding="utf-8") as f:
        d2 = json.load(f)
    assert d2 == d1, (
        "Tips: if this fails, try to run .hooks/generate-context-and-doc.sh "
        "before spending time on debugging"
    )

    keywords.save_markdown(outdir / "keywords.md")
    keywords.save_markdown_prefixes(outdir / "prefixes.md")


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
    import warnings

    from tripper import DCTERMS
    from tripper.datadoc.errors import InvalidKeywordError

    # Ignore deprecation warnings from testing deprecated function
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        assert keywords.keywordname("title") == "title"
        assert keywords.keywordname("dcterms:title") == "title"
        assert keywords.keywordname(DCTERMS.title) == "title"
        with pytest.raises(InvalidKeywordError):
            keywords.keywordname("xxx")


def test_shortname():
    """Test shortname() method."""
    from tripper import DCAT, DCTERMS
    from tripper.datadoc.errors import InvalidKeywordError

    assert keywords.shortname("title") == "title"
    assert keywords.shortname("dcterms:title") == "title"
    assert keywords.shortname(DCTERMS.title) == "title"
    with pytest.raises(InvalidKeywordError):
        keywords.shortname("xxx")

    assert keywords.shortname("Dataset") == "Dataset"
    assert keywords.shortname("dcat:Dataset") == "Dataset"
    assert keywords.shortname(DCAT.Dataset) == "Dataset"


def test_prefixed():
    """Test prefixed() method."""
    from tripper import DCAT, DCTERMS
    from tripper.datadoc.errors import InvalidKeywordError

    assert keywords.prefixed("title") == "dcterms:title"
    assert keywords.prefixed("dcterms:title") == "dcterms:title"
    assert keywords.prefixed(DCTERMS.title) == "dcterms:title"
    with pytest.raises(InvalidKeywordError):
        keywords.shortname("xxx")

    assert keywords.prefixed("Dataset") == "dcat:Dataset"
    assert keywords.prefixed("dcat:Dataset") == "dcat:Dataset"
    assert keywords.prefixed(DCAT.Dataset) == "dcat:Dataset"


def test_typename():
    """Test typename() method."""
    from tripper import DCAT
    from tripper.datadoc.errors import NoSuchTypeError

    assert keywords.typename("Dataset") == "Dataset"
    assert keywords.typename("dcat:Dataset") == "Dataset"
    assert keywords.typename(DCAT.Dataset) == "Dataset"
    with pytest.raises(NoSuchTypeError):
        keywords.typename("xxx")

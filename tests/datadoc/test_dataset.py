"""Test the dataset module."""

# pylint: disable=invalid-name,too-many-locals,duplicate-code

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")


def test_get_jsonld_context():
    """Test get_jsonld_context()."""
    from tripper.datadoc import get_jsonld_context
    from tripper.datadoc.dataset import CONTEXT_URL

    context = get_jsonld_context()
    assert isinstance(context, dict)
    assert len(context) > 80
    assert context["@version"] == 1.1
    assert context["status"] == "adms:status"

    # Test online context. It should equal context on disk.
    # However, since they are updated asynchronously, we do not test for
    # equality.
    online_context = get_jsonld_context(fromfile=False)
    assert isinstance(online_context, dict)
    assert len(online_context) > 80
    assert online_context["@version"] == 1.1
    assert online_context["status"] == "adms:status"

    # Test context argument
    context2 = get_jsonld_context(context=CONTEXT_URL, fromfile=False)
    assert context2 == online_context

    assert "newkey" not in context
    context3 = get_jsonld_context(context={"newkey": "onto:newkey"})
    assert context3["newkey"] == "onto:newkey"

    with pytest.raises(TypeError):
        get_jsonld_context(context=[None])


def test_get_prefixes():
    """Test get_prefixes()."""
    from tripper.datadoc import get_prefixes

    prefixes = get_prefixes()
    assert prefixes["dcat"] == "http://www.w3.org/ns/dcat#"
    assert prefixes["emmo"] == "https://w3id.org/emmo#"

    # Test context argument
    prefixes2 = get_prefixes(context={"onto": "http://example.com/onto#"})
    assert prefixes2["onto"] == "http://example.com/onto#"


def test_get_shortnames():
    """Test get_shortnames()."""
    from tripper import DCTERMS
    from tripper.datadoc.dataset import get_shortnames

    # Short names that are not equal to the last component of the IRI
    exceptions = (
        "datamodel",
        "datamodelStorage",
        "prefixes",
        "configuration",
        "statements",
        "mappings",
        "@type",
    )

    shortnames = get_shortnames()
    assert shortnames[DCTERMS.title] == "title"

    for k, v in shortnames.items():
        if v not in exceptions and not k.startswith(
            (
                "https://w3id.org/emmo#EMMO_",
                "https://w3id.org/emmo/domain/"
                "characterisation-methodology/chameo#EMMO_",
            )
        ):
            assert k.rsplit("#", 1)[-1].rsplit("/", 1)[-1] == v


def test_add():
    """Test help-function add()."""
    from tripper.datadoc.dataset import add

    d = {}
    add(d, "a", "1")
    add(d, "b", "1")
    add(d, "b", "1")
    add(d, "a", "2")
    add(d, "a", "1")
    add(d, "a", {"c": "3"})
    assert d == {"a": ["1", "2", {"c": "3"}], "b": "1"}


def test_addnested():
    """Test help-function addnested()."""
    from tripper.datadoc.dataset import addnested
    from tripper.utils import AttrDict

    d = AttrDict()
    addnested(d, "a.b", "1")
    assert d == {"a": {"b": "1"}}

    addnested(d, "a", "2")
    assert d == {"a": ["2", {"b": "1"}]}

    addnested(d, "a.b.c", {"d": "3"})
    assert d.a[0] == "2"
    assert d.a[1].b[1].c == {"d": "3"}
    assert d == {"a": ["2", {"b": ["1", {"c": {"d": "3"}}]}]}


def test_get():
    """Test help-function get()."""
    from tripper.datadoc.dataset import get

    d = {"a": [1, 2], "b": 1}
    assert get(d, "a") == [1, 2]
    assert get(d, "b") == [1]
    assert get(d, "b", aslist=False) == 1
    assert get(d, "c") == []
    assert get(d, "c", default="x") == ["x"]
    assert get(d, "c", aslist=False) is None
    assert get(d, "c", default="x", aslist=False) == "x"


# if True:
def test_save_dict():
    """Test save_dict()."""
    from tripper import Triplestore
    from tripper.datadoc import as_jsonld, save_dict

    ts = Triplestore("rdflib")
    EX = ts.bind("ex", "http://example.com/ex#")
    d = {
        "@id": EX.exdata,
        "@type": EX.ExData,
        "creator": {"name": "John Doe"},
        "inSeries": EX.series,
        "distribution": {
            "downloadURL": "http://example.com/downloads/exdata.csv",
            "mediaType": "text/csv",
        },
    }
    ld = as_jsonld(d)
    ld2 = save_dict(ts, d)
    print(ts.serialize())
    assert ld2 == ld


def test_as_jsonld():
    """Test as_jsonld()."""
    from tripper import DCAT, EMMO, OWL, Namespace
    from tripper.datadoc import as_jsonld
    from tripper.datadoc.dataset import CONTEXT_URL

    with pytest.raises(ValueError):
        as_jsonld({})

    EX = Namespace("http://example.com/ex#")
    SER = Namespace("http://example.com/series#")
    dct = {"@id": "ex:indv", "a": "val"}
    context = {"ex": EX, "a": "ex:a"}

    d = as_jsonld(dct, _context=context)
    assert len(d["@context"]) == 2
    assert d["@context"][0] == CONTEXT_URL
    assert d["@context"][1] == context
    assert d["@id"] == EX.indv
    assert len(d["@type"]) == 2
    assert set(d["@type"]) == {DCAT.Dataset, EMMO.Dataset}
    assert d.a == "val"

    d2 = as_jsonld(dct, type="resource", _context=context)
    assert d2["@context"] == d["@context"]
    assert d2["@id"] == d["@id"]
    assert d2["@type"] == OWL.NamedIndividual
    assert d2.a == "val"

    d3 = as_jsonld(
        {"inSeries": "ser:main"},
        prefixes={"ser": SER},
        a="value",
        _id="ex:indv2",
        _type="ex:Item",
        _context=context,
    )
    assert d3["@context"] == d["@context"]
    assert d3["@id"] == EX.indv2
    assert set(d3["@type"]) == {DCAT.Dataset, EMMO.Dataset, EX.Item}
    assert d3.a == "value"
    assert d3.inSeries == SER.main


# if True:
def test_datadoc():
    """Test save_datadoc() and load_dict()/save_dict()."""
    # pylint: disable=too-many-statements

    from dataset_paths import indir  # pylint: disable=import-error

    from tripper import CHAMEO, DCAT, EMMO, OTEIO, Triplestore
    from tripper.datadoc import load_dict, save_datadoc, save_dict, search_iris

    pytest.importorskip("dlite")
    pytest.importorskip("rdflib")

    ts = Triplestore("rdflib")

    # Load data documentation into triplestore
    datadoc = save_datadoc(ts, indir / "semdata.yaml")
    assert isinstance(datadoc, dict)
    assert "@context" in datadoc

    # Test load dict-representation of a dataset from the triplestore
    SEM = ts.namespaces["sem"]
    SEMDATA = ts.namespaces["semdata"]
    iri = SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"]
    d = load_dict(ts, iri, use_sparql=False)
    assert d["@id"] == iri
    assert set(d["@type"]) == {
        DCAT.Dataset,
        EMMO.Dataset,
        SEM.SEMImage,
        "http://onto-ns.com/meta/matchmaker/0.2/SEMImage",
    }
    assert d.inSeries == SEMDATA["SEM_cement_batch2/77600-23-001"]
    assert d.distribution.mediaType == "image/tiff"

    assert not load_dict(ts, "non-existing")
    assert not load_dict(ts, "non-existing", use_sparql=True)

    # Test load using SPARQL - this should give the same result as above
    d2 = load_dict(ts, iri, use_sparql=True)
    assert d2 == d

    # Test loading a parser
    PARSER = ts.namespaces["parser"]
    parser = load_dict(ts, PARSER.sem_hitachi)
    assert parser["@id"] == PARSER.sem_hitachi
    assert parser["@type"] == OTEIO.Parser
    assert parser.configuration == {"driver": "hitachi"}
    assert parser.parserType == "application/vnd.dlite-parse"
    assert parser["@id"] == d.distribution.parser

    # Add generator to distribution (in KB)
    GEN = ts.namespaces["gen"]
    ts.add((d.distribution["@id"], OTEIO.generator, GEN.sem_hitachi))

    # Test saving a generator and add it to the distribution
    dist = load_dict(ts, d.distribution["@id"])
    assert dist.generator == GEN.sem_hitachi

    gen = load_dict(ts, dist.generator)
    assert gen["@id"] == GEN.sem_hitachi
    assert gen["@type"] == OTEIO.Generator
    assert gen.generatorType == "application/vnd.dlite-generate"

    # Test save dict
    save_dict(
        ts,
        dct={"@id": SEMDATA.newdistr, "format": "txt"},
        type="distribution",
        prefixes={"echem": "https://w3id.org/emmo/domain/electrochemistry"},
    )
    newdistr = load_dict(ts, SEMDATA.newdistr)
    assert newdistr["@type"] == DCAT.Distribution
    assert newdistr.format == "txt"

    # Test load updated distribution
    dd = load_dict(ts, iri)
    assert dd.distribution.generator == GEN.sem_hitachi
    del dd.distribution["generator"]
    assert dd == d

    # Test searching the triplestore
    SAMPLE = ts.namespaces["sample"]
    datasets = search_iris(ts, type="dataset")
    assert search_iris(ts, type="dcat:Dataset") == datasets
    named_datasets = {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }
    assert not named_datasets.difference(datasets)
    assert set(
        search_iris(ts, criterias={"dcterms:creator": "Sigurd Wenner"})
    ) == {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }
    assert set(search_iris(ts, type=CHAMEO.Sample)) == {
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }

    with pytest.raises(ValueError):
        search_iris(ts, type="invalid-type")

    # Find all individuals that has "SEM images"in the title
    assert set(search_iris(ts, regex={"dcterms:title": "SEM images"})) == {
        SEMDATA.SEM_cement_batch2,
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }
    assert set(search_iris(ts, regex={"dcterms:title": "SEM i[^ ]*s"})) == {
        SEMDATA.SEM_cement_batch2,
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }

    # Get individual with given IRI
    assert search_iris(ts, criterias={"@id": SEMDATA.SEM_cement_batch2}) == [
        SEMDATA.SEM_cement_batch2,
    ]


def test_custom_context():
    """Test saving YAML file with custom context to triplestore."""
    from dataset_paths import indir  # pylint: disable=import-error

    from tripper import Triplestore
    from tripper.datadoc import save_datadoc

    ts = Triplestore("rdflib")
    d = save_datadoc(ts, indir / "custom_context.yaml")

    KB = ts.namespaces["kb"]
    assert d.resources[0]["@id"] == KB.sampleA
    assert d.resources[0].fromBatch == KB.batch1

    assert d.resources[1]["@id"] == KB.sampleB
    assert d.resources[1].fromBatch == KB.batch1

    assert d.resources[2]["@id"] == KB.sampleC
    assert d.resources[2].fromBatch == KB.batch2

    assert d.resources[3]["@id"] == KB.batch1
    assert d.resources[3].batchNumber == 1

    assert d.resources[4]["@id"] == KB.batch2
    assert d.resources[4].batchNumber == 2


# if True:
def test_pipeline():
    """Test creating OTEAPI pipeline."""
    from tripper import Triplestore

    otelib = pytest.importorskip("otelib")
    from dataset_paths import indir  # pylint: disable=import-error

    from tripper.datadoc import get_partial_pipeline, save_datadoc

    # Prepare triplestore
    ts = Triplestore("rdflib")
    save_datadoc(ts, indir / "semdata.yaml")

    SEMDATA = ts.namespaces["semdata"]

    client = otelib.OTEClient("python")
    iri = SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"]
    parse = get_partial_pipeline(ts, client, iri, parser=True)

    # The generator was removed for clarity
    # GEN = ts.namespaces["gen"]
    # generate = get_partial_pipeline(
    #     ts, client, iri, generator=GEN.sem_hitachi
    # )
    # assert generate

    # Entity-service doesn't work, so we skip the generate part for now...
    # pipeline = parse >> generate
    pipeline = parse

    pipeline.get()


def test_fuseki():
    """Test save and load dataset with Fuseki."""
    import os

    from tripper import Triplestore

    host = os.getenv("TRIPLESTORE_HOST", "localhost")
    port = os.getenv("TRIPLESTORE_PORT", "3030")
    fuseki_args = {
        "backend": "fusekix",
        "base_iri": "http://example.com/ontology#",
        "triplestore_url": f"http://{host}:{port}",
        "database": "openmodel",
    }
    try:
        ts = Triplestore(**fuseki_args)
    except ModuleNotFoundError:
        pytest.skip("Cannot connect to Fuseki server")
    ts.remove_database(**fuseki_args)

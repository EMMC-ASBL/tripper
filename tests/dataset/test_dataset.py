"""Test the dataset module."""

# pylint: disable=invalid-name,too-many-locals,duplicate-code

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")


def test_get_jsonld_context():
    """Test get_jsonld_context()."""
    from tripper.dataset import get_jsonld_context

    context = get_jsonld_context()
    assert isinstance(context, dict)
    assert "@version" in context
    assert len(context) > 20

    # Check for consistency between context online and on disk
    online_context = get_jsonld_context(fromfile=False)
    assert online_context == context


def test_get_prefixes():
    """Test get_prefixes()."""
    from tripper.dataset import get_prefixes

    prefixes = get_prefixes()
    assert prefixes["dcat"] == "http://www.w3.org/ns/dcat#"
    assert prefixes["emmo"] == "https://w3id.org/emmo#"


def test_get_shortnames():
    """Test get_shortnames()."""
    from tripper import DCTERMS
    from tripper.dataset.dataset import get_shortnames

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
    from tripper.dataset.dataset import add

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
    from tripper.dataset.dataset import addnested
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
    from tripper.dataset.dataset import get

    d = {"a": [1, 2], "b": 1}
    assert get(d, "a") == [1, 2]
    assert get(d, "b") == [1]
    assert get(d, "b", aslist=False) == 1
    assert get(d, "c") == []
    assert get(d, "c", default="x") == ["x"]
    assert get(d, "c", aslist=False) is None
    assert get(d, "c", default="x", aslist=False) == "x"


def test_expand_iri():
    """Test help-function expand_iri()."""
    from tripper import CHAMEO, DCTERMS, OTEIO, RDF
    from tripper.dataset.dataset import expand_iri, get_prefixes

    prefixes = get_prefixes()
    assert expand_iri("chameo:Sample", prefixes) == CHAMEO.Sample
    assert expand_iri("dcterms:title", prefixes) == DCTERMS.title
    assert expand_iri("oteio:Parser", prefixes) == OTEIO.Parser
    assert expand_iri("rdf:type", prefixes) == RDF.type
    assert expand_iri("xxx", prefixes) == "xxx"
    with pytest.warns(UserWarning):
        assert expand_iri("xxx:type", prefixes) == "xxx:type"


# if True:
def test_datadoc():
    """Test save_datadoc() and load_dict()/save_dict()."""
    # pylint: disable=too-many-statements

    from dataset_paths import indir  # pylint: disable=import-error

    from tripper import CHAMEO, DCAT, EMMO, OTEIO, Triplestore
    from tripper.dataset import load_dict, save_datadoc, save_dict, search_iris

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
    assert set(d["@type"]) == {DCAT.Dataset, EMMO.DataSet, SEM.SEMImage}
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
    assert parser == d.distribution.parser

    # Add generator to distribution (in KB)
    GEN = ts.namespaces["gen"]
    ts.add((d.distribution["@id"], OTEIO.generator, GEN.sem_hitachi))

    # Test saving a generator and add it to the distribution
    dist = load_dict(ts, d.distribution["@id"])
    assert dist.generator["@id"] == GEN.sem_hitachi
    assert dist.generator["@type"] == OTEIO.Generator
    assert dist.generator.generatorType == "application/vnd.dlite-generate"

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
    assert dd.distribution.generator == load_dict(ts, GEN.sem_hitachi)
    del dd.distribution["generator"]
    assert dd == d

    # Test searching the triplestore
    SAMPLE = ts.namespaces["sample"]
    datasets = search_iris(ts)
    named_datasets = {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }
    assert not named_datasets.difference(datasets)
    assert set(search_iris(ts, creator="Sigurd Wenner")) == {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }
    assert set(search_iris(ts, type=CHAMEO.Sample)) == {
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }


# if True:
def test_pipeline():
    """Test creating OTEAPI pipeline."""
    from tripper import Triplestore

    otelib = pytest.importorskip("otelib")
    from dataset_paths import indir  # pylint: disable=import-error

    from tripper.dataset import get_partial_pipeline, save_datadoc

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

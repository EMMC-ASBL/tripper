"""Test the dataset module."""

# pylint: disable=invalid-name,too-many-locals,duplicate-code

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")
pytest.importorskip("pyld")


def test__get_range():
    """Test _get_default_keywords()."""
    from tripper.datadoc.dataset import _get_range

    assert _get_range("mediaType") == "dcterms:MediaType"
    assert _get_range("dcat:mediaType") == "dcterms:MediaType"
    assert _get_range("dcat:distribution") == "dcat:Distribution"


def test_told():
    """Test told()."""
    # pylint: disable=too-many-statements
    from pathlib import Path

    from tripper import DCAT, DCTERMS, OWL, RDF, Literal, Triplestore
    from tripper.datadoc.dataset import store, told

    indir = Path(__file__).resolve().parent.parent / "input"
    prefixes = {"ex": "http://example.com/ex#"}
    ts = Triplestore("rdflib")

    # Single-resource representations
    descrA = {
        "@id": "ex:a",
        "@type": "ex:A",
        "title": "Dataset a",
        "distribution": {
            "mediaType": "iana:text/csv",
            "downloadURL": "http://json.org/ex.txt",
        },
        "mappingURL": str(indir / "mappings.ttl"),
        "mappings": [("@id", "rdf:type", "ex:TechnicalDataset")],
    }
    d1 = told(descrA)
    assert d1["@id"] == "ex:a"
    assert d1["@type"] == "ex:A"
    assert d1["distribution"]["@type"] == [
        "dcat:Distribution",
        "dcat:Resource",
    ]
    assert set(d1["mappings"]) == {
        (
            "http://data.com/domain#doc",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://xmlns.com/foaf/0.1/Document",
        ),
        (  # unexpanded
            "ex:a",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            "ex:TechnicalDataset",
        ),
    }

    # Test store() on descrA
    store(ts, descrA, prefixes=prefixes)
    EX = ts.namespaces["ex"]  # store() adds the namespace to `ts`
    assert ts.has(EX.a, RDF.type, EX.A)
    # assert ts.has(EX.a, RDF.type, EX.TechnicalDataset)

    d2 = told(descrA, prefixes=prefixes)
    assert d2["@id"] == "ex:a"
    assert d2["@type"] == "ex:A"
    assert d2["distribution"]["@type"] == [
        "dcat:Distribution",
        "dcat:Resource",
    ]
    assert set(d2["mappings"]) == {
        (
            "http://data.com/domain#doc",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://xmlns.com/foaf/0.1/Document",
        ),
        (  # expanded
            "http://example.com/ex#a",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            "http://example.com/ex#TechnicalDataset",
        ),
    }

    d3 = told(descrA, type="ex:AA")
    assert d3["@id"] == "ex:a"
    assert d3["@type"] == ["ex:A", "ex:AA"]
    assert d3["distribution"]["@type"] == [
        "dcat:Distribution",
        "dcat:Resource",
    ]

    descrB = {
        "@graph": [
            {
                "@id": "ex:a",
                "@type": "ex:A",
                "title": "Dataset a",
                "distribution": {
                    "mediaType": "iana:text/csv",
                    "downloadURL": "http://json.org/ex.txt",
                },
            },
            {
                "@id": "ex:b",
                "title": "Dataset b",
            },
        ],
    }
    d4 = told(descrB)
    assert d4["@graph"][0]["@id"] == "ex:a"
    assert d4["@graph"][1]["@id"] == "ex:b"
    assert len(d4["@graph"]) == 2
    assert d4["@graph"][0]["distribution"]["@type"] == [
        "dcat:Distribution",
        "dcat:Resource",
    ]
    assert d4["@graph"][1]["@type"] == "owl:NamedIndividual"

    # Test store() on descrB
    ts.remove()
    store(ts, descrB, prefixes=prefixes)
    EX = ts.namespaces["ex"]  # store() adds the namespace to `ts`
    assert ts.has(EX.a, DCAT.distribution)
    assert ts.has(EX.a, DCTERMS.title, Literal("Dataset a"))

    descrC = [
        {
            "@id": "ex:a",
            "@type": "ex:A",
            "title": "Dataset a",
            "distribution": {
                "mediaType": "iana:text/csv",
                "downloadURL": "http://json.org/ex.txt",
            },
        },
        {
            "@id": "ex:b",
            "title": "Dataset b",
        },
    ]
    d5 = told(descrC)
    assert d5 == d4

    # Test store() on descrC
    ts.remove()
    store(ts, descrB, prefixes=prefixes)
    EX = ts.namespaces["ex"]  # store() adds the namespace to `ts`
    assert ts.has(EX.a, DCAT.distribution)
    assert ts.has(EX.a, DCTERMS.title, Literal("Dataset a"))

    # Multi-resource representation
    descrD = {
        "prefixes": prefixes,
        "base": "http://base.com#",
        "Dataset": [
            {
                "@id": "a",
                "@type": "ex:A",
                "title": "Dataset a",
                "distribution": {
                    "mediaType": "iana:text/csv",
                    "downloadURL": "http://json.org/ex.txt",
                },
            },
            {
                "@id": "b",
                "title": "Dataset b",
            },
        ],
    }
    d6 = told(descrD)
    assert len(d6["@graph"]) == 2
    assert d6["@graph"][0]["distribution"]["@type"] == [
        "dcat:Distribution",
        "dcat:Resource",
    ]
    assert d6["@graph"][1]["@type"] == [
        "dcat:Dataset",
        "dcat:Resource",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
    ]

    # Test store() on descrC
    ts.remove()
    store(ts, descrB, prefixes=prefixes)
    EX = ts.namespaces["ex"]  # store() adds the namespace to `ts`
    assert ts.has(EX.a, DCAT.distribution)
    assert ts.has(EX.a, DCTERMS.title, Literal("Dataset a"))
    assert ts.has(EX.a, RDF.type, EX.A)
    assert ts.has(EX.b, RDF.type, OWL.NamedIndividual)


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

    shortnames = get_shortnames()
    assert shortnames[DCTERMS.title] == "title"
    assert shortnames[DCTERMS.issued] == "releaseDate"


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


def test_store():
    """Test store()."""
    from tripper import Triplestore
    from tripper.datadoc import acquire, store
    from tripper.datadoc.errors import IRIExistsError, IRIExistsWarning

    ts = Triplestore("rdflib")
    EX = ts.bind("ex", "http://example.com/ex#")
    d = {
        "@id": EX.exdata,
        "@type": EX.ExData,
        "creator": {"name": "John Doe"},
        "inSeries": EX.series,
        "distribution": {
            "downloadURL": "http://example.com/downloads/exdata.csv",
            "mediaType": (
                "http://www.iana.org/assignments/media-types/text/csv"
            ),
        },
    }
    store(ts, d, type="Dataset")
    print(ts.serialize())

    with pytest.raises(IRIExistsError):
        store(ts, d, type="Dataset")

    d1 = acquire(ts, EX.exdata)
    assert isinstance(d1.distribution, dict)

    store(ts, d, type="Dataset", method="overwrite")
    d2 = acquire(ts, EX.exdata)
    assert isinstance(d2.distribution, dict)
    assert d2.distribution.downloadURL == d1.distribution.downloadURL

    with pytest.warns(IRIExistsWarning):
        store(ts, d, type="Dataset", method="ignore")
    d3 = acquire(ts, EX.exdata)
    assert isinstance(d3.distribution, dict)
    assert d3.distribution.downloadURL == d1.distribution.downloadURL

    store(ts, d, type="Dataset", method="merge")
    d4 = acquire(ts, EX.exdata)
    assert isinstance(d4.distribution, list)

    with pytest.raises(ValueError):
        store(ts, d, type="Dataset", method="invalid_method_name")


def test_update_classes():
    """Test update_classes()."""
    from copy import deepcopy

    from tripper import DCAT
    from tripper.datadoc.dataset import update_classes

    d1 = {"title": "About tripper"}
    r1 = d1.copy()
    update_classes(r1)
    assert r1 == d1

    d2 = {
        "@context": {"ex": "http://example.com/ex#"},
        "@id": "ex:myclass",
        "@type": "owl:Class",
        "subClassOf": "dcat:Dataset",
        "title": "About tripper",
        "distribution": {
            "@type": ["owl:Class", "dcat:Distribution"],
            "accessService": "ex:service",
        },
    }
    r2 = deepcopy(d2)
    update_classes(r2)
    assert "dcat:Dataset" in r2["subClassOf"]
    assert {
        "rdf:type": "owl:Restriction",
        "owl:onProperty": DCAT.distribution,
        "owl:someValuesFrom": {
            "@type": "owl:Class",
            "accessService": "ex:service",
            "subClassOf": DCAT.Distribution,
        },
    } in r2["subClassOf"]

    r3 = deepcopy(d2)
    update_classes(r3, restrictions=("accessService",))
    assert "dcat:Dataset" in r3["subClassOf"]
    assert {
        "rdf:type": "owl:Restriction",
        "owl:onProperty": DCAT.distribution,
        "owl:someValuesFrom": {
            "@type": "owl:Class",
            "subClassOf": [
                DCAT.Distribution,
                {
                    "rdf:type": "owl:Restriction",
                    "owl:onProperty": DCAT.accessService,
                    "owl:hasValue": "ex:service",
                },
            ],
        },
    } in r3["subClassOf"]


def test_datadoc():
    """Test save_datadoc() and acquire()/store()."""
    # pylint: disable=too-many-statements

    from dataset_paths import indir  # pylint: disable=import-error

    from tripper import CHAMEO, DCAT, DCTERMS, EMMO, OTEIO, Triplestore
    from tripper.datadoc import acquire, save_datadoc, search, store
    from tripper.datadoc.errors import NoSuchTypeError

    pytest.importorskip("dlite")
    pytest.importorskip("rdflib")

    ts = Triplestore("rdflib")

    # Load data documentation into triplestore
    datadoc = save_datadoc(ts, indir / "semdata.yaml")
    assert isinstance(datadoc, dict)
    # assert "@context" in datadoc

    # Test load dict-representation of a dataset from the triplestore
    SEM = ts.namespaces["sem"]
    SEMDATA = ts.namespaces["semdata"]
    iri = SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"]
    d = acquire(ts, iri, use_sparql=False)
    assert d["@id"] == iri
    assert set(d["@type"]) == {
        DCAT.Dataset,
        DCAT.Resource,
        EMMO.Dataset,
        SEM.SEMImage,
        "http://onto-ns.com/meta/matchmaker/0.2/SEMImage",
    }
    assert d.inSeries == SEMDATA["SEM_cement_batch2/77600-23-001"]
    assert d.distribution.mediaType == (
        "http://www.iana.org/assignments/media-types/image/tiff"
    )

    assert not acquire(ts, "non-existing")
    assert not acquire(ts, "non-existing", use_sparql=True)

    # Test load using SPARQL - this should give the same result as above
    d2 = acquire(ts, iri, use_sparql=True)
    assert d2 == d

    # Test loading a parser
    PAR = ts.namespaces["par"]
    parser = acquire(ts, PAR.sem_hitachi)
    assert parser["@id"] == PAR.sem_hitachi
    assert parser["@type"] == OTEIO.Parser
    assert parser.configuration == {"driver": "hitachi"}
    assert parser.parserType == "application/vnd.dlite-parse"
    assert parser["@id"] == d.distribution.parser

    # Add generator to distribution (in KB)
    GEN = ts.namespaces["gen"]
    ts.add((d.distribution["@id"], OTEIO.generator, GEN.sem_hitachi))

    # Test saving a generator and add it to the distribution
    dist = acquire(ts, d.distribution["@id"])
    assert dist.generator == GEN.sem_hitachi

    gen = acquire(ts, dist.generator)
    assert gen["@id"] == GEN.sem_hitachi
    assert gen["@type"] == [OTEIO.Generator, OTEIO.Parser]
    assert gen.generatorType == "application/vnd.dlite-generate"

    # Test save dict
    store(
        ts,
        source={
            "@id": SEMDATA.newdistr,
            "mediaType": (
                "http://www.iana.org/assignments/media-types/text/plain"
            ),
        },
        type="Distribution",
        prefixes={"echem": "https://w3id.org/emmo/domain/electrochemistry"},
    )
    newdistr = acquire(ts, SEMDATA.newdistr)
    assert newdistr["@type"] == [DCAT.Distribution, DCAT.Resource]
    assert (
        newdistr.mediaType
        == "http://www.iana.org/assignments/media-types/text/plain"
    )

    # Test load updated distribution
    dd = acquire(ts, iri)
    assert dd.distribution.generator == GEN.sem_hitachi
    del dd.distribution["generator"]
    assert dd == d

    # Test searching the triplestore
    SAMPLE = ts.namespaces["sample"]
    datasets = search(ts, type="Dataset")
    assert search(ts, type="dcat:Dataset") == datasets
    named_datasets = {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }
    assert not named_datasets.difference(datasets)

    assert set(search(ts, criteria={"creator.name": "Sigurd Wenner"})) == {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }
    assert set(search(ts, type=CHAMEO.Sample)) == {
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }

    # Filter on more than one type in the search
    assert search(ts, type=["dcat:Dataset", SEM.SEMImage]) == [
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"]
    ]

    # Filter on one criterion, but add it as a list
    assert set(search(ts, criteria={"creator.name": ["Sigurd Wenner"]})) == {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
        SEMDATA["SEM_cement_batch2/77600-23-001"],
        SEMDATA["SEM_cement_batch2"],
    }

    # Filter on more than one value for a criterion
    assert set(
        search(
            ts,
            criteria={
                "creator.name": ["Sigurd Wenner", "Named Lab Assistant"]
            },
        )
    ) == {
        SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"],
    }

    with pytest.raises(NoSuchTypeError):
        search(ts, type="invalid-type")

    # Find all individuals that has "SEM images"in the title
    assert set(search(ts, regex={"dcterms:title": "SEM images"})) == {
        SEMDATA.SEM_cement_batch2,
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }
    assert set(search(ts, regex={"dcterms:title": "SEM i[^ ]*s"})) == {
        SEMDATA.SEM_cement_batch2,
        SAMPLE["SEM_cement_batch2/77600-23-001"],
    }

    # Get individual with given IRI
    assert search(ts, criteria={"@id": SEMDATA.SEM_cement_batch2}) == [
        SEMDATA.SEM_cement_batch2,
    ]

    title = "Nested series of SEM images of cement batch2"
    dset = [SEMDATA.SEM_cement_batch2]
    # Search with predefined keyword
    assert search(ts, criteria={"title": title}) == dset
    # Search with prefixed IRIs
    assert search(ts, criteria={"dcterms:title": title}) == dset
    assert search(ts, criteria={DCTERMS.title: title}) == dset
    # Search with full IRI
    assert (
        search(ts, criteria={"http://purl.org/dc/terms/title": title}) == dset
    )


def test_custom_context():
    """Test saving YAML file with custom context to triplestore."""
    from dataset_paths import indir  # pylint: disable=import-error

    from tripper import Triplestore
    from tripper.datadoc import save_datadoc

    ts = Triplestore("rdflib")
    d = save_datadoc(ts, indir / "custom_context.yaml")
    resources = d["@graph"]

    assert resources[0]["@id"] == "kb:sampleA"
    assert resources[0]["fromBatch"] == "kb:batch1"

    assert resources[1]["@id"] == "kb:sampleB"
    assert resources[1]["fromBatch"] == "kb:batch1"

    assert resources[2]["@id"] == "kb:sampleC"
    assert resources[2]["fromBatch"] == "kb:batch2"

    assert resources[3]["@id"] == "kb:batch1"
    assert resources[3]["batchNumber"] == 1

    assert resources[4]["@id"] == "kb:batch2"
    assert resources[4]["batchNumber"] == 2


def test_validate():
    """Test validate datadoc dict."""
    from tripper import Namespace
    from tripper.datadoc import validate
    from tripper.datadoc.errors import ValidateError

    EX = Namespace("http://example.com/ex#")

    d = {
        "@id": EX.data,
        "@type": EX.MyData,
        "creator": {"name": "John Doe"},
        "title": "Special data",
        "description": "My dataset with some special data ...",
        "theme": "ex:Data",
    }
    validate(d)

    d2 = d.copy()
    d2["unknownKeyword"] = EX.unknownKeyword
    with pytest.raises(ValidateError):
        validate(d2)

    d3 = d.copy()
    d3["distribution"] = "invalid-distribution-iri"
    with pytest.raises(ValidateError):
        validate(d3)


def test_pipeline():
    """Test creating OTEAPI pipeline."""
    pytest.skip()

    from tripper import Triplestore

    otelib = pytest.importorskip("otelib")
    from dataset_paths import indir  # pylint: disable=import-error

    from tripper.datadoc import get_partial_pipeline, save_datadoc

    # Prepare triplestore
    ts = Triplestore("rdflib")
    save_datadoc(ts, indir / "semdata.yaml")

    SEMDATA = ts.namespaces["semdata"]
    iri = SEMDATA["SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"]

    client = otelib.OTEClient("python")
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


def test_deprecated():
    """Test deprecated save_dict(), load_dict() and search_iris()."""
    from tripper import Triplestore
    from tripper.datadoc import load_dict, save_dict, search_iris

    ts = Triplestore("rdflib")
    EX = ts.bind("ex", "http://example.com/ex#")
    d = {
        "@id": EX.exdata,
        "@type": EX.ExData,
        "creator": {"name": "John Doe"},
        "inSeries": EX.series,
        "distribution": {
            "downloadURL": "http://example.com/downloads/exdata.csv",
            "mediaType": (
                "http://www.iana.org/assignments/media-types/text/csv"
            ),
        },
    }
    with pytest.warns(DeprecationWarning):
        save_dict(ts, d, type="Dataset")
    print(ts.serialize())

    with pytest.warns(DeprecationWarning):
        d2 = load_dict(ts, EX.exdata)
    assert d2["@id"] == d["@id"]
    assert d2.creator.name == d["creator"]["name"]
    assert d2.distribution.downloadURL == d["distribution"]["downloadURL"]

    with pytest.warns(DeprecationWarning):
        iris = search_iris(ts, criterias={"creator.name": "John Doe"})
    assert iris == [EX.exdata]

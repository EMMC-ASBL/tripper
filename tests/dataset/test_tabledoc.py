"""Test the dataset module."""

import pytest


# if True:
def test_as_dicts():
    """Test the as_dicts() method."""

    pytest.importorskip("rdflib")

    from tripper import DCAT, EMMO, Namespace, Triplestore
    from tripper.dataset import TableDoc

    ONTO = Namespace("http:/example.com/onto#")
    DS = Namespace("http:/example.com/datasets#")

    td = TableDoc(
        header=[
            "@id",
            "@type",
            "@type",
            "inSeries",
            "distribution.downloadURL",
        ],
        data=[
            ("ds:s1", "onto:T1", "onto:T2", None, "file:///data/"),
            ("ds:d1", "onto:T1", None, "ds:s1", "file:///data/d1.txt"),
            ("ds:d2", "onto:T2", None, "ds:s1", "file:///data/d2.txt"),
        ],
        prefixes={
            "onto": "http:/example.com/onto#",
            "ds": "http:/example.com/datasets#",
        },
        # context={
        #    "ds": "http:/example.com/datasets#",
        # },
    )

    s1, d1, d2 = td.asdicts()  # pylint: disable=unbalanced-tuple-unpacking

    assert s1["@id"] == DS.s1
    assert set(s1["@type"]) == {
        DCAT.Dataset,
        EMMO.DataSet,
        ONTO.T1,
        ONTO.T2,
    }
    assert "inSeries" not in s1
    assert s1.distribution == {
        "@type": DCAT.Distribution,
        "downloadURL": "file:///data/",
    }

    assert d1["@id"] == DS.d1
    assert set(d1["@type"]) == {
        DCAT.Dataset,
        EMMO.DataSet,
        ONTO.T1,
    }
    assert d1.inSeries == DS.s1
    assert d1.distribution == {
        "@type": DCAT.Distribution,
        "downloadURL": "file:///data/d1.txt",
    }

    assert d2["@id"] == DS.d2
    assert set(d2["@type"]) == {
        DCAT.Dataset,
        EMMO.DataSet,
        ONTO.T2,
    }
    assert d2.inSeries == DS.s1
    assert d2.distribution == {
        "@type": DCAT.Distribution,
        "downloadURL": "file:///data/d2.txt",
    }

    ts = Triplestore(backend="rdflib")
    td.save(ts)
    print(ts.serialize())


# if True:
def test_csv():
    """Test parsing a csv file."""
    from dataset_paths import indir, outdir  # pylint: disable=import-error

    pytest.importorskip("rdflib")

    from tripper import Triplestore
    from tripper.dataset import TableDoc

    # Read csv file
    td = TableDoc.parse_csv(
        indir / "semdata.csv",
        delimiter=";",
        prefixes={
            "sem": "https://w3id.com/emmo/domain/sem/0.1#",
            "semdata": "https://he-matchmaker.eu/data/sem/",
            "sample": "https://he-matchmaker.eu/sample/",
            "mat": "https://he-matchmaker.eu/material/",
            "dm": "http://onto-ns.com/meta/characterisation/0.1/SEMImage#",
            "parser": "http://sintef.no/dlite/parser#",
            "gen": "http://sintef.no/dlite/generator#",
        },
    )

    # pylint: disable=unused-variable,unbalanced-tuple-unpacking
    img, series, batch, sample = td.asdicts()

    assert img["@id"] == (
        "https://he-matchmaker.eu/data/sem/SEM_cement_batch2/"
        "77600-23-001/77600-23-001_5kV_400x_m001"
    )
    assert img.distribution.downloadURL == (
        "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/dataset/"
        "tests/input/77600-23-001_5kV_400x_m001.tif"
    )

    # Write the table to a new csv file
    td.write_csv(outdir / "semdata.csv")

    # Print serialised KB
    ts = Triplestore(backend="rdflib")
    td.save(ts)
    print(ts.serialize())

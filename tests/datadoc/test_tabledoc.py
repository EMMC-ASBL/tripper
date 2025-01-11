"""Test the TableDoc class."""

import pytest


# if True:
def test_asdicts():
    """Test the asdicts() method."""

    pytest.importorskip("rdflib")

    from tripper import DCAT, EMMO, Namespace, Triplestore
    from tripper.datadoc import TableDoc

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
        # Replace the "ds" prefix above with this, once the "context" keyword
        # argument is fully implemented.
        # context={
        #    "ds": "http:/example.com/datasets#",
        # },
    )

    s1, d1, d2 = td.asdicts()  # pylint: disable=unbalanced-tuple-unpacking

    assert s1["@id"] == DS.s1
    assert set(s1["@type"]) == {
        DCAT.Dataset,
        EMMO.Dataset,
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
        EMMO.Dataset,
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
        EMMO.Dataset,
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


def test_fromdicts():
    """Test the fromdicts() method."""

    pytest.importorskip("rdflib")

    from tripper import Namespace
    from tripper.datadoc import TableDoc

    EX = Namespace("http://example.com/ex#")
    dicts = [
        {"@id": EX.data1, "label": "data1"},
        {
            "@id": EX.data2,
            "distribution": {"downloadURL": "http://example.com/data2"},
        },
    ]
    td = TableDoc.fromdicts(dicts)

    assert td.header == ["@id", "label", "distribution.downloadURL"]
    assert td.data == [
        [EX.data1, "data1", None],
        [EX.data2, None, "http://example.com/data2"],
    ]


# if True:
def test_csv():
    """Test parsing a csv file."""
    import io

    from dataset_paths import indir, outdir  # pylint: disable=import-error

    pytest.importorskip("rdflib")

    from tripper import Triplestore
    from tripper.datadoc import TableDoc

    # Read csv file
    td = TableDoc.parse_csv(
        indir / "semdata.csv",
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
        "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/master/"
        "tests/input/77600-23-001_5kV_400x_m001.tif"
    )

    # Write the table to a new csv file
    td.write_csv(outdir / "semdata.csv")

    # Write table to string
    with io.StringIO() as f:
        td.write_csv(f)
        s = f.getvalue()

    # Re-read the csv file from the string
    with io.StringIO(s) as f:
        td2 = TableDoc.parse_csv(
            f,
            delimiter=",",
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
    assert td2.header == td.header
    assert td2.data == td.data

    # Print serialised KB
    ts = Triplestore(backend="rdflib")
    td.save(ts)
    ts.serialize(outdir / "semdata.ttl")
    print(ts.serialize())


def test_csv_duplicated_columns():
    """Test CSV with duplicated columns."""
    from dataset_paths import indir, outdir  # pylint: disable=import-error

    pytest.importorskip("rdflib")

    from tripper.datadoc import TableDoc

    prefixes = {"pm": "https://www.ntnu.edu/physmet/data#"}

    td = TableDoc.parse_csv(
        indir / "tem.csv",
        prefixes=prefixes,
    )

    # pylint: disable=unused-variable,unbalanced-tuple-unpacking
    img1, img2, img3 = td.asdicts()

    assert set(img1["@type"]) == {
        "http://www.w3.org/ns/dcat#Dataset",
        "https://w3id.org/emmo#EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
        "https://www.ntnu.edu/physmet/data#BrightFieldImage",
        "https://www.ntnu.edu/physmet/data#TEMImage",
    }

    td2 = TableDoc.fromdicts([img2, img3], prefixes=prefixes)
    assert td2.header == [
        "@id",
        "@type",
        "@type",
        "@type",
        "@type",
        "description",
        "distribution.downloadURL",
    ]
    td2.write_csv(outdir / "tem.csv", prefixes=prefixes)

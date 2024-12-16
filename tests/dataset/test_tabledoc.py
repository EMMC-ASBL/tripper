"""Test the dataset module."""

import pytest

from tripper import Triplestore
from tripper.dataset import TableDoc


# if True:
def test_as_dicts():
    """Test the as_dicts() method."""

    from tripper import DCAT, EMMO, Namespace

    pytest.importorskip("rdflib")

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

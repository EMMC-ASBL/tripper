"""Test the TableDoc class."""

import pytest

pytest.importorskip("pyld")


def test_asdicts():
    """Test the asdicts() method."""

    pytest.importorskip("rdflib")

    from tripper import IANA, Triplestore
    from tripper.datadoc import TableDoc

    td = TableDoc(
        header=[
            "@id",
            "@type",
            "@type",
            "inSeries",
            "distribution[1].downloadURL",
            "distribution[1].mediaType",
            "distribution[2].downloadURL",
        ],
        data=[
            (
                "ds:s1",
                "onto:T1",
                "onto:T2",
                None,
                "file:///d0.txt",
                IANA["text/plain"],
                "file:///data/",
            ),
            ("ds:d1", "onto:T1", None, "ds:s1", "file:///d1.txt", None, None),
            ("ds:d2", "onto:T2", None, "ds:s1", "file:///d2.txt", None, None),
        ],
        prefixes={
            "onto": "http://example.com/onto#",
            "ds": "http://example.com/datasets#",
        },
        # Replace the "ds" prefix above with this, once the "context" keyword
        # argument is fully implemented.
        # context={
        #    "ds": "http:/example.com/datasets#",
        # },
    )

    s1, d1, d2 = td.asdicts()  # pylint: disable=unbalanced-tuple-unpacking

    assert s1["@id"] == "ds:s1"
    assert set(s1["@type"]) == {
        "onto:T1",
        "onto:T2",
    }
    assert "inSeries" not in s1
    assert s1["distribution"] == [
        {
            "@type": ["dcat:Distribution", "dcat:Resource"],
            "downloadURL": "file:///d0.txt",
            "mediaType": IANA["text/plain"],
        },
        {
            "@type": ["dcat:Distribution", "dcat:Resource"],
            "downloadURL": "file:///data/",
        },
    ]

    assert d1["@id"] == "ds:d1"
    assert d1["@type"] == "onto:T1"
    assert d1["inSeries"] == "ds:s1"
    assert d1["distribution"] == {
        "@type": ["dcat:Distribution", "dcat:Resource"],
        "downloadURL": "file:///d1.txt",
    }

    assert d2["@id"] == "ds:d2"
    assert d2["@type"] == "onto:T2"
    assert d2["inSeries"] == "ds:s1"
    assert d2["distribution"] == {
        "@type": ["dcat:Distribution", "dcat:Resource"],
        "downloadURL": "file:///d2.txt",
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
            "par": "http://sintef.no/dlite/parser#",
            "gen": "http://sintef.no/dlite/generator#",
        },
    )

    # pylint: disable=unused-variable,unbalanced-tuple-unpacking
    img, series, batch, sample = td.asdicts()

    assert img["@id"] == (
        "semdata:SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"
    )
    assert img["distribution"]["downloadURL"] == (
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
                "par": "http://sintef.no/dlite/parser#",
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

    # Test that prefixes are included in the serialisation
    content = (outdir / "semdata.ttl").read_text()
    assert "sem:SEMImageSeries" in content


def test_csv_duplicated_columns():
    """Test CSV with duplicated columns."""
    pytest.importorskip("rdflib")

    from dataset_paths import indir, outdir  # pylint: disable=import-error

    from tripper import Namespace
    from tripper.datadoc import TableDoc

    PM = Namespace("https://www.ntnu.edu/physmet/data#")
    prefixes = {"pm": str(PM)}

    td = TableDoc.parse_csv(
        indir / "tem.csv",
        prefixes=prefixes,
    )

    # pylint: disable=unused-variable,unbalanced-tuple-unpacking
    img1, img2, img3 = td.asdicts()

    assert set(img1["@type"]) == {
        "pm:BrightFieldImage",
        "pm:TEMImage",
    }

    td2 = TableDoc.fromdicts([img2, img3], prefixes=prefixes)
    assert td2.header == [
        "@id",
        "@type",  # TEMImage
        "@type",  # BrightFieldEmage
        "description",
        "distribution.downloadURL",
    ]
    td2.write_csv(outdir / "tem.csv", prefixes=prefixes)


def test_parse_excel():
    """Test parse_excel() method."""
    pytest.importorskip("openpyxl")

    from dataset_paths import indir  # pylint: disable=import-error

    from tripper import Namespace
    from tripper.datadoc import TableDoc

    PM = Namespace("https://www.ntnu.edu/physmet/data#")
    td = TableDoc.parse_excel(
        excelfile=indir / "tem.xlsx",
        sheet="tem",
        prefixes={"pm": PM},
    )
    d1, d2, d3 = td.asdicts()
    assert d1["@id"] == "pm:TEM_BF_lowmag"
    assert set(d1["@type"]) == {"pm:BrightFieldImage", "pm:TEMImage"}
    assert d1["description"].startswith("Low-magnification TEM ")
    assert d1["distribution"] == {
        "@type": ["dcat:Distribution", "dcat:Resource"],
        # pylint: disable=line-too-long
        "downloadURL": "https://folk.ntnu.no/friisj/temdata/BF_100-at-m5-and-2_001.dm3",
        "format": "dm3",
    }
    assert d2["@id"] == "pm:TEM_BF"
    assert d3["@id"] == "pm:TEM_HAADF"


def test_unique_header():
    """Test unique_header() method."""
    from tripper.datadoc import TableDoc

    header = [
        "@id",
        "@type",
        "@type",
        "inSeries",
        "distribution.downloadURL",
        "distribution.downloadURL",
    ]
    unique_header = [
        "@id",
        "@type[1]",
        "@type[2]",
        "inSeries",
        "distribution[1].downloadURL",
        "distribution[2].downloadURL",
    ]
    td = TableDoc(header=header, data=[])
    assert td.unique_header() == unique_header

    td.header = unique_header
    assert td.unique_header() == unique_header


def test_csvsniff():
    """Test csvsniff()."""
    pytest.importorskip("yaml")
    from tripper.datadoc.tabledoc import csvsniff

    lines = [
        "A,B,C,D",
        "a,'b,bb','c1;c2;c3;c4',d",
    ]
    dialect = csvsniff("\r\n".join(lines))
    assert dialect.delimiter == ","
    assert dialect.lineterminator == "\r\n"
    assert dialect.quotechar == "'"

    dialect = csvsniff("\n".join(lines))
    assert dialect.delimiter == ","
    assert dialect.lineterminator == "\n"
    assert dialect.quotechar == "'"


def test_csv_keywords():
    """Test load CSV with custom keywords file."""
    from dataset_paths import indir  # pylint: disable=import-error

    pytest.importorskip("rdflib")

    from tripper.datadoc import TableDoc

    td = TableDoc.parse_csv(
        indir / "batchdata.csv",
        type="dcat:Dataset",
        keywords=indir / "custom_keywords.yaml",
    )
    batch1 = td.asdicts()[0]
    assert batch1["@type"] == [
        "dcat:Dataset",
        "dcat:Resource",
        "emmo:EMMO_194e367c_9783_4bf5_96d0_9ad597d48d9a",
        "myonto:Batch",
    ]
    assert batch1["batchNumber"] == 1


def test_column():
    """Test Column class."""
    from tripper import XSD
    from tripper.datadoc import get_context
    from tripper.datadoc.tabledoc import Column

    col1 = Column("title")
    assert col1.head == "title"
    assert col1.label == ""
    assert not col1.options

    col2 = Column(" title ")
    assert col2.head == "title"

    col3 = Column(" title ", strip=False)
    assert col3.head == " title "

    col4 = Column("distribution[0].accessURL[?sep=,]")
    assert col4.head == "distribution[0].accessURL[?sep=,]"
    assert col4.label == "0"
    assert col4.options == {"sep": ","}

    col5 = Column("profile[?sep=,&unit=m]")
    assert col5.names[0] == "profile"
    assert col5.label == ""
    assert col5.options == {"sep": ",", "unit": "m"}
    assert col5.datatype is None

    col6 = Column("creationDate", context=get_context())
    assert col6.head == "creationDate"
    assert col6.datatype == XSD.dateTime


def test_sep():
    """Test the column separation."""

    from tripper.datadoc import TableDoc

    td = TableDoc(
        header=["@id", "@type[?sep=,]", "title"],
        data=[("kb:s1", "kb:T1,kb:T2", "A title, with a comma")],
        prefixes={"kb": "http://example.com/kb#"},
    )
    (s1,) = td.asdicts()  # pylint: disable=unbalanced-tuple-unpacking
    assert s1["@id"] == "kb:s1"
    assert s1["@type"] == ["kb:T1", "kb:T2"]
    assert s1["title"] == "A title, with a comma"

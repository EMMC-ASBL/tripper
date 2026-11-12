"""Test the dataaccess module."""

import tempfile
from pathlib import Path

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")
pytest.importorskip("pyld")

EX = "http://example.com/"


def test_save():
    """Test save() with local files."""
    pytest.importorskip("dlite")
    pytest.importorskip("rdflib")

    from tripper import DCAT, Triplestore
    from tripper.datadoc import acquire, save, store

    ts = Triplestore("rdflib")

    with tempfile.TemporaryDirectory() as tmpdir:
        file1 = Path(tmpdir) / "data1.txt"
        file2 = Path(tmpdir) / "data2.txt"

        # Save data to a new dataset, documented with a dict, and a new
        # distribution.  The data is written to the downloadURL of the
        # distribution and the dataset is documented in the triplestore.
        # The query part of the URL is passed as options to DLite.
        # "mode=w" allows overwriting the file later.
        url1 = f"file:{file1}?mode=w"
        iri = save(
            ts,
            b"first data",
            dataset={"@id": EX + "dataset1", "title": "My first dataset"},
            distribution={"downloadURL": url1},
        )
        assert iri == EX + "dataset1"
        assert file1.read_bytes() == b"first data"
        dataset = acquire(ts, iri)
        assert DCAT.Dataset in dataset["@type"]
        assert dataset.distribution.downloadURL == url1

        # Without `dataset`, a new anonymous dataset is created for the
        # given distribution, which is already documented
        store(
            ts,
            {"@id": EX + "distribution2", "downloadURL": f"file:{file2}"},
            type="Distribution",
        )
        iri = save(ts, b"second data", distribution=EX + "distribution2")
        assert iri.startswith("_:")
        assert file2.read_bytes() == b"second data"

        # Saving to an existing dataset uses its distribution
        save(ts, b"updated data", dataset=EX + "dataset1")
        assert file1.read_bytes() == b"updated data"

    # `dataset` and `distribution` must be either a string or dict
    with pytest.raises(TypeError):
        save(ts, b"data", dataset=1)
    with pytest.raises(TypeError):
        save(ts, b"data", dataset=EX + "dataset3", distribution=1)

    # A distribution that is not documented has no URL to save to
    with pytest.raises(ValueError, match="neither a downloadURL nor"):
        save(ts, b"data", dataset=EX + "dataset3", distribution=EX + "nodistr")

    # Asking for a generator that the distribution doesn't have
    with pytest.raises(ValueError, match="has no such generator"):
        save(
            ts,
            b"data",
            dataset=EX + "dataset4",
            distribution={
                "downloadURL": "file:data4.txt",
                "generator": {"@id": EX + "generator1"},
            },
            generator=EX + "generator2",
        )


def test_load():
    """Test load() with local files."""
    pytest.importorskip("dlite")
    pytest.importorskip("rdflib")

    from tripper import Triplestore
    from tripper.datadoc import load, store

    ts = Triplestore("rdflib")

    with tempfile.TemporaryDirectory() as tmpdir:
        datafile = Path(tmpdir) / "data.txt"
        datafile.write_bytes(b"some data")

        store(
            ts,
            {
                "@id": EX + "mydata",
                "@type": "dcat:Dataset",
                "distribution": {"downloadURL": f"file:{datafile}"},
            },
        )
        store(
            ts,
            {
                "@id": EX + "missing",
                "@type": "dcat:Dataset",
                "distribution": {
                    "downloadURL": f"file:{Path(tmpdir) / 'missing.txt'}"
                },
            },
        )

        # Load the data from the downloadURL of the distribution
        assert load(ts, EX + "mydata") == b"some data"

        # Loading from a file that doesn't exist fails
        with pytest.raises(OSError, match="Cannot access dataset"):
            load(ts, EX + "missing")

    # The IRI must refer to a dataset
    store(ts, {"@id": EX + "notadataset", "title": "Not a dataset"})
    with pytest.raises(TypeError, match="expected IRI .* to be a dataset"):
        load(ts, EX + "notadataset")


@pytest.mark.network
def test_save_and_load():
    """Test save() and load()."""

    from dataset_paths import outdir

    from tripper import DCAT, DCTERMS, EMMO, IANA, Triplestore
    from tripper.datadoc import acquire, load, save, store

    pytest.importorskip("dlite")
    pytest.importorskip("rdflib")

    ts = Triplestore("rdflib")

    GEN = ts.bind("gen", "http://sintef.no/dlite/generator#")
    PARSER = ts.bind("parser", "http://sintef.no/dlite/parser#")
    SEM = ts.bind("sem", "https://w3id.com/emmo/domain/sem/0.1#")
    SEMDATA = ts.bind("semdata", "https://he-matchmaker.eu/data/sem/")

    iri = SEMDATA.img1

    # Test save dict
    store(
        ts,
        source={
            "@id": SEMDATA.img1,
            "distribution": {
                "downloadURL": (
                    "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/"
                    "master/tests/input/77600-23-001_5kV_400x_m001.tif"
                ),
                "mediaType": (
                    "https://www.iana.org/assignments/media-types/image/tiff"
                ),
            },
        },
        type="Dataset",
    )
    newdistr = acquire(ts, SEMDATA.img1)
    assert set(newdistr["@type"]) == {
        DCAT.Dataset,
        DCAT.Resource,
        EMMO.Dataset,
    }
    assert set(newdistr.distribution["@type"]) == {
        DCAT.Distribution,
        DCAT.Resource,
    }
    assert (
        newdistr.distribution.mediaType
        == "https://www.iana.org/assignments/media-types/image/tiff"
    )

    store(
        ts,
        source={
            "@id": GEN.sem_hitachi,
            "generatorType": "application/vnd.dlite-generate",
            "configuration": {"driver": "hitachi"},
        },
        type="Generator",
    )

    # Test load dataset (this downloads an actual image from github)
    data = load(ts, iri, retries=3)
    assert len(data) == 53502

    # Test load non-existing IRI
    with pytest.raises(TypeError):
        load(ts, "<nonexisting>", retries=2)

    # Test save dataset with anonymous distribution
    newfile = outdir / "newimage.tiff"
    newfile.unlink(missing_ok=True)
    buf = b"some bytes..."
    save(
        ts,
        buf,
        dataset={
            "@id": SEMDATA.newimage,
            "@type": SEM.SEMImage,
            DCTERMS.title: "New SEM image",
        },
        distribution={"downloadURL": f"file:{newfile}"},
    )
    assert newfile.exists()
    assert newfile.stat().st_size == len(buf)
    newimage = acquire(ts, SEMDATA.newimage)
    assert newimage["@id"] == SEMDATA.newimage
    assert DCAT.Dataset in newimage["@type"]
    assert SEM.SEMImage in newimage["@type"]
    assert newimage.distribution["@id"].startswith("_:")
    assert newimage.distribution["@type"] == [DCAT.Distribution, DCAT.Resource]
    assert newimage.distribution.downloadURL == f"file:{newfile}"

    # Test save dataset with named distribution
    newfile2 = outdir / "newimage.png"
    newfile2.unlink(missing_ok=True)
    save(
        ts,
        buf,
        dataset=SEMDATA.newimage2,
        distribution={
            "@id": SEMDATA.newdistr2,
            "downloadURL": f"file:{newfile2}",
            "mediaType": (
                "https://www.iana.org/assignments/media-types/image/png"
            ),
            "generator": GEN.sem_hitachi,
            "parser": PARSER.sem_hitachi,
        },
        method="overwrite",
    )
    assert newfile2.exists()
    assert newfile2.stat().st_size == len(buf)
    newimage2 = acquire(ts, SEMDATA.newimage2)
    assert newimage2["@id"] == SEMDATA.newimage2
    assert newimage2["@type"] == [DCAT.Dataset, DCAT.Resource, EMMO.Dataset]
    assert newimage2.distribution == SEMDATA.newdistr2

    newdist2 = acquire(ts, newimage2.distribution)
    assert newdist2["@id"] == newimage2.distribution
    assert newdist2["@type"] == [DCAT.Distribution, DCAT.Resource]
    assert newdist2.downloadURL == f"file:{newfile2}"

    # Test save anonymous dataset with existing distribution
    newfile2.unlink(missing_ok=True)
    save(ts, buf, distribution=SEMDATA.newdistr2)
    assert newfile2.exists()
    assert newfile2.stat().st_size == len(buf)

    # Test save existing dataset with anonymous distribution
    newfile2.unlink(missing_ok=True)
    save(ts, buf, dataset=SEMDATA.newimage2)
    assert newfile2.exists()
    assert newfile2.stat().st_size == len(buf)

    # Test save new dataset with reference to existing distribution
    newfile2.unlink(missing_ok=True)
    save(
        ts,
        buf,
        dataset={
            "@id": SEMDATA.newimage3,
            "title": "A dataset with no default distribution",
            "distribution": SEMDATA.newdistr2,
        },
        generator=GEN.sem_hitachi,
    )
    assert newfile2.exists()
    assert newfile2.stat().st_size == len(buf)

    # Test save and load dataset with invalid downloadURL
    store(
        ts,
        source={
            "@id": "ex:mydata",
            "@type": "dcat:Dataset",
            "distribution": {
                "downloadURL": "file:///non-existing.txt",
                "mediaType": IANA["text/plain"],
            },
        },
        prefixes={"ex": "http://example.com/"},
    )
    with pytest.raises(IOError):
        load(ts, "ex:mydata", retries=2)

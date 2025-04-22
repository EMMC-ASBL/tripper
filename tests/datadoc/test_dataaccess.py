"""Test the dataaccess module."""

# pylint: disable=invalid-name,too-many-locals,duplicate-code

import pytest

pytest.importorskip("yaml")
pytest.importorskip("requests")


def test_save_and_load():
    """Test save() and load()."""
    # pylint: disable=too-many-statements

    from dataset_paths import outdir  # pylint: disable=import-error

    from tripper import DCAT, DCTERMS, EMMO, Triplestore
    from tripper.datadoc import load, load_dict, save, save_dict

    pytest.importorskip("dlite")
    pytest.importorskip("rdflib")

    ts = Triplestore("rdflib")

    GEN = ts.bind("gen", "http://sintef.no/dlite/generator#")
    PARSER = ts.bind("parser", "http://sintef.no/dlite/parser#")
    SEM = ts.bind("sem", "https://w3id.com/emmo/domain/sem/0.1#")
    SEMDATA = ts.bind("semdata", "https://he-matchmaker.eu/data/sem/")

    iri = SEMDATA.img1

    # Test save dict
    save_dict(
        ts,
        source={
            "@id": SEMDATA.img1,
            "distribution": {
                "downloadURL": (
                    "https://github.com/EMMC-ASBL/tripper/raw/refs/heads/"
                    "master/tests/input/77600-23-001_5kV_400x_m001.tif"
                ),
                "mediaType": (
                    "http://www.iana.org/assignments/media-types/image/tiff"
                ),
            },
        },
        type="Dataset",
    )
    newdistr = load_dict(ts, SEMDATA.img1)
    assert newdistr["@type"] == [DCAT.Dataset, DCAT.Resource, EMMO.Dataset]
    assert newdistr.distribution["@type"] == [DCAT.Distribution, DCAT.Resource]
    assert (
        newdistr.distribution.mediaType
        == "http://www.iana.org/assignments/media-types/image/tiff"
    )

    save_dict(
        ts,
        source={
            "@id": GEN.sem_hitachi,
            "generatorType": "application/vnd.dlite-generate",
            "configuration": {"driver": "hitachi"},
        },
        type="Generator",
    )

    # Test load dataset (this downloads an actual image from github)
    data = load(ts, iri)
    assert len(data) == 53502

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
    newimage = load_dict(ts, SEMDATA.newimage)
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
                "http://www.iana.org/assignments/media-types/image/png"
            ),
            "generator": GEN.sem_hitachi,
            "parser": PARSER.sem_hitachi,
        },
    )
    assert newfile2.exists()
    assert newfile2.stat().st_size == len(buf)
    newimage2 = load_dict(ts, SEMDATA.newimage2)
    assert newimage2["@id"] == SEMDATA.newimage2
    assert newimage2["@type"] == [DCAT.Dataset, DCAT.Resource, EMMO.Dataset]
    assert newimage2.distribution == SEMDATA.newdistr2

    newdist2 = load_dict(ts, newimage2.distribution)
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

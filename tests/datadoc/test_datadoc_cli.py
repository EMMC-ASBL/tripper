"""Test the datadoc clitool."""

import pytest

pytest.importorskip("yaml")
pytest.importorskip("rdflib")
pytest.importorskip("SPARQLWrapper")

from tripper.datadoc.clitool import (  # pylint: disable=wrong-import-position
    maincommand,
)
from tripper.utils import (  # pylint: disable=wrong-import-position
    check_service_availability,
)

# Skip all tests if Fuseki is not available
available = check_service_availability("http://localhost:3030", timeout=1)
if not available:
    pytest.skip("Fuseki service is not available", allow_module_level=True)


def test_delete():
    """Test `datadoc delete` with Fuseki."""
    from dataset_paths import indir  # pylint: disable=import-error

    iri = "semdata:SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"

    cmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "delete",
        f"--criteria=@id={iri}",
    ]
    maincommand(cmd)

    # Ensure that KB doesn't contain the removed dataset
    findcmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "find",
        f"--criteria=@id={iri}",
    ]
    r = maincommand(findcmd)
    iris = set(r.split())
    assert not iris


def test_delete_regex():
    """Test `datadoc delete` with Fuseki."""
    from dataset_paths import indir  # pylint: disable=import-error

    iri_regexp = "https://he-matchmaker.eu/data/sem/.*"

    cmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "delete",
        f"--criteria=@id=~{iri_regexp}",
    ]
    maincommand(cmd)

    # Ensure that KB doesn't contain the removed dataset
    findcmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "find",
        f"--criteria=@id=~{iri_regexp}",
    ]
    r = maincommand(findcmd)
    iris = set(r.split())
    assert not iris


def test_add():
    """Test `datadoc add` with Fuseki."""
    from dataset_paths import indir, outdir  # pylint: disable=import-error

    cmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "add",
        f"--context={indir/'semdata-context.json'}",
        f"--dump={outdir/'semdata.ttl'}",
        f"{indir/'semdata.csv'}",
    ]
    maincommand(cmd)

    # Ensure that KB contains the added datasets
    findcmd = [
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "find",
        "--criteria=@id=~https://he-matchmaker.eu/data/sem/.*",
    ]
    r = maincommand(findcmd)
    iris = set(r.split())
    assert set(iris) == set(
        [
            (
                "https://he-matchmaker.eu/data/sem/SEM_cement_batch2/"
                "77600-23-001/77600-23-001_5kV_400x_m001"
            ),
            "https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001",
            "https://he-matchmaker.eu/data/sem/SEM_cement_batch2",
        ]
    )


def test_find():
    """Test `datadoc find` with Fuseki."""
    from dataset_paths import indir  # pylint: disable=import-error

    cmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "find",
        "--criteria=creator.name=Sigurd Wenner",
    ]
    r = maincommand(cmd)
    iris = set(r.split())
    assert iris == set(
        [
            (
                "https://he-matchmaker.eu/data/sem/SEM_cement_batch2/"
                "77600-23-001/77600-23-001_5kV_400x_m001"
            ),
            "https://he-matchmaker.eu/data/sem/SEM_cement_batch2/77600-23-001",
            "https://he-matchmaker.eu/data/sem/SEM_cement_batch2",
        ]
    )


def test_find_json():
    """Test `datadoc find` with Fuseki."""
    import json

    from dataset_paths import indir  # pylint: disable=import-error

    cmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "find",
        "--criteria=creator.name=Sigurd Wenner",
        "--format=json",
    ]
    r = maincommand(cmd)
    lst = json.loads(r)
    resources = {d["@id"]: d for d in lst}
    assert "https://he-matchmaker.eu/data/sem/SEM_cement_batch2" in resources
    assert len(resources) == 3


def test_fetch():
    """Test `datadoc fetch` with Fuseki."""
    from dataset_paths import indir, outdir  # pylint: disable=import-error

    outfile = outdir / "sem.tif"
    outfile.unlink(missing_ok=True)

    iri = (
        "https://he-matchmaker.eu/data/sem/"
        "SEM_cement_batch2/77600-23-001/77600-23-001_5kV_400x_m001"
    )

    cmd = [
        "--debug",
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "fetch",
        iri,
        f"--output={outfile}",
    ]
    maincommand(cmd)

    assert outfile.exists()

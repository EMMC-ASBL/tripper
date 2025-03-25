"""Test the datadoc clitool."""

from tripper.datadoc.clitool import maincommand


def test_delete():
    """Test `datadoc delete` with Fuseki."""
    from dataset_paths import indir

    cmd = [
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "delete",
        (
            "--criteria=@id=semdata:SEM_cement_batch2/"
            "77600-23-001/77600-23-001_5kV_400x_m001"
        ),
    ]
    maincommand(cmd)


def test_add():
    """Test `datadoc add` with Fuseki."""
    from dataset_paths import indir, outdir

    cmd = [
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "add",
        f"--context={indir/'semdata-context.json'}",
        f"--dump={outdir/'semdata.ttl'}",
        f"{indir/'semdata.csv'}",
    ]
    maincommand(cmd)


def test_find():
    """Test `datadoc find` with Fuseki."""
    from dataset_paths import indir

    cmd = [
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

    from dataset_paths import indir

    cmd = [
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

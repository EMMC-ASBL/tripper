"""Test the datadoc clitool."""

from tripper.datadoc.clitool import main

if True:
    # def test_delete_fuseki(tsname: str):
    """Test `datadoc delete` with Fuseki."""
    from dataset_paths import indir, outdir

    cmd = [
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "delete",
        (
            "--criteria=@id=semdata:SEM_cement_batch2/"
            "77600-23-001/77600-23-001_5kV_400x_m001"
        ),
    ]
    print(f"*** datadoc {' '.join(cmd)}")
    main(cmd)


if True:
    # def test_add_fuseki(tsname: str):
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
    print(f"*** datadoc {' '.join(cmd)}")
    main(cmd)


if True:
    # def test_find_fuseki(tsname: str):
    """Test `datadoc find` with Fuseki."""
    from dataset_paths import outdir

    cmd = [
        "--triplestore=FusekiTest",
        f"--config={indir/'session.yaml'}",
        "find",
        "--criteria=creator.name='Sigurd Wenner'",
    ]
    print(f"*** datadoc {' '.join(cmd)}")
    r = main(cmd)

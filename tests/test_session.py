"""Test session."""


def test_session():
    """Test session."""
    import pytest

    pytest.importorskip("yaml")

    from paths import indir

    from tripper import Literal, Session

    session = Session(config=indir / "session.yaml")
    ts = session.get_triplestore("RdflibTest")
    EX = ts.bind("ex", "http://example.com#")

    ts.add_triples(
        [
            (EX.john, EX.hasName, Literal("John")),
            (EX.john, EX.hasSon, EX.lars),
        ]
    )
    assert (set(ts.triples())) == {
        (
            "http://example.com#john",
            "http://example.com#hasName",
            Literal("John"),
        ),
        (
            "http://example.com#john",
            "http://example.com#hasSon",
            "http://example.com#lars",
        ),
    }

    assert session.get_names() == ["RdflibTest", "FusekiTest", "GraphDBTest"]

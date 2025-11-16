"""Test the tripper.datadoc.utils module."""

import pytest

# This annoying dependency is injected by pytest.
# We can only get rid of it by moving the tripper.datadoc.utils out of the
# datadoc folder.
pytest.importorskip("pyld")


def test_merge():
    """Test help-function merge()."""
    from tripper.datadoc.utils import merge

    assert merge(None, None) is None
    assert merge(None, "b") == "b"
    assert merge(None, ["b", "c"]) == ["b", "c"]
    assert merge("a", None) == "a"
    assert merge(["a", "c"], None) == ["a", "c"]
    assert merge("a", "a") == "a"
    assert merge("a", "b") == ["a", "b"]
    assert merge("a", ["b", "c"]) == ["a", "b", "c"]
    assert merge("a", ["b", "c", "a"]) == ["a", "b", "c"]
    assert merge(["a", "c"], "b") == ["a", "c", "b"]
    assert merge(["a", "b", "c"], "b") == ["a", "b", "c"]
    assert merge(["a", "c"], ["b", "c"]) == ["a", "c", "b"]
    with pytest.raises(TypeError):
        merge({}, "b")


def test_add():
    """Test help-function add()."""
    from tripper.datadoc.utils import add

    d = {}
    add(d, "a", "1")
    add(d, "b", "1")
    add(d, "b", "1")
    add(d, "a", "2")
    add(d, "a", "1")
    add(d, "a", {"c": "3"})
    assert d == {"a": ["1", "2", {"c": "3"}], "b": "1"}


def test_addnested():
    """Test help-function addnested()."""
    from tripper.datadoc.utils import addnested
    from tripper.utils import AttrDict

    d = AttrDict()
    addnested(d, "a.b", "1")
    assert d == {"a": {"b": "1"}}

    addnested(d, "a", "2")
    assert d == {"a": ["2", {"b": "1"}]}

    addnested(d, "a.b.c", {"d": "3"})
    assert d.a[0] == "2"
    assert d.a[1].b[1].c == {"d": "3"}
    assert d == {"a": ["2", {"b": ["1", {"c": {"d": "3"}}]}]}
    assert isinstance(d.a[1], AttrDict)

    l = []
    assert addnested(l, "a.b", 1) == [{"a": {"b": 1}}]
    assert addnested(l, "a.b", 1) == [{"a": {"b": 1}}]
    assert addnested(l, "a.b", 2) == [{"a": {"b": [1, 2]}}]

    d2 = {}
    addnested(d2, "a[1].x", 1)
    addnested(d2, "a[1].y", 2)
    addnested(d2, "a[2].x", 3)


def test_get():
    """Test help-function get()."""
    from tripper.datadoc.utils import get

    d = {"a": [1, 2], "b": 1}
    assert get(d, "a") == [1, 2]
    assert get(d, "b") == [1]
    assert get(d, "b", aslist=False) == 1
    assert get(d, "c") == []
    assert get(d, "c", default="x") == ["x"]
    assert get(d, "c", aslist=False) is None
    assert get(d, "c", default="x", aslist=False) == "x"


def test_asseq():
    """Test help-function asseq()."""
    from tripper.datadoc.utils import asseq

    assert asseq("abc") == ["abc"]
    assert asseq(["abc"]) == ["abc"]


def test_iriname():
    """Test utility function iriname()."""
    from tripper.datadoc.utils import iriname

    assert iriname("abc") == "abc"
    assert iriname("rdf:JSON") == "JSON"
    assert iriname("https://w3id.org/emmo#Ampere") == "Ampere"

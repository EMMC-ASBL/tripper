"""Test the dictutils module."""


def test_merge():
    """Test help-function merge()."""
    from tripper.datadoc.dictutils import merge

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


def test_add():
    """Test help-function add()."""
    from tripper.datadoc.dictutils import add

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
    from tripper.datadoc.dictutils import addnested
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


def test_get():
    """Test help-function get()."""
    from tripper.datadoc.dictutils import get

    d = {"a": [1, 2], "b": 1}
    assert get(d, "a") == [1, 2]
    assert get(d, "b") == [1]
    assert get(d, "b", aslist=False) == 1
    assert get(d, "c") == []
    assert get(d, "c", default="x") == ["x"]
    assert get(d, "c", aslist=False) is None
    assert get(d, "c", default="x", aslist=False) == "x"

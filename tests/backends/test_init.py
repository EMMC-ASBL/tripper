"""Test the functions in tripper/backends/__init__.py."""

from unittest import mock


def _import_only(*available):
    """Return a replacement for import_module() that only can import the
    modules in `available`."""

    def import_module(name):
        if name not in available:
            raise ModuleNotFoundError(f"No module named '{name}'")

    return import_module


def test_get_backends():
    """Test get_backends()."""
    from tripper.backends import get_backends

    # All known backends are returned by default
    assert get_backends() == ["rdflib", "ontopy"]

    # With only_available=True, only backends whose dependencies can be
    # imported are returned
    with mock.patch("tripper.backends.import_module", _import_only("rdflib")):
        assert get_backends(only_available=True) == ["rdflib"]

    with mock.patch("tripper.backends.import_module", _import_only()):
        assert get_backends(only_available=True) == []


def test_get_dependencies():
    """Test get_dependencies()."""
    from tripper.backends import get_dependencies

    # Dependencies of a given backend
    assert get_dependencies("rdflib") == ["rdflib"]
    assert get_dependencies("ontopy") == ["EMMOntoPy"]

    # Without argument, the dependencies of all backends are returned
    assert sorted(get_dependencies()) == ["EMMOntoPy", "rdflib"]

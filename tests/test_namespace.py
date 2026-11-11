"""Test namespaces."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest

FAMILY_IRI = "http://onto-ns.com/ontologies/examples/family#"


def _env_with_cachedir(cachedir):
    """Patch os.environ, such that `cachedir` is used as cache directory."""
    environ = {k: v for k, v in os.environ.items() if k != "XDG_CACHE_HOME"}
    if cachedir is not None:
        environ["XDG_CACHE_HOME"] = str(cachedir)
    return mock.patch.dict(os.environ, environ, clear=True)


@pytest.mark.network
def test_namespaces() -> None:
    """Test namespaces."""
    pytest.importorskip("rdflib")
    from paths import ontodir

    from tripper import RDF, Namespace
    from tripper.errors import NoSuchIRIError

    assert str(RDF) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    assert RDF.type == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

    FAM = Namespace(
        "http://onto-ns.com/ontologies/examples/family#",
        check=True,
        triplestore=ontodir / "family.ttl",
    )
    FOOD = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=True,
        triplestore=ontodir / "food.ttl",
    )
    FOOD2 = Namespace(
        "http://onto-ns.com/ontologies/examples/food#",
        label_annotations=True,
        check=False,
        triplestore=ontodir / "food.ttl",
    )
    assert FAM.Son == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM["Son"] == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM + "Son" == "http://onto-ns.com/ontologies/examples/family#Son"

    name = "FOOD_345ecde3_3cac_41d2_aad6_cb6835a27b41"
    assert FOOD[name] == FOOD + name
    assert FOOD.Vegetable == FOOD + name

    assert FOOD2[name] == FOOD2 + name
    assert FOOD2.Vegetable == FOOD2 + name

    with pytest.raises(NoSuchIRIError):
        FAM.NonExisting

    with pytest.raises(NoSuchIRIError):
        FOOD.NonExisting

    assert FOOD2.NonExisting == FOOD2 + "NonExisting"

    # Save and reuse the cache
    FOOD2._save_cache()
    FOOD3 = Namespace(
        "http://onto-ns.com/ontologies/examples/food#", check=True
    )
    assert FOOD3[name] == FOOD3 + name
    assert FOOD3.Vegetable == FOOD3 + name
    with pytest.raises(NoSuchIRIError):
        FOOD3.NonExisting

    # Test __dir__() method
    assert "Age" in dir(FAM)
    assert "Child" in dir(FAM)

    # Test __contains__() method
    # The assesment `"nonexisting" in RDF` may require an explanation.
    # Since the RDF namespace is not created with check=False, the
    # namespace object is not doing any checking on the validity of
    # the IRI. That means that if you write `RDF.nonexisting` it will
    # return 'https://www.w3.org/1999/02/22-rdf-syntax-ns#nonexisting'.
    # Hence, it behaves like "nonexisting" exists in the RDF namespace,
    # which is why `"nonexisting" in RDF` should be true.
    assert "type" in RDF
    assert "nonexisting" in RDF  # Surprising? See explanation above
    assert "Son" in FAM
    assert "foot" not in FAM


def test_namespace_label_precedence() -> None:
    """A real IRI in the ontology should take precedence over a
    clashing label on a different IRI."""
    pytest.importorskip("rdflib")
    from tripper import Namespace, Triplestore
    from tripper.literal import Literal

    base = "http://example.com/onto-precedence#"
    ts = Triplestore(backend="rdflib")
    # "somethingElse" is labelled "DFT", clashing with the real "DFT" IRI.
    ts.add(
        (
            base + "somethingElse",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#label",
            Literal("DFT"),
        )
    )
    ts.add(
        (
            base + "DFT",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#label",
            Literal("Density Functional Theory"),
        )
    )

    onto = Namespace(base, label_annotations=True, triplestore=ts, reload=True)

    assert base + "DFT" == onto.DFT
    assert onto["DFT"] == base + "DFT"
    assert onto["Density Functional Theory"] == base + "DFT"
    assert onto["somethingElse"] == base + "somethingElse"


def test_neg():
    """Test negation and plus operators."""
    from tripper import DCTERMS, RDF

    assert -DCTERMS == "http://purl.org/dc/terms"
    assert +DCTERMS == "http://purl.org/dc/terms/"
    assert -RDF == "http://www.w3.org/1999/02/22-rdf-syntax-ns"
    assert +RDF == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


def test_call():
    """Test the __call__() method."""
    pytest.importorskip("rdflib")
    from tripper import DCTERMS, EMMO
    from tripper.errors import NamespaceError

    assert DCTERMS("http://purl.org/dc/terms/issued") == "issued"
    assert EMMO(EMMO.Atom) == "Atom"

    with pytest.raises(NamespaceError):
        DCTERMS("xxx:issued")

    with pytest.raises(NamespaceError):
        EMMO("https://w3id.org/emmo#xxx")


def test_triplestore_arg() -> None:
    """Test triplestore argument of Namespace.__init__()."""
    pytest.importorskip("rdflib")
    from paths import ontodir

    from tripper import RDF, Namespace, Triplestore
    from tripper.errors import NamespaceError, NoSuchIRIError

    assert str(RDF) == "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    assert RDF.type == "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

    ts = Triplestore("rdflib")
    ts.parse(ontodir / "family.ttl")

    FAM = Namespace(
        "http://onto-ns.com/ontologies/examples/family#",
        check=True,
        triplestore=ts,
    )
    assert FAM.Son == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM["Son"] == "http://onto-ns.com/ontologies/examples/family#Son"
    assert FAM + "Son" == "http://onto-ns.com/ontologies/examples/family#Son"
    with pytest.raises(NoSuchIRIError):
        FAM.NonExisting

    # Unresolvable namespace IRI fails lazily at attribute access time
    EX = Namespace("http://example.com", check=True, triplestore=Ellipsis)
    with pytest.raises(NamespaceError):
        EX.Class

    # The deprecated `triplestore_url` argument still works, but warns
    with pytest.warns(DeprecationWarning, match="triplestore_url"):
        FAM2 = Namespace(
            FAMILY_IRI, check=True, triplestore_url=str(ontodir / "family.ttl")
        )
    assert FAM2.Son == FAMILY_IRI + "Son"

    # The deprecated `cachemode` argument still works, but warns
    with pytest.warns(DeprecationWarning, match="cachemode"):
        FAM3 = Namespace(FAMILY_IRI, check=True, triplestore=ts, cachemode=0)
    assert FAM3.Son == FAMILY_IRI + "Son"


def test_namespace_emmo():
    """Test EMMO namespace."""
    pytest.importorskip("rdflib")
    from tripper import EMMO
    from tripper.errors import NoSuchIRIError

    assert EMMO.Atom == (
        "https://w3id.org/emmo#EMMO_eb77076b_a104_42ac_a065_798b2d2809ad"
    )
    with pytest.raises(NoSuchIRIError):
        EMMO.NonExisting

    # Test _get_labels() method.
    assert EMMO._get_labels(EMMO.Atom) == ["Atom"]
    assert EMMO._get_labels("EMMO_eb77076b_a104_42ac_a065_798b2d2809ad") == [
        "Atom"
    ]


def test_save_cache():
    """Test Namespace._save_cache()."""
    pytest.importorskip("rdflib")
    from paths import ontodir

    from tripper import Namespace

    with tempfile.TemporaryDirectory() as tmpdir, _env_with_cachedir(tmpdir):
        FAM = Namespace(
            FAMILY_IRI, check=True, triplestore=ontodir / "family.ttl"
        )
        cachefile = FAM._get_cachefile()

        # The IRIs are loaded lazily, at the first lookup
        assert FAM.Son == FAMILY_IRI + "Son"

        # The cache file is written to the cache directory
        FAM._save_cache()
        assert cachefile.exists()
        assert cachefile.parent == Path(tmpdir) / "tripper"
        del FAM

    # A warning is issued if the cache file cannot be written
    FAM = Namespace(FAMILY_IRI, check=False)
    FAM._iris = {"Son": FAMILY_IRI + "Son"}
    with (
        mock.patch.object(Namespace, "_get_cachefile", side_effect=OSError),
        pytest.warns(UserWarning, match="Cannot access cache file"),
    ):
        FAM._save_cache()
    FAM._iris = None  # avoid saving the cache when FAM is deleted


def test_load_cache():
    """Test Namespace._load_cache()."""
    pytest.importorskip("rdflib")
    from paths import ontodir

    from tripper import Namespace

    with tempfile.TemporaryDirectory() as tmpdir, _env_with_cachedir(tmpdir):
        FAM = Namespace(
            FAMILY_IRI, check=True, triplestore=ontodir / "family.ttl"
        )

        # Without a cache file, there is nothing to load
        assert FAM._load_cache() is False

        # After saving the cache, a new namespace can load it.
        # The IRIs are loaded lazily, at the first lookup.
        assert FAM.Son == FAMILY_IRI + "Son"
        FAM._save_cache()
        FAM2 = Namespace(FAMILY_IRI, check=False)
        FAM2._iris = {}
        assert FAM2._load_cache() is True
        assert FAM2._iris["Son"] == FAMILY_IRI + "Son"
        del FAM, FAM2

    # A warning is issued if the cache directory cannot be accessed
    FAM = Namespace(FAMILY_IRI, check=False)
    with (
        mock.patch.object(Namespace, "_get_cachefile", side_effect=OSError),
        pytest.warns(UserWarning, match="Cannot create cache directory"),
    ):
        assert FAM._load_cache() is False
    FAM._iris = None  # avoid saving the cache when FAM is deleted


def test_get_cachedir():
    """Test get_cachedir()."""
    from tripper.errors import PermissionWarning
    from tripper.namespace import get_cachedir

    home = Path("/home/john")

    # XDG_CACHE_HOME is used if it is set
    with _env_with_cachedir("/xdg/cache"):
        assert get_cachedir(create=False) == Path("/xdg/cache/tripper")

    # Otherwise the default location of the platform is used
    with (
        _env_with_cachedir(None),
        mock.patch("tripper.namespace.Path.home", return_value=home),
    ):
        with mock.patch("sys.platform", "linux"):
            assert get_cachedir(create=False) == home / ".cache/tripper"

        with mock.patch("sys.platform", "darwin"):
            assert (
                get_cachedir(create=False) == home / "Library/Caches/tripper"
            )

        with mock.patch("sys.platform", "win32"):
            assert get_cachedir(create=False) == (
                home / "AppData/Local/tripper/Cache"
            )

    # With create=True, the directory is created
    with tempfile.TemporaryDirectory() as tmpdir, _env_with_cachedir(tmpdir):
        cachedir = get_cachedir()
        assert cachedir == Path(tmpdir) / "tripper"
        assert cachedir.is_dir()

    # A warning is issued if the directory cannot be created
    with (
        _env_with_cachedir("/xdg/cache"),
        mock.patch("pathlib.Path.mkdir", side_effect=PermissionError),
        pytest.warns(PermissionWarning),
    ):
        get_cachedir()

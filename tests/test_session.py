"""Test session."""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest


def _env_without_xdg(**kwargs):
    """Patch os.environ with the given variables and without any of the
    XDG_CONFIG_* variables."""
    environ = {
        k: v for k, v in os.environ.items() if not k.startswith("XDG_CONFIG_")
    }
    environ.update(kwargs)
    return mock.patch.dict(os.environ, environ, clear=True)


def test_session():
    """Test session."""
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

    # Without arguments, session.yaml in the config directory is used
    with tempfile.TemporaryDirectory() as tmpdir:
        configfile = Path(tmpdir) / "tripper" / "session.yaml"
        configfile.parent.mkdir()
        configfile.write_text("MyStore:\n  backend: rdflib\n")

        with _env_without_xdg(XDG_CONFIG_HOME=tmpdir):
            session = Session()

    assert session.get_names() == ["MyStore"]


def test_get_config():
    """Test Session._get_config()."""
    pytest.importorskip("yaml")

    from paths import indir

    from tripper import Session

    session = Session(config=indir / "session.yaml")

    # The configuration is returned as given in the config file
    assert session._get_config("RdflibTest") == {"backend": "rdflib"}
    assert session._get_config("FusekiTest")["password"] == "admin0"

    # A password given as argument replaces the configured password
    conf = session._get_config("FusekiTest", password="secret")
    assert conf["password"] == "secret"

    # Unknown session names raise ValueError
    with pytest.raises(ValueError, match="no session configured for"):
        session._get_config("UnknownStore")


def test_keyring():
    """Test that the password "KEYRING" is looked up in the keyring."""
    pytest.importorskip("yaml")
    pytest.importorskip("keyring")

    from tripper import Session

    with tempfile.TemporaryDirectory() as tmpdir:
        configfile = Path(tmpdir) / "session.yaml"
        configfile.write_text(
            "MyStore:\n"
            "  backend: rdflib\n"
            "  username: john\n"
            "  password: KEYRING\n"
        )
        session = Session(config=configfile)

    with mock.patch("keyring.get_password", return_value="secret") as get:
        conf = session._get_config("MyStore")

    get.assert_called_once_with("MyStore", "john")
    assert conf["password"] == "secret"


def test_get_configdir():
    """Test get_configdir()."""
    from tripper.session import get_configdir

    home = Path("/home/john")

    # XDG_CONFIG_HOME is used if it is set
    with _env_without_xdg(XDG_CONFIG_HOME="/xdg/home"):
        assert get_configdir(create=False) == Path("/xdg/home/tripper")

    # Otherwise the first directory in XDG_CONFIG_DIRS is used
    with _env_without_xdg(XDG_CONFIG_DIRS="/xdg/dir1:/xdg/dir2"):
        assert get_configdir(create=False) == Path("/xdg/dir1/tripper")

    # Otherwise the default location of the platform is used
    with (
        _env_without_xdg(),
        mock.patch("tripper.session.Path.home", return_value=home),
    ):
        with mock.patch("sys.platform", "linux"):
            assert get_configdir(create=False) == home / ".config/tripper"

        with mock.patch("sys.platform", "darwin"):
            assert get_configdir(create=False) == (
                home / "Library/Config/tripper"
            )

        with mock.patch("sys.platform", "win32"):
            assert get_configdir(create=False) == (
                home / "AppData/Local/tripper/Config"
            )

    # With create=True, the directory is created
    with tempfile.TemporaryDirectory() as tmpdir:
        with _env_without_xdg(XDG_CONFIG_HOME=tmpdir):
            configdir = get_configdir()
        assert configdir == Path(tmpdir) / "tripper"
        assert configdir.is_dir()

"""Test tripper.testutils.

The tests take no arguments (no pytest fixtures), such that they can be
called directly when debugging.  Local servers are started on free
ports, so the tests need neither internet access nor external services.
"""

import contextlib
import os
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

import pytest


class _Handler(BaseHTTPRequestHandler):
    """Responds with 200 on "/" and 404 on any other path."""

    def do_GET(self):  # pylint: disable=invalid-name
        """Handle GET request."""
        self.send_response(200 if self.path == "/" else 404)
        self.end_headers()

    def log_message(self, format, *args):  # pylint: disable=redefined-builtin
        """Silence logging."""


@contextlib.contextmanager
def _http_server():
    """Context manager running a local HTTP server.  Yields its URL."""
    server = HTTPServer(("localhost", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://localhost:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@contextlib.contextmanager
def _listening_socket():
    """Context manager with a socket listening on a free port.
    Yields the port number."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        sock.listen()
        yield sock.getsockname()[1]


def _closed_port():
    """Return a port number that nothing listens on."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("localhost", 0))
        return sock.getsockname()[1]


def _env(**kwargs):
    """Patch os.environ with the given variables, and remove all other
    TRIPPER_TEST_* variables."""
    environ = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("TRIPPER_TEST_")
    }
    environ.update(kwargs)
    return mock.patch.dict(os.environ, environ, clear=True)


def test_service_responds():
    """Test service_responds()."""
    pytest.importorskip("requests")
    from tripper.testutils import service_responds

    # Nothing is expected to listen on port 1
    assert not service_responds("http://localhost:1", timeout=0.5)

    with _http_server() as url:
        assert service_responds(url)
        assert service_responds(url + "/", timeout=0.5)
        assert not service_responds(url + "/missing")  # 404


def test_service_responds_without_requests():
    """Test that service_responds() returns false if requests is not
    installed."""
    from tripper.testutils import service_responds

    with _http_server() as url:
        with mock.patch.dict(sys.modules, {"requests": None}):
            assert not service_responds(url)


def test_serverskip():
    """Test serverskip()."""
    from tripper.testutils import serverskip

    default_timeout = socket.getdefaulttimeout()

    with _listening_socket() as port:
        assert serverskip("localhost", port, timeout=0.5) is None

    port = _closed_port()
    with pytest.raises(SystemExit) as excinfo:
        serverskip("localhost", port, timeout=0.5)
    assert excinfo.value.code == 44

    with pytest.raises(SystemExit) as excinfo:
        serverskip("localhost", port, timeout=0.5, exitcode=3)
    assert excinfo.value.code == 3

    # serverskip() must not change the global socket default timeout
    assert socket.getdefaulttimeout() == default_timeout


def test_service_config():
    """Test service_config()."""
    from tripper.testutils import TEST_SERVICES, service_config

    with _env():
        for service, defaults in TEST_SERVICES.items():
            config = service_config(service)
            assert config == defaults
            assert config is not defaults  # a copy is returned

    with _env(
        TRIPPER_TEST_FUSEKI_PORT="3031",
        TRIPPER_TEST_FUSEKI_PASSWORD="secret",
        TRIPPER_TEST_GRAPHDB_HOST="graphdb.example.com",
    ):
        fuseki = service_config("fuseki")
        assert fuseki["port"] == 3031
        assert isinstance(fuseki["port"], int)  # converted to default type
        assert fuseki["password"] == "secret"  # nosec B105
        assert fuseki["host"] == TEST_SERVICES["fuseki"]["host"]

        graphdb = service_config("graphdb")
        assert graphdb["host"] == "graphdb.example.com"
        assert graphdb["port"] == TEST_SERVICES["graphdb"]["port"]

    with _env(TRIPPER_TEST_FUSEKI_PORT="not-a-port"):
        with pytest.raises(ValueError):
            service_config("fuseki")

    with pytest.raises(KeyError):
        service_config("unknown-service")


def test_service_available():
    """Test service_available()."""
    from tripper.testutils import service_available

    with _listening_socket() as port:
        with _env(
            TRIPPER_TEST_FUSEKI_HOST="localhost",
            TRIPPER_TEST_FUSEKI_PORT=str(port),
        ):
            assert service_available("fuseki", timeout=0.5)

    with _env(
        TRIPPER_TEST_FUSEKI_HOST="localhost",
        TRIPPER_TEST_FUSEKI_PORT=str(_closed_port()),
    ):
        assert not service_available("fuseki", timeout=0.5)


def test_serviceskip():
    """Test serviceskip()."""
    from tripper.testutils import serviceskip

    with _listening_socket() as port:
        with _env(
            TRIPPER_TEST_GRAPHDB_HOST="localhost",
            TRIPPER_TEST_GRAPHDB_PORT=str(port),
        ):
            config = serviceskip("graphdb", timeout=0.5)
            assert config["host"] == "localhost"
            assert config["port"] == port
            assert config["repository"] == "test_repo"

    with _env(
        TRIPPER_TEST_GRAPHDB_HOST="localhost",
        TRIPPER_TEST_GRAPHDB_PORT=str(_closed_port()),
    ):
        with pytest.raises(SystemExit) as excinfo:
            serviceskip("graphdb", timeout=0.5, exitcode=5)
        assert excinfo.value.code == 5

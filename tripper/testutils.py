"""Some utilities for testing."""

import os
import socket
import sys

__all__ = [
    "service_responds",
    "serverskip",
    "service_config",
    "service_available",
    "serviceskip",
]


def service_responds(url: str, timeout: float = 1.0) -> bool:
    """Return whether the service with given URL responds with status 200.

    Unlike `check_service_availability()`, this makes a single request
    without retrying.  It is therefore fast when the service is not
    running, but doesn't wait for a service that is starting up.

    Arguments:
        url: URL of the service to check.
        timeout: Time in seconds to wait for a response.

    Returns:
        Returns true if the service responds with code 200, otherwise
        false is returned.  False is also returned if `requests` is not
        installed.
    """
    try:
        import requests  # pylint: disable=import-outside-toplevel
    except ImportError:
        return False

    try:
        return requests.get(url, timeout=timeout).status_code == 200
    except requests.exceptions.RequestException:
        return False


def serverskip(server, port, timeout=2, exitcode=44):
    """Ping a remote server and calls `sys.exit()` with given exitcode if it
    doesn't respond within the timeout."""
    try:
        with socket.create_connection((server, port), timeout=timeout):
            pass
    except OSError as exc:
        print(
            f"Server {server}:{port} seems to be down: {exc}", file=sys.stderr
        )
        sys.exit(exitcode)


# Default configurations of external services used by the tests.  They
# agree with test-services/compose.yaml, which starts all of them with
#
#     docker compose -f test-services/compose.yaml up -d
#
# Any value can be overridden with an environment variable named
# TRIPPER_TEST_<SERVICE>_<KEY>, e.g. TRIPPER_TEST_FUSEKI_PASSWORD.  The
# same environment variables are used by test-services/compose.yaml.
TEST_SERVICES = {
    "fuseki": {
        "host": "localhost",
        "port": 3030,
        "user": "admin",
        "password": "admin0",  # nosec B105
        "dataset": "test_repo",
    },
    "graphdb": {
        "host": "localhost",
        "port": 7200,
        "repository": "test_repo",
    },
}


def service_config(service):
    """Return a dict with the configuration of the given test service.

    Arguments:
        service: Name of the service.  Should be a key in `TEST_SERVICES`.

    Returns:
        Dict with the default configuration in `TEST_SERVICES`, where
        each value may be overridden by the environment variable
        TRIPPER_TEST_<SERVICE>_<KEY>.
    """
    config = {}
    prefix = f"TRIPPER_TEST_{service.upper()}_"
    for key, default in TEST_SERVICES[service].items():
        value = os.environ.get(prefix + key.upper(), default)
        config[key] = type(default)(value)
    return config


def service_available(service, timeout=2):
    """Return true if the given test service can be contacted, otherwise
    false."""
    config = service_config(service)
    try:
        with socket.create_connection(
            (config["host"], config["port"]), timeout=timeout
        ):
            pass
    except OSError:
        return False
    return True


def serviceskip(service, timeout=2, exitcode=44):
    """Call `sys.exit()` with the given exit code if the given test
    service cannot be contacted.  Otherwise return its configuration
    (see `service_config()`)."""
    config = service_config(service)
    serverskip(
        config["host"], config["port"], timeout=timeout, exitcode=exitcode
    )
    return config

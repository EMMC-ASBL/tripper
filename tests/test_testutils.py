"""Test utils"""

import pytest


def test_service_responds():
    """Test service_responds()."""
    pytest.importorskip("requests")
    from tripper.testutils import service_responds

    # Nothing is expected to listen on port 1
    assert not service_responds("http://localhost:1", timeout=0.5)

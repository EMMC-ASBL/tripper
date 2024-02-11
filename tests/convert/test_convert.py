"""Test convertions."""

# pylint: disable=invalid-name

import pytest


def test_convertions():
    """Test convertions. Uses rdflib as triplestore backend"""

    pytest.importorskip("rdflib")
    from tripper import Triplestore
    from tripper.convert import load_container, save_container

    ts = Triplestore(backend="rdflib")
    EX = ts.bind("ex", "http://example.com/ex#")

    config1 = {
        "downloadUrl": "http://example.com/somedata.txt",
        "mediaType": "application/text",
        "anotherField": "More info...",
    }

    config2 = {
        "downloadUrl": "http://example.com/somedata.txt",
        "mediaType": "application/text",
        "anotherField": "More info...",
        "configurations": {
            "key1": "val1",
            "key2": 2,
            "key3": 3.14,
            "key4": None,
            "key5": True,
            "key6": False,
            "key7": ["a", 1, 2.2, True, None],
        },
    }

    # Store dictionaries to triplestore
    save_container(ts, config1, EX.config1)
    save_container(ts, config2, EX.config2)

    # Print content of triplestore
    # print(ts.serialize())

    # Load dictionaries from triplestore
    d1 = load_container(ts, EX.config1)
    d2 = load_container(ts, EX.config2)

    # Check that we got back what we stored
    assert d1 == config1
    assert d2 == config2

    # Now, test serialising using recognised_keys
    save_container(ts, config1, EX.config1b, recognised_keys="basic")
    save_container(ts, config2, EX.config2b, recognised_keys="basic")

    d1b = load_container(ts, EX.config1b, recognised_keys="basic")
    d2b = load_container(ts, EX.config2b, recognised_keys="basic")

    assert d1b == config1
    assert d2b == config2

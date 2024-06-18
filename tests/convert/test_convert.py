"""Test convertions."""

# pylint: disable=invalid-name

import pytest


# if True:
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
            "key8": [{"a": 1, "b": 2}, {"a": 2.2, "b": 3.3}],
            "key9": [["a11", "a12", "a13"], ["a21", "a22", "a23"]],
        },
    }

    config3 = {
        "Simulation": {
            "command": "run_sim",
            "files": [
                {"target_file": "run_sim.sh", "source_iri": "http://..."},
                {"target_file": "other.txt", "source_iri": "http://..."},
            ],
            "input": {
                "onto:DataSet": [
                    {
                        "function": {
                            "functionType": "application/vnd.dlite-generate",
                            "configuration": {
                                "driver": "myplugin",
                                "location": "myfile.inp",
                                "datamodel": "http:...",
                            },
                        },
                    },
                ],
            },
        },
    }

    # Store dictionaries to triplestore
    save_container(ts, config1, EX.config1)
    save_container(ts, config2, EX.config2)
    save_container(ts, config3, EX.config3)

    # Print content of triplestore
    # print(ts.serialize())

    # Load dictionaries from triplestore
    d1 = load_container(ts, EX.config1)
    d2 = load_container(ts, EX.config2)
    d3 = load_container(ts, EX.config3)

    # Check that we got back what we stored
    assert d1 == config1
    assert d2 == config2
    assert d3 == config3

    # Now, test serialising using recognised_keys
    save_container(ts, config1, EX.config1b, recognised_keys="basic")
    save_container(ts, config2, EX.config2b, recognised_keys="basic")
    save_container(ts, config3, EX.config3b, recognised_keys="basic")

    d1b = load_container(ts, EX.config1b, recognised_keys="basic")
    d2b = load_container(ts, EX.config2b, recognised_keys="basic")
    d3b = load_container(ts, EX.config3b, recognised_keys="basic")

    assert d1b == config1
    assert d2b == config2
    assert d3b == config3

    # Check custom recognised keys
    from tripper.convert import BASIC_RECOGNISED_KEYS

    reg_keys = BASIC_RECOGNISED_KEYS.copy()
    reg_keys.update(
        Simulation=EX.Simulation,
        files=EX.files,
        command=EX.command,
        input=EX.input,
        output=EX.output,
    )
    save_container(ts, config3, EX.config3c, recognised_keys=reg_keys)
    d3c = load_container(ts, EX.config3c, recognised_keys=reg_keys)
    assert d3c == config3

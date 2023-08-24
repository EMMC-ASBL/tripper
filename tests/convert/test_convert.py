"""Test convertions."""
# pylint: disable=invalid-name
from tripper import Triplestore
from tripper.convert import load_dict, save_dict

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
        # "key5": ["a", 1, 2.2, None],  # lists are not supported yet...
    },
}

# Store dictionaries to triplestore
save_dict(ts, config1, EX.config1)
save_dict(ts, config2, EX.config2)

# Print content of triplestore
# print(ts.serialize())

# Load dictionaries from triplestore
d1 = load_dict(ts, EX.config1)
d2 = load_dict(ts, EX.config2)

# Check that we got back what we stored
assert d1 == config1
assert d2 == config2

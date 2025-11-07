"""Utilities for manipulating dicts and lists."""

import re
from typing import TYPE_CHECKING, Sequence

from tripper.utils import AttrDict

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Iterable, Optional, Union

    MergeType = Optional[Union[str, Sequence]]


def merge(a: "MergeType", b: "MergeType") -> "MergeType":
    """Return the merged result of `a` and `b`, where `a` and `b` can be
    None, string or a sequence of strings.

    The result will be None if both `a` and `b` are None and a string if one
    is None and the other is a string or both are the same string.  Otherwise,
    the result will be a list with the unique strings from `a` and `b`.

    Examples:
    >>> merge(None, None)

    >>> merge("a", None)
    'a'

    >>> merge(None, "b")
    'b'

    >>> merge("a", "b")
    ['a', 'b']

    >>> merge("a", ["c", "b", "a"])
    ['a', 'c', 'b']

    >>> merge(["a", "d"], ["c", "b", "a"])
    ['a', 'd', 'c', 'b']

    """
    # pylint: disable=too-many-return-statements
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    if isinstance(a, str) and isinstance(b, str):
        return a if b == a else [a, b]
    if isinstance(a, str) and isinstance(b, Sequence):
        return [a] + [x for x in b if x != a]
    if isinstance(a, Sequence) and isinstance(b, str):
        return a if b in a else list(a) + [b]
    if isinstance(a, Sequence) and isinstance(b, Sequence):
        return list(a) + [x for x in b if x not in a]
    raise TypeError("input must be None, string or a sequence")


def add(d: dict, key: str, value: "Any") -> None:
    """Append key-value pair to dict `d`.

    If `key` already exists in `d`, its value is converted to a list
    and `value` is appended to it.  `value` may also be a list. Values
    are not duplicated.

    """
    if key not in d:
        d[key] = value
    else:
        klst = d[key] if isinstance(d[key], list) else [d[key]]
        if isinstance(value, dict):
            v = klst if value in klst else klst + [value]
        else:
            vlst = value if isinstance(value, list) else [value]
            try:
                v = list(set(klst).union(vlst))
            except TypeError:  # klst contains unhashable dicts
                v = klst + [x for x in vlst if x not in klst]
        d[key] = (
            v[0]
            if len(v) == 1
            else sorted(
                # Sort dicts at end, by representing them with a huge
                # unicode character
                v,
                key=lambda x: "\uffff" if isinstance(x, dict) else str(x),
            )
        )


def addnested(
    d: "Union[dict, list]", key: str, value: "Any"
) -> "Union[dict, list]":
    """Like add(), but allows `key` to be a dot-separated list of sub-keys.
    Returns the updated `d`.

    Each sub-key will be added to `d` as a corresponding sub-dict.

    Example:

        >>> d = {}
        >>> addnested(d, "a.b.c", "val") == {'a': {'b': {'c': 'val'}}}
        True

    """
    if "." in key:
        first, rest = key.split(".", 1)
        if isinstance(d, list):
            for ele in d:
                if isinstance(ele, dict):
                    addnested(ele, key, value)
                    break
            else:
                d.append(addnested({}, key, value))
        elif first in d and isinstance(d[first], (dict, list)):
            addnested(d[first], rest, value)
        else:
            addnested(d, first, addnested(AttrDict(), rest, value))
    elif isinstance(d, list):
        for ele in d:
            if isinstance(ele, dict):
                add(ele, key, value)
                break
        else:
            d.append({key: value})
    else:
        add(d, key, value)
    return d


def get(
    d: dict, key: str, default: "Any" = None, aslist: bool = True
) -> "Any":
    """Like `d.get(key, default)` but returns the value as a list if
    `aslist` is True and value is not already a list.

    An empty list is returned in the special case that `key` is not in
    `d` and `default` is None.

    """
    value = d.get(key, default)
    if aslist:
        return (
            value
            if isinstance(value, list)
            else [] if value is None else [value]
        )
    return value


def asseq(value: "Union[str, Sequence]") -> "Sequence":
    """Returns a string or sequence as an iterable."""
    return [value] if isinstance(value, str) else value


def iriname(value: str) -> str:
    """Return the name part of an IRI or CURIE.
    If value has no ":", it is returned as-is.
    """
    if ":" not in value:
        return value
    m = re.search("[:/#]([a-zA-Z_][a-zA-Z0-9_.+-]*)$", value)
    if not m or not m.groups():
        raise ValueError(f"Cannot infer name of IRI: {value}")
    return m.groups()[0]

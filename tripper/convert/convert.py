"""Tripper module for converting between RDF and other repetations."""

# pylint: disable=invalid-name,redefined-builtin
import warnings
from typing import TYPE_CHECKING, Mapping, Sequence
from uuid import uuid4

from tripper import (
    DCAT,
    DCTERMS,
    EMMO,
    MAP,
    OWL,
    RDF,
    RDFS,
    Literal,
    Namespace,
)
from tripper.utils import parse_literal

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Dict, Optional, Union

    from tripper import Triplestore


OTEIO = Namespace("http://emmo.info/oteio#")

BASIC_RECOGNISED_KEYS = {
    "downloadUrl": DCAT.downloadUrl,
    "mediaType": DCAT.mediaType,
    "accessUrl": DCAT.accessUrl,
    "accessService": DCAT.accessService,
    "license": DCTERMS.license,
    "accessRights": DCTERMS.accessRights,
    "publisher": DCTERMS.publisher,
    "description": DCTERMS.description,
    "creator": DCTERMS.creator,
    "contributor": DCTERMS.contributor,
    "title": DCTERMS.title,
    "available": DCTERMS.available,
    "bibliographicCitation": DCTERMS.bibliographicCitation,
    "conformsTo": DCTERMS.conformsTo,
    "created": DCTERMS.created,
    "references": DCTERMS.references,
    "isReplacedBy": DCTERMS.isReplacedBy,
    "requires": DCTERMS.requires,
    "label": RDFS.label,
    "comment": RDFS.comment,
    "mapsTo": MAP.mapsTo,
}


def from_container(
    container: "Union[Mapping[str, Any], Sequence[Any]]",
    iri: str,
    lang: str = "en",
    recognised_keys: "Optional[Union[Dict, str]]" = None,
    keep: bool = False,
) -> list:
    """Serialise a basic Python container type (mapping or sequence) as RDF.

    Arguments:
        container: The container to be saved.  Should be a mapping or
            sequence.  The `load_container()` function will deserialise
            them as dict and list, respectively.
        iri: IRI of individual that stands for the container.
        lang: Language to use for mapping keys.
        recognised_keys: An optional dict that maps mapping keys that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.
        keep: Whether to keep the key-value pair representation for
            mapping items serialised with recognised_keys.  Note that this
            may duplicate potential large literal values.

    Returns:
        List of RDF triples.

    Note:
        `container` should not be an empty sequence.  The reason for this
        is that is represented with rdf:nil, which is a single IRI and not
        a triple.
    """
    if recognised_keys == "basic":
        recognised_keys = BASIC_RECOGNISED_KEYS

    rdf = []

    def get_obj_iri(obj, uuid):
        """Return IRI for Python object `obj`.  The `uuid` argument is
        appended to blank nodes for uniques."""
        if isinstance(obj, Mapping):
            if not obj:
                return OTEIO.Dictionary
            obj_iri = f"_:{dict}_{uuid}"
        elif isinstance(obj, Sequence) and not isinstance(obj, str):
            if not obj:
                return RDF.List
            obj_iri = f"_:{list}_{uuid}"
        elif obj is None:
            return OWL.Nothing
        else:
            return parse_literal(obj)

        rdf.extend(
            from_container(
                obj,
                obj_iri,
                lang=lang,
                recognised_keys=recognised_keys,
                keep=keep,
            )
        )
        return obj_iri

    if isinstance(container, Sequence):
        assert not isinstance(container, str)  # nosec
        if not container:
            raise ValueError("empty sequence is not supported")

        rdf.append((iri, RDF.type, RDF.List))

        for i, element in enumerate(container):
            uuid = uuid4()
            first_iri = get_obj_iri(element, uuid)
            rest_iri = RDF.nil if i >= len(container) - 1 else f"_:rest_{uuid}"
            rdf.append((iri, RDF.first, first_iri))
            rdf.append((iri, RDF.rest, rest_iri))
            iri = rest_iri

    elif isinstance(container, Mapping):
        rdf.append((iri, RDF.type, OTEIO.Dictionary))

        for key, value in container.items():
            uuid = uuid4()
            recognised = recognised_keys and key in recognised_keys
            value_iri = get_obj_iri(value, uuid)
            if recognised:
                rdf.append(
                    (iri, recognised_keys[key], value_iri)  # type: ignore
                )
            if not recognised or keep:
                key_indv = f"_:key_{uuid}"
                value_indv = f"_:value_{uuid}"
                pair = f"_:pair_{uuid}"
                rdf.extend(
                    [
                        (key_indv, RDF.type, OTEIO.DictionaryKey),
                        (
                            key_indv,
                            EMMO.hasStringValue,
                            Literal(key, lang=lang),
                        ),
                        (value_indv, RDF.type, OTEIO.DictionaryValue),
                        (value_indv, EMMO.hasValue, value_iri),
                        (pair, RDF.type, OTEIO.KeyValuePair),
                        (pair, OTEIO.hasDictionaryKey, key_indv),
                        (pair, OTEIO.hasDictionaryValue, value_indv),
                        (iri, OTEIO.hasKeyValuePair, pair),
                    ]
                )
    else:
        raise TypeError("container must be a mapping or sequence")

    return rdf


def save_container(
    ts: "Triplestore",
    container: "Union[Mapping[str, Any], Sequence[Any]]",
    iri: str,
    lang: str = "en",
    recognised_keys: "Optional[Union[Dict, str]]" = None,
    keep: bool = False,
) -> None:
    """Save a basic Python container object to a triplestore.

    Arguments:
        ts: Triplestore to which to write the container object.
        container: The container object to be saved.
        iri: IRI of individual that stands for the container object.
        lang: Language to use for keys.
        recognised_keys: An optional dict that maps dict mapping that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.
        keep: Whether to keep the key-value pair representation for
            items serialised with recognised_keys.  Note that this
            will duplicate potential large literal values.
    """
    if "rdf" not in ts.namespaces:
        ts.bind("rdf", RDF)
    if "dcat" not in ts.namespaces:
        ts.bind("dcat", DCAT)
    if "emmo" not in ts.namespaces:
        ts.bind("emmo", EMMO)
    if "oteio" not in ts.namespaces:
        ts.bind("oteio", OTEIO)

    ts.add_triples(
        from_container(
            container,
            iri,
            lang=lang,
            recognised_keys=recognised_keys,
            keep=keep,
        )
    )


def load_container(
    ts: "Triplestore",
    iri: str,
    recognised_keys: "Optional[Union[Dict, str]]" = None,
) -> "Union[dict, list]":
    """Deserialise a Python container object from a triplestore.

    Arguments:
        ts: Triplestore from which to fetch the dict.
        iri: IRI of individual that stands for the dict to fetch.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.

    Returns:
        A Python container object corresponding to `iri`.
    """
    if iri == RDF.nil:
        return []

    if recognised_keys == "basic":
        recognised_keys = BASIC_RECOGNISED_KEYS

    parents = set(o for s, p, o in ts.triples(subject=iri, predicate=RDF.type))

    def get_obj(value):
        """Return Python object for `value`."""
        value_type = ts.value(value, RDF.type)
        if value_type == OTEIO.Dictionary:
            return load_container(ts, value, recognised_keys=recognised_keys)
        if value_type == RDF.List:
            return load_container(ts, value, recognised_keys=recognised_keys)
        if value == OWL.Nothing:
            return None
        return value.value if isinstance(value, Literal) else value

    if OTEIO.Dictionary in parents:
        container = {}
        for _, _, pair in ts.triples(
            subject=iri, predicate=OTEIO.hasKeyValuePair
        ):
            key_iri = ts.value(pair, OTEIO.hasDictionaryKey)
            key = ts.value(key_iri, EMMO.hasStringValue)
            value_iri = ts.value(pair, OTEIO.hasDictionaryValue)
            value = ts.value(value_iri, EMMO.hasValue)
            container[str(key)] = get_obj(value)

        # Recognised IRIs
        if recognised_keys:
            iris = {v: k for k, v in recognised_keys.items()}  # type: ignore
            for _, p, o in ts.triples(subject=iri):
                key = iris.get(p)  # type: ignore
                if key and p in iris and key not in container:
                    container[key] = (
                        o.value
                        if isinstance(o, Literal)  # type: ignore
                        else o
                    )

    elif RDF.List in parents:
        container = []  # type: ignore
        while True:
            first = ts.value(iri, RDF.first)
            rest = ts.value(iri, RDF.rest)
            container.append(get_obj(first))  # type: ignore
            if rest == RDF.nil:
                break
            iri = rest

    else:
        raise TypeError(
            f"iri '{iri}' should be either a rdf:List or an oteio:Dictionary"
        )

    return container


# === Deprecated functions ===


def from_dict(
    dct: dict,
    iri: str,
    bases: "Optional[Sequence]" = None,
    lang: str = "en",
    recognised_keys: "Optional[Union[Dict, str]]" = None,
    keep: bool = False,
) -> list:
    """Serialise a dict as RDF.

    Arguments:
        dct: The dict to be saved.
        iri: IRI of individual that stands for the dict.
        bases: Parent class(es) or the dict.  Unused.
        lang: Language to use for keys.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.
        keep: Whether to keep the key-value pair representation for
            items serialised with recognised_keys.  Note that this
            will duplicate potential large literal values.

    Returns:
        List of RDF triples.
    """
    del bases  # silence pylint about unused variable
    warnings.warn(
        "from_dict() is deprecated.  Use from_container() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return from_container(
        dct, iri, lang=lang, recognised_keys=recognised_keys, keep=keep
    )


def save_dict(
    ts: "Triplestore",
    dct: "Mapping[str, Any]",
    iri: str,
    bases: "Optional[Sequence]" = None,
    lang: str = "en",
    recognised_keys: "Optional[Union[Dict, str]]" = None,
    keep: bool = False,
) -> None:
    """Save a dict to a triplestore.

    Arguments:
        ts: Triplestore to which to write the dict.
        dct: The dict to be saved.
        iri: IRI of individual that stands for the dict.
        bases: Parent class(es) or the dict.  Unused.
        lang: Language to use for keys.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.
        keep: Whether to keep the key-value pair representation for
            items serialised with recognised_keys.  Note that this
            will duplicate potential large literal values.
    """
    del bases  # silence pylint about unused variable
    warnings.warn(
        "save_dict() is deprecated.  Use save_container() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return save_container(
        ts, dct, iri, lang=lang, recognised_keys=recognised_keys, keep=keep
    )


def load_dict(
    ts: "Triplestore",
    iri: str,
    recognised_keys: "Optional[Union[Dict, str]]" = None,
) -> "Union[dict, list]":
    """Deserialise a dict from an RDF triplestore.

    Arguments:
        ts: Triplestore from which to fetch the dict.
        iri: IRI of individual that stands for the dict to fetch.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.

    Returns:
        A dict corresponding to `iri`.
    """
    warnings.warn(
        "load_dict() is deprecated.  Use load_container() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return load_container(ts, iri, recognised_keys=recognised_keys)

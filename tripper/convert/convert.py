"""Tripper module for converting between RDF and other repetations."""
# pylint: disable=invalid-name,redefined-builtin
from collections.abc import Mapping
from uuid import uuid4

from tripper import DCAT, DCTERMS, EMMO, OWL, RDF, RDFS, Literal, Namespace
from tripper.utils import parse_literal

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
}


def from_dict(
    dct,
    iri,
    bases=(OTEIO.Dictionary,),
    lang="en",
    recognised_keys=None,
    keep=False,
):
    """Serialise a dict as RDF.

    Arguments:
        dct: The dict to be saved.
        iri: IRI of indicidual that stands for the dict.
        bases: Parent class(es) or the dict.
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
    if recognised_keys == "basic":
        recognised_keys = BASIC_RECOGNISED_KEYS

    rdf = []
    for base in bases:
        rdf.append((iri, RDF.type, base))

    for dkey, dvalue in dct.items():
        uuid = uuid4()

        recognised = recognised_keys and dkey in recognised_keys

        if isinstance(dvalue, Mapping):
            # Ideally this should be a blank node, but that becomes
            # too nested for rdflib.  Instead we make the IRI unique
            # by embedding the UUID.
            value = f"dict_{uuid}"
            rdf.extend(
                from_dict(
                    dvalue,
                    value,
                    lang=lang,
                    recognised_keys=recognised_keys,
                    keep=keep,
                )
            )
        elif dvalue is None:
            value = OWL.Nothing
        else:
            value = parse_literal(dvalue)

        if recognised:
            rdf.append((iri, recognised_keys[dkey], value))

        if not recognised or keep:
            uuid = uuid4()
            key = f"_:key_{uuid}"
            value_indv = f"_:value_{uuid}"
            pair = f"_:pair_{uuid}"
            rdf.extend(
                [
                    (key, RDF.type, OTEIO.DictionaryKey),
                    (key, EMMO.hasStringValue, Literal(dkey, lang=lang)),
                    (value_indv, RDF.type, OTEIO.DictionaryValue),
                    (value_indv, EMMO.hasValue, value),
                    (pair, RDF.type, OTEIO.KeyValuePair),
                    (pair, OTEIO.hasDictionaryKey, key),
                    (pair, OTEIO.hasDictionaryValue, value_indv),
                    (iri, OTEIO.hasKeyValuePair, pair),
                ]
            )

    return rdf


def save_dict(
    ts, dct, iri, bases=(OTEIO.Dictionary,), recognised_keys=None, keep=False
):
    """Save a dict to a triplestore.

    Arguments:
        dct: The dict to be saved.
        iri: IRI of indicidual that stands for the dict.
        bases: Parent class(es) or the dict.
        lang: Language to use for keys.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.
        keep: Whether to keep the key-value pair representation for
            items serialised with recognised_keys.  Note that this
            will duplicate potential large literal values.
    """
    if "dcat" not in ts.namespaces:
        ts.bind("dcat", DCAT)
    if "emmo" not in ts.namespaces:
        ts.bind("emmo", EMMO)
    if "oteio" not in ts.namespaces:
        ts.bind("oteio", OTEIO)

    ts.add_triples(
        from_dict(
            dct,
            iri,
            bases=bases,
            recognised_keys=recognised_keys,
            keep=keep,
        )
    )


def load_dict(ts, iri, recognised_keys=None):
    """Serialise a dict as RDF.

    Arguments:
        ts: Triplestore from which to fetch the dict.
        iri: IRI of indicidual that stands for the dict to fetch.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to the special string "basic", the
            `BASIC_RECOGNISED_KEYS` module will be used.

    Returns:
        A dict corresponding to `iri`.
    """
    if recognised_keys == "basic":
        recognised_keys = BASIC_RECOGNISED_KEYS

    dct = {}

    for _, _, pair in ts.triples(subject=iri, predicate=OTEIO.hasKeyValuePair):
        key_iri = ts.value(pair, OTEIO.hasDictionaryKey)
        key = ts.value(key_iri, EMMO.hasStringValue)
        value_iri = ts.value(pair, OTEIO.hasDictionaryValue)
        value = ts.value(value_iri, EMMO.hasValue)
        value_type = ts.value(value, RDF.type)

        raw_value = value.value if isinstance(value, Literal) else value

        if value_type == OTEIO.Dictionary:
            val = load_dict(ts, value, recognised_keys=recognised_keys)
        elif value == OWL.Nothing:
            val = None
        else:
            val = raw_value

        dct[str(key)] = val

    # Recognised IRIs
    if recognised_keys:
        iris = {v: k for k, v in recognised_keys.items()}
        for _, p, o in ts.triples(subject=iri):
            key = iris.get(p)
            if key and p in iris and key not in dct:
                dct[key] = o.value if isinstance(o, Literal) else o

    return dct

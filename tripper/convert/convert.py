"""Tripper module for converting between RDF and other repetations."""
# pylint: disable=invalid-name,redefined-builtin
from uuid import uuid4

from tripper import DCAT, DCTERMS, EMMO, RDF, RDFS, Literal, Namespace
from tripper.utils import parse_literal

OTEIO = Namespace("http://emmo.info/oteio#")

BASIC_RECOGNISED_KEYS = {
    "downloadUrl": DCAT.downloadUrl,
    "medieType": DCAT.medieType,
    "accessUrl": DCAT.accessUrl,
    "accessService": DCAT.accessService,
    "license": DCTERMS.license,
    "accessRights": DCTERMS.accessRights,
    "publisher": DCTERMS.publisher,
}


def from_dict(dct, iri, bases=(OTEIO.Dictionary, ), lang="en",
              recognised_keys=None):
    """Serialise a dict as RDF.

    Arguments:
        dct: The dict to be saved.
        iri: IRI of indicidual that stands for the dict.
        bases: Parent class(es) or the dict.
        lang: Language to use for keys.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to "basic", the `BASIC_RECOGNISED_KEYS` module
            will be used.

    Returns:
        List of RDF triples.
    """
    if recognised_keys == "basic":
        recognised_keys = BASIC_RECOGNISED_KEYS

    rdf = []
    for base in bases:
        rdf.append((iri, RDF.type, base))

    for dkey, dvalue in dct.items():
        literal_value = parse_litetal(dvalue)
        recon = recognised_keys and dkey in recognised_keys
        if recon:
            rdf.append((iri, recognised_keys[dkey], literal_value))
        if not recon or

        uuid = uuid4()
        key = f"_key_{uuid}"
        value = f"_value_{uuid}"
        pair = f"_pair_{uuid}"
        rdf.extend([
            (key, RDF.type, OTEIO.DictionaryKey),
            (key, EMMO.hasStringValue, Literal(dkey, lang=lang)),
            (value, RDF.type, OTEIO.DictionaryValue),
            (value, EMMO.hasValue, literal_value),
            (pair, RDF.type, OTEIO.KeyValuePair),
            (pair, OTEIO.hasDictionaryKey, key),
            (pair, OTEIO.hasDictionaryValue, value),
            (iri, OTEIO.hasKeyValuePair, pair),
        ])


def save_dict(ts, dct, iri, bases=(OTEIO.Dictionary, ), recognised_keys=None):
    """Save a dict to a triplestore.

    Arguments:
        ts: Triplestore to save to.
        dct: The dict to be saved.
        iri: IRI of indicidual that stands for the dict.
        bases: Parent class(es) or the dict.
        recognised_keys: An optional dict that maps dict keys that
            correspond to IRIs of recognised RDF properties.
            If set to "basic", the `BASIC_RECOGNISED_KEYS` module
            will be used.

    Returns:
        Value of provided `iri`.
    """

"""Tripper subpackage for documenting datasets."""

from .context import Context, get_context
from .dataaccess import load, save
from .dataset import get_jsonld_context  # deprecated
from .dataset import get_prefixes  # deprecated
from .dataset import (
    acquire,
    delete,
    delete_iri,
    get_partial_pipeline,
    load_dict,
    read_datadoc,
    save_datadoc,
    save_dict,
    search,
    search_iris,
    store,
    told,
    validate,
)
from .keywords import Keywords, get_keywords
from .prefixes import load_prefixes, save_prefixes
from .tabledoc import TableDoc

"""Tripper subpackage for documenting datasets."""

from .dataaccess import load, save
from .dataset import (
    as_jsonld,
    get_jsonld_context,
    get_partial_pipeline,
    get_prefixes,
    load_dict,
    read_datadoc,
    save_datadoc,
    save_dict,
    search_iris,
)
from .tabledoc import TableDoc

"""Tripper sub-package for converting between RDF and other repetations."""
from .convert import from_dict, load_dict, save_dict

__all__ = [
    "from_dict",
    "save_dict",
    "load_dict",
]

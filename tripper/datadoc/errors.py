"""Exceptions and warnings for the tripper.datadoc package."""


class InvalidKeywordError(KeyError):
    """Keyword is not defined."""


class NoSuchTypeError(KeyError):
    """There are no pre-defined type defined with the given name."""

"""Exceptions and warnings for the tripper.datadoc package."""

from tripper.errors import TripperError, TripperWarning


class InvalidDatadocError(TripperError):
    """Invalid data documentation dict (or list)."""


class InvalidKeywordError(TripperError, KeyError):
    """Keyword is not defined."""


class NoSuchTypeError(TripperError, KeyError):
    """There are no pre-defined type defined with the given name."""


class ValidateError(TripperError):
    """Error validating data documentation dict."""


class PrefixMismatchError(TripperError):
    """Prefix mismatch between two sources."""


class InvalidContextError(TripperError):
    """Context is invalid."""


class UnknownKeywordWarning(TripperWarning):
    """Unknown keyword in data documentation."""


class MissingKeywordsClassWarning(UnknownKeywordWarning):
    """A class is referred to that is not defined in a keywords file."""

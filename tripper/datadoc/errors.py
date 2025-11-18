"""Exceptions and warnings for the tripper.datadoc package."""

from tripper.errors import TripperError, TripperWarning


# ========
# Errors
# ========
class InvalidDatadocError(TripperError):
    """Invalid data documentation dict (or list)."""


class MissingKeyError(InvalidDatadocError):
    """Missing required key in description of a resource or keyword."""


class InvalidKeywordError(InvalidDatadocError, KeyError):  # remove?
    """Keyword is not defined."""


class RedefineError(TripperWarning):
    """Trying to redefine an existing concept or keyword."""


class DatadocValueError(InvalidDatadocError, ValueError):
    """Invalid/inconsistent value (of correct type)."""


class NoSuchTypeError(TripperError, KeyError):
    """There are no pre-defined type defined with the given name."""


class ValidateError(TripperError):
    """Error validating data documentation dict."""


class PrefixMismatchError(TripperError):
    """Prefix mismatch between two sources."""


class InvalidContextError(TripperError):
    """Context is invalid."""


class IRIExistsError(TripperError):
    """The IRI already exists in the triplestore."""


class ParseError(TripperError):
    """Error when parsing a file."""


# ==========
# Warnings
# ==========
class UnknownKeywordWarning(TripperWarning):
    """Unknown keyword in data documentation."""


class IRIExistsWarning(TripperWarning):
    """The IRI already exists in the triplestore."""


class RedefineKeywordWarning(TripperWarning):
    """Redefine an existing keyword (by mapping it to a new IRI)."""


class SkipRedefineKeywordWarning(TripperWarning):
    """Skip redefining an existing keyword in a user-defined keyword
    definition (by mapping it to a new IRI)."""

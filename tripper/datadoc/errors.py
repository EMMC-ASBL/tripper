"""Exceptions and warnings for the tripper.datadoc package."""

from tripper.errors import TripperError


class InvalidKeywordError(TripperError, KeyError):
    """Keyword is not defined."""


class NoSuchTypeError(TripperError, KeyError):
    """There are no pre-defined type defined with the given name."""


class ValidateError(TripperError):
    """Error validating data documentation dict."""

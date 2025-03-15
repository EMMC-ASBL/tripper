"""Exceptions and warnings for the tripper.datadoc package."""


class InvalidKeywordError(KeyError):
    """Keyword is not defined."""


class NoSuchClassError(KeyError):
    """There are no class defined with the given name."""

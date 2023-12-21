"""Exceptions and warnings for the triplestore package."""


# === Exceptions ===
class TriplestoreError(Exception):
    """Base exception for triplestore errors."""


class UniquenessError(TriplestoreError):
    """More than one matching triple."""


class NamespaceError(TriplestoreError):
    """Namespace error."""


class NoSuchIRIError(NamespaceError):
    """Namespace has no such IRI."""


class CannotGetFunctionError(TriplestoreError):
    """Not able to get function documented in the triplestore."""


# === Warnings ===
class UnusedArgumentWarning(Warning):
    """Argument is unused."""

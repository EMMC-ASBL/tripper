"""Exceptions and warnings for the tripper package."""


# === Exceptions ===
class TripperError(Exception):
    """Base exception for tripper errors."""


class UniquenessError(TripperError):
    """More than one matching triple."""


class NamespaceError(TripperError):
    """Namespace error."""


class NoSuchIRIError(NamespaceError):
    """Namespace has no such IRI."""


class CannotGetFunctionError(TripperError):
    """Not able to get function documented in the triplestore."""


class ArgumentTypeError(TripperError, TypeError):
    """Invalid argument type."""


class ArgumentValueError(TripperError, ValueError):
    """Invalid argument value (of correct type)."""


class IRIExistsError(NamespaceError):
    """IRI already exists."""


# === Warnings ===
class TripperWarning(Warning):
    """Base class for tripper warnings."""


class UnusedArgumentWarning(TripperWarning):
    """Argument is unused."""


class UnknownDatatypeWarning(TripperWarning):
    """Unknown datatype."""


class PermissionWarning(TripperWarning, UserWarning):
    """Not enough permissions."""

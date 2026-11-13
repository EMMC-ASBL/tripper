"""Sup-package for working with ontologically defined units and quantities."""

from .units import UnitRegistry, get_unit_namespace, get_ureg

__all__ = ("EMMO", "UnitRegistry", "get_unit_namespace", "get_ureg")


def __getattr__(name):
    # `EMMO` is the EMMO namespace with label lookup in the default version
    # of EMMO used for units (see tripper.units.units.EMMO_VERSION).  It is
    # created on first access, since that requires loading EMMO.
    if name == "EMMO":
        return get_unit_namespace()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

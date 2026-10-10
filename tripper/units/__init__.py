"""Sup-package for working with ontologically defined units and quantities."""

from tripper import Namespace

from .units import UnitRegistry, get_unit_namespace, get_ureg

# Create EMMO namespace for the correct version of EMMO
EMMO = get_unit_namespace()

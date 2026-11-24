"""Create the tripper cache before running the tests in parallel.

The cache holds e.g. the units table generated from EMMO, which takes
some time to create.  With `pytest -n auto` and an empty cache, every
worker would otherwise create it at the same time.

Usage:

    python tests/warm_cache.py
    pytest -n auto

"""

if __name__ == "__main__":
    from tripper.units import UnitRegistry

    # Creating a unit registry creates the units triplestore, the units
    # table and the pint unit definitions caches
    UnitRegistry()

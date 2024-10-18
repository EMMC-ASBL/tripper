"""Defines paths for tests.

It defines some directories and some utility functions that can be used
with or without conftest.
"""

from pathlib import Path

testdir = Path(__file__).resolve().parent
ontodir = testdir / "ontologies"
outdir = testdir / "output"

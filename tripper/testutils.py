"""Motule primarly intended to be imported by tests.

It defines some directories and some utility functions that can be used
with or without conftest.
"""

from pathlib import Path

rootdir = Path(__file__).resolve().parent.parent
testdir = rootdir / "tests"
ontodir = testdir / "ontologies"
outdir = testdir / "output"

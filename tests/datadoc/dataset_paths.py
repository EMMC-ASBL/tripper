"""Defines paths for tests.

It defines some directories and some utility functions that can be used
with or without conftest.
"""

from pathlib import Path

testdir = Path(__file__).absolute().parent.parent.resolve()
rootdir = testdir.parent.resolve()
ontodir = testdir / "ontologies"
indir = testdir / "input"
outdir = testdir / "output"

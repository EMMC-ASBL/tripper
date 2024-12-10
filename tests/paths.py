"""Test paths"""

from pathlib import Path

rootdir = Path(__file__).resolve().parent.parent
testdir = rootdir / "tests"
ontodir = testdir / "ontologies"
outdir = testdir / "output"

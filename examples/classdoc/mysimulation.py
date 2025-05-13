"""Example of documenting a computation."""

from pathlib import Path

from tripper import Triplestore
from tripper.datadoc import save_datadoc

thisdir = Path(__file__).resolve().parent


ts = Triplestore("rdflib")
save_datadoc(ts, thisdir / "mysimulation.yaml")


print(ts.serialize())

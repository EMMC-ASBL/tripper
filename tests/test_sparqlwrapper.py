from tripper import Literal, Triplestore, Namespace
from tripper import RDFS, SKOS


ts = Triplestore(
    backend="sparqlwrapper",
    base_iri="http://vocabs.ardc.edu.au/repository/api/sparql/"
    "csiro_international-chronostratigraphic-chart_geologic-time-scale-2020",
  )
for s, p, o in ts.triples((None, SKOS.notation, None)):
    print()
    print(s)
    print(p)
    print(o)


# These will fail because we do not have credentials to modify the triplestore
if False:

    q = ts.remove((None, SKOS.notation, None))

    EX = Namespace("http://example.com#")
    q = ts.add_triples([
        (EX.a, RDFS.subClassOf, EX.base),
        (EX.a, SKOS.prefLabel, Literal("An a class.", lang="en")),
    ])

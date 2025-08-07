# pylint: disable=redefined-builtin,invalid-name
"""A module for providing access to data based on data documentation
from the datasets module.

High-level functions for accessing and storing actual data:

  - `load()`: Load documented dataset from its source.
  - `save()`: Save documented dataset to a data resource.

Note:
    This module may eventually be moved out of tripper into a separate
    package.

"""
from __future__ import annotations

import secrets  # From Python 3.9+ we could use random.randbytes(16).hex()
import time
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from tripper import DCAT, Triplestore
from tripper.datadoc.dataset import acquire, add, get, store
from tripper.utils import AttrDict

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Iterable, List, Mapping, Optional, Sequence, Union


def save(
    ts: Triplestore,
    data: bytes,
    class_iri: "Optional[str]" = None,
    dataset: "Optional[Union[str, dict]]" = None,
    distribution: "Optional[Union[str, dict]]" = None,
    generator: "Optional[str]" = None,
    prefixes: "Optional[dict]" = None,
    use_sparql: "Optional[bool]" = None,
    method: str = "raise",
) -> str:
    """Saves data to a dataresource and document it in the triplestore.

    Arguments:
        ts: Triplestore that documents the data to save.
        data: Bytes representation of the data to save.
        class_iri: IRI of a class in the ontology (e.g. an `emmo:Dataset`
            subclass) that describes the dataset that is saved.
            Is used to select the `distribution` if that is not given.
            If `distribution` is also given, a
            `dcat:distribution value <distribution>` restriction will be
            added to `class_iri`
        dataset: Either the IRI of the dataset individual standing for
            the data to be saved or or a dict that in addition to the IRI
            ('@id' keyword) can provide with additional documentation of
            the dataset.
            If `dataset` is None, a new blank node IRI will be created.
        distribution: Either the IRI of distribution for the data to be saved
            or a dict additional documentation of the distribution,
            like media type, parsers, generators etc...
            If `distribution` is None and dataset is not a dict with a
            'distribution' keyword, a new distribution will be added
            to the dataset.
        generator: Name of generator to use in case the distribution has
            several generators.
        prefixes: Dict with prefixes in addition to those included in the
            JSON-LD context.  Should map namespace prefixes to IRIs.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to `ts.prefer_sparql`.
        method: How to handle the case where `ts` already contains a document
            with the same id as `source`. Possible values are:
            - "overwrite": Remove existing documentation before storing.
            - "raise": Raise an `IRIExistsError` if the IRI of `source`
              already exits in the triplestore (default).
            - "merge": Merge `source` with existing documentation. This will
              duplicate non-literal properties with no explicit `@id`. If this
              is unwanted, merge manually and use "overwrite".
            - "ignore": If the IRI of `source` already exists, do nothing but
              issueing an `IRIExistsWarning`.

    Returns:
        IRI of the dataset.

    """
    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    # pylint: disable=import-outside-toplevel
    # Use the Protocol plugin system from DLite.  Should we move it to tripper?
    from dlite.protocol import Protocol

    triples = []
    save_dataset = save_distribution = False

    if dataset is None:
        # __TODO__: Infer dataset from value restriction on `class_iri`
        # This require that we make a SPARQL-version of ts.restriction().
        newiri = f"_:N{secrets.token_hex(16)}"
        typeiri = [DCAT.Dataset, class_iri] if class_iri else DCAT.Dataset
        dataset = AttrDict({"@id": newiri, "@type": typeiri})
        save_dataset = True
    elif isinstance(dataset, str):
        dset = acquire(ts, iri=dataset, use_sparql=use_sparql)
        if dset:
            dataset = dset
        else:
            typeiri = [DCAT.Dataset, class_iri] if class_iri else DCAT.Dataset
            dataset = AttrDict({"@id": dataset, "@type": typeiri})
            save_dataset = True
    elif isinstance(dataset, dict):
        save_dataset = True
    else:
        raise TypeError(
            "if given, `dataset` should be either a string or dict"
        )
    dataset: dict  # Tell mypy that this now is a dict

    if distribution is None:
        if "distribution" in dataset:
            distribution = get(dataset, "distribution")[0]
        else:
            newiri = f"_:N{secrets.token_hex(16)}"
            distribution = AttrDict(
                {"@id": newiri, "@type": DCAT.Distribution}
            )
            add(dataset, "distribution", distribution)
            triples.append((dataset["@id"], DCAT.distribution, newiri))
            save_distribution = True
    if isinstance(distribution, str):
        distr = acquire(ts, iri=distribution, use_sparql=use_sparql)
        if distr:
            distribution = distr
        else:
            distribution = AttrDict(
                {"@id": distribution, "@type": DCAT.Distribution}
            )
            add(dataset, "distribution", distribution)
            triples.append((dataset["@id"], DCAT.distribution, newiri))
            save_distribution = True
    elif isinstance(distribution, dict):
        add(dataset, DCAT.distribution, distribution)
        if "@id" in distribution:
            triples.append(
                (dataset["@id"], DCAT.distribution, distribution["@id"])
            )
        save_distribution = True
    else:
        raise TypeError(
            "if given, `distribution` should be either a string or dict"
        )
    distribution: dict  # Tell mypy that this now is a dict

    if isinstance(generator, str):
        gen = get(distribution, "generator")
        if isinstance(gen, (str, dict)):
            gen = [gen]
        for g in gen:
            if isinstance(g, dict):
                if gen.get("@id") == generator:
                    break
            else:
                break  # ???
        else:
            raise ValueError(
                f"dataset '{dataset}' has no such generator: {generator}"
            )
    elif "generator" in distribution:
        gen = get(distribution, "generator")[0]
    else:
        gen = None

    # __TODO__: Check if `class_iri` already has the value restriction.
    # If not, add it to triples

    # __TODO__: Move this mapping of supported schemes into the protocol
    # module.
    schemes = {
        "https": "http",
    }

    # Save data
    url = distribution.get("downloadURL", distribution.get("accessURL"))
    p = urlparse(str(url.decode() if isinstance(url, bytes) else url))
    scheme = (
        schemes.get(p.scheme, p.scheme) if p.scheme else "file"  # type: ignore
    )
    location = (
        f"{scheme}://{p.netloc}{p.path}" if p.netloc else f"{scheme}:{p.path}"
    )
    options = [p.query] if p.query else []
    if gen and "configuration" in gen and "options" in gen.configuration:
        # __TODO__: allow options to also be a dict
        options.append(gen.configuration["options"])
    id = (
        distribution["accessService"].get("identifier")
        if "accessService" in distribution
        else None
    )
    with Protocol(scheme, location, options=";".join(options)) as pr:
        pr.save(data, id)

    # Update triplestore
    ts.add_triples(triples)
    if save_dataset:
        store(ts, dataset, type="Dataset", prefixes=prefixes, method=method)
    elif save_distribution:
        store(
            ts,
            distribution,
            type="Distribution",
            prefixes=prefixes,
            method=method,
        )

    return dataset["@id"]


def load(
    ts: Triplestore,
    iri: str,
    distributions: "Optional[Union[str, Sequence[str]]]" = None,
    use_sparql: "Optional[bool]" = None,
    retries: int = 1,
) -> bytes:
    """Load dataset with given IRI from its source.

    Arguments:
        ts: Triplestore documenting the data to load.
        iri: IRI of the data to load.
        distributions: Name or sequence of names of distribution(s) to
            try in case the dataset has multiple distributions.  The
            default is to try all documented distributions.
        use_sparql: Whether to access the triplestore with SPARQL.
            Defaults to `ts.prefer_sparql`.
        retries: Number of times to try accessing the dataset. After each
            failed access, it will sleep for 1 second before trying again.
            The default is to only make one attempt to access the dataset.

    Returns:
        Bytes object with the underlying data.

    Note:
        For now this requires DLite.
    """
    # pylint: disable=import-outside-toplevel
    # Use the Protocol plugin system from DLite.  Should we move it to tripper?
    import dlite
    from dlite.protocol import Protocol

    dct = acquire(ts, iri=iri, use_sparql=use_sparql)
    if DCAT.Dataset not in get(dct, "@type"):
        raise TypeError(
            f"expected IRI '{iri}' to be a dataset, but got: "
            f"{', '.join(get(dct, '@type'))}"
        )

    if distributions is None:
        distributions = get(dct, "distribution")

    for dist in distributions:
        url = dist.get("downloadURL", dist.get("accessURL"))  # type: ignore
        if url:
            p = urlparse(url)
            # Mapping of supported schemes - should be moved into the protocol
            # module.
            schemes = {
                "https": "http",
            }
            scheme = schemes.get(p.scheme, p.scheme) if p.scheme else "file"
            location = (
                f"{scheme}://{p.netloc}{p.path}"
                if p.netloc
                else f"{scheme}:{p.path}"
            )
            id = (
                dist.accessService.get("identifier")  # type: ignore
                if "accessService" in dist
                else None
            )
            for n in range(retries):
                try:
                    with Protocol(scheme, location, options=p.query) as pr:
                        return pr.load(id)
                    # pylint: disable=no-member
                except (dlite.DLiteProtocolError, dlite.DLiteIOError):
                    pass
                # pylint: disable=broad-exception-caught
                except Exception as exc:
                    if n < retries - 1:
                        time.sleep(1)
                    else:
                        raise IOError(
                            f"cannot access dataset '{iri}' using "
                            f"scheme={scheme}, location={location} "
                            f"and options='{p.query}'"
                        ) from exc

    raise IOError(f"Cannot access dataset: {iri}")

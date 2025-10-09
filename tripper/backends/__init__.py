"""Implementation of triplestore backends"""

from importlib import import_module

# A dict mapping backend names to a list of dependencies
backend_dependencies = {
    "rdflib": ["rdflib"],
    "ontopy": ["EMMOntoPy"],
}


def get_backends(only_available=False):
    """Returns a list with the name of backends.

    If `only_available` is true, only backends whos dependencies can be
    imported are returned.
    """
    if only_available:
        backends = []
        for backend, dependencies in backend_dependencies.items():
            module_found = True
            for dependency in dependencies:
                try:
                    import_module(dependency)
                except ModuleNotFoundError:
                    module_found = False
            if module_found:
                backends.append(backend)
        return backends
    return list(backend_dependencies)


def get_dependencies(backend=None):
    """Returns a list with the names of all dependencies of the given
    backend.

    If `backend` is not given, return a list with dependencies for all
    backends.
    """
    if backend:
        return backend_dependencies[backend]

    dependencies = set()
    for deps in backend_dependencies.values():
        for dep in deps:
            dependencies.add(dep)
    return list(dependencies)

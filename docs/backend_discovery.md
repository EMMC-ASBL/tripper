Discovery of custom backends
============================
A tripper backend is a normal importable Python module that defines the class `{Name}Strategy`, where `{Name}` is the name of the backend with the first letter capitalized (as it would be with the `str.title()` method).
The methods they are supposed to define are documented in [tripper/interface.py].

Tripper support several use cases for discovery of custom backends.


Installed backend package
-------------------------
It is possible to create a pip installable Python package that provides new tripper backends that will be automatically discovered.

The backend package should add the following to its `pyproject.toml` file:

```toml
[project.entry-points."tripper.backends"]
mybackend1 = "subpackage.mybackend1"
mybackend2 = "subpackage.mybackend2"
```

When your package is installed, this would make `mybackend1` and `mybackend2` automatically discovarable by tripper, such that you can write

```python
>>> from tripper import Triplestore
>>> ts = Triplestore(backend="mybackend1")
```


Backend module
--------------
If you have a tripper backend that is specific to your application, or that you for some other reason don't want or feel the need to publish as a separate Python package, you can keep the backend as a module within your application.

In this case you have two options, either specify explicitly backend module when you instantiate your triplestore or append your package to the `tripper.backend_packages` module variable:


### Instantiate triplestore with explicit module path
An explicit module path can either be absolute or relative as shown in the example below:

```
# Absolute
>>> ts = Triplestore(backend="mypackage.backends.mybackend")

# Relative to the `package` argument
>>> ts = Triplestore(backend="backends.mybackend", package="mypackage")
```

A backend is considered to be specified explicitly if the `backend` argument contain a dot (.) or if the `package` argument is provided.


### Append to `tripper.backend_packages`
Finally you can insert/append the sub-package with your backend to the `tripper.backend_packages` list module variable:

```python
import tripper
tripper.backend_packages.append("mypackage.backends")
ts = Triplestore(backend="mybackend")
```


Search order for backends
-------------------------
Tripper backends are looked up in the following order:
1. explicit specified backend modules
2. backend packages
3. checking `tripper.backend_packages`

By default the built-in backends are looked up as the first element in `tripper.backend_packages` (but it is possible for the insert a custom backend sub-package before it).
This means that backend packages are looked up before the built-in backends.
Hence it is possible for a backend package to overwrite or extend a built-in backend.



[tripper/interface.py]: https://emmc-asbl.github.io/tripper/latest/api_reference/interface/

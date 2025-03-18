"""A session that makes it easy to manage triplestore connections."""

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from tripper.triplestore import Triplestore

if TYPE_CHECKING:  # pragma: no cover
    from typing import Optional, Union


class Session:
    """A class making it easy to access pre-configured triplestores.

    Each triplestore is identified by a name and configured in a
    user-defined YAML file.

    See https://emmc-asbl.github.io/tripper/latest/session/ for more info.

    This class can also be used to configure other resources. The
    easies is to create a subclass that implements a method similar to
    get_triplestore() for the other resource.

    """

    # pylint: disable=too-few-public-methods

    def __init__(self, config: "Optional[Union[Path, str]]" = None):
        """Initialises a session.

        Arguments:
            config: Configuration file.


        The default location of the configuration file depends on the system:

        - Linux: $HOME/.config/tripper/session.yaml
        - Windows: $HOME/AppData/Local/tripper/Config/session.yaml
        - Darwin: $HOME/Library/Config/tripper/session.yaml

        """
        import yaml  # pylint: disable=import-outside-toplevel,import-error

        if config is None:
            config = get_configdir() / "session.yaml"

        with open(config, "rt", encoding="utf-8") as f:
            self.sessions = yaml.safe_load(f)

    def _get_config(self, name: str, password: "Optional[str]" = None) -> dict:
        """Returns configrations for the named service."""
        if name not in self.sessions:
            raise ValueError(f"no session configured for: '{name}'")

        conf = self.sessions[name]

        if "password" in conf:
            if password:
                conf["password"] = password
            elif "username" in conf and conf["password"] == "KEYRING":
                import keyring  # pylint: disable=import-outside-toplevel,import-error

                conf["password"] = keyring.get_password(name, conf["username"])

        return conf

    def get_names(self) -> list:
        """Return a list with all configured session names."""
        return list(self.sessions.keys())

    def get_triplestore(
        self, name: str, password: "Optional[str]" = None
    ) -> "Triplestore":
        """Return a new triplestore instance with the given name."""
        conf = self._get_config(name, password=password)

        return Triplestore(**conf)


def get_configdir(create: bool = True) -> Path:
    """Returns cross-platform path to tripper config directory.

    If `create` is true, create the config directory if it doesn't exists.

    The XDG_CONFIG_HOME environment variable is used if it exists.
    """
    site_configdir = os.getenv("XDG_CONFIG_HOME")
    if not site_configdir:
        site_configdir = os.getenv("XDG_CONFIG_DIRS")
        if site_configdir:
            site_configdir = site_configdir.split(":")[0]

    finaldir = None
    if not site_configdir:
        if sys.platform.startswith("win32"):
            site_configdir = Path.home() / "AppData" / "Local"
            finaldir = "Config"
        elif sys.platform.startswith("darwin"):
            site_configdir = Path.home() / "Library" / "Config"
        else:  # Default to UNIX
            site_configdir = Path.home() / ".config"  # type: ignore
    configdir = Path(site_configdir) / "tripper"  # type: ignore
    if finaldir:
        configdir /= finaldir

    if create:
        path = Path(configdir.root)
        for part in configdir.parts[1:]:
            path /= part
            if not path.exists():
                path.mkdir()

    return configdir

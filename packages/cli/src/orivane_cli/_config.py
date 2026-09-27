"""Static, strict TOML validation; never imports application code."""

import keyword
import tomllib
from pathlib import Path


class _ConfigError(ValueError):
    """Contains only messages authored by the CLI, never input contents."""


def load_config(root: Path) -> tuple[str, str]:
    try:
        with (root / "orivane.toml").open("rb") as source:
            data = tomllib.load(source)
    except (OSError, ValueError) as error:
        raise _ConfigError("cannot read valid TOML") from error
    if set(data) != {"schema_version", "app"}:
        raise _ConfigError("expected only schema_version and app")
    version = data["schema_version"]
    if type(version) is not int or version != 1:
        raise _ConfigError("unsupported schema_version")
    app = data["app"]
    if not isinstance(app, dict) or set(app) != {"factory"}:
        raise _ConfigError("app must contain only factory")
    factory = app["factory"]
    if not isinstance(factory, str) or factory.count(":") != 1:
        raise _ConfigError("factory must be module.path:callable_name")
    module, attribute = factory.split(":")
    if not all(
        part.isidentifier() and not keyword.iskeyword(part)
        for part in [*module.split("."), attribute]
    ):
        raise _ConfigError("factory must be module.path:callable_name")
    return module, attribute

from pathlib import Path

import pytest
from orivane_cli._config import _ConfigError, load_config


@pytest.mark.parametrize("factory", ["app:create_runner", "package.app:create_runner"])
def test_valid_cli_configuration(tmp_path: Path, factory: str) -> None:
    (tmp_path / "orivane.toml").write_text(
        f'schema_version = 1\n[app]\nfactory = "{factory}"\n', encoding="utf-8"
    )
    assert load_config(tmp_path) == tuple(factory.split(":"))


@pytest.mark.parametrize(
    "content",
    [
        b"not valid TOML SECRET_CONTEXT_CLI_9f12",
        b"\xff",
        b'[app]\nfactory = "app:run"',
        b"schema_version = 1",
        b'schema_version = 1\nmodle = "SECRET_CONTEXT_CLI_9f12"\n[app]\nfactory = "app:run"',
        b'schema_version = 0\n[app]\nfactory = "app:run"',
        b'schema_version = 2\n[app]\nfactory = "app:run"',
        b'schema_version = 999\n[app]\nfactory = "app:run"',
        b'schema_version = true\n[app]\nfactory = "app:run"',
        b'schema_version = "1"\n[app]\nfactory = "app:run"',
        b'schema_version = 1.0\n[app]\nfactory = "app:run"',
        b'schema_version = 1\napp = "SECRET_CONTEXT_CLI_9f12"',
        b"schema_version = 1\n[app]",
        b'schema_version = 1\n[app]\nfactory = "app:run"\napi_key = "SECRET_CONTEXT_CLI_9f12"',
        b"schema_version = 1\n[app]\nfactory = 1",
    ],
)
def test_cli_configuration_rejects_invalid_schema_without_echoing_content(
    tmp_path: Path, content: bytes
) -> None:
    (tmp_path / "orivane.toml").write_bytes(content)
    with pytest.raises(_ConfigError) as caught:
        load_config(tmp_path)
    assert "SECRET_" not in str(caught.value)


@pytest.mark.parametrize(
    "factory",
    [
        "",
        "app",
        ":run",
        "app:",
        "app:run:extra",
        ".app:run",
        "app..sub:run",
        "app:run.attr",
        "bad-name:run",
        "class:run",
        "app:class",
        " app:run",
    ],
)
def test_cli_factory_syntax_is_static_and_strict(tmp_path: Path, factory: str) -> None:
    (tmp_path / "orivane.toml").write_text(
        f'schema_version = 1\n[app]\nfactory = "{factory}"\n', encoding="utf-8"
    )
    with pytest.raises(_ConfigError, match="factory must be"):
        load_config(tmp_path)


def test_cli_missing_config_is_safe(tmp_path: Path) -> None:
    with pytest.raises(_ConfigError, match="cannot read valid TOML"):
        load_config(tmp_path)

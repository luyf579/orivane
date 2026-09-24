from collections.abc import Iterator

import pytest
from pydantic_ai.models import override_allow_model_requests


@pytest.fixture(autouse=True)
def offline_models_only(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # No credential values are read. Even if present, they are unavailable to tests.
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "DEEPSEEK_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    with override_allow_model_requests(False):
        yield

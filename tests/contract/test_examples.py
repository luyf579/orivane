import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "name,expected",
    [
        ("01_offline_agent.py", "offline agent\n"),
        ("02_session_runtime.py", "offline session\n"),
        ("03_workflow.py", "offline workflow\n"),
    ],
)
def test_offline_examples(tmp_path: Path, name: str, expected: str) -> None:
    example = Path(__file__).resolve().parents[2] / "examples" / name
    result = subprocess.run(
        [sys.executable, str(example)], cwd=tmp_path, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == expected

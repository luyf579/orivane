import ast
import sys
import tomllib
from pathlib import Path

import agent_framework_core
import agent_framework_pydantic

ROOT = Path(__file__).resolve().parents[2]


def test_core_source_has_no_backend_imports() -> None:
    for path in (ROOT / "packages/core/src").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            assert not any(
                name.split(".")[0] in {"pydantic_ai", "agent_framework_pydantic"} for name in names
            ), path


def test_distribution_dependency_direction() -> None:
    core = tomllib.loads((ROOT / "packages/core/pyproject.toml").read_text())
    adapter = tomllib.loads((ROOT / "packages/backend-pydantic/pyproject.toml").read_text())
    assert core["project"]["dependencies"] == ["pydantic>=2.12,<3"]
    assert "agent-framework-core==0.1.0.dev0" in adapter["project"]["dependencies"]
    assert "pydantic-ai-slim==2.48.0" in adapter["project"]["dependencies"]
    assert adapter["tool"]["uv"]["sources"]["agent-framework-core"] == {"workspace": True}


def test_workflow_imports_only_standard_library() -> None:
    path = ROOT / "packages/core/src/agent_framework_core/_workflow.py"
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] in sys.stdlib_module_names for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            assert node.module is not None
            assert node.module.split(".")[0] in sys.stdlib_module_names


def test_adapter_can_use_core_without_initializing_a_model() -> None:
    state = agent_framework_core.SessionState("pydantic-ai", 1, "2.48.0", b"opaque")
    agent_framework_pydantic.validate_session_state(state)


def test_core_has_no_native_history_types_or_new_public_abstractions() -> None:
    forbidden = {
        "ModelMessage",
        "ModelRequest",
        "ModelResponse",
        "ModelMessagesTypeAdapter",
        "Message",
        "ChatMessage",
        "UniversalMessage",
        "ToolCall",
        "ToolResult",
        "ProviderBackend",
        "ModelBackend",
        "TraceEvent",
        "UniversalRunContext",
        "WorkflowStep",
        "WorkflowNode",
        "BranchNode",
        "Graph",
        "DAG",
        "StateMachine",
        "WorkflowContext",
        "WorkflowResult",
        "WorkflowBuilder",
        "WorkflowEngine",
        "WorkflowExecutor",
    }
    for path in (ROOT / "packages/core/src").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        names.update(n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        assert names.isdisjoint(forbidden), path
    assert forbidden.isdisjoint(agent_framework_core.__all__)

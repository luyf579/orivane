import ast
import sys
import tomllib
from pathlib import Path

import orivane_core
import orivane_pydantic

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
                name.split(".")[0] in {"pydantic_ai", "orivane_pydantic"} for name in names
            ), path


def test_distribution_dependency_direction() -> None:
    core = tomllib.loads((ROOT / "packages/core/pyproject.toml").read_text())
    adapter = tomllib.loads((ROOT / "packages/backend-pydantic/pyproject.toml").read_text())
    assert core["project"]["dependencies"] == ["pydantic>=2.12,<3", "opentelemetry-api>=1.44,<2"]
    assert "orivane-core==0.1.1" in adapter["project"]["dependencies"]
    assert "pydantic-ai-slim==2.48.0" in adapter["project"]["dependencies"]
    assert adapter["tool"]["uv"]["sources"]["orivane-core"] == {"workspace": True}


def test_workflow_imports_only_standard_library_and_private_observability() -> None:
    path = ROOT / "packages/core/src/orivane_core/_workflow.py"
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] in sys.stdlib_module_names for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 1 and node.module == "_observability":
                assert [alias.name for alias in node.names] == ["_operation"]
                continue
            assert node.level == 0
            assert node.module is not None
            assert node.module.split(".")[0] in sys.stdlib_module_names


def test_adapter_can_use_core_without_initializing_a_model() -> None:
    state = orivane_core.SessionState("pydantic-ai", 1, "2.48.0", b"opaque")
    orivane_pydantic.validate_session_state(state)


def test_observability_does_not_expand_public_api_or_install_exporters() -> None:
    assert set(orivane_pydantic.__all__) == {
        "PydanticAgentBackend",
        "BACKEND_ID",
        "BACKEND_VERSION",
        "FORMAT_VERSION",
        "validate_session_state",
    }
    forbidden_calls = {
        "basicConfig",
        "addHandler",
        "setLevel",
        "set_tracer_provider",
        "instrument_all",
    }
    for root in [ROOT / "packages/core/src", ROOT / "packages/backend-pydantic/src"]:
        for path in root.rglob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.Import):
                    imports = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imports = [node.module or ""]
                else:
                    imports = []
                assert not any(
                    name.startswith(
                        (
                            "opentelemetry.sdk",
                            "opentelemetry.exporter",
                            "opentelemetry.semconv",
                            "opentelemetry_semantic_conventions",
                        )
                    )
                    for name in imports
                ), path
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in forbidden_calls, path


def test_cli_dependency_and_private_import_boundary() -> None:
    manifest = tomllib.loads((ROOT / "packages/cli/pyproject.toml").read_text())
    assert manifest["project"]["dependencies"] == [
        "orivane-core==0.1.1",
        "orivane-backend-pydantic==0.1.1",
        "opentelemetry-sdk>=1.44,<2",
    ]
    for path in (ROOT / "packages/cli/src").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                names = []
            assert not any(name.startswith("orivane_core._") for name in names)
            assert not any(name.startswith("opentelemetry.exporter") for name in names)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in {"eval", "exec"}


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
    assert forbidden.isdisjoint(orivane_core.__all__)

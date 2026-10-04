import ast
import sys
import tomllib
from pathlib import Path

import orivane_commerce

PACKAGE = Path(__file__).resolve().parents[1]


def test_public_exports_and_model_fields_are_exact() -> None:
    assert orivane_commerce.__all__ == ["Product", "Listing", "MarketplaceAdapter"]
    assert set(orivane_commerce.Product.model_fields) == {
        "name",
        "brand",
        "description",
        "features",
        "attributes",
        "category",
        "target_audience",
        "language",
    }
    assert set(orivane_commerce.Listing.model_fields) == {
        "title",
        "description",
        "language",
        "bullet_points",
        "keywords",
    }


def test_source_imports_only_stdlib_pydantic_and_own_modules() -> None:
    for path in (PACKAGE / "src/orivane_commerce").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
                assert all(name in sys.stdlib_module_names | {"pydantic"} for name in names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1 and node.module == "_domain"
                else:
                    assert node.module is not None
                    assert node.module.split(".")[0] in sys.stdlib_module_names | {"pydantic"}
        assert not any(
            isinstance(n, ast.Name) and n.id in {"runtime_checkable", "eval", "exec", "__import__"}
            for n in ast.walk(tree)
        )


def test_only_pydantic_dependency_and_no_extra_domain_classes() -> None:
    project = tomllib.loads((PACKAGE / "pyproject.toml").read_text())["project"]
    assert project["dependencies"] == ["pydantic>=2.12,<3"]
    assert project["version"] == "0.1.1"
    classes = {
        n.name
        for path in (PACKAGE / "src/orivane_commerce").glob("*.py")
        for n in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(n, ast.ClassDef)
    }
    assert classes == {"Product", "Listing", "MarketplaceAdapter"}

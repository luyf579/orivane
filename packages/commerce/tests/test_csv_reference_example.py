import ast
import csv
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import ModuleType

import pytest
from orivane_commerce import Listing, Product

ROOT = Path(__file__).resolve().parents[3]
EXAMPLE = ROOT / "examples/04_commerce_csv_pipeline.py"
SAMPLE = ROOT / "examples/data/commerce_products.csv"
EXPECTED = ROOT / "examples/data/commerce_expected.jsonl"
COLUMNS = [
    "name",
    "brand",
    "description",
    "features_json",
    "attributes_json",
    "category",
    "target_audience",
    "language",
]
CANARY = "CSV_PRIVATE_CANARY_DO_NOT_PRINT"


def _record() -> dict[str, str]:
    return {
        "name": "Hand Trowel",
        "brand": "Fable Tools",
        "description": CANARY + ', a tool with a "blue" handle.',
        "features_json": '["Steel scoop","Blue grip"]',
        "attributes_json": '{"Color":"blue","dimensions":{"length_cm":28},"care":["wipe",null]}',
        "category": "Garden tools",
        "target_audience": "Adult gardeners",
        "language": "en",
    }


def _write_csv(
    tmp_path: Path,
    records: list[dict[str, str]],
    columns: list[str] | None = None,
    *,
    bom: bool = False,
) -> Path:
    path = tmp_path / "products.csv"
    header = COLUMNS if columns is None else columns
    with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for record in records:
            writer.writerow([record.get(column, "") for column in header])
    return path


def _run(path: Path, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(EXAMPLE), str(path)], cwd=cwd, capture_output=True, timeout=30
    )


def _assert_error(result: subprocess.CompletedProcess[bytes], message: str) -> None:
    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr == f"commerce_csv_pipeline: {message}{os.linesep}".encode()
    assert CANARY.encode() not in result.stderr
    assert b"Traceback" not in result.stderr


def _example_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("commerce_csv_reference_example", EXAMPLE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_sample_matches_generated_golden_bytes(tmp_path: Path) -> None:
    result = _run(SAMPLE, tmp_path)
    assert result.returncode == 0 and result.stderr == b""
    assert result.stdout == EXPECTED.read_bytes()
    records = [json.loads(line) for line in result.stdout.splitlines()]
    assert [record["row"] for record in records] == [1, 2]
    assert all(record["platform"] == "offline-reference" for record in records)


def test_repeatability_and_working_directory_independence(tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    first, second = _run(SAMPLE, tmp_path), _run(SAMPLE, other)
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout


def test_header_order_has_no_semantics(tmp_path: Path) -> None:
    record = _record()
    normal = _run(_write_csv(tmp_path, [record]), tmp_path)
    reordered = _run(_write_csv(tmp_path, [record], list(reversed(COLUMNS))), tmp_path)
    assert normal.returncode == reordered.returncode == 0
    assert normal.stdout == reordered.stdout and reordered.stderr == b""


@pytest.mark.parametrize(
    "header",
    [
        COLUMNS[:-1],
        [*COLUMNS, "unknown"],
        [*COLUMNS[:-1], "name"],
        [" name", *COLUMNS[1:]],
    ],
)
def test_invalid_headers_fail_safely(tmp_path: Path, header: list[str]) -> None:
    _assert_error(_run(_write_csv(tmp_path, [_record()], header), tmp_path), "invalid CSV header")


def test_empty_file_rejects_missing_header(tmp_path: Path) -> None:
    path = tmp_path / "empty.csv"
    path.write_bytes(b"")
    _assert_error(_run(path, tmp_path), "invalid CSV header")


@pytest.mark.parametrize(
    "field,value",
    [
        ("features_json", CANARY),
        ("features_json", '{"private":"' + CANARY + '"}'),
        ("attributes_json", CANARY),
        ("attributes_json", '["' + CANARY + '"]'),
    ],
)
def test_json_syntax_and_shape_fail_without_echo(tmp_path: Path, field: str, value: str) -> None:
    record = _record()
    record[field] = value
    _assert_error(_run(_write_csv(tmp_path, [record]), tmp_path), f"row 1: invalid {field}")


@pytest.mark.parametrize(
    "field,value",
    [
        ("features_json", "[7]"),
        ("attributes_json", '{" Color":"' + CANARY + '"}'),
        ("attributes_json", '{"Color ":"' + CANARY + '"}'),
        ("attributes_json", '{"number":NaN}'),
        ("attributes_json", '{"number":Infinity}'),
    ],
)
def test_product_validation_is_authoritative(tmp_path: Path, field: str, value: str) -> None:
    record = _record()
    record[field] = value
    category = (
        "invalid attributes_json"
        if value in ('{"number":NaN}', '{"number":Infinity}')
        else "invalid Product"
    )
    _assert_error(_run(_write_csv(tmp_path, [record]), tmp_path), f"row 1: {category}")


@pytest.mark.parametrize("blank", ["", "   "])
@pytest.mark.parametrize("field", ["name", "description", "language"])
def test_required_listing_inputs_have_no_fallback(tmp_path: Path, blank: str, field: str) -> None:
    record = _record()
    record[field] = blank
    category = "invalid Product" if field == "name" else f"{field} is required"
    _assert_error(_run(_write_csv(tmp_path, [record]), tmp_path), f"row 1: {category}")


@pytest.mark.parametrize(
    "field,value,category",
    [
        ("features_json", CANARY, "invalid features_json"),
        ("attributes_json", '{" Color":"' + CANARY + '"}', "invalid Product"),
        ("description", "", "description is required"),
        ("language", "", "language is required"),
    ],
)
def test_later_row_failure_has_no_partial_output_and_uses_logical_rows(
    tmp_path: Path, field: str, value: str, category: str
) -> None:
    first, second = _record(), _record()
    first["description"] += "\nA quoted second physical line."
    second[field] = value
    path = _write_csv(tmp_path, [first, second])
    _assert_error(_run(path, tmp_path), f"row 2: {category}")


@pytest.mark.parametrize("bom", [False, True])
def test_unicode_bom_and_csv_quoting_roundtrip(tmp_path: Path, bom: bool) -> None:
    record = _record()
    record["name"] = "桌面灯"
    record["description"] = '用于阅读，带有 "可调" 灯臂,\n第二行。'
    record["features_json"] = '["可调灯臂","白色灯罩"]'
    result = _run(_write_csv(tmp_path, [record], bom=bom), tmp_path)
    assert result.returncode == 0 and result.stderr == b""
    assert "桌面灯".encode() in result.stdout and b"\\u684c" not in result.stdout
    assert len(result.stdout.splitlines()) == 1
    draft = json.loads(result.stdout)["draft"]
    assert draft["headline"] == record["name"]
    assert draft["body"] == record["description"]
    assert draft["bullets"] == ["可调灯臂", "白色灯罩"]
    assert draft["search_terms"] == []


def test_blank_json_and_optional_fields_are_preserved_as_empty_or_none(tmp_path: Path) -> None:
    record = _record()
    for field in ["features_json", "attributes_json", "brand", "category", "target_audience"]:
        record[field] = " "
    result = _run(_write_csv(tmp_path, [record]), tmp_path)
    assert result.returncode == 0 and result.stderr == b""
    assert json.loads(result.stdout)["draft"]["bullets"] == []
    product: Product = _example_module()._read_product(record, 1)
    assert product.features == () and product.attributes == {}
    assert product.brand is product.category is product.target_audience is None


def test_product_keeps_unused_facts_and_listing_adds_no_claims() -> None:
    module = _example_module()
    record = _record()
    product: Product = module._read_product(record, 1)
    assert product.brand == record["brand"]
    assert product.category == record["category"]
    assert product.target_audience == record["target_audience"]
    assert product.attributes == {
        "Color": "blue",
        "dimensions": {"length_cm": 28},
        "care": ["wipe", None],
    }
    original = product.model_dump()
    listing: Listing = module._make_listing(product, 1)
    assert listing.title == product.name
    assert listing.description == product.description
    assert listing.language == product.language
    assert listing.bullet_points == product.features
    assert listing.keywords == ()
    assert product.model_dump() == original


def test_adapter_returns_frozen_application_owned_draft() -> None:
    module = _example_module()
    listing = Listing(
        title="Desk Lamp",
        description="A supplied description.",
        language="en",
        bullet_points=("Adjustable arm",),
        keywords=("supplied",),
    )
    adapter = module.OfflineReferenceAdapter()
    draft = adapter.adapt(listing)
    assert adapter.platform == "offline-reference"
    assert (draft.headline, draft.body, draft.locale) == (
        listing.title,
        listing.description,
        listing.language,
    )
    assert draft.bullets == listing.bullet_points and draft.search_terms == listing.keywords
    with pytest.raises(FrozenInstanceError):
        draft.headline = "changed"


@pytest.mark.parametrize("delta", [-1, 1])
def test_ragged_records_fail_closed(tmp_path: Path, delta: int) -> None:
    path = _write_csv(tmp_path, [_record()])
    with path.open("a", encoding="utf-8", newline="") as stream:
        csv.writer(stream).writerow(["private"] * (len(COLUMNS) + delta))
    _assert_error(_run(path, tmp_path), "row 2: invalid CSV record")


def test_invalid_csv_quoting_is_safe(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text(",".join(COLUMNS) + '\n"unterminated,' + CANARY, encoding="utf-8")
    _assert_error(_run(path, tmp_path), "invalid or unreadable CSV")


def test_invalid_utf8_is_safe_and_atomic(tmp_path: Path) -> None:
    path = _write_csv(tmp_path, [_record()])
    with path.open("ab") as stream:
        stream.write(b"\xff" + CANARY.encode())
    _assert_error(_run(path, tmp_path), "invalid or unreadable CSV")


def test_missing_path_does_not_echo_the_path(tmp_path: Path) -> None:
    _assert_error(_run(tmp_path / CANARY, tmp_path), "invalid or unreadable CSV")


@pytest.mark.parametrize("arguments", [[], [CANARY, CANARY]])
def test_argument_errors_do_not_echo_inputs(tmp_path: Path, arguments: list[str]) -> None:
    result = subprocess.run(
        [sys.executable, str(EXAMPLE), *arguments], cwd=tmp_path, capture_output=True, timeout=30
    )
    _assert_error(result, "expected one input CSV path")


def test_header_only_is_empty_success(tmp_path: Path) -> None:
    result = _run(_write_csv(tmp_path, []), tmp_path)
    assert result.returncode == 0 and result.stdout == result.stderr == b""


def test_example_import_boundary_has_no_network_models_or_telemetry() -> None:
    tree = ast.parse(EXAMPLE.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0 and node.module is not None
            imports.add(node.module.split(".")[0])
    assert imports <= sys.stdlib_module_names | {"orivane_commerce"}
    assert not imports & {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "pydantic_ai",
        "orivane_pydantic",
        "orivane_core",
        "orivane_cli",
        "logging",
        "opentelemetry",
        "logfire",
    }
    assert not any(
        isinstance(node, ast.Name)
        and node.id in {"eval", "exec", "literal_eval", "__import__", "runtime_checkable"}
        for node in ast.walk(tree)
    )


@pytest.mark.parametrize("row", [1, 2])
@pytest.mark.parametrize(
    "field,payload",
    [
        ("attributes_json", '{"secret":1,"secret":2}'),
        ("attributes_json", '{"outer":{"secret":1,"secret":2}}'),
        ("attributes_json", '{"items":[{"secret":1,"secret":2}]}'),
        ("attributes_json", '{"数":1,"\\u6570":2}'),
        ("attributes_json", '{"n":0,"\\u006e":1}'),
        ("attributes_json", '{"n":NaN,"n":1}'),
        ("attributes_json", '{"n":Infinity,"n":1}'),
        ("attributes_json", '{"n":-Infinity,"n":1}'),
        ("attributes_json", '{"n":1e9999,"n":1}'),
        ("attributes_json", '{"n":NaN}'),
        ("attributes_json", '{"n":Infinity}'),
        ("attributes_json", '{"n":-Infinity}'),
        ("attributes_json", '{"outer":{"n":NaN}}'),
        ("attributes_json", '{"items":[{"n":-Infinity}]}'),
        ("features_json", '[{"n":1,"n":2}]'),
        ("features_json", '[{"outer":{"n":1,"n":2}}]'),
        ("features_json", "[NaN]"),
        ("features_json", "[Infinity]"),
        ("features_json", "[-Infinity]"),
        ("features_json", '[{"n":NaN,"n":1}]'),
    ],
)
def test_strict_json_rejects_duplicates_and_constants_atomically(
    tmp_path: Path, field: str, payload: str, row: int
) -> None:
    invalid = _record()
    invalid[field] = payload
    records = [invalid]
    if row == 2:
        first = _record()
        first["description"] += "\nA second physical line."
        records.insert(0, first)
    result = _run(_write_csv(tmp_path, records), tmp_path)
    _assert_error(result, f"row {row}: invalid {field}")
    assert payload.encode() not in result.stderr
    assert b"secret" not in result.stderr


@pytest.mark.parametrize("row", [1, 2])
@pytest.mark.parametrize(
    "payload",
    [
        '{"n":1e9999}',
        '{"n":-1e9999}',
        '{"outer":{"n":1e9999}}',
        '{"items":[-1e9999]}',
    ],
)
def test_numeric_overflow_still_reaches_product_validation(
    tmp_path: Path, payload: str, row: int
) -> None:
    invalid = _record()
    invalid["attributes_json"] = payload
    records = [invalid] if row == 1 else [_record(), invalid]
    _assert_error(_run(_write_csv(tmp_path, records), tmp_path), f"row {row}: invalid Product")


def test_legal_nested_unicode_json_preserves_values_and_key_order(tmp_path: Path) -> None:
    record = _record()
    record["attributes_json"] = (
        '{"é":"雪","nested":{"alpha":1,"β":true},"items":[{"値":null}],"empty":{}}'
    )
    record["features_json"] = '["NaN","Infinity","-Infinity","雪"]'
    product: Product = _example_module()._read_product(record, 1)
    assert product.attributes == {
        "é": "雪",
        "nested": {"alpha": 1, "β": True},
        "items": [{"値": None}],
        "empty": {},
    }
    assert list(product.attributes) == ["é", "nested", "items", "empty"]
    assert isinstance(product.attributes["nested"], dict)
    assert list(product.attributes["nested"]) == ["alpha", "β"]
    result = _run(_write_csv(tmp_path, [record], bom=True), tmp_path)
    assert result.returncode == 0 and result.stderr == b""
    assert json.loads(result.stdout)["draft"]["bullets"] == ["NaN", "Infinity", "-Infinity", "雪"]


@pytest.mark.parametrize("later", [False, True])
@pytest.mark.parametrize("ending", ["\n", "\r\n"])
@pytest.mark.parametrize(
    "raw_row",
    [
        'bad"quote,brand,description,,,category,audience,en',
        'name,mi"ddle,description,,,category,audience,en',
        '"closed"x,brand,description,,,category,audience,en',
        '"closed" ,brand,description,,,category,audience,en',
        '"unterminated,brand,description,,,category,audience,en',
        'a",b,description,,,category,audience,en',
        '"a",b"c,description,,,category,audience,en',
        '商品"异常,品牌,说明,,,分类,受众,zh',
    ],
)
def test_manual_invalid_csv_quotes_fail_without_partial_output(
    tmp_path: Path, raw_row: str, ending: str, later: bool
) -> None:
    text = ",".join(COLUMNS) + ending
    if later:
        text += 'valid,brand,"first physical line' + ending
        text += 'second physical line",,,category,audience,en' + ending
    text += raw_row + ending + CANARY
    path = tmp_path / "manual-invalid.csv"
    path.write_bytes(text.encode("utf-8"))
    _assert_error(_run(path, tmp_path), "invalid or unreadable CSV")


@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("final_ending", [False, True])
@pytest.mark.parametrize(
    "encoded,decoded",
    [
        ("普通说明", "普通说明"),
        ('"正常引用"', "正常引用"),
        ('"说明,含逗号"', "说明,含逗号"),
        ('"说明含""双引号"""', '说明含"双引号"'),
        ('"第一行\n第二行"', "第一行\n第二行"),
        ('"第一行\r\n第二行"', "第一行\r\n第二行"),
    ],
)
def test_legal_manual_csv_preserves_quoting_and_record_endings(
    tmp_path: Path, encoded: str, decoded: str, ending: str, final_ending: bool
) -> None:
    text = ",".join(COLUMNS) + ending + f"商品,品牌,{encoded},,,分类,受众,zh"
    if final_ending:
        text += ending
    path = tmp_path / "manual-valid.csv"
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    result = _run(path, tmp_path)
    assert result.returncode == 0 and result.stderr == b""
    draft = json.loads(result.stdout)["draft"]
    assert draft["headline"] == "商品" and draft["body"] == decoded
    assert draft["locale"] == "zh" and draft["bullets"] == draft["search_terms"] == []


def test_reordered_columns_accept_empty_and_trailing_empty_fields(tmp_path: Path) -> None:
    columns = ["language", *COLUMNS[:-1]]
    text = ",".join(columns) + "\r\nen,name,,description,,,,"
    path = tmp_path / "trailing-empty.csv"
    path.write_bytes(text.encode())
    result = _run(path, tmp_path)
    assert result.returncode == 0 and result.stderr == b""
    assert json.loads(result.stdout)["draft"]["body"] == "description"


def test_quote_validation_and_parsing_use_the_same_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _example_module()
    path = _write_csv(tmp_path, [_record()])
    original_validator = module._validate_csv_quotes

    def change_file_after_validation(snapshot: str) -> None:
        original_validator(snapshot)
        path.write_bytes(b'changed"invalid')

    monkeypatch.setattr(module, "_validate_csv_quotes", change_file_after_validation)
    output: bytes = module._render_jsonl(path)
    assert json.loads(output)["draft"]["headline"] == _record()["name"]
    assert path.read_bytes() == b'changed"invalid'

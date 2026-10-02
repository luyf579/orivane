import json
from pathlib import Path

import pytest
from orivane_commerce import Product
from pydantic import JsonValue, ValidationError


def test_minimum_incomplete_product_and_selected_configuration() -> None:
    product = Product(name="Example")
    assert product.model_dump() == {
        "name": "Example",
        "brand": None,
        "description": None,
        "features": (),
        "attributes": {},
        "category": None,
        "target_audience": None,
        "language": None,
    }
    selected = Product(name="T-Shirt", attributes={"color": "blue", "size": "L"})
    assert selected.attributes == {"color": "blue", "size": "L"}


def test_all_fields_normalize_text_preserving_case_order_and_duplicates() -> None:
    product = Product.model_validate(
        {
            "name": "  Hand Trowel  ",
            "brand": "  Example Brand ",
            "description": " Garden tool.\n",
            "category": " Gardening ",
            "target_audience": " Home gardeners ",
            "language": " en-GB ",
            "features": [" Steel head ", " Wood handle ", " Steel head "],
            "attributes": {"Length": {"value": 28, "unit": "cm"}},
        }
    )
    assert product.name == "Hand Trowel"
    assert product.brand == "Example Brand"
    assert product.description == "Garden tool."
    assert product.category == "Gardening"
    assert product.target_audience == "Home gardeners"
    assert product.language == "en-GB"
    assert product.features == ("Steel head", "Wood handle", "Steel head")
    assert product.attributes == {"Length": {"value": 28, "unit": "cm"}}


def test_missing_name_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({})


@pytest.mark.parametrize("value", ["", " \t\n", None, 42, b"name"])
def test_invalid_name(value: object) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({"name": value})


@pytest.mark.parametrize(
    "field", ["brand", "description", "category", "target_audience", "language"]
)
@pytest.mark.parametrize("value", ["", " \t\n", 12, b"text"])
def test_optional_strings_reject_empty_or_non_string(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({"name": "Example", field: value})


@pytest.mark.parametrize(
    "field", ["brand", "description", "category", "target_audience", "language"]
)
def test_optional_strings_allow_explicit_none(field: str) -> None:
    assert getattr(Product.model_validate({"name": "Example", field: None}), field) is None


@pytest.mark.parametrize("value", ["", "  ", None, 1, b"text"])
def test_invalid_feature(value: object) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({"name": "Example", "features": [value]})


def test_json_roundtrip_preserves_nested_facts_types_and_unicode() -> None:
    attributes: dict[str, JsonValue] = {
        "text": "花园",
        "number": 2,
        "fraction": 1.25,
        "flag": True,
        "unknown": None,
        "nested": {"items": [False, 0, None, {"unit": "cm", "value": 28}]},
    }
    product = Product(name="Trowel", features=("Steel", "Wood"), attributes=attributes)
    encoded = product.model_dump_json()
    restored = Product.model_validate_json(encoded)
    assert restored == product
    assert isinstance(json.loads(encoded)["features"], list)
    assert isinstance(restored.features, tuple)
    assert type(restored.attributes["number"]) is int
    assert type(restored.attributes["flag"]) is bool
    assert restored.attributes["unknown"] is None


@pytest.mark.parametrize("value", [object(), b"bytes", Path("example"), (1, 2), {1, 2}])
@pytest.mark.parametrize("nested", [False, True])
def test_non_json_values_rejected_at_creation(value: object, nested: bool) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate(
            {"name": "Example", "attributes": {"value": [value] if nested else value}}
        )


def test_file_handle_is_rejected(tmp_path: Path) -> None:
    with (tmp_path / "input.txt").open("w") as handle, pytest.raises(ValidationError):
        Product.model_validate({"name": "Example", "attributes": {"handle": handle}})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nested_non_finite_numbers_rejected(value: float) -> None:
    with pytest.raises(ValidationError):
        Product(name="Example", attributes={"nested": [{"value": value}]})


@pytest.mark.parametrize(
    "key",
    [
        "",
        " \t",
        " Color",
        "Color ",
        " Color ",
        "\tColor",
        "Color\n",
        "\u00a0Color",
        "Color\u3000",
        1,
        b"bytes",
    ],
)
def test_invalid_attribute_key(key: object) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({"name": "Example", "attributes": {key: "value"}})


def test_keys_preserve_case_and_internal_whitespace() -> None:
    attributes: dict[str, JsonValue] = {
        "Color": "red",
        "color": "blue",
        "Product Type": "tool",
        "Product  Size": "L",
        "Product\tGrade": "A",
        "产品 类型": "园艺",
    }
    product = Product(name="Example", attributes=attributes)
    assert product.attributes == attributes
    assert Product.model_validate_json(product.model_dump_json()).attributes == attributes


@pytest.mark.parametrize("key", ["", "   ", " Color", "Color ", "\tColor", "Color\n"])
def test_invalid_attribute_keys_in_json(key: str) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate_json(json.dumps({"name": "Example", "attributes": {key: "value"}}))


def test_surrounding_whitespace_is_rejected_without_merging_or_mutating_input() -> None:
    attributes: dict[str, JsonValue] = {"Color": "red", " Color ": "blue"}
    with pytest.raises(ValidationError):
        Product(name="Example", attributes=attributes)
    assert attributes == {"Color": "red", " Color ": "blue"}


def test_assignment_rejects_attribute_keys_with_surrounding_whitespace() -> None:
    product = Product(name="Example", attributes={"Color": "red"})
    with pytest.raises(ValidationError):
        product.attributes = {"Color ": "blue"}
    assert product.attributes == {"Color": "red"}


@pytest.mark.parametrize("key", [b"bytes", 1])
def test_nested_non_string_keys_rejected_without_coercion(key: object) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({"name": "Example", "attributes": {"nested": {key: 1}}})


@pytest.mark.parametrize(
    "field", ["titel", "id", "source_description", "files", "source_url", "price", "variants"]
)
def test_unknown_or_out_of_scope_field(field: str) -> None:
    with pytest.raises(ValidationError):
        Product.model_validate({"name": "Example", field: "unexpected"})


def test_mutable_defaults_and_validated_input_are_isolated() -> None:
    first, second = Product(name="First"), Product(name="Second")
    first.attributes["color"] = "blue"
    assert second.attributes == {}
    raw: dict[str, JsonValue] = {"nested": {"color": "red"}}
    one = Product(name="One", attributes=raw)
    two = Product(name="Two", attributes=raw)
    nested = one.attributes["nested"]
    assert isinstance(nested, dict)
    nested["color"] = "blue"
    assert two.attributes == raw == {"nested": {"color": "red"}}


def test_product_assignment_is_mutable_but_validated() -> None:
    product = Product(name="Example")
    product.name = " Corrected "
    assert product.name == "Corrected"
    with pytest.raises(ValidationError):
        product.name = "  "
    assert product.name == "Corrected"
    product.attributes["invalid"] = float("nan")
    with pytest.raises(ValidationError):
        Product.model_validate(product.model_dump())


def test_json_schema_matches_required_fields_and_json_attributes() -> None:
    schema = Product.model_json_schema()
    assert schema["required"] == ["name"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["attributes"]["type"] == "object"

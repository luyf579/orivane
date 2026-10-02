import json

import pytest
from orivane_commerce import Listing
from pydantic import ValidationError


def test_minimum_listing() -> None:
    listing = Listing(title="Hand Trowel", description="A garden tool.", language="en")
    assert listing.bullet_points == listing.keywords == ()
    assert listing.model_dump() == {
        "title": "Hand Trowel",
        "description": "A garden tool.",
        "language": "en",
        "bullet_points": (),
        "keywords": (),
    }


def test_full_content_normalizes_without_sorting_or_deduplicating() -> None:
    listing = Listing.model_validate(
        {
            "title": " Hand Trowel ",
            "description": " A garden tool.\n",
            "language": " en-GB ",
            "bullet_points": [" Wood handle ", " Steel head ", " Wood handle "],
            "keywords": [" Garden ", "Hand tool", " Garden "],
        }
    )
    assert listing.title == "Hand Trowel"
    assert listing.description == "A garden tool."
    assert listing.language == "en-GB"
    assert listing.bullet_points == ("Wood handle", "Steel head", "Wood handle")
    assert listing.keywords == ("Garden", "Hand tool", "Garden")


@pytest.mark.parametrize("field", ["title", "description", "language"])
def test_required_fields_have_no_fallback(field: str) -> None:
    data = {"title": "Trowel", "description": "Tool", "language": "en"}
    del data[field]
    with pytest.raises(ValidationError):
        Listing.model_validate(data)


@pytest.mark.parametrize("field", ["title", "description", "language"])
@pytest.mark.parametrize("value", ["", " \n\t", None, 1, b"text"])
def test_invalid_required_text(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Listing.model_validate(
            {"title": "Trowel", "description": "Tool", "language": "en", field: value}
        )


@pytest.mark.parametrize("field", ["bullet_points", "keywords"])
@pytest.mark.parametrize("value", ["", "  ", None, 1, b"text"])
def test_invalid_sequence_item(field: str, value: object) -> None:
    with pytest.raises(ValidationError):
        Listing.model_validate(
            {"title": "Trowel", "description": "Tool", "language": "en", field: [value]}
        )


@pytest.mark.parametrize(
    "field",
    [
        "titel",
        "attributes",
        "marketplace_metadata",
        "platform",
        "price",
        "sku",
        "variant",
        "inventory",
        "media",
    ],
)
def test_unknown_and_platform_fields_rejected(field: str) -> None:
    with pytest.raises(ValidationError):
        Listing.model_validate(
            {"title": "Trowel", "description": "Tool", "language": "en", field: "unexpected"}
        )


def test_frozen_and_input_sequences_do_not_alias() -> None:
    bullets = ["Steel head"]
    listing = Listing.model_validate(
        {"title": "Trowel", "description": "Tool", "language": "en", "bullet_points": bullets}
    )
    bullets.append("New input")
    assert listing.bullet_points == ("Steel head",)
    with pytest.raises(ValidationError):
        listing.title = "Changed"
    with pytest.raises(ValidationError):
        listing.bullet_points += ("Added",)
    with pytest.raises(ValidationError):
        del listing.language


def test_json_roundtrip_restores_tuples_and_unicode() -> None:
    listing = Listing(
        title="园艺铲",
        description="木柄工具。",
        language="zh-CN",
        bullet_points=("木柄", "钢头"),
        keywords=("园艺", "花园"),
    )
    encoded = listing.model_dump_json()
    assert json.loads(encoded)["bullet_points"] == ["木柄", "钢头"]
    restored = Listing.model_validate_json(encoded)
    assert restored == listing
    assert isinstance(restored.bullet_points, tuple)
    assert isinstance(restored.keywords, tuple)


def test_schema_and_no_platform_specific_title_limit() -> None:
    schema = Listing.model_json_schema()
    assert schema["required"] == ["title", "description", "language"]
    assert schema["additionalProperties"] is False
    long_title = "x" * 1000
    assert Listing(title=long_title, description="Tool", language="xx-test").title == long_title

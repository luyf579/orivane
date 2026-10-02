from dataclasses import dataclass
from typing import assert_type

import pytest
from orivane_commerce import Listing, MarketplaceAdapter


@dataclass(frozen=True)
class _ExampleDraft:
    title: str
    bullets: tuple[str, ...]


class _ExampleAdapter:
    platform = "amazon"

    def adapt(self, listing: Listing) -> _ExampleDraft:
        # Synthetic test-only limit, not an Amazon rule.
        if len(listing.title) > 12:
            raise ValueError("test_title_limit")
        return _ExampleDraft(listing.title, listing.bullet_points)


class _OtherAdapter:
    @property
    def platform(self) -> str:
        return "third-party-store"

    def adapt(self, listing: Listing) -> tuple[str, str]:
        return listing.title, listing.description


def test_structural_protocol_retains_adapter_owned_output() -> None:
    adapter: MarketplaceAdapter[_ExampleDraft] = _ExampleAdapter()
    listing = Listing(
        title="Trowel", description="Garden tool", language="en", bullet_points=("Steel head",)
    )
    draft = adapter.adapt(listing)
    assert_type(draft, _ExampleDraft)
    assert draft == _ExampleDraft("Trowel", ("Steel head",))
    assert adapter.platform == "amazon"
    assert adapter.adapt(listing) == draft
    widened: MarketplaceAdapter[object] = adapter
    assert widened.adapt(listing) == draft


def test_open_platform_and_independent_result_type() -> None:
    adapter: MarketplaceAdapter[tuple[str, str]] = _OtherAdapter()
    assert adapter.platform == "third-party-store"
    draft = adapter.adapt(Listing(title="Trowel", description="Tool", language="en"))
    assert_type(draft, tuple[str, str])
    assert draft == ("Trowel", "Tool")


def test_validation_belongs_to_adapter() -> None:
    adapter: MarketplaceAdapter[_ExampleDraft] = _ExampleAdapter()
    assert (
        adapter.adapt(Listing(title="x" * 12, description="Tool", language="en")).title == "x" * 12
    )
    listing = Listing(title="x" * 13, description="Tool", language="en")
    with pytest.raises(ValueError, match="test_title_limit"):
        adapter.adapt(listing)
    assert listing.title == "x" * 13


def test_protocol_has_no_publishing_or_target_context_contract() -> None:
    public = {name for name in vars(MarketplaceAdapter) if not name.startswith("_")}
    assert public == {"platform", "adapt"}

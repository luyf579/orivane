"""Data validation only; ingestion, generation and publication belong to callers."""

from typing import Annotated, Protocol, TypeVar

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, JsonValue, StringConstraints


def _attribute_key(value: str) -> str:
    if value != value.strip():
        raise ValueError("Attribute keys must not have surrounding whitespace")
    return value


_Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_Key = Annotated[str, StringConstraints(min_length=1), AfterValidator(_attribute_key)]
_DraftT_co = TypeVar("_DraftT_co", covariant=True)


class Product(BaseModel):
    """Supplied facts for one selected configuration, including incomplete input.

    Assignment is validated; nested mutable attributes require revalidation after
    edits. No identity, provenance, catalog family or commercial offer is implied.
    """

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )

    name: _Text
    brand: _Text | None = None
    description: _Text | None = None
    features: tuple[_Text, ...] = Field(default=(), strict=False)
    attributes: dict[_Key, JsonValue] = Field(default_factory=dict)
    category: _Text | None = None
    target_audience: _Text | None = None
    language: _Text | None = None


class Listing(BaseModel):
    """Immutable presentation content, without platform or publishing metadata."""

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid", hide_input_in_errors=True)

    title: _Text
    description: _Text
    language: _Text
    bullet_points: tuple[_Text, ...] = Field(default=(), strict=False)
    keywords: tuple[_Text, ...] = Field(default=(), strict=False)


class MarketplaceAdapter(Protocol[_DraftT_co]):
    """Validate known target constraints and return an offline, adapter-owned draft.

    Target context belongs to the implementation's constructor. This contract
    neither publishes nor guarantees remote platform acceptance.
    """

    @property
    def platform(self) -> str: ...

    def adapt(self, listing: Listing) -> _DraftT_co: ...

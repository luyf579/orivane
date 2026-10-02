# Commerce domain v0

The experimental `orivane-commerce` source package, import `orivane_commerce`,
version 0.1.0, provides platform-neutral domain models and an adapter contract.
It was published on [PyPI](https://pypi.org/project/orivane-commerce/0.1.0/)
on 2026-10-02. [ADR-0006](../adr/0006-commerce-domain-v0.md) is
Accepted; the [research report](../research/commerce-domain-design.md) preserves
historical design evidence.

## Product and Listing

Product represents supplied source facts for one selected configuration. It has
one required field, `name`, and optional `brand`, `description`, `features`,
`attributes`, `category`, `target_audience`, and `language`. Optional strings default
to None, features to (), and attributes to an independent empty dict. Category and
audience are supplied descriptions, not platform taxonomy IDs or inferred claims.

Listing is a separate presentation artifact: required title, description, language;
optional bullet_points and keywords as tuples. Generated titles must not replace
Product.name to disguise generated content as source facts. Listing has no
attributes, platform metadata, variants, price, inventory, or media.

Both use Pydantic v2, reject extra fields, and require strict string values. Text
is stripped at its ends, then rejected if empty. Case, internal whitespace, ordering,
and duplicates are preserved. Python sequence inputs normalize to tuples; JSON
arrays restore as tuples. There is no default language, SEO rewriting, sorting,
deduplication, platform truncation, or language-tag registry.

Top-level attribute keys must be non-empty strings without leading or trailing
whitespace. `Color` and `Product Type` are valid; ` Color`, `Color `, and whitespace-only
keys are rejected. Do not strip or lowercase keys: rejection prevents accidental
whitespace and silent collisions. Preserve case and legal internal whitespace.
Nested JSON object keys follow JSON's string-key rule, including an empty string;
the stricter attribute-name rule applies to top-level fact names only.
Values use the official Pydantic JsonValue and reject non-finite numbers, bytes,
Path, handles, arbitrary objects, and non-string keys without coercing them to JSON.
JSON validation checks shape, not truth, units, or platform suitability.

Product is not frozen; field assignment revalidates. In-place nested mutations are
not intercepted. After editing, create a fresh validated snapshot using
`Product.model_validate(product.model_dump())` before use/export. Do not rely on
validating an existing model instance to revalidate its contents. Avoid shared
mutable Product objects across concurrent application runs. Listing's scalar/tuple
fields and frozen configuration prohibit ordinary field assignment/deletion.
Revisions construct a new validated Listing; unchecked model construction/copying
is outside the validation contract.

## Single-configuration example

```python
from orivane_commerce import Listing, Product

product = Product(
    name="Hand Trowel",
    description="A hand tool for garden planting.",
    features=("Steel head", "Wood handle"),
    attributes={"length": {"value": 28, "unit": "cm"}},
    category="Gardening",
)
listing = Listing(
    title="Hand Trowel with Wood Handle",
    description="A garden planting tool with a steel head and wood handle.",
    language="en",
    bullet_points=("Steel head", "Wood handle"),
    keywords=("garden planting",),
)
assert Product.model_validate_json(product.model_dump_json()) == product
assert Listing.model_validate_json(listing.model_dump_json()) == listing
```

The example manually constructs content; no agent or generation function is implied.
`Product(name="Example")` is valid incomplete input. A blue, size-L T-shirt can
be represented by attributes on a selected Product; this does not define SKU
identity, available combinations, or a variant family. These remain deferred.

## Adapter contract

```python
from dataclasses import dataclass

from orivane_commerce import Listing, MarketplaceAdapter


@dataclass(frozen=True)
class ExampleDraft:
    title: str
    bullets: tuple[str, ...]


class ExampleAdapter:
    platform = "example-store"

    def adapt(self, listing: Listing) -> ExampleDraft:
        if len(listing.title) > 80:  # Synthetic example rule, not a marketplace rule.
            raise ValueError("example_title_limit")
        return ExampleDraft(listing.title, listing.bullet_points)


adapter: MarketplaceAdapter[ExampleDraft] = ExampleAdapter()
```

This partial example projects title/bullets only; it intentionally does not map
description, language, or keywords. A real adapter must document that scope and
account for unsupported content rather than promise a lossless universal mapping.
The example is application-owned, not a supplied production adapter.

The Protocol is generic and covariant in its result, with no BaseModel bound:
typed dataclasses, Pydantic models, and other typed drafts are adapter-owned.
`platform` is a read-only Protocol property satisfied by a property or an ordinary
string attribute. No enum, registry, runtime isinstance support, target fields,
base-class inheritance, or plugin discovery is required.

`adapt()` checks known content constraints and transforms into that draft. It is
synchronous and offline. Constructor arguments on the implementation own country,
marketplace, shop, locale, and rule context. Failures can be ValueError or Pydantic
ValidationError; no custom error hierarchy is defined. A successful draft does not
establish remote acceptance. There is no publish/create/update product operation,
ListingPublisher, MarketplaceClient, SDK, or real platform implementation.

## Ingestion and application composition

Manual input and CSV/Excel/PDF/Word/image/URL sources belong to the application
ingestion layer. Parse, normalize, and resolve missing/conflicting facts there,
then create Product. Raw file bytes, document handles, scraper/client objects,
source URLs, and provenance do not become domain fields or attribute payloads.
SourceReference, SourceDocument, and RawProductInput are deferred public types.

An application may compose Product -> Agent/Workflow -> Listing -> adapter-owned
typed draft. Use existing Core APIs with application-owned state if needed; Commerce
imports no Core, backend-pydantic, CLI, or PydanticAI. No Listing Agent, prompt,
workflow change, or model selection is implemented by this package.

## Serialization and privacy

Valid, normalized Product and Listing values have tested JSON round-trip equality.
This does not preserve source-document bytes or claim a versioned persistence format.
The generic adapter's behavior is not serializable data. Each adapter owns its
draft's format and serialization policy; consumers must not assume BaseModel methods
exist on every DraftT.

Commerce installs no logging, tracing, or exporter. Full model dumps, descriptions,
features, keywords, attributes, and provenance must not be automatically added to
[structural telemetry](observability.md). Error strings and structured validation
errors can expose values or attribute keys; `hide_input_in_errors` is not a universal
redaction system. Host instrumentation remains the application's responsibility.

## Tests and deferred scope

Workspace tests cover normalization, missing/extra fields, mutable isolation,
invalid JSON data, non-finite numbers, immutable Listing behavior, JSON round-trips,
typed structural adapter assignment, and import boundaries. The packaging checker
includes commerce wheel/sdist metadata, py.typed, and installed import smoke tests.
The first implementation keeps the existing 100% statement/branch coverage gate.

Full families, publishing, marketplace APIs, ingestion parsers, agents, inventory,
orders, advertising, and customer support remain deferred. Platform observations
in research are not Orivane support guarantees.

# ADR-0006: Commerce domain v0

Status: Accepted

Date: 2026-09-28

Accepted by the Maintainer for Phase 2C implementation, with the Phase 2C-R1
attribute-key contract refinement. This decision supersedes the earlier Phase 2B API sketch;
the [research report](../research/commerce-domain-design.md) retains its historical
observations. The [commerce architecture](../architecture/commerce.md) describes
the actual contract and examples.

## Context

Manual and file-driven applications need a shared representation for supplied
product facts and generated content. Core is a generic runtime; the domain can
remain independent of it. Platform schemas differ beyond content preparation.

## Goals

Provide exactly three public concepts with strict validation, typed offline adapter
replacement, and tested JSON round-trips for Product and Listing. Preserve all
existing runtime APIs and the current 0.1.0 monorepo version.

## Non-goals

No real marketplace adapters, publishing, Listing Agent, ingestion parser, variant
family, inventory, offers, orders, plugin discovery, or network calls.

## Domain boundaries

Application ingestion -> Product -> application generation/review -> Listing ->
MarketplaceAdapter -> adapter-owned typed draft. Source files/provenance and
publication live outside these data models. Core and all existing runtime types
remain unaware of commerce.

## Product

Use a mutable Pydantic BaseModel with strict validation, extra fields forbidden,
assignment validation, and finite JSON values. Required: name only. Optional:
brand, description, category, target_audience, language (None); features (tuple);
attributes (independent dict using the public Pydantic JsonValue).

Strip text and reject empty/whitespace-only supplied strings; preserve case and
sequence order/duplicates. Top-level attribute keys must be non-empty strings
without leading or trailing whitespace. Reject surrounding whitespace rather than
strip it, avoiding both accidental whitespace and silent key collisions. Preserve
case and legal internal whitespace; do not lowercase keys. Nested JSON string keys
retain JSON semantics. Neither keys nor values encode a
platform payload vocabulary. Unknown facts remain unknown.

Assignment validation does not intercept nested mutations; callers create a fresh
validated snapshot after editing. Source facts and generated copy remain distinct.
The accepted name is description, not the former source_description sketch; id is
not a Product field. Category/audience are supplied descriptive facts, not inferred
claims or platform taxonomy IDs.

## Listing

Use a frozen Pydantic model, extra fields forbidden. Required: title, description,
language. Optional: bullet_points and keywords, both tuples. All strings strip and
must remain non-blank. No metadata, attributes, SKU, price, inventory, or media.
Immutable scalar/tuple values prevent ordinary nested mutation of content. Revisions
construct a new validated Listing, without unchecked copy/construction shortcuts.

## Marketplace abstraction

Use an open platform string. Do not create a Marketplace type, enum, or registry.
The implementation constructor owns marketplace/site/shop/locale context; the
generic Protocol has none of those properties. Output language is separate.

## Adapter boundary

MarketplaceAdapter is a synchronous structural Protocol, covariant in an unbounded
DraftT. Its complete surface is a read-only platform: str property and
adapt(listing: Listing) -> DraftT. There is no runtime_checkable decorator.

An implementation validates known target content constraints and transforms into
its own typed draft. Dataclasses and Pydantic models are both permitted: DraftT is
not constrained to BaseModel. Draft serialization belongs to that implementation;
there is no universal MarketplaceDraft/MarketplaceListing/AdapterResult wrapper.
This supersedes the Phase 2B transform method and BaseModel-bound result sketch.

Use ordinary ValueError or Pydantic ValidationError for failures. Document the
supported content/rule scope; a successful draft never promises remote acceptance.
No platform rule enters Core, Product, or Listing. Private test/example adapters
exercise synthetic rules only; none is a production integration or public export.

## Why publishing is deferred

No real client lifecycle, idempotency, remote errors, or interchangeable publishing
implementation exists. Defer ListingPublisher/MarketplaceClient and all publishing
methods rather than attach speculative side effects to a pure transformation.

## Why ingestion is separate

Manual input and CSV/Excel/PDF/Word/image/URL readers produce the same Product after
parsing/correction. Raw bytes, document handles, source URLs, scraper/client objects,
and provenance remain application-owned. No public ingestion types or parser
dependencies are introduced.

## Validation model

Use existing Pydantic v2, not a new schema system. Reject malformed strings, extra
fields, non-JSON objects, non-string keys, and non-finite numbers at validation.
Tuple fields accept sequence inputs and restore from JSON arrays. Valid normalized
Product and Listing values must round-trip equally through their JSON methods.
Schema validity is not factual verification or marketplace compliance.

Commerce adds no logging. Content, model dumps, and full validation exceptions must
not enter automatic structural telemetry. See [observability](../architecture/observability.md).
Mutable bypasses, unchecked construction, persisted schema migration, and arbitrary
host instrumentation are outside the validation/privacy guarantee.

## Dependency direction

The fourth monorepo package is packages/commerce, distribution orivane-commerce,
import orivane_commerce. Production dependency: pydantic>=2.12,<3 only. No Core,
backend-pydantic, CLI, PydanticAI, platform SDK, or new third-party dependency.
Use the existing locked versions without external drift. Any later Core-dependent
integration requires a separate decision; applications compose both packages today.

## Public API budget

Exactly Product, Listing, MarketplaceAdapter in __all__. No public helpers, aliases,
draft wrappers, mock adapters, exception hierarchy, or extra domain classes.

## Examples

An incomplete Product with only a name is valid. A t-shirt with color=blue and size=L
describes one selected configuration, not a variant family. A garden trowel example
illustrates source facts and separate content. Tests use an application-owned frozen
dataclass result to verify static Protocol assignment and a synthetic adapter limit.

## Future evolution

Defer full variant families, publishing/client contracts, ingestion abstractions,
agents, inventory, orders, advertising, and customer service until concrete scope
and replacement needs justify them. Current Workflow requires no change; applications
can compose it around these data structures using their own state.

## Open questions

The implementation choices above are settled for Phase 2C. Future work still needs
real input fixtures, the first parser format, a precise target/rule revision, and
separate decisions on complete families and publication. Exact TikTok Shop API
compatibility remains unverified. None of those is implicitly delivered by v0.

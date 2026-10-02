# Commerce domain design research

Status: Design research; proposed APIs only

Date: 2026-09-28

Baseline: `701ba7b9e019526824e27d815de0d75cba89d76b` (Orivane 0.1.0).
See [ADR-0006](../adr/0006-commerce-domain-v0.md) for the proposed decision.
No model, adapter, agent, parser, or test implementation is included in this phase.


## Phase 2C accepted implementation decisions

The sections below preserve the Phase 2B research and proposal, not the final API.
Maintainer approval for Phase 2C selects Product.description (no id or
source_description), adds optional category/target_audience as supplied facts, and
selects MarketplaceAdapter.platform plus synchronous adapt(listing). DraftT is
unbounded so adapter-owned dataclasses are supported; no BaseModel-only result
contract remains. Phase 2C-R1 rejects surrounding whitespace in top-level attribute
keys rather than stripping it; valid case and internal whitespace are preserved.
This refines the initial implementation without changing the historical research. Commerce depends directly on Pydantic only, with no Core/backend edge.
See the [accepted ADR](../adr/0006-commerce-domain-v0.md) and
[implemented contract](../architecture/commerce.md). Observed platform facts below
remain research observations, never Orivane support or acceptance guarantees.

## Evidence method and limits

Only public official documentation was read. No seller login, account creation,
credential use, marketplace API call, live payload validation, or publishing was
performed. The examples below use invented, non-sensitive product data.

The three labels below distinguish platform observations from design judgments and
our own suggested API. A paper fit is not a successful platform integration. Links
were accessed on the date above; current platform requirements must be checked again
for a concrete implementation, target, category, and schema revision.

## OBSERVED PLATFORM FACT

### Source register

| ID | Official source | Scope observed |
| --- | --- | --- |
| A1 | [Amazon: Manage Product Listings](https://developer-docs.amazon.com/sp-api/docs/manage-product-listings-guide) | Example product attributes and separate offer, image, and variation information. |
| A2 | [Amazon: Product Type Definitions API](https://developer-docs.amazon.com/sp-api/docs/product-type-definitions-api) | JSON Schema requirements and version/context dependence. |
| A3 | [Amazon: Retrieve a Product Type Definition](https://developer-docs.amazon.com/sp-api/lang-en_EN/docs/retrieve-a-product-type-definition) | Marketplace, product type, locale, and parentage-specific schema context. |
| S1 | [Shopify: ProductCreateInput](https://shopify.dev/docs/api/admin-graphql/latest/input-objects/productcreateinput) | Content, category, vendor, options, tags, and SEO input fields. |
| S2 | [Shopify: ProductVariant](https://shopify.dev/docs/api/admin-graphql/latest/objects/ProductVariant) | Options and variant-specific commercial data. |
| T1 | [TikTok Shop US Academy: Listing and Managing Products](https://seller-us.tiktok.com/university/course?content_id=7073362639816491&learning_id=6037851293763342) | US seller-facing listing concepts, including variations. |
| T2 | [TikTok Shop US Academy: Product Detail Pages and Listing Quality](https://seller-us.tiktok.com/university/essay?knowledge_id=481891871868714) | Content quality and category information; not an API field schema. |
| T3 | [TikTok Shop Partner Center: Create Product](https://partner.tiktokshop.com/docv2/page/create-product-202309) | Access limitation: only a JavaScript application shell was readable. |

Shopify's versioned 2026-07 object URL redirected to `latest`, whose page displayed
2026-07. This is a dated observation of that reference, not a pinned future schema.
TikTok GO Dining's product documentation was excluded because it describes a
different product/service. T3's inaccessible body is not evidence for exact field
names, types, requiredness, limits, or API compatibility.

### Platform comparison

| Concern | Amazon | Shopify | TikTok Shop |
| --- | --- | --- | --- |
| Content | A1 shows `item_name`, `bullet_point`, `product_description`. | S1 has `title` and HTML `descriptionHtml`. | T1/T2 describe title, description, images, and category information. |
| Classification | A2/A3 requirements depend on product type and marketplace context. | S1 distinguishes taxonomy category ID from merchant-defined `productType`. | T1 discusses category selection and brand information. |
| Search metadata | A1's example does not establish one universal search field. | S1 separates `tags` from `seo` title/description. | No exact API search/keyword field verified. |
| Variations | A3 distinguishes parent, child, and standalone schema contexts. | S2 links option selections to variants with SKU, price, inventory, and media. | T1 describes size/color choices as SKUs under a common product. |
| Beyond copy | A1 separates offers, images, and relationships from descriptive attributes. | S1/S2 include more than copy, including category and commercial variant data. | T1/T2 include media and category/variation requirements beyond copy. |

Amazon's documentation also describes a custom vocabulary extending JSON Schema;
a generic Pydantic model is not a replacement for its complete validation system.
[Source A2](https://developer-docs.amazon.com/sp-api/docs/product-type-definitions-api).

### Supporting technology facts

Pydantic BaseModel exposes validation, JSON serialization, and JSON Schema methods;
its frozen option blocks ordinary attribute assignment but does not freeze contained
dictionaries. [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/).
Pydantic dataclasses can validate data; TypeAdapter supplies their schema and JSON
operations. [Pydantic dataclasses](https://docs.pydantic.dev/latest/concepts/dataclasses/).
JsonValue describes recursive JSON-shaped data. It does not define product semantics.
[Pydantic JsonValue](https://docs.pydantic.dev/latest/api/types/#pydantic.types.JsonValue).

The repository's Core manifest already accepts `pydantic>=2.12,<3`; the unchanged
lock resolves 2.13.5. Core's [contracts](../architecture/backend-contract.md) and
[Workflow](../architecture/workflow.md) already support application-owned data types.
These are local code observations, not platform claims.

## DESIGN INFERENCE

### Scope that survives the comparison

Use a content-preparation boundary for a single known configuration. Product is
supplied information; Listing is editable-by-replacement output copy; an adapter
creates an offline content projection. None claims catalog completeness.

The naive Product -> Listing -> publish abstraction breaks on required category
context, media, seller offers, and family relationships. Adding all of these to
Listing would turn a small content model into an incomplete universal seller API.
Keep these gaps explicit rather than encoding platform dictionaries in `metadata`.

### Product field decisions

| Candidate | v0 decision | Reason and meaning |
| --- | --- | --- |
| id | Optional string | Caller identity; not automatically SKU, ASIN, or a global platform ID. No database uniqueness check. |
| title/name | Required `name` | A non-blank supplied name is the minimum useful input. Generated `title` belongs to Listing. |
| brand | Optional string | `None` means unknown, not an assertion of no brand. |
| description/source_description | Optional `source_description` | Supplied plain text, not an original file or proof that statements are true. |
| features | Optional tuple of strings | Supplied factual statements, kept distinct from generated selling points. |
| attributes | Optional `dict[str, JsonValue]` | Retain category-specific facts without a new attribute type system; JSON-compatible values, finite numbers, string keys. |
| dimensions | No first-class field | Use known facts with explicit units, e.g. `{"height": {"value": 12, "unit": "cm"}}`; no automatic unit conversion. |
| materials | No first-class field | A known materials fact can be a JSON string/list; do not infer composition. |
| target_audience | No first-class field | Inference stays in workflow scratch state; explicitly supplied intended-use facts may be attributes. |
| category | No first-class field | A source category label may be an attribute; platform taxonomy/type IDs are adapter context. |
| language | Optional string | Source language may be unknown. Use language tags by convention, not a marketplace enum. |
| source_metadata | Excluded | Provenance stays with the application ingestion record. |
| variants | Excluded family structure | One selected configuration per Product; unresolved family input must remain outside the domain boundary. |
| image/file/URL | Excluded | Parsing inputs and provenance references belong to ingestion. Do not insert bytes or URLs as a raw-document escape hatch. |

Missing keys mean not supplied; explicit JSON null represents a supplied unknown.
Neither means zero, false, or an empty material/brand. Conflicting facts need user
correction, not silent last-value-wins merging. String keys and JSON values enforce
shape, not vocabulary, truth, or marketplace suitability. Attribute dictionaries
are intentionally limited in purpose; they do not silently add variant support.

Product may be corrected between runs. Assignment validation does not validate an
in-place mutation to a nested dict/list. Reconstruct through validation at each
ingestion/run boundary and use an independent snapshot per run. No frozen mapping
library, generic facts registry, or custom schema language is warranted in v0.

### Listing field decisions

| Candidate | v0 decision | Reason |
| --- | --- | --- |
| title | Required non-blank string | Human-facing output, distinct from source name. |
| description | Required non-blank plain text | A complete content result needs a description; incomplete work remains application state. |
| bullet_points | Tuple of non-blank strings, default empty | Stable order and no in-place list mutation; no global bullet count or length. |
| keywords | Tuple of non-blank strings, default empty | Editorial suggestions; no SEOKeywords class or implied ranking guarantee. |
| attributes | Defer | Facts remain Product data; generated claims must be checked against them. No generic structured catalog output promised. |
| language | Required non-blank language tag | Output language must be explicit; do not silently guess from marketplace. |
| platform metadata | Excluded | Adapter draft/configuration owns platform fields; extra model fields rejected. |

Make Listing frozen. All current value fields are immutable strings/tuples, so
ordinary API usage cannot mutate nested content. Python's deliberate bypasses and
unvalidated construction/copying are outside that guarantee. Validate replacements;
do not use unchecked `model_construct` or assume `model_copy(update=...)` validates.

Strict Product/Listing separation allows many language or channel drafts from one
source and prevents generated claims from being fed back as source facts. Association
with Product IDs or file provenance is the application's job; no unused public
ListingBatch, Result, or SourceReference envelope is introduced.

### Marketplace representation alternatives

| Choice | Tradeoff | Recommendation |
| --- | --- | --- |
| Marketplace class | Would soon accumulate shop, region, locale, auth, and rules. No demonstrated common lifecycle. | Defer. |
| Closed enum | Discoverable names, but every third-party platform requires a base-package release. Country combinations grow quickly. | Reject for v0. |
| Open platform string plus separate target context | Extensible; an adapter checks the target identifiers it understands. | Choose. |

Use `amazon`, `shopify`, or `tiktok-shop` as application labels. Keep an Amazon
marketplace ID or a shop ID opaque and scoped to that adapter. `amazon-us` can be a
UI alias, not a string parser with hidden locale defaults. US/UK/JP targeting and
English/Japanese copy are independent choices. Language tags, schema locales, and
market IDs are not interchangeable. No public Marketplace class or registry follows.

### Adapter responsibility and output alternatives

| Responsibility | Benefit / failure mode | Decision |
| --- | --- | --- |
| A: transform only | Simple, but can knowingly emit content invalid for its configured target/rules. | Too weak once target rules are claimed. |
| B: transform plus scoped validation | Mapping and local rules share context; deterministic offline checks are possible. | Choose; document precisely what is checked. |
| C: transform plus publish | Couples conversion to authentication, remote state, retries, and resource ownership. | Defer publishing entirely. |

For B, validate domain structure and the adapter's documented local content rules;
then construct a typed draft. Do not fetch schemas over the network. Any future
offline rule material must be deliberately supplied and tied to its source revision,
product type/category, target, and language. A mock profile validates only synthetic
rules. Passing it does not establish compliance with current platform requirements.

Failures use ordinary ValueError with a safe static category in the mock contract.
No public exception hierarchy or validation-report protocol is needed. Report all
unsupported fields/context explicitly to the caller, either by refusal or a
documented adapter-owned draft field. Never silently truncate, translate, erase
keywords, invent facts, or infer missing category/variant/offer information.

| Output | Typing | Extension and third parties | Serialization / future integration |
| --- | --- | --- | --- |
| `dict[str, JsonValue]` | JSON shape only; misspelled fields pass static checks. | Very easy to extend, easy to produce undocumented shapes. | Convenient JSON; future code must rediscover the schema. |
| Typed platform dataclass | Good field typing. | Ordinary Python; can use TypeAdapter without a new framework. | Viable, but callers need a separate serialization adapter. |
| Generic MarketplaceListing | Only useful with a generic payload or a growing union. | Makes the base package own unrelated platform details. | Moves rather than resolves schema/version differences. |
| Adapter-owned Pydantic model via generic result type | Concrete callers retain exact fields. | Structural Protocol; each adapter owns and can evolve its schema. | Choose; standard JSON methods and explicit later payload assembly. |

The generic result parameter expresses a real observed difference: Amazon-like
attribute copy and Shopify-like HTML content are different shapes. An unused
universal payload/extension registry would not improve that typing.

### Validation choice

| Model technology | Schema and validation | Ergonomics and interoperability |
| --- | --- | --- |
| Stdlib dataclass alone | Annotations are not an input validator; manual validation/schema work remains. | Small internal state records are a good use; external normalized data needs more. |
| Dataclass plus Pydantic TypeAdapter | Existing validation/schema/JSON tooling; no invented schema engine. | Viable alternative, with an extra adapter at common I/O call sites. |
| Pydantic BaseModel | Existing field validation, schema, and JSON methods on the type. | Choose for Product, Listing, and adapter drafts; familiar to existing Orivane consumers. |

Commerce's direct Pydantic use must be declared directly in its future manifest.
It is a validation dependency, not a PydanticAI backend dependency. The current Core
uses dataclasses for internal contracts; that does not require external commerce
input models to copy that choice.

### Ingestion, variants, and agent boundary

Manual fields and parsed file fields converge on the same Product validation.
An application keeps a private provenance record associating the run/product with
source document, page/cell, URL, and unresolved facts. No shared RawProductInput,
SourceDocument, SourceReference, file parser, or plugin API is proposed yet.
For the first B-input implementation, choose one explicit file format and fixture;
this design does not promise simultaneous Excel/CSV/PDF/Word support.

For size/color families, a caller selects or explicitly enumerates known concrete
configurations outside Product and copies only facts known to hold for each. It
must not generate a size x color cartesian product or publish separate listings as
a substitute for platform family relationships. The family remains unsupported.
A list of Product objects is content batching, not a variation-family schema.

The application or a later separately justified workflow layer owns ListingAgent,
prompts, backend selection, self-check, and human review. A content model neither
calls an LLM nor decides when a factual claim is safe to publish.

## PROPOSED ORIVANE API

### Model and adapter pseudocode

The following is a design signature sketch, not runnable production code. Recursive
finite-number checks, boundary revalidation, rule profiles, and the test plan below
are requirements for a later implementation; this phase implements none of them.
Private names shown here do not expand the proposed base-package exports.

```python
from typing import Annotated, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints

_Text = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]


class Product(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )
    name: _Text
    id: _Text | None = None
    brand: _Text | None = None
    source_description: _Text | None = None
    features: tuple[_Text, ...] = ()
    attributes: dict[str, JsonValue] = Field(default_factory=dict)
    language: _Text | None = None


class Listing(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    title: _Text
    description: _Text
    language: _Text
    bullet_points: tuple[_Text, ...] = ()
    keywords: tuple[_Text, ...] = ()


_DraftT_co = TypeVar("_DraftT_co", bound=BaseModel, covariant=True)


class MarketplaceAdapter(Protocol[_DraftT_co]):
    def transform(self, listing: Listing, /) -> _DraftT_co: ...
```

Exactly three proposed exports: Product, Listing, MarketplaceAdapter. The private
text alias means non-blank strict text, not a general language-tag validator.
Ingestion normalizes external forms; no lossy scalar coercion is permitted in facts.
Language-tag validity and target compatibility require the intended adapter profile.
Empty optional text should be normalized deliberately to absence by ingestion;
non-empty strings are otherwise stripped only at their outer whitespace boundaries.

The proposed JSON contract uses `model_validate_json` and `model_dump_json` on
validated, normalized models. Python tuple/list differences in input are allowed
normalization for sequence fields, not a loss of content. Reject NaN/Infinity at all
depths rather than serializing them as null. Do not assume one configuration flag
alone proves recursive JSON validity; make that an explicit implementation test.

Model methods can be bypassed and Product's nested facts can be mutated. Revalidate
a plain-data snapshot before each run/export and avoid concurrent shared mutation.
Only valid domain values are covered by the round-trip promise. No file handles,
database connections, API clients, LLM objects, dates, Decimal objects, or raw bytes
belong inside JsonValue; ingestion must choose explicit JSON representations where
appropriate instead of relying on arbitrary-object serialization.

### Mock adapter sketches and content projections

AmazonMockAdapter and ShopifyMockAdapter are example names, not classes created by
this task. They structurally satisfy MarketplaceAdapter without inheritance.
Constructor details are adapter-owned. A future optional package such as
`orivane-commerce-amazon` could use the same contract through a normal explicit
import; installation alone does not register or execute anything.

| Mock | Draft shape (adapter-owned Pydantic model) | Local transformation contract |
| --- | --- | --- |
| AmazonMockAdapter -> `_AmazonContentDraft` | `marketplace_id`, `product_type`, `language`, `item_name`, `bullet_point`, `product_description`, `keyword_suggestions` | Title/bullets/description become copy fields; target and product type come from explicit construction context. Preserve keyword suggestions. |
| ShopifyMockAdapter -> `_ShopifyContentDraft` | `language`, `title`, `description_html`, `keyword_suggestions` | Escape plain description into paragraphs and bullets into an HTML list; keep title and keyword suggestions. |

Example shared input, using invented data (constructors only, no execution):

```python
product = Product(
    id="CASE-01",
    name="Travel organizer case",
    features=("Zip closure",),
    attributes={"color": "blue", "height": {"value": 12, "unit": "cm"}},
    language="en-US",
)
listing = Listing(
    title="Blue travel organizer case",
    description="A blue organizer case with a zip closure.",
    language="en-US",
    bullet_points=("Zip closure", "Height: 12 cm"),
    keywords=("travel organizer",),
)
```

In the Amazon-like paper projection, `item_name` is the title, `bullet_point` retains
both bullets, and `product_description` retains the plain description. A caller
would have to supply an appropriate product type and market; none is inferred from
the name. This flat draft is not the actual nested Amazon attributes representation.

In the Shopify-like paper projection, `description_html` would contain the escaped
description paragraph followed by two list items. Input such as `<script>` must be
rendered as text, not copied as executable markup. Keyword suggestions are not
silently applied as store tags or SEO metadata; those choices require caller policy.
`language` and `keyword_suggestions` are local draft fields, not claimed GraphQL keys.

Every Listing field is either represented or explicitly preserved as a suggestion.
There is no brand/category extraction from text, price/stock default, image upload,
variant grouping, or publishable payload. Real rule limits are absent; any future
mock title/bullet boundary test uses a clearly synthetic rule, never a claimed
current Amazon/Shopify constraint.

### Application workflow pseudocode

This sketch uses Core's actual same-T signatures. Bodies are deliberately omitted:
they are application work, not domain primitives or production ListingAgent code.

```python
from dataclasses import dataclass

from orivane_core import Workflow


@dataclass
class _ListingWork:
    product: Product
    output_language: str
    extracted_features: tuple[str, ...] = ()
    audience_hypothesis: str | None = None
    listing: Listing | None = None
    needs_review: bool = True


async def understand(s: _ListingWork) -> _ListingWork: ...
async def extract_features(s: _ListingWork) -> _ListingWork: ...
async def target_audience(s: _ListingWork) -> _ListingWork: ...
async def draft_listing(s: _ListingWork) -> _ListingWork: ...
async def self_check(s: _ListingWork) -> _ListingWork: ...
async def stop_for_review(s: _ListingWork) -> _ListingWork: ...
async def accept(s: _ListingWork) -> _ListingWork: ...


async def prepare(product: Product, output_language: str) -> Listing:
    flow = (
        Workflow[_ListingWork]()
        .then("understand", understand)
        .then("extract_features", extract_features)
        .then("target_audience", target_audience)
        .then("draft_listing", draft_listing)
        .then("self_check", self_check)
        .branch(
            "review_gate",
            lambda s: s.needs_review,
            if_true=stop_for_review,
            if_false=accept,
        )
    )
    result = await flow.run(_ListingWork(product, output_language))
    assert result.listing is not None
    return result.listing
```

`self_check` sets `needs_review` when claims lack support, information conflicts,
or output structure is incomplete. `stop_for_review` raises a safe ordinary
application error and returns no Listing; it is not a durable wait or retry loop.
`accept` returns the same state after its Listing is valid. Backend calls, if later
needed, live in application closures through existing AgentBackend/RunRequest.
Every step receives and returns `_ListingWork`, and the branch predicate is
synchronous. Nothing assumes that Workflow can change T from Product to Listing.

### Paper scenarios: three products across three targets

These are analytical outcomes, not executable tests or platform acceptance results.

| Product | Amazon-like marketplace | Shopify-like storefront | TikTok-Shop-like content commerce |
| --- | --- | --- | --- |
| A: one known configuration of a travel case; closure/color/height known | Copy fits a flat draft. Real type schema, catalog identifiers, media, and offer context are missing: not publishable. | Copy and escaped HTML fit. Vendor/category/options/commercial setup are not supplied: not a complete product input. | Title/description can be prepared. Category and matching media still need a separate process; exact API shape unverified. |
| B: shirt offered in blue/red and S/M; only three combinations actually exist | Per-configuration copy fits; parent/child family relationships cannot be represented. Do not invent a fourth SKU. | Per-configuration copy fits; option/variant associations and per-variant commercial data cannot be assembled. | Copy for one selected SKU fits conceptually; a grouped variation listing, media associations, and API representation remain unsupported. |
| C: name supplied, material/size/brand unknown | Product accepts unknowns; either conservative copy or human correction. Full schema validation cannot be claimed. | Product accepts unknowns; no fabricated vendor/material/size, and no automatic metadata assignment. | Product accepts unknowns; avoid unsupported claims. Content/category/media review remains necessary. |

A name-only Product is structurally valid but does not force the application to
generate a useful final Listing. If the name itself is absent/blank, keep the input
in ingestion for correction; do not manufacture a placeholder product identity.

Counterexamples that bound the recommendation:

1. Requiring an SKU/brand on Product rejects legitimate manual drafts too early.
2. A single `variants: dict` cannot encode shared/per-SKU facts, allowed combinations,
   and platform relationships safely; family publication needs a new design.
3. Copying Listing keywords into Shopify SEO loses the distinction between editorial
   suggestions and a title/description pair. Keep them separate.
4. Passing Product attributes straight to Amazon assumes its schema vocabulary,
   context, and nesting. An adapter content draft makes no such claim.
5. Passing uploaded file objects through Product prevents portable JSON and resource
   ownership. Keep parsing outside the domain model.
6. A public ListingPublisher today would specify remote lifecycle and failures with
   no implemented behavior to compare. Defer it.

### Future test/spec plan (not executed in Phase 2B)

| ID | Fixture or action | Required acceptance observation |
| --- | --- | --- |
| D01 | Minimal name-only Product; absent and explicit unknown facts | Accepted without fabricated ID, brand, values, or platform defaults; blank name rejected. |
| D02 | Manual form and one approved uploaded-document fixture with equivalent facts | Both yield equivalent Product data; provenance stays outside. Conflicts require correction. |
| D03 | String/number/bool/null/nested JSON, Unicode, and units | Normalized Product JSON round-trip preserves values/types and meaning of missing/null. |
| D04 | Bytes, objects/clients, non-string keys, nested NaN/Infinity | Rejected; no automatic serialization of resources or silent conversion to null. |
| D05 | Corrected Product with a nested invalid mutation | A fresh run/export revalidates and rejects it; two independent run snapshots do not share mutable facts. |
| D06 | Listing missing description/language; tuple JSON round-trip; attempted mutation | Invalid output rejected; valid ordering retained; ordinary field assignment and sequence mutation disallowed. |
| D07 | Unexpected model fields and attempted platform metadata on Listing | Rejected; no silent acceptance/dropping of platform payloads. |
| A01 | Two mock adapters against the same Listing | Deterministic typed drafts; no network, filesystem, or mutation; concrete result type retained by static checking. |
| A02 | Unsupported target/language/context and synthetic local-rule boundaries | Explicit safe failure; no silent default, truncation, or translation; synthetic rules labelled clearly. |
| A03 | HTML special characters, bullets, keywords | Shopify mock escapes text; both mocks account for every content field; keywords not mislabelled as SEO metadata. |
| A04 | A third-party structural adapter with its own BaseModel draft | Fits the Protocol without inheritance, registration, package scanning, or backend imports. |
| V01 | Three known shirt configurations out of a possible four | Content only for explicit configurations; no generated cartesian SKU, family publication, or cross-variant fact mixing. |
| W01 | Stub async steps with success, review, error, and cancellation outcomes | Same state type throughout; only selected branch runs; existing Core propagation semantics sufficient. |
| P01 | Sensitive sentinels in Product, Listing, attribute keys, input filenames, and validation failures | No sentinels in complete captured logs/spans, repr, exception messages/events, or schema examples produced by the integration. |
| B01 | Future minimal installation and import graph | No backend-pydantic, PydanticAI, platform SDK, exporter, or parser dependency required for domain import; no reverse Core import. |

Do not create a generic adapter certification framework to run these tests. Start
with concrete fixtures and ordinary unit/type checks in the later implementation.
Do not add new Core tests just to restate unchanged Workflow behavior; a small
application integration test should exercise the proposed same-T composition.

### Privacy and serialization acceptance boundary

Preserve the existing [structural-only policy](../architecture/observability.md).
Models and transformations install no loggers/exporters or automatic dumps. Safe
node names are fixed operational labels; never derive them from product titles,
SKUs, file paths, or attribute names. Validation errors may contain raw input,
arbitrary key paths, or user-authored validator messages. `hide_input_in_errors`
is only defense in depth, not a log-redaction guarantee. Never automatically log
the exception, its structured error collection, or traceback.
[Pydantic error configuration](https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.hide_input_in_errors).

Only data objects (Product, Listing, adapter drafts) need JSON round-trip. The
adapter behavior object and application Workflow do not become serializable domain
objects. Application persistence, secrets handling, and retained source documents
need their own lifecycle and access policy; no storage subsystem is proposed.

### Dependency direction and package planning

Future names are `packages/commerce`, `orivane-commerce`, `orivane_commerce`.
No path/package, manifest, workspace membership, lock entry, or dependency is added
by this design. Core remains domain-neutral; imports must never point from Core
to commerce. Backend selection remains the composition root's concern.

The ideal commerce -> core relationship describes integration direction. For the
three proposed concepts alone, the domain module directly uses only Pydantic and
stdlib typing. Declare Pydantic directly if the package is implemented. Avoid a
mandatory Core dependency solely to obtain a transitive Pydantic installation;
add a direct Core edge only when shipping an actual Core-dependent integration.
Applications can explicitly depend on and compose both. No dependency on the
PydanticAI adapter is warranted in either case.

### Premature abstraction audit and review entry questions

Defer ListingPublisher/MarketplaceClient (no remote behavior to generalize),
Marketplace class/enum (no uniform target semantics), generic MarketplaceListing
(unrelated schemas), SEOKeywords (tuple suffices), CommerceAgent/SEOAgent (application
behavior), VariantGraph (family scope excluded), and Inventory/Order/Advertisement/
CustomerService (outside content preparation). Defer public ingestion types,
Dimensions/Material registries, a rule engine, and plugin discovery until repeated
requirements demonstrate their need.

The design is ready for review, not implementation approval. Review selected-SKU
scope, initial manual/file examples and file format, optional Product fields,
Listing's intentionally absent attributes, the first target/rule profile, and
whether the implementation actually needs a hard Core dependency. Re-read TikTok
Shop's API schema in a separately authorized integration task before promising API
compatibility. No extra class is introduced to conceal these open questions.

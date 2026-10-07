# orivane-commerce

orivane-commerce is an experimental platform-neutral Commerce domain package.
Version 0.2.0; Python 3.11+; MIT. Python 3.11/3.12/3.13 are tested.
This is unreleased development source; the latest published release remains v0.1.1.

The only public concepts are Product, Listing, and MarketplaceAdapter. Pydantic v2
is the only direct dependency. Core, CLI, a model backend, and marketplace SDKs are
not required. Typed distributions include `py.typed`.

Install with:

```powershell
pip install orivane-commerce
```

```python
from orivane_commerce import Listing, Product

product = Product(name="Hand Trowel", attributes={"material": "steel"})
listing = Listing(title="Hand Trowel", description="A steel garden tool.", language="en")
assert Product.model_validate_json(product.model_dump_json()) == product
assert Listing.model_validate_json(listing.model_dump_json()) == listing
```

Product holds supplied facts for one selected configuration; Listing holds separate
presentation content. Ingestion and generation are application responsibilities.
MarketplaceAdapter is a synchronous structural Protocol with a `platform` property
and `adapt(listing)` method returning the implementation's own typed draft.
There are no real marketplace adapters, marketplace publishing, Listing Agent,
variant family, or network calls.

Text values are stripped and must remain non-blank; optional text may instead be
None. Top-level attribute keys must be non-empty strings with no leading or
trailing whitespace. Keys are rejected rather than stripped; case and internal
whitespace are preserved. Values are finite JSON data. Product is mutable with assignment validation, but
nested edits require fresh validation through `Product.model_validate(product.model_dump())`.
Listing is frozen and uses tuples for bullets and keywords. Neither type installs
logging; callers must protect content and validation errors from automatic telemetry.

For local development,
run `uv sync --locked --all-packages` from the monorepo root. This package does not claim marketplace acceptance
or production readiness. The included LICENSE matches the repository MIT license.

The repository's [offline CSV reference example](../../examples/README.md#commerce-csv-reference)
shows application-owned CSV -> Product -> deterministic Listing -> a frozen typed
draft for offline-reference. The parser, adapter and draft are example code,
not package APIs. It uses no model, network or real marketplace publishing;
the only public package concepts remain Product, Listing and MarketplaceAdapter.

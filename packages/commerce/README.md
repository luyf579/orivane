# orivane-commerce

Platform-neutral commerce domain models and marketplace adapter contracts for
Orivane. Version 0.1.0; Python 3.11+; MIT. This is an experimental source package,
not yet published to PyPI; publication is deferred.

The only public concepts are Product, Listing, and MarketplaceAdapter. Pydantic v2
is the only direct dependency. Core, CLI, a model backend, and marketplace SDKs are
not required. Typed distributions include `py.typed`.

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
There are no supplied platform adapters, publisher, variant family, or network calls.

Text values are stripped and must remain non-blank; optional text may instead be
None. Top-level attribute keys must be non-empty strings with no leading or
trailing whitespace. Keys are rejected rather than stripped; case and internal
whitespace are preserved. Values are finite JSON data. Product is mutable with assignment validation, but
nested edits require fresh validation through `Product.model_validate(product.model_dump())`.
Listing is frozen and uses tuples for bullets and keywords. Neither type installs
logging; callers must protect content and validation errors from automatic telemetry.

For local development, run `uv sync --locked --all-packages` from the monorepo root,
or install a locally built wheel. This package does not claim marketplace acceptance
or production readiness. The included LICENSE matches the repository MIT license.

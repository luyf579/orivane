# Offline examples

From the repository root in PowerShell, after `uv sync --locked --all-packages`:

```powershell
uv run --no-sync python examples/01_offline_agent.py
uv run --no-sync python examples/02_session_runtime.py
uv run --no-sync python examples/03_workflow.py
```

Expected stdout respectively: `offline agent`, `offline session`, `offline workflow`.
No API key or network model request is required. These are executed by pytest and
again against installed wheels in a clean environment. They are Ruff/strict-mypy
checked. The first example is the README quickstart; sessions explicitly create and
delete an in-memory session, and the workflow example exercises both branch paths.
The separate local upstream startup banner may appear on stderr; it is not telemetry.

## Commerce CSV reference

Run from the repository root in PowerShell after development setup:

```powershell
uv run --no-sync python examples/04_commerce_csv_pipeline.py examples/data/commerce_products.csv
```

The application example writes deterministic UTF-8 JSONL. It needs only the
standard library and orivane-commerce: no API key, model, network request or
marketplace credential. The sample contains two synthetic, fictional products;
Fable Tools is a fictional brand. Compare stdout byte-for-byte with
[data/commerce_expected.jsonl](data/commerce_expected.jsonl).

The header must contain exactly these columns once each. Order is immaterial;
the canonical sample uses this order:

| Column | Meaning |
| --- | --- |
| name | Required; validated by Product |
| brand | Optional; blank becomes None |
| description | Required for this pipeline |
| features_json | JSON array of strings; blank becomes [] |
| attributes_json | JSON object; blank becomes {} |
| category | Optional; blank becomes None |
| target_audience | Optional; blank becomes None |
| language | Required for this pipeline |

Input accepts UTF-8 with or without BOM, standard CSV quoting and quoted
multiline fields. Bare double quotes in unquoted fields and characters after a
closing quote are rejected. JSON rejects duplicate object keys at every depth,
including objects in arrays, and rejects NaN, Infinity and -Infinity constants.
Product still owns text, attribute-key, JSON-value and finite-number validation.
Brand, category, target audience and attributes remain in Product.

Quote validation and stdlib CSV parsing use the same input text snapshot, read
once. Input and output are buffered in memory; memory grows with both sizes.

Listing projects only name -> title, description -> description,
language -> language, features -> bullet_points; keywords=(). No description,
language, keyword or marketing claim is generated. Missing description/language
fails; the example supplies no fallback.

The frozen application-owned OfflineReferenceDraft maps Listing to headline,
body, locale, bullets and search_terms through a structural MarketplaceAdapter.
offline-reference is a teaching target. It represents no Amazon, Shopify,
TikTok Shop, eBay, Etsy or other marketplace field limits, taxonomy, remote
acceptance or publishing support. These example types and parser are not package
APIs; Commerce still exports only Product, Listing and MarketplaceAdapter.

Each JSONL record has row (logical data row, starting at 1), platform and draft.
JSON uses ensure_ascii=False, sorted keys and compact separators.
All records are parsed, validated and adapted before writing stdout. On input
failure stdout is empty, stderr gives a safe fixed category/optional logical row,
and exit status is 2; raw rows, descriptions, JSON inputs and tracebacks are not
printed. The example emits no logs, traces or telemetry.

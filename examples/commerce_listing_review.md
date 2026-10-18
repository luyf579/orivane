# Offline Listing proposal and human review application

This example is application-owned. The installable Core, Backend, CLI and
Commerce packages, public exports, dependencies, lockfile and workflows remain
unchanged. All products in the supplied input are fictional.

## What the offline modes prove

| Mode | Composition | Evidence |
| --- | --- | --- |
| fake | ListingGenerationService → AgentBackend protocol → DeterministicFakeBackend | Repeatable projection and controllable failure, invalid output and cancellation |
| test-model | ListingGenerationService → AgentBackend protocol → existing PydanticAgentBackend → PydanticAI 2.54.0 TestModel | Real structured output path with output_type=Listing; synthetic custom_output_args |
| real provider | Unavailable in this example | No real LLM marketing generation or paid-provider validation has occurred |

The fake and TestModel fixtures copy supplied name, description, language and
features. TestModel's custom_output_args is an explicitly supplied fixture;
neither mode demonstrates model intelligence or factual accuracy.

## Run the local flow

From the repository root, after uv sync --locked --all-packages:

~~~powershell
uv run --no-sync python examples/05_commerce_listing_review.py propose --input examples/data/listing_products.json --output proposals.json --mode fake
uv run --no-sync python examples/05_commerce_listing_review.py review --input proposals.json --id row-0001
~~~

The inspection command deliberately displays the original facts, Listing,
risks and proposal_hash in local stdout. Read them, verify every claim and
copy the exact hash before making a decision.

~~~powershell
uv run --no-sync python examples/05_commerce_listing_review.py review --input proposals.json --output proposals.json --id row-0001 --decision APPROVE --reviewer "your-name" --note "I checked the source facts, claims and language." --expected-proposal-hash "COPY_EXACT_HASH_FROM_REVIEW" --acknowledge-risks
uv run --no-sync python examples/05_commerce_listing_review.py export-approved --input proposals.json --output approved.jsonl
~~~

Replace the quoted hash placeholder. APPROVE requires a reviewer, a nonempty
note, exact viewed hash and explicit acknowledgement of factual and semantic
risks. This local application cannot authenticate who is physically typing.
It never approves in the generation path.

To reject, use --decision REJECT with reviewer, note and the exact hash;
risk acknowledgement is optional for rejection. Reviewed rows cannot be
reviewed again. Review --output may be the same ledger as --input for a
validated pending-row transition, or a new path to retain the original file.
A different existing output path is refused. New proposals and exports
always require new output paths.

Use --mode test-model for the PydanticAgentBackend integration. These are the
only accepted modes. No provider key, model name or Agent tools can be
configured by this CLI. Real PydanticAI model requests are disabled during
generation using its public override_allow_model_requests(False) context.

## Input, proposal and export formats

Input uses UTF-8 .json (one Product object or an array) or .jsonl (one Product
object per nonblank line). There is no CSV input in this example. Every record
is validated before any backend run. Product is revalidated from a fresh
dump immediately before each run to catch nested mutable-state corruption.
Description and language must be present and nonblank. The application also
requires a conservative language-tag syntax: 2–3 letters followed by optional
2–8 character alphanumeric subtags. This is not a complete BCP 47 registry
validator or automatic language detector.

Rows receive logical IDs row-0001, row-0002, etc. Input order determines
identity; the example provides no catalog identity or deduplication service.

The proposal ledger is a single canonical UTF-8 JSON document, with one
trailing LF, format_version=orivane-listing-review/1 and a proposals array.
Each record includes row_id, an immutable canonical JSON string containing
source_product_snapshot, SHA-256 source_product_snapshot_hash, proposed_listing,
generation_mode, prompt_version, validation_flags, risk_flags, proposal_hash,
review_status and optional review_decision.

Snapshot hashes and proposal hashes are derived from canonical JSON with
sorted keys, compact separators, literal Unicode and allow_nan=False.
The proposal hash binds row identity, source snapshot and its hash, Listing,
generation mode, prompt version, validation flags and risk flags. The human
decision separately binds that proposal hash and includes decision, reviewer,
note, timezone-bearing timestamp and acknowledged_risks.

JSON loading rejects duplicate keys at every depth, NaN/Infinity constants,
unknown fields, unknown states, noncanonical source snapshots, duplicate
row IDs, status/decision contradictions and stale content hashes. Every record
is checked on load, before review, and again before export. Bypassing a frozen
model with model_copy/model_construct does not bypass those checks.

Approved export uses UTF-8 JSONL. Each line has
format_version=orivane-approved-listing/1, row_id, proposal_hash,
source_product_snapshot_hash, listing and review_decision. It includes only
APPROVED rows. Pending/rejected rows are filtered out; zero approved rows
fails without creating a file. Malformed or tampered records fail the entire
operation even if they would otherwise be filtered. Listing can be parsed
again with Listing.model_validate. Full product facts and SessionState payload
are not included in export.

## Review and content safety

| Category | Behavior |
| --- | --- |
| Invalid Product or Listing structure | Fixed safe error; no partial proposal file |
| Missing description/language or invalid application language syntax | Fail before the backend |
| Output language metadata differs from source | LANGUAGE_METADATA_MISMATCH; approval blocked, rejection allowed |
| New numeric token or candidate certification/material/dimension/price/warranty/feature text | Advisory risk flags requiring human verification |
| Suspected content-language mismatch | Advisory script heuristic requiring human review |
| Input includes instruction-like text | Marked as untrusted data; no tools or autoapproval |
| Claims outside lexical patterns | HUMAN_FACT_CHECK_REQUIRED remains present for every proposal |
| Proposal regenerated or edited | New generation always PENDING_REVIEW; prior decision cannot transfer to changed content |

The versioned instructions are separate from the JSON user-message data.
Escaping and instruction separation improve boundaries but do not prove
prompt-injection immunity. No actual adversarial LLM has been evaluated.
Keyword checks can miss semantic claims and can produce false positives;
they never justify automatic approval.

Errors and progress output use fixed categories and counts, not source facts,
full prompts, model responses, keys or session payloads. Explicit inspection
is a separate local user action. The application persists the required facts
and Listing in the explicitly named local review file, not in Trace/logs.
The existing backend's content-disabled tracing remains unchanged; application
contracts check both successful and failed runs for leakage.

## Filesystem and trust limits

New files are buffered completely, written to a temporary file in the target
directory, flushed and fsynced, then published with an exclusive hard link.
Existing files, including dangling symlink targets, are not silently replaced.
Filesystems without hard-link support fail safely.

An explicit same-ledger review compares original bytes before writing and
again immediately before os.replace. Temporary files are removed. Simulated
link/replace/fsync failures preserve existing content. This is single-user
local-file behavior, not a concurrent transaction or guaranteed power-loss
durability. Do not use simultaneous writers.

Hashes detect content replacement under the honest-file workflow. They are
not signatures: someone able to rewrite the entire file, decision and hashes
can forge a review. Identity authentication, authorization, trusted signatures,
audit storage, database transactions and multi-user workflows are out of scope.

## Later CSV integration

The strict Phase 3C parser and its golden file are unchanged. Do not rebuild
Product facts from the CSV example's Listing or reference draft: that loses
source fields. In a later reviewed change, extract/reuse its application-owned
CSV-to-validated-Product stage with logical row identity, preserving the strict
quoting/JSON behavior and golden hash, then pass those Product objects to this
service. No Commerce public API or runtime dependency is needed.

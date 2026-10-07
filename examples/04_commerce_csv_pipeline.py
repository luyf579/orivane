"""Offline, application-owned CSV -> Product -> Listing -> typed reference draft."""

import csv
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from orivane_commerce import Listing, MarketplaceAdapter, Product

_COLUMNS = (
    "name",
    "brand",
    "description",
    "features_json",
    "attributes_json",
    "category",
    "target_audience",
    "language",
)


class _PipelineError(ValueError):
    """A fixed diagnostic safe to show without echoing source values."""


@dataclass(frozen=True)
class OfflineReferenceDraft:
    headline: str
    body: str
    locale: str
    bullets: tuple[str, ...]
    search_terms: tuple[str, ...]


class OfflineReferenceAdapter:
    platform = "offline-reference"

    def adapt(self, listing: Listing) -> OfflineReferenceDraft:
        return OfflineReferenceDraft(
            headline=listing.title,
            body=listing.description,
            locale=listing.language,
            bullets=listing.bullet_points,
            search_terms=listing.keywords,
        )


def _read_product(values: dict[str, str], row: int) -> Product:
    try:
        features: object = (
            json.loads(values["features_json"]) if values["features_json"].strip() else []
        )
    except (ValueError, RecursionError):
        raise _PipelineError(f"row {row}: invalid features_json") from None
    if not isinstance(features, list):
        raise _PipelineError(f"row {row}: invalid features_json")
    try:
        attributes: object = (
            json.loads(values["attributes_json"]) if values["attributes_json"].strip() else {}
        )
    except (ValueError, RecursionError):
        raise _PipelineError(f"row {row}: invalid attributes_json") from None
    if not isinstance(attributes, dict):
        raise _PipelineError(f"row {row}: invalid attributes_json")
    data: dict[str, object] = {
        "name": values["name"],
        "features": features,
        "attributes": attributes,
    }
    for field in ("brand", "description", "category", "target_audience", "language"):
        data[field] = values[field] if values[field].strip() else None
    try:
        return Product.model_validate(data)
    except ValueError:
        raise _PipelineError(f"row {row}: invalid Product") from None


def _make_listing(product: Product, row: int) -> Listing:
    if product.description is None:
        raise _PipelineError(f"row {row}: description is required")
    if product.language is None:
        raise _PipelineError(f"row {row}: language is required")
    return Listing(
        title=product.name,
        description=product.description,
        language=product.language,
        bullet_points=product.features,
        keywords=(),
    )


def _render_jsonl(path: Path) -> bytes:
    adapter: MarketplaceAdapter[OfflineReferenceDraft] = OfflineReferenceAdapter()
    lines: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if header is None or len(header) != len(_COLUMNS) or set(header) != set(_COLUMNS):
            raise _PipelineError("invalid CSV header")
        for row, values in enumerate(reader, start=1):
            if len(values) != len(header):
                raise _PipelineError(f"row {row}: invalid CSV record")
            product = _read_product(dict(zip(header, values, strict=True)), row)
            draft = adapter.adapt(_make_listing(product, row))
            lines.append(
                json.dumps(
                    {"row": row, "platform": adapter.platform, "draft": asdict(draft)},
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
    return ("".join(line + "\n" for line in lines)).encode("utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("commerce_csv_pipeline: expected one input CSV path", file=sys.stderr)
        return 2
    try:
        output = _render_jsonl(Path(sys.argv[1]))
    except _PipelineError as error:
        print(f"commerce_csv_pipeline: {error}", file=sys.stderr)
        return 2
    except (OSError, UnicodeError, csv.Error):
        print("commerce_csv_pipeline: invalid or unreadable CSV", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

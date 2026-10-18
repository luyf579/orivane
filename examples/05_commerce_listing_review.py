"""Standalone offline application CLI; no real provider or publishing support."""

import sys
from pathlib import Path

# Keep the canonical application import identical when launched from any cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from examples.commerce_listing_review import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())

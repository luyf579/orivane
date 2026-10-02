"""Platform-neutral commerce data and an offline adapter contract."""

from ._domain import Listing, MarketplaceAdapter, Product

__all__ = ["Product", "Listing", "MarketplaceAdapter"]

"""Explicit assembly of Core and temporary compatibility capability contributions."""

from agentos.core.planning.capabilities import CapabilityCatalog
from agentos.core.planning.compat.legal_legacy import register_legal_compatibility_capabilities
from agentos.core.planning.native_capabilities import register_native_capabilities


def build_default_capability_catalog() -> CapabilityCatalog:
    catalog = CapabilityCatalog()
    register_native_capabilities(catalog)
    register_legal_compatibility_capabilities(catalog)
    catalog.validate()
    return catalog


__all__ = ["build_default_capability_catalog"]

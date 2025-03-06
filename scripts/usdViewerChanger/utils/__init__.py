"""
Utilities for the USD Prim Editor.

This module contains utility functions for working with USD data.
"""

from .usd_utils import (
    PrimPurpose, PrimInfo, VariantSetInfo, AttributeInfo, PrimvarInfo,
    get_prim_info, get_attributes, get_primvars, get_variant_sets,
    set_variant_selection, set_prim_kind, set_prim_purpose,
    has_payload, load_payload, unload_payload,
    get_stage_as_text, update_stage_from_text,
    add_attribute, add_primvar, remove_attribute, remove_primvar,
    set_attribute_value, clear_caches
)

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Tuple, Generator, Any, Union
from functools import lru_cache

from pxr import Usd, UsdGeom, Sdf, Kind

from ..config import config

class PrimPurpose(Enum):
    DEFAULT = "default"
    RENDER = "render"
    PROXY = "proxy"
    GUIDE = "guide"

@dataclass
class PrimInfo:
    """Information about a USD prim"""
    name: str
    type_name: str
    kind: str
    purpose: str
    path: Sdf.Path
    has_variants: bool = False
    has_payload: bool = False
    is_active: bool = True
    is_defined: bool = True
    is_abstract: bool = False
    is_instance: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class VariantSetInfo:
    """Information about a variant set"""
    name: str
    variants: List[str]
    current_selection: str

@dataclass
class AttributeInfo:
    """Information about an attribute"""
    name: str
    value: Any
    type_name: str
    is_custom: bool = False
    is_authored: bool = True
    default_value: Any = None
    has_time_samples: bool = False
    time_samples: List[float] = None
    
    def __post_init__(self):
        if self.time_samples is None:
            self.time_samples = []

@dataclass
class PrimvarInfo:
    """Information about a primvar"""
    name: str
    value: Any
    type_name: str
    interpolation: str = "constant"
    element_size: int = 1
    indices: List[int] = None
    
    def __post_init__(self):
        if self.indices is None:
            self.indices = []

# Cache for prim info to improve performance
_prim_info_cache = {}
_prim_attr_cache = {}
_prim_primvar_cache = {}

def clear_caches():
    """Clear all caches"""
    global _prim_info_cache, _prim_attr_cache, _prim_primvar_cache
    _prim_info_cache = {}
    _prim_attr_cache = {}
    _prim_primvar_cache = {}

def get_prim_info(prim: Usd.Prim) -> PrimInfo:
    """Get basic information about a prim with optional caching"""
    path_str = str(prim.GetPath())
    
    # Return cached info if available and caching is enabled
    if config.cache_prim_info and path_str in _prim_info_cache:
        return _prim_info_cache[path_str]
    
    # Get prim kind
    model_api = Usd.ModelAPI(prim)
    kind = model_api.GetKind() or ""
    
    # Get purpose
    purpose = ""
    if prim.IsA(UsdGeom.Imageable):
        purpose = UsdGeom.Imageable(prim).GetPurposeAttr().Get() or PrimPurpose.DEFAULT.value
    
    # Get metadata
    metadata = {}
    for key in prim.GetMetadataInfos():
        if prim.HasAuthoredMetadata(key):
            metadata[key] = prim.GetMetadata(key)
    
    # Create prim info
    info = PrimInfo(
        name=prim.GetName(),
        type_name=prim.GetTypeName(),
        kind=kind,
        purpose=purpose,
        path=prim.GetPath(),
        has_variants=len(prim.GetVariantSets().GetNames()) > 0,
        has_payload=prim.HasPayload(),
        is_active=prim.IsActive(),
        is_defined=prim.IsDefined(),
        is_abstract=prim.IsAbstract(),
        is_instance=prim.IsInstance(),
        metadata=metadata
    )
    
    # Cache the result if caching is enabled
    if config.cache_prim_info:
        _prim_info_cache[path_str] = info
    
    return info

def get_child_prims(prim: Usd.Prim, predicate=None) -> List[Usd.Prim]:
    """Get child prims with optional filtering"""
    if predicate is None:
        predicate = Usd.PrimIsActive & ~Usd.PrimIsAbstract
    
    return list(prim.GetFilteredChildren(predicate=predicate))

def get_child_prims_lazy(prim: Usd.Prim, predicate=None) -> Generator[Usd.Prim, None, None]:
    """Generator for child prims to support lazy loading"""
    if predicate is None:
        predicate = Usd.PrimIsActive & ~Usd.PrimIsAbstract
    
    for child in prim.GetFilteredChildren(predicate=predicate):
        yield child

def get_variant_sets(prim: Usd.Prim) -> List[VariantSetInfo]:
    """Get information about variant sets on a prim"""
    variant_sets = []
    for vs_name in prim.GetVariantSets().GetNames():
        vs = prim.GetVariantSet(vs_name)
        variants = vs.GetVariantNames()
        current_selection = vs.GetVariantSelection()
        variant_sets.append(VariantSetInfo(vs_name, variants, current_selection))
    return variant_sets

def set_variant_selection(prim: Usd.Prim, variant_set: str, variant: str) -> bool:
    """Set a variant selection on a prim"""
    try:
        vs = prim.GetVariantSet(variant_set)
        vs.SetVariantSelection(variant)
        clear_cache_for_prim(prim)
        return True
    except Exception as e:
        print(f"Error setting variant selection: {str(e)}")
        return False

def has_payload(prim: Usd.Prim) -> bool:
    """Check if the prim has a payload"""
    return prim.HasPayload()

def load_payload(prim: Usd.Prim) -> bool:
    """Load the payload for a prim"""
    try:
        if prim.HasPayload():
            prim.Load()
            clear_cache_for_prim(prim)
            return True
        return False
    except Exception as e:
        print(f"Error loading payload: {str(e)}")
        return False

def unload_payload(prim: Usd.Prim) -> bool:
    """Unload the payload for a prim"""
    try:
        if prim.HasPayload():
            prim.Unload()
            clear_cache_for_prim(prim)
            return True
        return False
    except Exception as e:
        print(f"Error unloading payload: {str(e)}")
        return False

def set_prim_kind(prim: Usd.Prim, kind: str) -> bool:
    """Set the kind of a prim"""
    try:
        model_api = Usd.ModelAPI(prim)
        model_api.SetKind(kind)
        clear_cache_for_prim(prim)
        return True
    except Exception as e:
        print(f"Error setting prim kind: {str(e)}")
        return False

def set_prim_purpose(prim: Usd.Prim, purpose: PrimPurpose) -> bool:
    """Set the purpose of a prim"""
    try:
        if prim.IsA(UsdGeom.Imageable):
            UsdGeom.Imageable(prim).CreatePurposeAttr().Set(purpose.value)
            clear_cache_for_prim(prim)
            return True
        return False
    except Exception as e:
        print(f"Error setting prim purpose: {str(e)}")
        return False

def get_stage_as_text(stage: Usd.Stage) -> str:
    """Get the stage content as text"""
    return stage.GetRootLayer().ExportToString()

def update_stage_from_text(stage: Usd.Stage, text: str) -> bool:
    """Update the stage from text"""
    try:
        stage.GetRootLayer().ImportFromString(text)
        clear_caches()  # Clear all caches when updating the entire stage
        return True
    except Exception as e:
        print(f"Error updating stage from text: {str(e)}")
        return False

def get_attributes(prim: Usd.Prim) -> List[AttributeInfo]:
    """Get all attributes for a prim with caching"""
    path_str = str(prim.GetPath())
    
    # Return cached attributes if available and caching is enabled
    if config.cache_prim_info and path_str in _prim_attr_cache:
        return _prim_attr_cache[path_str]
    
    attr_infos = []
    for attr in prim.GetAttributes():
        # Skip attributes that are internal to UsdGeom.Primvar to avoid duplication
        if UsdGeom.Primvar.IsPrimvarName(attr.GetName()):
            continue
            
        has_time_samples = attr.GetNumTimeSamples() > 0
        time_samples = []
        
        if has_time_samples:
            time_samples = attr.GetTimeSamples()
        
        attr_info = AttributeInfo(
            name=attr.GetName(),
            value=attr.Get(),
            type_name=str(attr.GetTypeName().GetAsToken()),
            is_custom=attr.IsCustom(),
            is_authored=attr.IsAuthored(),
            default_value=attr.GetDefaultValue(),
            has_time_samples=has_time_samples,
            time_samples=time_samples
        )
        attr_infos.append(attr_info)
    
    # Cache the attributes if caching is enabled
    if config.cache_prim_info:
        _prim_attr_cache[path_str] = attr_infos
    
    return attr_infos

def get_primvars(prim: Usd.Prim) -> List[PrimvarInfo]:
    """Get all primvars for a prim with caching"""
    path_str = str(prim.GetPath())
    
    # Return cached primvars if available and caching is enabled
    if config.cache_prim_info and path_str in _prim_primvar_cache:
        return _prim_primvar_cache[path_str]
    
    primvar_infos = []
    if prim.IsA(UsdGeom.Imageable):
        primvar_api = UsdGeom.PrimvarsAPI(prim)
        for primvar in primvar_api.GetPrimvars():
            primvar_info = PrimvarInfo(
                name=primvar.GetPrimvarName(),
                value=primvar.Get(),
                type_name=str(primvar.GetTypeName().GetAsToken()),
                interpolation=primvar.GetInterpolation(),
                element_size=primvar.GetElementSize(),
                indices=primvar.GetIndices() if primvar.IsIndexed() else []
            )
            primvar_infos.append(primvar_info)
    
    # Cache the primvars if caching is enabled
    if config.cache_prim_info:
        _prim_primvar_cache[path_str] = primvar_infos
    
    return primvar_infos

def add_attribute(prim: Usd.Prim, name: str, type_name: str, value: Any) -> bool:
    """Add a new attribute to a prim"""
    try:
        attr = prim.CreateAttribute(name, Sdf.ValueTypeNames.Find(type_name))
        if attr:
            attr.Set(value)
            clear_cache_for_prim(prim)
            return True
        return False
    except Exception as e:
        print(f"Error adding attribute: {str(e)}")
        return False

def add_primvar(prim: Usd.Prim, name: str, type_name: str, value: Any, interpolation: str = "constant") -> bool:
    """Add a new primvar to a prim"""
    try:
        if prim.IsA(UsdGeom.Imageable):
            primvar = UsdGeom.PrimvarsAPI(prim).CreatePrimvar(name, Sdf.ValueTypeNames.Find(type_name))
            if primvar:
                primvar.Set(value)
                primvar.SetInterpolation(interpolation)
                clear_cache_for_prim(prim)
                return True
        return False
    except Exception as e:
        print(f"Error adding primvar: {str(e)}")
        return False

def remove_attribute(prim: Usd.Prim, name: str) -> bool:
    """Remove an attribute from a prim"""
    try:
        result = prim.RemoveProperty(name)
        clear_cache_for_prim(prim)
        return result
    except Exception as e:
        print(f"Error removing attribute: {str(e)}")
        return False

def remove_primvar(prim: Usd.Prim, name: str) -> bool:
    """Remove a primvar from a prim"""
    try:
        if prim.IsA(UsdGeom.Imageable):
            result = UsdGeom.PrimvarsAPI(prim).RemovePrimvar(name)
            clear_cache_for_prim(prim)
            return result
        return False
    except Exception as e:
        print(f"Error removing primvar: {str(e)}")
        return False

def set_attribute_value(prim: Usd.Prim, name: str, value: Any, time: float = None) -> bool:
    """Set an attribute value, optionally at a specific time"""
    try:
        attr = prim.GetAttribute(name)
        if attr:
            if time is not None:
                attr.Set(value, time)
            else:
                attr.Set(value)
            clear_cache_for_prim(prim)
            return True
        return False
    except Exception as e:
        print(f"Error setting attribute value: {str(e)}")
        return False

def clear_cache_for_prim(prim: Usd.Prim):
    """Clear cache for a specific prim"""
    if not config.cache_prim_info:
        return
        
    path_str = str(prim.GetPath())
    if path_str in _prim_info_cache:
        del _prim_info_cache[path_str]
    if path_str in _prim_attr_cache:
        del _prim_attr_cache[path_str]
    if path_str in _prim_primvar_cache:
        del _prim_primvar_cache[path_str]

from typing import Dict, List, Optional, Tuple, Any, Generator, Set
from dataclasses import dataclass
from PySide6 import QtCore

from pxr import Usd, UsdGeom, Sdf, Gf

from ..utils.usd_utils import (
    PrimInfo, AttributeInfo, PrimvarInfo, VariantSetInfo,
    get_prim_info, get_attributes, get_primvars, get_variant_sets,
    set_variant_selection, set_prim_kind, set_prim_purpose,
    has_payload, load_payload, unload_payload,
    add_attribute, add_primvar, remove_attribute, remove_primvar,
    set_attribute_value, clear_caches
)
from ..config import config


class PrimModel(QtCore.QObject):
    """Model for handling USD prim data operations"""
    
    # Signals
    prim_changed = QtCore.Signal(str)  # Emitted when a prim changes (path)
    stage_changed = QtCore.Signal()    # Emitted when the stage changes
    
    def __init__(self, parent=None):
        super(PrimModel, self).__init__(parent)
        self.stage = None
        self.current_prim_path = None
        self.prim_info_cache = {}
        
    def set_stage(self, stage: Usd.Stage) -> None:
        """Set the USD stage"""
        self.stage = stage
        self.current_prim_path = None
        self.prim_info_cache = {}
        
        # Clear caches in utils module
        clear_caches()
        
        # Emit signal
        self.stage_changed.emit()
        
    def set_current_prim(self, prim_path: str) -> bool:
        """Set the current prim by path"""
        if not self.stage:
            return False
            
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim:
            return False
            
        old_path = self.current_prim_path
        self.current_prim_path = prim_path
        
        # Emit signal if changed
        if old_path != prim_path:
            self.prim_changed.emit(prim_path)
            
        return True
        
    def get_current_prim(self) -> Optional[Usd.Prim]:
        """Get the current prim"""
        if not self.stage or not self.current_prim_path:
            return None
            
        return self.stage.GetPrimAtPath(self.current_prim_path)
        
    def get_current_prim_info(self) -> Optional[PrimInfo]:
        """Get info for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return None
            
        return get_prim_info(prim)
        
    def get_attributes(self) -> List[AttributeInfo]:
        """Get attributes for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return []
            
        return get_attributes(prim)
        
    def get_primvars(self) -> List[PrimvarInfo]:
        """Get primvars for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return []
            
        return get_primvars(prim)
        
    def get_variant_sets(self) -> List[VariantSetInfo]:
        """Get variant sets for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return []
            
        return get_variant_sets(prim)
        
    def set_variant_selection(self, variant_set: str, variant: str) -> bool:
        """Set variant selection for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = set_variant_selection(prim, variant_set, variant)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def set_kind(self, kind: str) -> bool:
        """Set kind for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = set_prim_kind(prim, kind)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def set_purpose(self, purpose: str) -> bool:
        """Set purpose for the current prim"""
        from ..utils.usd_utils import PrimPurpose
        
        prim = self.get_current_prim()
        if not prim:
            return False
            
        try:
            purpose_enum = PrimPurpose(purpose)
            success = set_prim_purpose(prim, purpose_enum)
            if success:
                self.prim_changed.emit(self.current_prim_path)
            return success
        except ValueError:
            return False
            
    def has_payload(self) -> bool:
        """Check if the current prim has a payload"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        return has_payload(prim)
        
    def load_payload(self) -> bool:
        """Load payload for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = load_payload(prim)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def unload_payload(self) -> bool:
        """Unload payload for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = unload_payload(prim)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def add_attribute(self, name: str, type_name: str, value: Any) -> bool:
        """Add attribute to the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = add_attribute(prim, name, type_name, value)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def add_primvar(self, name: str, type_name: str, value: Any, interpolation: str = "constant") -> bool:
        """Add primvar to the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = add_primvar(prim, name, type_name, value, interpolation)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def remove_attribute(self, name: str) -> bool:
        """Remove attribute from the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = remove_attribute(prim, name)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def remove_primvar(self, name: str) -> bool:
        """Remove primvar from the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = remove_primvar(prim, name)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def set_attribute_value(self, name: str, value: Any, time: float = None) -> bool:
        """Set attribute value for the current prim"""
        prim = self.get_current_prim()
        if not prim:
            return False
            
        success = set_attribute_value(prim, name, value, time)
        if success:
            self.prim_changed.emit(self.current_prim_path)
        return success
        
    def convert_to_type(self, value_str: str, type_name: str) -> Any:
        """Convert string value to typed value"""
        # Handle common USD types
        try:
            if type_name == "bool":
                return value_str.lower() in ('true', '1', 'yes', 'on')
            elif type_name in ("int", "int32", "int64"):
                return int(value_str)
            elif type_name in ("uint", "uint32", "uint64"):
                return int(value_str)
            elif type_name in ("float", "float2", "float3", "float4"):
                if "," in value_str:
                    # Handle array types
                    components = [float(v.strip()) for v in value_str.strip("()[]").split(",")]
                    if len(components) == 2:
                        return Gf.Vec2f(*components)
                    elif len(components) == 3:
                        return Gf.Vec3f(*components)
                    elif len(components) == 4:
                        return Gf.Vec4f(*components)
                    else:
                        return components
                else:
                    return float(value_str)
            elif type_name in ("double", "double2", "double3", "double4"):
                if "," in value_str:
                    # Handle array types
                    components = [float(v.strip()) for v in value_str.strip("()[]").split(",")]
                    if len(components) == 2:
                        return Gf.Vec2d(*components)
                    elif len(components) == 3:
                        return Gf.Vec3d(*components)
                    elif len(components) == 4:
                        return Gf.Vec4d(*components)
                    else:
                        return components
                else:
                    return float(value_str)
            elif type_name == "string":
                return value_str
            elif type_name == "token":
                return value_str
            elif type_name in ("color3f", "color3d"):
                components = [float(v.strip()) for v in value_str.strip("()[]").split(",")]
                if len(components) == 3:
                    return Gf.Vec3f(*components) if type_name == "color3f" else Gf.Vec3d(*components)
                else:
                    return components
            else:
                # For other types, return as string
                return value_str
        except Exception as e:
            print(f"Error converting value '{value_str}' to type '{type_name}': {str(e)}")
            return value_str
            
    def get_stage_as_text(self) -> str:
        """Get the USD stage as text"""
        if not self.stage:
            return ""
            
        from ..utils.usd_utils import get_stage_as_text
        return get_stage_as_text(self.stage)
        
    def update_stage_from_text(self, text: str) -> bool:
        """Update the USD stage from text"""
        if not self.stage:
            return False
            
        from ..utils.usd_utils import update_stage_from_text
        success = update_stage_from_text(self.stage, text)
        if success:
            # Clear everything
            self.prim_info_cache = {}
            clear_caches()
            self.stage_changed.emit()
        return success

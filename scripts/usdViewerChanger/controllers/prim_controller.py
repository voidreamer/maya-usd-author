from typing import Dict, List, Optional, Tuple, Any
from PySide2 import QtCore, QtWidgets

from ..models.prim_model import PrimModel


class PrimController(QtCore.QObject):
    """Controller for handling USD prim operations"""
    
    # Signals
    operation_completed = QtCore.Signal(bool, str)  # Success, message
    
    def __init__(self, prim_model: PrimModel, parent=None):
        super(PrimController, self).__init__(parent)
        self.prim_model = prim_model
        
    def set_variant_selection(self, variant_set: str, variant: str) -> None:
        """Set variant selection on current prim"""
        success = self.prim_model.set_variant_selection(variant_set, variant)
        message = f"Set variant '{variant}' for '{variant_set}'"
        self.operation_completed.emit(success, message)
        
    def load_payload(self) -> None:
        """Load payload for current prim"""
        success = self.prim_model.load_payload()
        message = "Loaded payload"
        self.operation_completed.emit(success, message)
        
    def unload_payload(self) -> None:
        """Unload payload for current prim"""
        success = self.prim_model.unload_payload()
        message = "Unloaded payload"
        self.operation_completed.emit(success, message)
        
    def add_attribute(self, parent: QtWidgets.QWidget) -> None:
        """Add an attribute to current prim with interactive dialog"""
        # Get attribute name
        name, ok = QtWidgets.QInputDialog.getText(parent, "Add Attribute", "Enter attribute name:")
        if not ok or not name:
            return
            
        # Get attribute type
        type_options = [
            "string", "token", "bool", 
            "int", "float", "double", 
            "color3f", "vector3f", "point3f",
            "normal3f", "matrix4d"
        ]
        type_name, ok = QtWidgets.QInputDialog.getItem(
            parent, "Add Attribute", "Select attribute type:", type_options, 0, False
        )
        if not ok:
            return
            
        # Get attribute value
        value_str, ok = QtWidgets.QInputDialog.getText(
            parent, "Add Attribute", f"Enter value for {name} ({type_name}):"
        )
        if not ok:
            return
            
        # Convert value to the correct type
        typed_value = self.prim_model.convert_to_type(value_str, type_name)
        
        # Add the attribute
        success = self.prim_model.add_attribute(name, type_name, typed_value)
        message = f"Added attribute '{name}'"
        self.operation_completed.emit(success, message)
        
    def add_primvar(self, parent: QtWidgets.QWidget) -> None:
        """Add a primvar to current prim with interactive dialog"""
        # Get primvar name
        name, ok = QtWidgets.QInputDialog.getText(parent, "Add Primvar", "Enter primvar name:")
        if not ok or not name:
            return
            
        # Get primvar type
        type_options = [
            "string", "token", "bool", 
            "int", "float", "double", 
            "color3f", "vector3f", "point3f",
            "normal3f", "matrix4d"
        ]
        type_name, ok = QtWidgets.QInputDialog.getItem(
            parent, "Add Primvar", "Select primvar type:", type_options, 0, False
        )
        if not ok:
            return
            
        # Get interpolation
        interpolation_options = ["constant", "uniform", "vertex", "varying", "faceVarying"]
        interpolation, ok = QtWidgets.QInputDialog.getItem(
            parent, "Add Primvar", "Select interpolation:", interpolation_options, 0, False
        )
        if not ok:
            return
            
        # Get primvar value
        value_str, ok = QtWidgets.QInputDialog.getText(
            parent, "Add Primvar", f"Enter value for {name} ({type_name}):"
        )
        if not ok:
            return
            
        # Convert value to the correct type
        typed_value = self.prim_model.convert_to_type(value_str, type_name)
        
        # Add the primvar
        success = self.prim_model.add_primvar(name, type_name, typed_value, interpolation)
        message = f"Added primvar '{name}'"
        self.operation_completed.emit(success, message)
        
    def edit_attribute(self, parent: QtWidgets.QWidget, name: str, current_value: Any) -> None:
        """Edit an attribute on current prim"""
        # Get new value
        value_str, ok = QtWidgets.QInputDialog.getText(
            parent, "Edit Attribute", f"Enter new value for {name}:", 
            text=str(current_value)
        )
        if not ok:
            return
            
        # Find attribute to get its type
        attributes = self.prim_model.get_attributes()
        attr_type = "string"  # Default type
        
        for attr in attributes:
            if attr.name == name:
                attr_type = attr.type_name
                break
                
        # Convert value to the correct type
        typed_value = self.prim_model.convert_to_type(value_str, attr_type)
        
        # Set the attribute value
        success = self.prim_model.set_attribute_value(name, typed_value)
        message = f"Updated attribute '{name}'"
        self.operation_completed.emit(success, message)
        
    def edit_primvar(self, parent: QtWidgets.QWidget, name: str, current_value: Any) -> None:
        """Edit a primvar on current prim"""
        # Get new value
        value_str, ok = QtWidgets.QInputDialog.getText(
            parent, "Edit Primvar", f"Enter new value for {name}:", 
            text=str(current_value)
        )
        if not ok:
            return
            
        # Find primvar to get its type
        primvars = self.prim_model.get_primvars()
        primvar_type = "string"  # Default type
        
        for primvar in primvars:
            if primvar.name == name:
                primvar_type = primvar.type_name
                break
                
        # Convert value to the correct type
        typed_value = self.prim_model.convert_to_type(value_str, primvar_type)
        
        # Remove the old primvar
        success = self.prim_model.remove_primvar(name)
        if not success:
            self.operation_completed.emit(False, f"Failed to update primvar '{name}'")
            return
            
        # Add the new primvar
        success = self.prim_model.add_primvar(name, primvar_type, typed_value)
        message = f"Updated primvar '{name}'"
        self.operation_completed.emit(success, message)
        
    def edit_time_sample(self, parent: QtWidgets.QWidget, attr_name: str, time: float, current_value: Any) -> None:
        """Edit a time sample on an attribute"""
        # Get new value
        value_str, ok = QtWidgets.QInputDialog.getText(
            parent, "Edit Time Sample", f"Enter new value for {attr_name} at time {time}:", 
            text=str(current_value)
        )
        if not ok:
            return
            
        # Find attribute to get its type
        attributes = self.prim_model.get_attributes()
        attr_type = "string"  # Default type
        
        for attr in attributes:
            if attr.name == attr_name:
                attr_type = attr.type_name
                break
                
        # Convert value to the correct type
        typed_value = self.prim_model.convert_to_type(value_str, attr_type)
        
        # Set the attribute value at the specified time
        success = self.prim_model.set_attribute_value(attr_name, typed_value, time)
        message = f"Updated time sample for '{attr_name}' at time {time}"
        self.operation_completed.emit(success, message)
        
    def remove_attribute(self, name: str) -> None:
        """Remove an attribute from current prim"""
        success = self.prim_model.remove_attribute(name)
        message = f"Removed attribute '{name}'"
        self.operation_completed.emit(success, message)
        
    def remove_primvar(self, name: str) -> None:
        """Remove a primvar from current prim"""
        success = self.prim_model.remove_primvar(name)
        message = f"Removed primvar '{name}'"
        self.operation_completed.emit(success, message)
        
    def update_stage_from_text(self, text: str) -> None:
        """Update the stage from text"""
        success = self.prim_model.update_stage_from_text(text)
        message = "Updated stage from text"
        self.operation_completed.emit(success, message)

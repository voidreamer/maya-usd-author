from typing import Dict, List, Optional, Tuple, Any
from PySide2 import QtCore, QtWidgets, QtGui

import maya.cmds as cmds
import mayaUsd

from ..models.prim_model import PrimModel
from ..models.tree_model import UsdTreeModel
from ..config import config


class UiController(QtCore.QObject):
    """Controller for managing UI interactions"""
    
    # Signals
    stage_loaded = QtCore.Signal(object)  # Emitted when a stage is loaded
    prim_selected = QtCore.Signal(str)    # Emitted when a prim is selected
    update_ui = QtCore.Signal()           # General UI update signal
    
    def __init__(self, prim_model: PrimModel, parent=None):
        super(UiController, self).__init__(parent)
        self.prim_model = prim_model
        self.tree_model = None
        self.selected_maya_node = None
        self.window = None
        
        # Connect prim model signals
        self.prim_model.prim_changed.connect(self._on_prim_changed)
        self.prim_model.stage_changed.connect(self._on_stage_changed)
        
    def set_window(self, window: QtWidgets.QWidget) -> None:
        """Set the main window"""
        self.window = window
        
    def load_stage_from_maya_selection(self) -> bool:
        """Load the USD stage from current Maya selection"""
        selected = cmds.ls(sl=True, ufe=True)
        if not selected:
            self._show_warning("No USD prim selected.")
            return False
            
        try:
            # Extract the proxy shape from the first selected item
            proxy_shape, _ = selected[0].split(',')
            stage = mayaUsd.ufe.getStage(proxy_shape)
            
            if not stage:
                self._show_warning("Could not get USD stage from selection.")
                return False
                
            # Save the selected node for later use
            self.selected_maya_node = proxy_shape
            
            # Set the stage in the prim model
            self.prim_model.set_stage(stage)
            
            # Create a new tree model
            self.tree_model = UsdTreeModel(stage)
            
            # Emit signal
            self.stage_loaded.emit(stage)
            
            return True
        except Exception as e:
            self._show_error(f"Error loading USD stage: {str(e)}")
            return False
            
    def select_prim(self, prim_path: str) -> bool:
        """Select a prim in the prim model"""
        if not self.prim_model:
            return False
            
        success = self.prim_model.set_current_prim(prim_path)
        if success:
            self.prim_selected.emit(prim_path)
        return success
        
    def apply_kind_purpose(self, kind: str, purpose: str) -> bool:
        """Apply kind and purpose to the current prim"""
        if not self.prim_model:
            return False
            
        kind_success = True
        purpose_success = True
        
        if kind:
            kind_success = self.prim_model.set_kind(kind)
            
        if purpose:
            purpose_success = self.prim_model.set_purpose(purpose)
            
        return kind_success and purpose_success
        
    def toggle_tree_expansion(self, tree_view: QtWidgets.QTreeView, index: QtCore.QModelIndex, expand: bool) -> None:
        """Handle tree expansion with tracking"""
        if not self.tree_model:
            return
            
        # Track the expansion in the model
        self.tree_model.track_expanded(index, expand)
        
    def restore_tree_expansion(self, tree_view: QtWidgets.QTreeView) -> None:
        """Restore tree expansion state"""
        if not self.tree_model:
            return
            
        def expand_to_stored_state(parent_index=QtCore.QModelIndex()):
            for row in range(self.tree_model.rowCount(parent_index)):
                index = self.tree_model.index(row, 0, parent_index)
                if self.tree_model.should_expand(index):
                    tree_view.expand(index)
                    expand_to_stored_state(index)
                
        # Do the expansion
        expand_to_stored_state()
        
    def _on_prim_changed(self, prim_path: str) -> None:
        """Handle prim changed signal"""
        self.update_ui.emit()
        
    def _on_stage_changed(self) -> None:
        """Handle stage changed signal"""
        self.update_ui.emit()
        
    def _show_warning(self, message: str) -> None:
        """Show a warning dialog"""
        if self.window:
            QtWidgets.QMessageBox.warning(self.window, "Warning", message)
        else:
            cmds.warning(message)
            
    def _show_error(self, message: str) -> None:
        """Show an error dialog"""
        if self.window:
            QtWidgets.QMessageBox.critical(self.window, "Error", message)
        else:
            cmds.error(message)

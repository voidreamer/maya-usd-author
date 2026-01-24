"""USD Prim Editor UI for Maya.

This module provides a graphical interface for editing USD prims within Maya,
including attributes, primvars, variants, and payloads.
"""

import logging
from typing import Optional

from PySide2 import QtWidgets, QtCore
from pxr import Usd, Sdf
import maya.cmds as cmds
import mayaUsd

from .usdTreeModel import UsdTreeModel
from .usdUtils import (
    PrimPurpose, set_prim_kind, set_prim_purpose, get_stage_as_text,
    update_stage_from_text
)
from .constants import (
    KIND_VALUES, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_TITLE
)
from .widgets import (
    AttributeEditor, TimeSamplesEditor, VariantEditor, PayloadControls
)

logger = logging.getLogger(__name__)


class UsdPrimEditor(QtWidgets.QWidget):
    """Main widget for editing USD prims.

    Provides a tree view of the USD stage hierarchy along with editors for:
    - Kind and Purpose properties
    - Attributes and Primvars
    - Time samples
    - Variant sets
    - Payload loading/unloading

    This widget composes several specialized sub-widgets for a modular architecture.
    """

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super(UsdPrimEditor, self).__init__(parent)
        self.stage: Optional[Usd.Stage] = None
        self._selection_connection: Optional[bool] = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the main UI layout."""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Main horizontal layout
        main_layout = QtWidgets.QHBoxLayout(self)

        # Left panel: Tree view and controls
        left_panel = QtWidgets.QVBoxLayout()
        self._setup_tree_view(left_panel)
        self._setup_property_editors(left_panel)
        self._setup_action_buttons(left_panel)
        self._setup_stage_text_editor(left_panel)

        # Variant editor widget
        self.variant_editor = VariantEditor()
        left_panel.addWidget(self.variant_editor)

        # Payload controls widget
        self.payload_controls = PayloadControls()
        left_panel.addWidget(self.payload_controls)

        main_layout.addLayout(left_panel)

        # Right panel: Attribute and time samples editors
        right_panel = QtWidgets.QVBoxLayout()

        self.attribute_editor = AttributeEditor()
        right_panel.addWidget(self.attribute_editor)

        self.time_samples_editor = TimeSamplesEditor()
        right_panel.addWidget(self.time_samples_editor)

        main_layout.addLayout(right_panel)

    def _setup_tree_view(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Set up the tree view for displaying prim hierarchy."""
        self.tree_view = QtWidgets.QTreeView()
        self.tree_view.setAlternatingRowColors(True)
        self.tree_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tree_view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tree_view)

    def _setup_property_editors(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Set up the Kind and Purpose property editors."""
        property_layout = QtWidgets.QHBoxLayout()

        property_layout.addWidget(QtWidgets.QLabel("Kind:"))
        self.kind_combo = QtWidgets.QComboBox()
        self.kind_combo.addItems(KIND_VALUES)
        property_layout.addWidget(self.kind_combo)

        property_layout.addWidget(QtWidgets.QLabel("Purpose:"))
        self.purpose_combo = QtWidgets.QComboBox()
        self.purpose_combo.addItems([p.value for p in PrimPurpose])
        property_layout.addWidget(self.purpose_combo)

        property_layout.addStretch()
        layout.addLayout(property_layout)

    def _setup_action_buttons(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Set up the Refresh and Apply buttons."""
        button_layout = QtWidgets.QHBoxLayout()

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        button_layout.addWidget(self.refresh_btn)

        self.apply_btn = QtWidgets.QPushButton("Apply Changes")
        button_layout.addWidget(self.apply_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _setup_stage_text_editor(self, layout: QtWidgets.QVBoxLayout) -> None:
        """Set up the stage text display and update button."""
        self.stage_text_edit = QtWidgets.QPlainTextEdit()
        self.stage_text_edit.setReadOnly(True)
        self.stage_text_edit.setMaximumHeight(150)
        layout.addWidget(self.stage_text_edit)

        self.update_stage_btn = QtWidgets.QPushButton("Update Stage")
        layout.addWidget(self.update_stage_btn)

    def _connect_signals(self) -> None:
        """Connect all signals to their handlers."""
        # Main buttons
        self.refresh_btn.clicked.connect(self.refresh_tree_view)
        self.apply_btn.clicked.connect(self._apply_changes)
        self.update_stage_btn.clicked.connect(self._update_stage_from_text)

        # Widget signals
        self.attribute_editor.attribute_changed.connect(self._on_attribute_changed)
        self.time_samples_editor.time_sample_changed.connect(self._on_time_sample_changed)
        self.variant_editor.variant_changed.connect(self._on_variant_changed)
        self.payload_controls.payload_changed.connect(self._on_payload_changed)

    def _update_property_editors(self) -> None:
        """Update all editors when selection changes."""
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            self._clear_editors()
            return

        model = self.tree_view.model()
        row = selected_indexes[0].row()

        kind_item = model.item(row, 2)
        purpose_item = model.item(row, 3)

        self.kind_combo.setCurrentText(kind_item.text() if kind_item else "")
        self.purpose_combo.setCurrentText(purpose_item.text() if purpose_item else "")

        prim = self.get_selected_prim()
        if not prim:
            return

        # Update all sub-editors with the selected prim
        self.variant_editor.set_prim(prim)
        self.payload_controls.set_prim(prim)
        self.attribute_editor.set_prim(prim)
        self.time_samples_editor.set_prim(prim)

    def _clear_editors(self) -> None:
        """Clear all editors when no prim is selected."""
        self.kind_combo.setCurrentText("")
        self.purpose_combo.setCurrentText("")
        self.variant_editor.set_prim(None)
        self.payload_controls.set_prim(None)
        self.attribute_editor.set_prim(None)
        self.time_samples_editor.set_prim(None)

    def get_selected_prim(self) -> Optional[Usd.Prim]:
        """Get the currently selected prim from the tree view.

        Returns:
            The selected Usd.Prim, or None if no selection.
        """
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            return None

        prim_path_str = selected_indexes[0].data(QtCore.Qt.UserRole)
        prim_path = Sdf.Path(prim_path_str)
        return self.stage.GetPrimAtPath(prim_path)

    def refresh_tree_view(self) -> None:
        """Refresh the tree view from Maya's current USD selection."""
        selected = cmds.ls(sl=1, ufe=1)
        if not selected:
            cmds.warning("No USD prim selected.")
            return

        try:
            proxy_shape, _ = selected[0].split(',')
            self.stage = mayaUsd.ufe.getStage(proxy_shape)
            model = UsdTreeModel(self.stage)

            # Disconnect previous selection signal to prevent memory leak
            if self._selection_connection is not None:
                try:
                    self.tree_view.selectionModel().selectionChanged.disconnect(self._update_property_editors)
                except RuntimeError:
                    pass  # Signal was already disconnected

            self.tree_view.setModel(model)
            self.tree_view.expandAll()

            # Connect the selection changed signal after setting the model
            self.tree_view.selectionModel().selectionChanged.connect(self._update_property_editors)
            self._selection_connection = True

            self._update_stage_text()

        except Exception as e:
            logger.error(f"Error refreshing tree view: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to refresh tree view: {str(e)}")

    def _apply_changes(self) -> None:
        """Apply Kind and Purpose changes to the selected prim."""
        prim = self.get_selected_prim()
        if not prim or not self.stage:
            cmds.warning("No prim selected or stage not available.")
            return

        try:
            new_kind = self.kind_combo.currentText()
            if new_kind:
                set_prim_kind(prim, new_kind)

            new_purpose = self.purpose_combo.currentText()
            if new_purpose:
                set_prim_purpose(prim, PrimPurpose(new_purpose))

            self.refresh_tree_view()

        except Exception as e:
            logger.error(f"Error applying changes: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to apply changes: {str(e)}")

    def _update_stage_text(self) -> None:
        """Update the stage text display."""
        if self.stage:
            self.stage_text_edit.setPlainText(get_stage_as_text(self.stage))

    def _update_stage_from_text(self) -> None:
        """Update the stage from the text editor content."""
        if not self.stage:
            return

        reply = QtWidgets.QMessageBox.warning(
            self,
            "Confirm Stage Update",
            "This will overwrite the current stage layer. Are you sure?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        try:
            update_stage_from_text(self.stage, self.stage_text_edit.toPlainText())
            self.refresh_tree_view()
        except Exception as e:
            logger.error(f"Error updating stage: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update stage: {str(e)}")

    def _on_attribute_changed(self) -> None:
        """Handle attribute changes from the attribute editor."""
        self._update_stage_text()

    def _on_time_sample_changed(self) -> None:
        """Handle time sample changes from the time samples editor."""
        self._update_stage_text()

    def _on_variant_changed(self) -> None:
        """Handle variant changes from the variant editor."""
        self.refresh_tree_view()

    def _on_payload_changed(self) -> None:
        """Handle payload changes from the payload controls."""
        self.refresh_tree_view()

    def showEvent(self, event: QtCore.QEvent) -> None:
        """Handle show event."""
        if self.stage:
            self.refresh_tree_view()
        super().showEvent(event)


class UsdPrimEditorWindow(QtWidgets.QMainWindow):
    """Main window wrapper for the USD Prim Editor widget."""

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(WINDOW_TITLE)
        self.setCentralWidget(UsdPrimEditor())


def show_usd_prim_editor() -> None:
    """Show the USD Prim Editor window. Closes any existing instance first."""
    global usd_prim_editor
    try:
        usd_prim_editor.close()
        usd_prim_editor.deleteLater()
    except (NameError, RuntimeError):
        # NameError: usd_prim_editor doesn't exist yet
        # RuntimeError: Qt object already deleted
        pass
    usd_prim_editor = UsdPrimEditorWindow()
    usd_prim_editor.show()


if __name__ == "__main__":
    show_usd_prim_editor()

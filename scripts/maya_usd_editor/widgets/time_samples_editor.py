"""Time Samples Editor Widget."""

import logging
from typing import Any, Optional

from ..qt_compat import QtWidgets, QtCore
from pxr import Usd, Sdf, Gf

logger = logging.getLogger(__name__)


class TimeSamplesEditor(QtWidgets.QWidget):
    """Widget for viewing and editing USD time samples.

    Signals:
        time_sample_changed: Emitted when a time sample value is modified.
    """

    time_sample_changed = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._prim: Optional[Usd.Prim] = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Group box container
        group_box = QtWidgets.QGroupBox("Time Samples")
        group_layout = QtWidgets.QVBoxLayout(group_box)

        # Tree widget
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Attribute", "Time", "Value"])
        self.tree.setAlternatingRowColors(True)
        group_layout.addWidget(self.tree)

        layout.addWidget(group_box)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.tree.itemDoubleClicked.connect(self._edit_time_sample)

    def set_prim(self, prim: Optional[Usd.Prim]) -> None:
        """Set the current prim to display time samples for.

        Args:
            prim: The USD prim, or None to clear.
        """
        self._prim = prim
        self.refresh()

    def refresh(self) -> None:
        """Refresh the time samples list from the current prim."""
        self.tree.clear()

        if not self._prim:
            return

        for attr in self._prim.GetAttributes():
            if attr.GetNumTimeSamples() > 0:
                parent_item = QtWidgets.QTreeWidgetItem(self.tree)
                parent_item.setText(0, attr.GetName())

                for time in attr.GetTimeSamples():
                    child_item = QtWidgets.QTreeWidgetItem(parent_item)
                    child_item.setText(1, str(time))
                    child_item.setText(2, str(attr.Get(time)))

        self.tree.expandAll()

    def _convert_value(self, value_str: str, type_name: Sdf.ValueTypeName) -> Any:
        """Convert a string value to the appropriate USD type."""
        type_converters = {
            Sdf.ValueTypeNames.Bool: lambda x: x.lower() in ('true', '1', 'yes', 'on'),
            Sdf.ValueTypeNames.Int: int,
            Sdf.ValueTypeNames.UInt: int,
            Sdf.ValueTypeNames.Float: float,
            Sdf.ValueTypeNames.Double: float,
            Sdf.ValueTypeNames.String: str,
            Sdf.ValueTypeNames.Token: str,
            Sdf.ValueTypeNames.Vector3f: lambda x: Gf.Vec3f(*[float(v) for v in x.strip('()').split(',')]),
            Sdf.ValueTypeNames.Vector3d: lambda x: Gf.Vec3d(*[float(v) for v in x.strip('()').split(',')]),
            Sdf.ValueTypeNames.Color3f: lambda x: Gf.Vec3f(*[float(v) for v in x.strip('()').split(',')])
        }

        converter = type_converters.get(type_name)
        if converter:
            return converter(value_str)
        else:
            logger.warning(f"Unsupported type {type_name}. Returning string value.")
            return value_str

    def _edit_time_sample(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        """Edit a time sample value on double-click."""
        # Only edit child items (actual time samples, not attribute headers)
        if not item.parent():
            return

        if not self._prim:
            return

        attr_name = item.parent().text(0)
        time = float(item.text(1))
        current_value = item.text(2)

        new_value, ok = QtWidgets.QInputDialog.getText(
            self,
            "Edit Time Sample",
            f"Enter new value for {attr_name} at time {time}:",
            text=current_value
        )

        if not ok:
            return

        try:
            attr = self._prim.GetAttribute(attr_name)
            if not attr:
                logger.warning(f"Could not find attribute named {attr_name}")
                QtWidgets.QMessageBox.warning(
                    self, "Warning", f"Could not find attribute named '{attr_name}'"
                )
                return

            typed_value = self._convert_value(new_value, attr.GetTypeName())
            attr.Set(typed_value, time)
            self.refresh()
            self.time_sample_changed.emit()

        except Exception as e:
            logger.error(f"Error setting time sample: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to set time sample: {str(e)}")

"""Attribute and Primvar Editor Widget."""

import logging
from typing import Any, Callable, Optional

from PySide2 import QtWidgets, QtCore, QtGui
from pxr import Usd, Sdf, UsdGeom, Gf

from ..constants import AttributeColors

logger = logging.getLogger(__name__)


class ColorCodedItemDelegate(QtWidgets.QStyledItemDelegate):
    """Custom item delegate that renders tree items with color coding."""

    def paint(self, painter: QtGui.QPainter, option: QtWidgets.QStyleOptionViewItem,
              index: QtCore.QModelIndex) -> None:
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        item_data = index.data(QtCore.Qt.UserRole)
        color = item_data.get('color', QtGui.QColor(255, 255, 255)) if item_data else option.palette.text().color()
        painter.setPen(color)
        painter.drawText(option.rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, index.data())


class AttributeEditor(QtWidgets.QWidget):
    """Widget for editing USD attributes and primvars.

    Signals:
        attribute_changed: Emitted when an attribute value is modified.
    """

    attribute_changed = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._prim: Optional[Usd.Prim] = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        layout.addWidget(QtWidgets.QLabel("Attributes and Primvars:"))

        # Tree widget
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Value"])
        self.tree.setItemDelegate(ColorCodedItemDelegate())
        self.tree.setAlternatingRowColors(True)
        layout.addWidget(self.tree)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        self.add_attr_btn = QtWidgets.QPushButton("Add Attribute")
        self.add_primvar_btn = QtWidgets.QPushButton("Add Primvar")
        self.edit_btn = QtWidgets.QPushButton("Edit")
        self.remove_btn = QtWidgets.QPushButton("Remove")

        button_layout.addWidget(self.add_attr_btn)
        button_layout.addWidget(self.add_primvar_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.remove_btn)
        layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.add_attr_btn.clicked.connect(self._add_attribute)
        self.add_primvar_btn.clicked.connect(self._add_primvar)
        self.edit_btn.clicked.connect(self._edit_selected)
        self.remove_btn.clicked.connect(self._remove_selected)

    def set_prim(self, prim: Optional[Usd.Prim]) -> None:
        """Set the current prim to display attributes for.

        Args:
            prim: The USD prim, or None to clear.
        """
        self._prim = prim
        self.refresh()

    def refresh(self) -> None:
        """Refresh the attribute list from the current prim."""
        self.tree.clear()

        if not self._prim:
            return

        # Add attributes
        for attr in self._prim.GetAttributes():
            self._add_attribute_item(attr)

        # Add primvars if applicable
        if self._prim.IsA(UsdGeom.Imageable):
            primvar_api = UsdGeom.PrimvarsAPI(self._prim)
            for primvar in primvar_api.GetPrimvars():
                self._add_primvar_item(primvar)

    def _add_attribute_item(self, attr: Usd.Attribute) -> None:
        """Add an attribute to the tree."""
        item = QtWidgets.QTreeWidgetItem(self.tree)
        item.setText(0, attr.GetName())
        item.setText(1, str(attr.Get()))

        color = self._get_attribute_color(attr)
        item.setData(0, QtCore.Qt.UserRole, {'color': color})
        item.setData(1, QtCore.Qt.UserRole, {'color': color})

    def _add_primvar_item(self, primvar: UsdGeom.Primvar) -> None:
        """Add a primvar to the tree."""
        item = QtWidgets.QTreeWidgetItem(self.tree)
        item.setText(0, primvar.GetName())
        item.setText(1, str(primvar.Get()))

        item.setData(0, QtCore.Qt.UserRole, {'color': AttributeColors.PRIMVAR})
        item.setData(1, QtCore.Qt.UserRole, {'color': AttributeColors.PRIMVAR})

    def _get_attribute_color(self, attr: Usd.Attribute) -> QtGui.QColor:
        """Get the display color for an attribute based on its type."""
        if attr.IsCustom():
            return AttributeColors.CUSTOM
        elif attr.GetName().startswith('xformOp:'):
            return AttributeColors.TRANSFORM
        elif isinstance(attr.Get(), Usd.TimeCode):
            return AttributeColors.TIME_CODE
        elif attr.GetTypeName() == 'token':
            return AttributeColors.TOKEN
        return AttributeColors.DEFAULT

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

    def _add_attribute(self) -> None:
        """Add a new attribute to the prim."""
        if not self._prim:
            return

        name, ok = QtWidgets.QInputDialog.getText(self, "Add Attribute", "Enter attribute name:")
        if not ok or not name:
            return

        value, ok = QtWidgets.QInputDialog.getText(self, "Add Attribute", f"Enter value for {name}:")
        if not ok:
            return

        self._prim.CreateAttribute(name, Sdf.ValueTypeNames.String).Set(value)
        self.refresh()
        self.attribute_changed.emit()

    def _add_primvar(self) -> None:
        """Add a new primvar to the prim."""
        if not self._prim:
            return

        name, ok = QtWidgets.QInputDialog.getText(self, "Add Primvar", "Enter primvar name:")
        if not ok or not name:
            return

        value, ok = QtWidgets.QInputDialog.getText(self, "Add Primvar", f"Enter value for {name}:")
        if not ok:
            return

        UsdGeom.PrimvarsAPI(self._prim).CreatePrimvar(name, Sdf.ValueTypeNames.String).Set(value)
        self.refresh()
        self.attribute_changed.emit()

    def _edit_selected(self) -> None:
        """Edit the currently selected attribute or primvar."""
        item = self.tree.currentItem()
        if not item or not self._prim:
            return

        name = item.text(0)
        current_value = item.text(1)

        new_value, ok = QtWidgets.QInputDialog.getText(
            self, "Edit", f"Enter new value for {name}:", text=current_value
        )
        if not ok:
            return

        try:
            # Determine if it's a primvar or regular attribute
            if UsdGeom.Primvar.IsPrimvarName(name):
                attr = UsdGeom.PrimvarsAPI(self._prim).GetPrimvar(name).GetAttr()
            else:
                attr = self._prim.GetAttribute(name)

            if not attr:
                logger.warning(f"Could not find attribute or primvar named {name}")
                QtWidgets.QMessageBox.warning(
                    self, "Warning", f"Could not find attribute or primvar named '{name}'"
                )
                return

            typed_value = self._convert_value(new_value, attr.GetTypeName())
            attr.Set(typed_value)
            self.refresh()
            self.attribute_changed.emit()

        except Exception as e:
            logger.error(f"Error setting value: {str(e)}")
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to set value: {str(e)}")

    def _remove_selected(self) -> None:
        """Remove the currently selected attribute or primvar."""
        item = self.tree.currentItem()
        if not item or not self._prim:
            return

        name = item.text(0)

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove '{name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        if UsdGeom.Primvar.IsPrimvarName(name):
            UsdGeom.PrimvarsAPI(self._prim).RemovePrimvar(name)
        else:
            self._prim.RemoveProperty(name)

        self.refresh()
        self.attribute_changed.emit()

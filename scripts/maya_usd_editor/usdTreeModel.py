"""Tree model for displaying USD stage hierarchy."""

from typing import List

from PySide2 import QtGui, QtCore
from pxr import Usd

from .usdUtils import get_prim_info, get_child_prims, PrimInfo, get_variant_sets, has_payload
from .constants import TREE_COLUMNS


class UsdTreeModel(QtGui.QStandardItemModel):
    """Qt model that represents a USD stage hierarchy as a tree structure.

    Displays prim information including name, type, kind, purpose,
    variant sets, and payload status.
    """

    def __init__(self, stage: Usd.Stage) -> None:
        super().__init__()
        self.stage = stage
        self.setHorizontalHeaderLabels(TREE_COLUMNS)
        self.populate_model()

    def populate_model(self) -> None:
        """Populate the model from the stage's prim hierarchy."""
        root_prim = self.stage.GetPseudoRoot()
        self.populate_prim(root_prim, self.invisibleRootItem())

    def populate_prim(self, prim: Usd.Prim, parent_item: QtGui.QStandardItem) -> None:
        """Recursively add a prim and its children to the model.

        Args:
            prim: The USD prim to add.
            parent_item: The parent item in the tree model.
        """
        prim_info = get_prim_info(prim)
        items = self.create_row(prim_info, prim)
        parent_item.appendRow(items)

        for child_prim in get_child_prims(prim):
            self.populate_prim(child_prim, items[0])

    def create_row(self, prim_info: PrimInfo, prim: Usd.Prim) -> List[QtGui.QStandardItem]:
        """Create a row of items for a prim.

        Args:
            prim_info: Information about the prim.
            prim: The USD prim.

        Returns:
            List of QStandardItem objects for each column.
        """
        name_item = QtGui.QStandardItem(prim_info.name)
        name_item.setData(str(prim_info.path), QtCore.Qt.UserRole)

        variant_sets = get_variant_sets(prim)
        variant_sets_str = ", ".join([f"{vs.name}: {vs.current_selection}" for vs in variant_sets])

        has_payload_str = "Yes" if has_payload(prim) else "No"

        return [
            name_item,
            QtGui.QStandardItem(prim_info.type_name),
            QtGui.QStandardItem(prim_info.kind),
            QtGui.QStandardItem(prim_info.purpose),
            QtGui.QStandardItem(variant_sets_str),
            QtGui.QStandardItem(has_payload_str)
        ]

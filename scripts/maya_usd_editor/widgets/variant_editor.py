"""Variant Sets Editor Widget."""

import logging
from typing import Optional

from ..qt_compat import QtWidgets, QtCore
from pxr import Usd

from ..usdUtils import get_variant_sets, set_variant_selection

logger = logging.getLogger(__name__)


class VariantEditor(QtWidgets.QWidget):
    """Widget for viewing and editing USD variant sets.

    Signals:
        variant_changed: Emitted when a variant selection changes.
    """

    variant_changed = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._prim: Optional[Usd.Prim] = None
        self._combos: list = []  # Track combo boxes for cleanup
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # Group box replaces header label + container
        self._group = QtWidgets.QGroupBox("Variant Sets")
        self._variant_layout = QtWidgets.QVBoxLayout(self._group)
        self._variant_layout.setContentsMargins(6, 6, 6, 6)
        self._variant_layout.setSpacing(6)
        self._layout.addWidget(self._group)

    def set_prim(self, prim: Optional[Usd.Prim]) -> None:
        """Set the current prim to display variant sets for.

        Args:
            prim: The USD prim, or None to clear.
        """
        self._prim = prim
        self.refresh()

    def refresh(self) -> None:
        """Refresh the variant sets from the current prim."""
        self._clear_variants()

        if not self._prim:
            return

        variant_sets = get_variant_sets(self._prim)

        if not variant_sets:
            no_variants_label = QtWidgets.QLabel("No variant sets")
            no_variants_label.setObjectName("dimLabel")
            self._variant_layout.addWidget(no_variants_label)
            return

        for vs_info in variant_sets:
            row_layout = QtWidgets.QHBoxLayout()

            label = QtWidgets.QLabel(vs_info.name + ":")
            label.setMinimumWidth(80)
            row_layout.addWidget(label)

            combo = QtWidgets.QComboBox()
            combo.addItems(vs_info.variants)
            combo.setCurrentText(vs_info.current_selection)

            # Store the variant set name in the combo's property for the callback
            combo.setProperty("variant_set_name", vs_info.name)
            combo.currentTextChanged.connect(self._on_variant_changed)

            row_layout.addWidget(combo)
            row_layout.addStretch()

            self._combos.append(combo)
            self._variant_layout.addLayout(row_layout)

    def _clear_variants(self) -> None:
        """Clear all variant set controls."""
        self._combos.clear()

        # Remove all items from the variant layout
        while self._variant_layout.count():
            item = self._variant_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _clear_layout(self, layout: QtWidgets.QLayout) -> None:
        """Recursively clear a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _on_variant_changed(self, variant: str) -> None:
        """Handle variant selection change."""
        combo = self.sender()
        if not combo or not self._prim:
            return

        variant_set_name = combo.property("variant_set_name")
        if variant_set_name:
            set_variant_selection(self._prim, variant_set_name, variant)
            self.variant_changed.emit()

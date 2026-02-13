"""Payload Controls Widget."""

import logging
from typing import Optional

from ..qt_compat import QtWidgets, QtCore
from pxr import Usd

from ..usdUtils import has_payload, load_payload, unload_payload

logger = logging.getLogger(__name__)


class PayloadControls(QtWidgets.QWidget):
    """Widget for loading and unloading USD payloads.

    Signals:
        payload_changed: Emitted when payload state changes.
    """

    payload_changed = QtCore.Signal()

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._prim: Optional[Usd.Prim] = None
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        outer_layout = QtWidgets.QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        group = QtWidgets.QGroupBox("Payloads")
        layout = QtWidgets.QHBoxLayout(group)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.load_btn = QtWidgets.QPushButton("Load Payload")
        self.load_btn.setEnabled(False)
        layout.addWidget(self.load_btn)

        self.unload_btn = QtWidgets.QPushButton("Unload Payload")
        self.unload_btn.setEnabled(False)
        layout.addWidget(self.unload_btn)

        layout.addStretch()
        outer_layout.addWidget(group)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.load_btn.clicked.connect(self._load_payload)
        self.unload_btn.clicked.connect(self._unload_payload)

    def set_prim(self, prim: Optional[Usd.Prim]) -> None:
        """Set the current prim to control payloads for.

        Args:
            prim: The USD prim, or None to clear.
        """
        self._prim = prim
        self.refresh()

    def refresh(self) -> None:
        """Refresh the payload controls based on current prim state."""
        if not self._prim:
            self.load_btn.setEnabled(False)
            self.unload_btn.setEnabled(False)
            return

        has_payload_value = has_payload(self._prim)
        self.load_btn.setEnabled(has_payload_value)
        self.unload_btn.setEnabled(has_payload_value)

    def _load_payload(self) -> None:
        """Load the prim's payload."""
        if self._prim:
            load_payload(self._prim)
            self.payload_changed.emit()

    def _unload_payload(self) -> None:
        """Unload the prim's payload."""
        if self._prim:
            unload_payload(self._prim)
            self.payload_changed.emit()

"""Centralized dark stylesheet matching Maya's native look."""

_STYLESHEET = """
/* ── Global ── */
QWidget {
    background-color: #3a3a3a;
    color: #cccccc;
    font-size: 12px;
}

/* ── Group Boxes ── */
QGroupBox {
    border: 1px solid #555555;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 14px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 6px;
    color: #dddddd;
}

/* ── Push Buttons ── */
QPushButton {
    background-color: #4a4a4a;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px 12px;
    min-height: 20px;
    color: #cccccc;
}

QPushButton:hover {
    background-color: #525252;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #3a3a3a;
}

QPushButton:disabled {
    background-color: #3a3a3a;
    color: #666666;
    border-color: #444444;
}

/* Primary accent button */
QPushButton#primaryButton {
    background-color: #5285a6;
    border-color: #5285a6;
    color: #ffffff;
}

QPushButton#primaryButton:hover {
    background-color: #6295b6;
}

QPushButton#primaryButton:pressed {
    background-color: #427596;
}

/* ── Combo Boxes ── */
QComboBox {
    background-color: #4a4a4a;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 3px 8px;
    min-height: 20px;
    color: #cccccc;
}

QComboBox:hover {
    border-color: #666666;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #4a4a4a;
    border: 1px solid #555555;
    selection-background-color: #5285a6;
    color: #cccccc;
}

/* ── Tree View / Tree Widget ── */
QTreeView, QTreeWidget {
    background-color: #2b2b2b;
    alternate-background-color: #323232;
    border: 1px solid #555555;
    border-radius: 3px;
    color: #cccccc;
    selection-background-color: #5285a6;
}

QTreeView::item:hover, QTreeWidget::item:hover {
    background-color: #3e3e3e;
}

QTreeView::item:selected, QTreeWidget::item:selected {
    background-color: #5285a6;
    color: #ffffff;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
    border-image: none;
}

/* ── Header View ── */
QHeaderView::section {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    padding: 4px 6px;
    color: #cccccc;
    font-weight: bold;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

/* ── Plain Text Edit ── */
QPlainTextEdit {
    background-color: #2b2b2b;
    border: 1px solid #555555;
    border-radius: 3px;
    color: #cccccc;
    font-family: monospace;
    font-size: 11px;
}

/* ── Scroll Bars ── */
QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 4px;
    min-height: 20px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 4px;
    min-width: 20px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #666666;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ── Labels ── */
QLabel {
    background-color: transparent;
    color: #cccccc;
}

QLabel#dimLabel {
    color: #888888;
    font-style: italic;
}
"""


def apply_stylesheet(widget):
    """Apply the dark stylesheet to a widget and all its children.

    Call once on the root widget; all children inherit the style.

    Args:
        widget: The root QWidget to style.
    """
    widget.setStyleSheet(_STYLESHEET)

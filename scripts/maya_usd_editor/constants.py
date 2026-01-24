"""Constants and configuration values for the USD Prim Editor."""

from PySide2.QtGui import QColor


# Attribute color coding
class AttributeColors:
    """Colors used to differentiate attribute types in the UI."""
    CUSTOM = QColor(255, 255, 0)       # Yellow - custom attributes
    TRANSFORM = QColor(200, 200, 255)  # Light blue - xformOp attributes
    TIME_CODE = QColor(0, 255, 0)      # Green - time samples
    TOKEN = QColor(217, 157, 52)       # Orange - token type
    DEFAULT = QColor(142, 211, 245)    # Light cyan - default attributes
    PRIMVAR = QColor(0, 255, 255)      # Cyan - primvars


# Kind values available in the editor
KIND_VALUES = ["", "component", "subcomponent", "assembly", "group"]

# Window settings
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_TITLE = "USD Prim Editor"

# Tree view columns
TREE_COLUMNS = ['Prim Name', 'Type', 'Kind', 'Purpose', 'Variant Sets', 'Has Payload']

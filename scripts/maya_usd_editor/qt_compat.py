"""Qt compatibility shim for PySide2/PySide6.

Maya 2025 and earlier use PySide2, Maya 2026+ uses PySide6.
In non-Maya environments, PySide6 is tried first, then PySide2.
"""

PYSIDE_VERSION = 0

try:
    import maya.cmds as _cmds
    _maya_version = int(_cmds.about(version=True))
    if _maya_version >= 2026:
        from PySide6 import QtWidgets, QtCore, QtGui
        from PySide6.QtGui import QColor
        PYSIDE_VERSION = 6
    else:
        from PySide2 import QtWidgets, QtCore, QtGui
        from PySide2.QtGui import QColor
        PYSIDE_VERSION = 2
except Exception:
    # Non-Maya environment: try PySide6 first, then PySide2
    try:
        from PySide6 import QtWidgets, QtCore, QtGui
        from PySide6.QtGui import QColor
        PYSIDE_VERSION = 6
    except ImportError:
        from PySide2 import QtWidgets, QtCore, QtGui
        from PySide2.QtGui import QColor
        PYSIDE_VERSION = 2

"""Maya USD Editor - USD Prim Editor for Maya.

A simple yet powerful tool for authoring USD edits directly within Maya.

Usage:
    # Method 1: Direct import
    from maya_usd_editor import show
    show()

    # Method 2: Full path
    import maya_usd_editor
    maya_usd_editor.show()
"""

__version__ = "0.1.0"
__author__ = "USD Author Contributors"

from .usdPrimEditorUI import show_usd_prim_editor

# Convenient alias for the main entry point
show = show_usd_prim_editor

__all__ = [
    "show",
    "show_usd_prim_editor",
    "__version__",
]

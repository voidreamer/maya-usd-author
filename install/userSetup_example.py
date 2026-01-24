"""Example userSetup.py for Maya.

Copy this file to your Maya scripts folder and rename it to userSetup.py,
or add these lines to your existing userSetup.py.

This will:
1. Add the USD Prim Editor to Maya's menu
2. Register a keyboard shortcut (optional)
"""

import maya.cmds as cmds
import maya.utils


def add_usd_editor_menu():
    """Add USD Prim Editor to Maya's main menu."""
    # Add to Windows menu
    if cmds.menu("MayaWindow|mainWindowMenu", exists=True):
        cmds.menuItem(
            "usdPrimEditorMenuItem",
            label="USD Prim Editor",
            parent="MayaWindow|mainWindowMenu",
            command="import maya_usd_editor; maya_usd_editor.show()",
            annotation="Open the USD Prim Editor"
        )


def register_usd_editor_shortcut():
    """Register a keyboard shortcut for the USD Prim Editor.

    Default: Ctrl+Shift+U
    """
    cmds.nameCommand(
        "usdPrimEditorCommand",
        annotation="USD Prim Editor",
        command="python(\"import maya_usd_editor; maya_usd_editor.show()\")"
    )
    cmds.hotkey(keyShortcut="u", ctrlModifier=True, shiftModifier=True, name="usdPrimEditorCommand")


# Execute after Maya is fully loaded
maya.utils.executeDeferred(add_usd_editor_menu)
# Uncomment the line below to enable keyboard shortcut
# maya.utils.executeDeferred(register_usd_editor_shortcut)

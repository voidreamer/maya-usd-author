"""Shelf button script for USD Prim Editor.

To add to Maya shelf:
1. Open the Script Editor
2. Paste this code
3. Select all text
4. Middle-mouse drag to your desired shelf

Or run this script to automatically add a shelf button.
"""

import maya.cmds as cmds


def create_shelf_button():
    """Create a shelf button for the USD Prim Editor."""
    # Get the current shelf
    current_shelf = cmds.tabLayout(
        "ShelfLayout",
        query=True,
        selectTab=True
    )

    # Create the shelf button
    cmds.shelfButton(
        parent=current_shelf,
        annotation="USD Prim Editor - Edit USD prims directly in Maya",
        image="pythonFamily.png",  # You can change this to a custom icon
        command="import maya_usd_editor; maya_usd_editor.show()",
        label="USD Editor",
        sourceType="python"
    )

    print("USD Prim Editor shelf button created successfully!")


# Uncomment the line below to create the button when this script runs
# create_shelf_button()

# Minimal command for shelf button (copy this to shelf directly):
# import maya_usd_editor; maya_usd_editor.show()

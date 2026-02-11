#!/usr/bin/env python
"""Installation script for USD Prim Editor.

This script helps install the USD Prim Editor into Maya's scripts folder.

Usage:
    python install.py [--maya-version VERSION] [--create-shelf]

Options:
    --maya-version VERSION  Target Maya version (e.g., 2024, 2025)
    --create-shelf         Also create a shelf button
"""

import argparse
import os
import shutil
import sys
from pathlib import Path


def get_maya_scripts_path(maya_version=None):
    """Get the Maya scripts folder path for the current platform.

    Args:
        maya_version: Optional Maya version string (e.g., "2024")

    Returns:
        Path to Maya scripts folder
    """
    home = Path.home()

    if sys.platform == "win32":
        base = home / "Documents" / "maya"
    elif sys.platform == "darwin":
        base = home / "Library" / "Preferences" / "Autodesk" / "maya"
    else:  # Linux
        base = home / "maya"

    if maya_version:
        return base / maya_version / "scripts"
    else:
        # Find the most recent Maya version
        if base.exists():
            versions = [d for d in base.iterdir() if d.is_dir() and d.name.isdigit()]
            if versions:
                latest = max(versions, key=lambda x: int(x.name))
                return latest / "scripts"

    # Fallback to generic scripts folder
    return base / "scripts"


def install(maya_version=None, create_shelf=False):
    """Install USD Prim Editor to Maya scripts folder.

    Args:
        maya_version: Target Maya version
        create_shelf: Whether to create a shelf button setup
    """
    # Get source and destination paths
    script_dir = Path(__file__).parent.parent
    source = script_dir / "scripts" / "maya_usd_editor"
    dest_base = get_maya_scripts_path(maya_version)
    dest = dest_base / "maya_usd_editor"

    print(f"Source: {source}")
    print(f"Destination: {dest}")

    # Verify source exists
    if not source.exists():
        print(f"Error: Source folder not found: {source}")
        sys.exit(1)

    # Create destination folder if needed
    dest_base.mkdir(parents=True, exist_ok=True)

    # Remove existing installation
    if dest.exists():
        print(f"Removing existing installation...")
        shutil.rmtree(dest)

    # Copy files
    print("Copying files...")
    shutil.copytree(source, dest)

    print(f"\nInstallation complete!")
    print(f"\nTo use the USD Prim Editor in Maya:")
    print(f"  import maya_usd_editor")
    print(f"  maya_usd_editor.show()")

    if create_shelf:
        shelf_script = script_dir / "install" / "shelf_button.py"
        shelf_dest = dest_base / "shelf_button_usd_editor.py"
        shutil.copy(shelf_script, shelf_dest)
        print(f"\nShelf button script copied to: {shelf_dest}")
        print("Run this in Maya to create the shelf button:")
        print("  exec(open(r'{}').read())".format(shelf_dest))


def main():
    parser = argparse.ArgumentParser(description="Install USD Prim Editor for Maya")
    parser.add_argument(
        "--maya-version",
        help="Target Maya version (e.g., 2024, 2025)"
    )
    parser.add_argument(
        "--create-shelf",
        action="store_true",
        help="Also create a shelf button setup"
    )

    args = parser.parse_args()
    install(args.maya_version, args.create_shelf)


if __name__ == "__main__":
    main()

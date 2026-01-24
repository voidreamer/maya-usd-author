# Maya USD Author

A simple yet powerful tool for authoring USD (Universal Scene Description) edits directly within Autodesk Maya.

![USD Prim Editor](https://github.com/user-attachments/assets/25e9f120-c5e3-4eba-80a9-b01539974364)

## Features

- **Hierarchy Browser**: Navigate USD stage hierarchy with a tree view
- **Property Editing**: Modify Kind and Purpose properties
- **Attribute & Primvar Editor**: View and edit attributes with color-coded types
- **Time Samples**: Edit animation keyframe data
- **Variant Sets**: Switch between variant selections
- **Payload Control**: Load and unload payloads

## Requirements

- Autodesk Maya 2022+ with MayaUSD plugin
- Python 3.7+
- PySide2

## Installation

### Method 1: Automatic Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/maya-usd-author.git
cd maya-usd-author

# Run the installer
python install/install.py

# Or specify a Maya version
python install/install.py --maya-version 2024

# With shelf button
python install/install.py --maya-version 2024 --create-shelf
```

### Method 2: Manual Installation

1. Copy the `scripts/maya_usd_editor` folder to your Maya scripts directory:
   - **Windows**: `C:\Users\<username>\Documents\maya\<version>\scripts\`
   - **macOS**: `~/Library/Preferences/Autodesk/maya/<version>/scripts/`
   - **Linux**: `~/maya/<version>/scripts/`

2. Restart Maya or reload the scripts.

## Usage

### Quick Start

In Maya's Script Editor (Python):

```python
import maya_usd_editor
maya_usd_editor.show()
```

### Adding to Shelf

1. Open Maya's Script Editor
2. Enter the code above
3. Select the text and middle-mouse drag it to your shelf

Or run in Maya:

```python
exec(open('/path/to/maya-usd-author/install/shelf_button.py').read())
```

### Adding to Menu

Add to your `userSetup.py`:

```python
import maya.cmds as cmds
import maya.utils

def add_usd_editor_menu():
    cmds.menuItem(
        label="USD Prim Editor",
        parent="MayaWindow|mainWindowMenu",
        command="import maya_usd_editor; maya_usd_editor.show()"
    )

maya.utils.executeDeferred(add_usd_editor_menu)
```

### Keyboard Shortcut

Add to your `userSetup.py`:

```python
import maya.cmds as cmds

cmds.nameCommand(
    "usdPrimEditorCommand",
    annotation="USD Prim Editor",
    command="python(\"import maya_usd_editor; maya_usd_editor.show()\")"
)
cmds.hotkey(keyShortcut="u", ctrlModifier=True, shiftModifier=True, name="usdPrimEditorCommand")
```

## Color Coding

The attribute editor uses color coding to differentiate attribute types:

| Color | Type |
|-------|------|
| Yellow | Custom attributes |
| Light Blue | Transform (xformOp) attributes |
| Green | Time-sampled attributes |
| Orange | Token attributes |
| Cyan | Primvars |
| Light Cyan | Default attributes |

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
```

### Project Structure

```
maya-usd-author/
├── scripts/
│   └── maya_usd_editor/
│       ├── __init__.py          # Package entry point
│       ├── usdPrimEditorUI.py   # Main UI
│       ├── usdTreeModel.py      # Tree data model
│       ├── usdUtils.py          # USD utilities
│       └── constants.py         # Configuration
├── install/
│   ├── install.py               # Installation script
│   ├── shelf_button.py          # Shelf button creator
│   └── userSetup_example.py     # Example userSetup.py
├── tests/
│   └── test_usdUtils.py         # Unit tests
├── pyproject.toml               # Package configuration
└── README.md
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

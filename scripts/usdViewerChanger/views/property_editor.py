from typing import Dict, List, Optional, Tuple, Any, Set
from PySide2 import QtWidgets, QtCore, QtGui

from ..utils.usd_utils import (
    AttributeInfo, PrimvarInfo, VariantSetInfo, PrimInfo, PrimPurpose
)


class ColorDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate for rendering colored items in trees and tables"""
    
    def __init__(self, parent=None):
        super(ColorDelegate, self).__init__(parent)
        
    def paint(self, painter, option, index):
        """Custom painting for items"""
        # Get color data (if any)
        color_data = index.data(QtCore.Qt.UserRole)
        
        # Handle selection
        if option.state & QtWidgets.QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        
        # Set text color
        if isinstance(color_data, dict) and 'color' in color_data:
            color = color_data['color']
            painter.setPen(color)
        else:
            painter.setPen(option.palette.text().color())
        
        # Draw the text
        text = index.data(QtCore.Qt.DisplayRole)
        painter.drawText(
            option.rect.adjusted(4, 0, -4, 0), 
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, 
            str(text)
        )


class AttributeTreeWidget(QtWidgets.QTreeWidget):
    """Tree widget for displaying attributes and primvars"""
    
    # Signals
    itemAction = QtCore.Signal(str, str, object)  # Action, name, value
    
    def __init__(self, parent=None):
        super(AttributeTreeWidget, self).__init__(parent)
        
        # Configure tree
        self.setHeaderLabels(["Name", "Value"])
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        
        # Set delegate for custom coloring
        self.setItemDelegate(ColorDelegate())
        
        # Connect signals
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)
        
    def _show_context_menu(self, position):
        """Show context menu for attributes"""
        item = self.itemAt(position)
        if not item:
            return
            
        # Get attribute name and value
        name = item.text(0)
        value = item.text(1)
        
        # Create context menu
        menu = QtWidgets.QMenu(self)
        
        # Add actions
        edit_action = menu.addAction("Edit")
        menu.addSeparator()
        remove_action = menu.addAction("Remove")
        
        # Execute menu
        action = menu.exec_(self.viewport().mapToGlobal(position))
        
        # Handle action
        if action == edit_action:
            self.itemAction.emit("edit", name, value)
        elif action == remove_action:
            self.itemAction.emit("remove", name, value)
            
    def _on_item_double_clicked(self, item, column):
        """Handle double-click on an item"""
        name = item.text(0)
        value = item.text(1)
        self.itemAction.emit("edit", name, value)
        
    def set_attributes(self, attributes: List[AttributeInfo], primvars: List[PrimvarInfo]):
        """Set the attributes and primvars to display"""
        self.clear()
        
        # Add attributes
        attr_root = QtWidgets.QTreeWidgetItem(self)
        attr_root.setText(0, "Attributes")
        attr_root.setExpanded(True)
        
        # Skip duplicate items
        seen_names = set()
        
        for attr in attributes:
            # Skip if already seen
            if attr.name in seen_names:
                continue
                
            seen_names.add(attr.name)
            
            item = QtWidgets.QTreeWidgetItem(attr_root)
            item.setText(0, attr.name)
            item.setText(1, str(attr.value))
            
            # Set color based on attribute type
            color = self._get_attribute_color(attr)
            item.setData(0, QtCore.Qt.UserRole, {'color': color})
            item.setData(1, QtCore.Qt.UserRole, {'color': color})
            
            # Add time samples if any
            if attr.has_time_samples:
                for time in attr.time_samples:
                    time_item = QtWidgets.QTreeWidgetItem(item)
                    time_item.setText(0, f"Time: {time}")
                    # We don't display the value for each time sample here to save space
                    
        # Add primvars
        primvar_root = QtWidgets.QTreeWidgetItem(self)
        primvar_root.setText(0, "Primvars")
        primvar_root.setExpanded(True)
        
        for primvar in primvars:
            # Skip if already seen
            if primvar.name in seen_names:
                continue
                
            seen_names.add(primvar.name)
            
            item = QtWidgets.QTreeWidgetItem(primvar_root)
            item.setText(0, primvar.name)
            item.setText(1, str(primvar.value))
            
            # Set color for primvars
            color = QtGui.QColor(0, 150, 255)  # Primvars in blue
            item.setData(0, QtCore.Qt.UserRole, {'color': color})
            item.setData(1, QtCore.Qt.UserRole, {'color': color})
            
            # Add interpolation info
            interp_item = QtWidgets.QTreeWidgetItem(item)
            interp_item.setText(0, "interpolation")
            interp_item.setText(1, primvar.interpolation)
            
    def _get_attribute_color(self, attr: AttributeInfo) -> QtGui.QColor:
        """Get color for attribute based on its properties"""
        if attr.is_custom:
            return QtGui.QColor(255, 255, 0)  # Yellow for custom attributes
        elif attr.name.startswith('xformOp:'):
            return QtGui.QColor(200, 200, 255)  # Light blue for transform attributes
        elif attr.has_time_samples:
            return QtGui.QColor(0, 255, 0)  # Green for time samples
        elif attr.type_name == 'token':
            return QtGui.QColor(255, 165, 0)  # Orange for tokens
        return QtGui.QColor(180, 180, 180)  # Default color


class TimelineWidget(QtWidgets.QWidget):
    """Widget for displaying and editing time samples"""
    
    # Signals
    timeAction = QtCore.Signal(str, float, object)  # attr_name, time, value
    
    def __init__(self, parent=None):
        super(TimelineWidget, self).__init__(parent)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create tree widget
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Attribute", "Time", "Value"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tree.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        
        layout.addWidget(self.tree)
        
        # Connect signals
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        
    def set_attributes(self, attributes: List[AttributeInfo]):
        """Set attributes with time samples"""
        self.tree.clear()
        
        for attr in attributes:
            if attr.has_time_samples:
                parent_item = QtWidgets.QTreeWidgetItem(self.tree)
                parent_item.setText(0, attr.name)
                parent_item.setExpanded(True)
                
                for time in attr.time_samples:
                    child_item = QtWidgets.QTreeWidgetItem(parent_item)
                    child_item.setText(1, str(time))
                    
                    # Get value at this time if possible
                    # (This is a bit of a simplification as we don't have easy access to the value at each time)
                    child_item.setText(2, "(Sample exists)")
        
    def _show_context_menu(self, position):
        """Show context menu for time samples"""
        item = self.tree.itemAt(position)
        if not item or not item.parent():
            return
            
        # Get attribute name and time
        attr_name = item.parent().text(0)
        time = float(item.text(1))
        value = item.text(2)
        
        # Create context menu
        menu = QtWidgets.QMenu(self)
        
        # Add actions
        edit_action = menu.addAction("Edit Time Sample")
        
        # Execute menu
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        
        # Handle action
        if action == edit_action:
            self.timeAction.emit(attr_name, time, value)
            
    def _on_item_double_clicked(self, item, column):
        """Handle double-click on an item"""
        if not item or not item.parent():
            return
            
        attr_name = item.parent().text(0)
        time = float(item.text(1))
        value = item.text(2)
        
        self.timeAction.emit(attr_name, time, value)


class VariantSetsWidget(QtWidgets.QWidget):
    """Widget for displaying and editing variant sets"""
    
    # Signals
    variantSelected = QtCore.Signal(str, str)  # variant_set, variant
    
    def __init__(self, parent=None):
        super(VariantSetsWidget, self).__init__(parent)
        
        # Create layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Add header
        self.header_label = QtWidgets.QLabel("Variant Sets")
        self.header_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.header_label)
        
        # Container for variant widgets
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QtWidgets.QFrame.NoFrame)
        
        self.scroll_content = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
        
        # List to keep track of created ComboBoxes
        self.variant_combos = []
        
    def set_variant_sets(self, variant_sets: List[VariantSetInfo]):
        """Set variant sets to display"""
        # Clear existing widgets
        self.clear()
        
        if not variant_sets:
            no_variants_label = QtWidgets.QLabel("No variant sets")
            no_variants_label.setEnabled(False)
            self.scroll_layout.addWidget(no_variants_label)
            return
            
        # Add each variant set
        for vs_info in variant_sets:
            # Create a layout for this variant set
            vs_layout = QtWidgets.QHBoxLayout()
            
            # Add label
            label = QtWidgets.QLabel(vs_info.name)
            vs_layout.addWidget(label)
            
            # Add combo box
            combo = QtWidgets.QComboBox()
            combo.addItems(vs_info.variants)
            combo.setCurrentText(vs_info.current_selection)
            combo.currentTextChanged.connect(lambda text, name=vs_info.name: self.variantSelected.emit(name, text))
            
            # Store combo box
            self.variant_combos.append((vs_info.name, combo))
            
            vs_layout.addWidget(combo)
            self.scroll_layout.addLayout(vs_layout)
            
        # Add stretch to push everything to the top
        self.scroll_layout.addStretch()
        
    def clear(self):
        """Clear all variant sets"""
        # Clear the combos list
        self.variant_combos = []
        
        # Remove all widgets from the layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()


class PropertyEditor(QtWidgets.QWidget):
    """Widget for editing USD prim properties"""
    
    # Signals
    kindChanged = QtCore.Signal(str)
    purposeChanged = QtCore.Signal(str)
    attributeAction = QtCore.Signal(str, str, object)  # action, name, value
    primvarAction = QtCore.Signal(str, str, object)    # action, name, value
    variantSelected = QtCore.Signal(str, str)          # variant_set, variant
    payloadAction = QtCore.Signal(str)                 # action (load/unload)
    timeSampleAction = QtCore.Signal(str, float, object)  # attr_name, time, value
    addAttribute = QtCore.Signal()
    addPrimvar = QtCore.Signal()
    
    def __init__(self, parent=None):
        super(PropertyEditor, self).__init__(parent)
        
        # Create main layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create type and kind/purpose editors
        self._create_type_editor(layout)
        self._create_kind_purpose_editor(layout)
        
        # Create tabs for detailed properties
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)
        
        # Create attribute and primvar editor
        self.attr_widget = AttributeTreeWidget()
        self.tabs.addTab(self.attr_widget, "Attributes")
        
        # Create timeline widget
        self.timeline_widget = TimelineWidget()
        self.tabs.addTab(self.timeline_widget, "Time Samples")
        
        # Create variant sets widget
        self.variant_widget = VariantSetsWidget()
        self.tabs.addTab(self.variant_widget, "Variant Sets")
        
        # Create button layout for attributes
        self._create_attribute_buttons(layout)
        
        # Connect signals
        self.attr_widget.itemAction.connect(self._on_attribute_action)
        self.timeline_widget.timeAction.connect(self._on_time_action)
        self.variant_widget.variantSelected.connect(self.variantSelected.emit)
        self.kind_combo.currentTextChanged.connect(self.kindChanged.emit)
        self.purpose_combo.currentTextChanged.connect(self.purposeChanged.emit)
        
    def _create_type_editor(self, layout):
        """Create type display area"""
        type_layout = QtWidgets.QHBoxLayout()
        
        # Prim type (read-only)
        type_layout.addWidget(QtWidgets.QLabel("Type:"))
        self.type_label = QtWidgets.QLineEdit()
        self.type_label.setReadOnly(True)
        type_layout.addWidget(self.type_label)
        
        layout.addLayout(type_layout)
        
    def _create_kind_purpose_editor(self, layout):
        """Create kind and purpose editors"""
        kind_purpose_layout = QtWidgets.QHBoxLayout()
        
        # Kind combo
        kind_purpose_layout.addWidget(QtWidgets.QLabel("Kind:"))
        self.kind_combo = QtWidgets.QComboBox()
        self.kind_combo.addItems(["", "component", "subcomponent", "assembly", "group"])
        kind_purpose_layout.addWidget(self.kind_combo)
        
        # Purpose combo
        kind_purpose_layout.addWidget(QtWidgets.QLabel("Purpose:"))
        self.purpose_combo = QtWidgets.QComboBox()
        self.purpose_combo.addItems([p.value for p in PrimPurpose])
        kind_purpose_layout.addWidget(self.purpose_combo)
        
        # Payload buttons
        kind_purpose_layout.addWidget(QtWidgets.QLabel("Payload:"))
        self.load_payload_button = QtWidgets.QPushButton("Load")
        self.load_payload_button.setToolTip("Load payload for this prim")
        self.load_payload_button.clicked.connect(lambda: self.payloadAction.emit("load"))
        kind_purpose_layout.addWidget(self.load_payload_button)
        
        self.unload_payload_button = QtWidgets.QPushButton("Unload")
        self.unload_payload_button.setToolTip("Unload payload for this prim")
        self.unload_payload_button.clicked.connect(lambda: self.payloadAction.emit("unload"))
        kind_purpose_layout.addWidget(self.unload_payload_button)
        
        layout.addLayout(kind_purpose_layout)
        
    def _create_attribute_buttons(self, layout):
        """Create buttons for attribute operations"""
        button_layout = QtWidgets.QHBoxLayout()
        
        # Add attribute button
        self.add_attr_button = QtWidgets.QPushButton("Add Attribute")
        self.add_attr_button.clicked.connect(self.addAttribute.emit)
        button_layout.addWidget(self.add_attr_button)
        
        # Add primvar button
        self.add_primvar_button = QtWidgets.QPushButton("Add Primvar")
        self.add_primvar_button.clicked.connect(self.addPrimvar.emit)
        button_layout.addWidget(self.add_primvar_button)
        
        layout.addLayout(button_layout)
        
    def set_prim_info(self, prim_info: PrimInfo):
        """Set the currently displayed prim info"""
        if not prim_info:
            return
            
        # Update type
        self.type_label.setText(prim_info.type_name)
        
        # Update kind and purpose
        self.kind_combo.setCurrentText(prim_info.kind)
        self.purpose_combo.setCurrentText(prim_info.purpose)
        
        # Update payload buttons
        self.load_payload_button.setEnabled(prim_info.has_payload)
        self.unload_payload_button.setEnabled(prim_info.has_payload)
        
    def set_attributes(self, attributes: List[AttributeInfo], primvars: List[PrimvarInfo]):
        """Set attributes and primvars"""
        self.attr_widget.set_attributes(attributes, primvars)
        self.timeline_widget.set_attributes(attributes)
        
    def set_variant_sets(self, variant_sets: List[VariantSetInfo]):
        """Set variant sets"""
        self.variant_widget.set_variant_sets(variant_sets)
        
    def _on_attribute_action(self, action, name, value):
        """Handle attribute action"""
        # Check if it's a primvar
        if name in [item.text(0) for item in self.attr_widget.findItems("Primvars", QtCore.Qt.MatchExactly)[0].takeChildren()]:
            self.primvarAction.emit(action, name, value)
        else:
            self.attributeAction.emit(action, name, value)
            
    def _on_time_action(self, attr_name, time, value):
        """Handle time sample action"""
        self.timeSampleAction.emit(attr_name, time, value)
    
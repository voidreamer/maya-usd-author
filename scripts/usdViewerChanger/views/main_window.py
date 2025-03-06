import os
from typing import Optional

from PySide2 import QtWidgets, QtCore, QtGui

from ..models.prim_model import PrimModel
from ..models.tree_model import UsdTreeModel
from ..controllers.ui_controller import UiController
from ..controllers.prim_controller import PrimController
from ..views.tree_view import UsdTreePanel
from ..views.property_editor import PropertyEditor
from ..views.stage_text_editor import StageTextPanel
from ..views.viewers.placeholder import ViewerPlaceholder
from ..config import config, load_config_from_file, save_config_to_file, get_default_config_path


class UsdPrimEditorWindow(QtWidgets.QMainWindow):
    """Main window for the USD Prim Editor"""
    
    def __init__(self, parent=None):
        super(UsdPrimEditorWindow, self).__init__(parent)
        
        # Set window properties
        self.setWindowTitle("USD Prim Editor")
        self.resize(config.window_width, config.window_height)
        
        # Create central widget
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create models
        self.prim_model = PrimModel()
        
        # Create controllers
        self.ui_controller = UiController(self.prim_model)
        self.ui_controller.set_window(self)
        self.prim_controller = PrimController(self.prim_model)
        
        # Create splitters for layout
        self.horizontal_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.vertical_splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        
        # Create main components
        self._create_menu_bar()
        self._create_toolbar(main_layout)
        self._create_views()
        
        # Add splitters to layout
        main_layout.addWidget(self.horizontal_splitter)
        
        # Create status bar
        self.statusBar().showMessage("Ready")
        
        # Connect signals
        self._connect_signals()
        
        # Load configuration
        self._load_config()
        
    def _create_menu_bar(self):
        """Create the menu bar"""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        refresh_action = QtWidgets.QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_from_maya)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        save_config_action = QtWidgets.QAction("Save Configuration", self)
        save_config_action.triggered.connect(self._save_config)
        file_menu.addAction(save_config_action)
        
        load_config_action = QtWidgets.QAction("Load Configuration", self)
        load_config_action.triggered.connect(self._load_config)
        file_menu.addAction(load_config_action)
        
        file_menu.addSeparator()
        
        exit_action = QtWidgets.QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        toggle_tree_action = QtWidgets.QAction("Show/Hide Tree", self)
        toggle_tree_action.setCheckable(True)
        toggle_tree_action.setChecked(True)
        toggle_tree_action.triggered.connect(lambda checked: self._toggle_widget_visibility(self.tree_panel, checked))
        view_menu.addAction(toggle_tree_action)
        
        toggle_props_action = QtWidgets.QAction("Show/Hide Properties", self)
        toggle_props_action.setCheckable(True)
        toggle_props_action.setChecked(True)
        toggle_props_action.triggered.connect(lambda checked: self._toggle_widget_visibility(self.property_editor, checked))
        view_menu.addAction(toggle_props_action)
        
        toggle_text_action = QtWidgets.QAction("Show/Hide Stage Text", self)
        toggle_text_action.setCheckable(True)
        toggle_text_action.setChecked(True)
        toggle_text_action.triggered.connect(lambda checked: self._toggle_widget_visibility(self.stage_text_panel, checked))
        view_menu.addAction(toggle_text_action)
        
        toggle_viewer_action = QtWidgets.QAction("Show/Hide Viewer", self)
        toggle_viewer_action.setCheckable(True)
        toggle_viewer_action.setChecked(True)
        toggle_viewer_action.triggered.connect(lambda checked: self._toggle_widget_visibility(self.viewer_placeholder, checked))
        view_menu.addAction(toggle_viewer_action)
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        
        light_theme_action = QtWidgets.QAction("Light", self)
        light_theme_action.setCheckable(True)
        light_theme_action.setChecked(not config.use_dark_theme)
        light_theme_action.triggered.connect(lambda: self._set_theme(False))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QtWidgets.QAction("Dark", self)
        dark_theme_action.setCheckable(True)
        dark_theme_action.setChecked(config.use_dark_theme)
        dark_theme_action.triggered.connect(lambda: self._set_theme(True))
        theme_menu.addAction(dark_theme_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QtWidgets.QAction("&About", self)
        about_action.triggered.connect(self._show_about_dialog)
        help_menu.addAction(about_action)
        
    def _create_toolbar(self, layout):
        """Create the main toolbar"""
        toolbar = QtWidgets.QToolBar()
        toolbar.setFloatable(False)
        toolbar.setMovable(False)
        
        # Add refresh button
        refresh_action = toolbar.addAction("Refresh")
        refresh_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        refresh_action.setToolTip("Refresh from Maya selection")
        refresh_action.triggered.connect(self._refresh_from_maya)
        
        # Add separator
        toolbar.addSeparator()
        
        # Add layout options
        layout_label = QtWidgets.QLabel("Layout:")
        toolbar.addWidget(layout_label)
        
        layout_combo = QtWidgets.QComboBox()
        layout_combo.addItems(["Horizontal", "Vertical", "Grid", "Custom"])
        layout_combo.setCurrentIndex(0)  # Default to horizontal
        layout_combo.currentIndexChanged.connect(self._change_layout)
        toolbar.addWidget(layout_combo)
        
        # Add separator
        toolbar.addSeparator()
        
        # Add expandable spacer
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # Add settings button
        settings_action = toolbar.addAction("Settings")
        settings_action.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        settings_action.triggered.connect(self._show_settings_dialog)
        
        # Add toolbar to layout
        layout.addWidget(toolbar)
        
    def _create_views(self):
        """Create the main view components"""
        # Create tree panel
        self.tree_panel = UsdTreePanel()
        
        # Create property editor
        self.property_editor = PropertyEditor()
        
        # Create stage text panel
        self.stage_text_panel = StageTextPanel()
        
        # Create viewer placeholder
        self.viewer_placeholder = ViewerPlaceholder()
        
        # Add panels to splitters
        self.left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(self.left_widget)
        left_layout.addWidget(self.tree_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.right_top_widget = QtWidgets.QWidget()
        right_top_layout = QtWidgets.QVBoxLayout(self.right_top_widget)
        right_top_layout.addWidget(self.property_editor)
        right_top_layout.setContentsMargins(0, 0, 0, 0)
        
        self.right_bottom_widget = QtWidgets.QWidget()
        right_bottom_layout = QtWidgets.QVBoxLayout(self.right_bottom_widget)
        
        # Add the stage text and viewer to a tab widget
        self.right_bottom_tabs = QtWidgets.QTabWidget()
        self.right_bottom_tabs.addTab(self.stage_text_panel, "Stage Text")
        self.right_bottom_tabs.addTab(self.viewer_placeholder, "Viewer (Not Implemented)")
        
        right_bottom_layout.addWidget(self.right_bottom_tabs)
        right_bottom_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add widgets to splitters
        self.vertical_splitter.addWidget(self.right_top_widget)
        self.vertical_splitter.addWidget(self.right_bottom_widget)
        
        self.horizontal_splitter.addWidget(self.left_widget)
        self.horizontal_splitter.addWidget(self.vertical_splitter)
        
        # Set splitter ratios
        self.horizontal_splitter.setSizes([300, 700])
        self.vertical_splitter.setSizes([300, 300])
        
    def _connect_signals(self):
        """Connect signals between components"""
        # Connect tree panel signals
        self.tree_panel.primSelected.connect(self.ui_controller.select_prim)
        self.tree_panel.refresh_requested.connect(self._refresh_from_maya)
        
        # Connect property editor signals
        self.property_editor.kindChanged.connect(self._on_kind_changed)
        self.property_editor.purposeChanged.connect(self._on_purpose_changed)
        self.property_editor.attributeAction.connect(self._on_attribute_action)
        self.property_editor.primvarAction.connect(self._on_primvar_action)
        self.property_editor.variantSelected.connect(self.prim_controller.set_variant_selection)
        self.property_editor.payloadAction.connect(self._on_payload_action)
        self.property_editor.timeSampleAction.connect(self.prim_controller.edit_time_sample)
        self.property_editor.addAttribute.connect(lambda: self.prim_controller.add_attribute(self))
        self.property_editor.addPrimvar.connect(lambda: self.prim_controller.add_primvar(self))
        
        # Connect stage text panel signals
        self.stage_text_panel.updateStage.connect(self.prim_controller.update_stage_from_text)
        self.stage_text_panel.findPrimInTree.connect(self.tree_panel.select_prim_path)
        
        # Connect UI controller signals
        self.ui_controller.stage_loaded.connect(self._on_stage_loaded)
        self.ui_controller.prim_selected.connect(self._on_prim_selected)
        self.ui_controller.update_ui.connect(self._update_ui)
        
        # Connect prim controller signals
        self.prim_controller.operation_completed.connect(self._on_operation_completed)
        
    def _refresh_from_maya(self):
        """Refresh the UI from Maya selection"""
        success = self.ui_controller.load_stage_from_maya_selection()
        if not success:
            self.statusBar().showMessage("Failed to load USD stage from selection")
        
    def _on_stage_loaded(self, stage):
        """Handle stage loaded event"""
        # Set the tree model
        self.tree_panel.set_model(self.ui_controller.tree_model)
        
        # Update the stage text
        self.stage_text_panel.set_text(self.prim_model.get_stage_as_text())
        
        # Clear property editor
        self.property_editor.set_prim_info(None)
        self.property_editor.set_attributes([], [])
        self.property_editor.set_variant_sets([])
        
        self.statusBar().showMessage("Stage loaded successfully")
        
    def _on_prim_selected(self, prim_path):
        """Handle prim selected event"""
        # Update property editor
        prim_info = self.prim_model.get_current_prim_info()
        self.property_editor.set_prim_info(prim_info)
        
        # Update attributes and primvars
        attributes = self.prim_model.get_attributes()
        primvars = self.prim_model.get_primvars()
        self.property_editor.set_attributes(attributes, primvars)
        
        # Update variant sets
        variant_sets = self.prim_model.get_variant_sets()
        self.property_editor.set_variant_sets(variant_sets)
        
        # Highlight in stage text
        self.stage_text_panel.find_prim(prim_path)
        
        self.statusBar().showMessage(f"Selected prim: {prim_path}")
        
    def _update_ui(self):
        """Update the UI after changes"""
        # Update prim info if there's a current prim
        if self.prim_model.current_prim_path:
            prim_info = self.prim_model.get_current_prim_info()
            self.property_editor.set_prim_info(prim_info)
            
            # Update attributes and primvars
            attributes = self.prim_model.get_attributes()
            primvars = self.prim_model.get_primvars()
            self.property_editor.set_attributes(attributes, primvars)
            
            # Update variant sets
            variant_sets = self.prim_model.get_variant_sets()
            self.property_editor.set_variant_sets(variant_sets)
        
        # Update stage text
        self.stage_text_panel.set_text(self.prim_model.get_stage_as_text())
        
    def _on_kind_changed(self, kind):
        """Handle kind changed event"""
        self.ui_controller.apply_kind_purpose(kind, None)
        
    def _on_purpose_changed(self, purpose):
        """Handle purpose changed event"""
        self.ui_controller.apply_kind_purpose(None, purpose)
        
    def _on_attribute_action(self, action, name, value):
        """Handle attribute action event"""
        if action == "edit":
            self.prim_controller.edit_attribute(self, name, value)
        elif action == "remove":
            self.prim_controller.remove_attribute(name)
            
    def _on_primvar_action(self, action, name, value):
        """Handle primvar action event"""
        if action == "edit":
            self.prim_controller.edit_primvar(self, name, value)
        elif action == "remove":
            self.prim_controller.remove_primvar(name)
            
    def _on_payload_action(self, action):
        """Handle payload action event"""
        if action == "load":
            self.prim_controller.load_payload()
        elif action == "unload":
            self.prim_controller.unload_payload()
            
    def _on_operation_completed(self, success, message):
        """Handle operation completed event"""
        if success:
            self.statusBar().showMessage(message)
        else:
            self.statusBar().showMessage(f"Error: {message}")
            
    def _toggle_widget_visibility(self, widget, visible):
        """Toggle the visibility of a widget"""
        widget.setVisible(visible)
        
    def _change_layout(self, index):
        """Change the layout of the splitters"""
        # Remove widgets from splitters
        self.horizontal_splitter.addWidget(self.left_widget)
        self.horizontal_splitter.addWidget(self.vertical_splitter)
        
        # Horizontal layout (default)
        if index == 0:
            self.horizontal_splitter.setOrientation(QtCore.Qt.Horizontal)
            self.vertical_splitter.setOrientation(QtCore.Qt.Vertical)
            
            # Restore widgets
            if self.horizontal_splitter.count() < 2:
                self.horizontal_splitter.addWidget(self.left_widget)
                self.horizontal_splitter.addWidget(self.vertical_splitter)
                
            # Set sizes
            self.horizontal_splitter.setSizes([300, 700])
            self.vertical_splitter.setSizes([300, 300])
            
        # Vertical layout
        elif index == 1:
            self.horizontal_splitter.setOrientation(QtCore.Qt.Vertical)
            self.vertical_splitter.setOrientation(QtCore.Qt.Horizontal)
            
            # Restore widgets
            if self.horizontal_splitter.count() < 2:
                self.horizontal_splitter.addWidget(self.left_widget)
                self.horizontal_splitter.addWidget(self.vertical_splitter)
                
            # Set sizes
            self.horizontal_splitter.setSizes([300, 700])
            self.vertical_splitter.setSizes([400, 400])
            
        # Grid layout
        elif index == 2:
            # Create new layout if needed
            if not hasattr(self, 'grid_widget'):
                self.grid_widget = QtWidgets.QWidget()
                grid_layout = QtWidgets.QGridLayout(self.grid_widget)
                grid_layout.addWidget(self.tree_panel, 0, 0)
                grid_layout.addWidget(self.property_editor, 0, 1)
                grid_layout.addWidget(self.stage_text_panel, 1, 0)
                grid_layout.addWidget(self.viewer_placeholder, 1, 1)
                grid_layout.setContentsMargins(0, 0, 0, 0)
                
            # Remove widgets from splitters
            for i in range(self.horizontal_splitter.count()):
                self.horizontal_splitter.widget(0).setParent(None)
                
            # Add grid widget
            self.horizontal_splitter.addWidget(self.grid_widget)
            
        # Custom layout (reset to default)
        else:
            self._change_layout(0)
            
    def _set_theme(self, dark_theme):
        """Set the application theme"""
        if dark_theme:
            # Dark theme
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor(42, 42, 42))
            palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(66, 66, 66))
            palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
            palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
            palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
            palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
            palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
            
            # Apply the palette
            QtWidgets.QApplication.setPalette(palette)
            
            # Save to config
            config.use_dark_theme = True
            
        else:
            # Light theme (default)
            QtWidgets.QApplication.setPalette(QtWidgets.QApplication.style().standardPalette())
            
            # Save to config
            config.use_dark_theme = False
            
    def _show_settings_dialog(self):
        """Show settings dialog"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(400)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # Create form layout for settings
        form = QtWidgets.QFormLayout()
        
        # Auto-expand tree
        auto_expand_check = QtWidgets.QCheckBox()
        auto_expand_check.setChecked(config.auto_expand_tree)
        form.addRow("Auto-expand tree:", auto_expand_check)
        
        # Max expanded depth
        depth_spin = QtWidgets.QSpinBox()
        depth_spin.setRange(1, 10)
        depth_spin.setValue(config.max_expanded_depth)
        form.addRow("Max auto-expand depth:", depth_spin)
        
        # Lazy loading
        lazy_loading_check = QtWidgets.QCheckBox()
        lazy_loading_check.setChecked(config.lazy_loading)
        form.addRow("Lazy loading:", lazy_loading_check)
        
        # Cache prim info
        cache_check = QtWidgets.QCheckBox()
        cache_check.setChecked(config.cache_prim_info)
        form.addRow("Cache prim info:", cache_check)
        
        # Alternating row colors
        alternating_check = QtWidgets.QCheckBox()
        alternating_check.setChecked(config.tree_background_alternating)
        form.addRow("Alternating row colors:", alternating_check)
        
        # Max items per batch
        batch_spin = QtWidgets.QSpinBox()
        batch_spin.setRange(10, 1000)
        batch_spin.setValue(config.max_items_per_batch)
        form.addRow("Max items per batch:", batch_spin)
        
        layout.addLayout(form)
        
        # Add buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        # Execute dialog
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Save settings to config
            config.auto_expand_tree = auto_expand_check.isChecked()
            config.max_expanded_depth = depth_spin.value()
            config.lazy_loading = lazy_loading_check.isChecked()
            config.cache_prim_info = cache_check.isChecked()
            config.tree_background_alternating = alternating_check.isChecked()
            config.max_items_per_batch = batch_spin.value()
            
            # Apply some settings immediately
            self.tree_panel.tree_view.setAlternatingRowColors(config.tree_background_alternating)
            
            # Save settings to file
            self._save_config()
            
            # Show success message
            self.statusBar().showMessage("Settings saved")
            
    def _show_about_dialog(self):
        """Show about dialog"""
        QtWidgets.QMessageBox.about(
            self, 
            "About USD Prim Editor",
            """<h2>USD Prim Editor</h2>
            <p>Version 2.0.0</p>
            <p>A tool for editing USD prims within Maya.</p>
            <p>Features:</p>
            <ul>
                <li>Edit prim properties (kind, purpose, etc.)</li>
                <li>Edit attributes and primvars</li>
                <li>Manage variant sets</li>
                <li>View and edit stage text</li>
                <li>Improved performance for large stages</li>
            </ul>
            """
        )
        
    def _save_config(self):
        """Save configuration to file"""
        # Save window size
        config.window_width = self.width()
        config.window_height = self.height()
        
        # Save to file
        config_path = get_default_config_path()
        if save_config_to_file(config_path):
            self.statusBar().showMessage(f"Configuration saved to {config_path}")
        else:
            self.statusBar().showMessage("Failed to save configuration")
            
    def _load_config(self):
        """Load configuration from file"""
        config_path = get_default_config_path()
        if load_config_from_file(config_path):
            # Apply some settings
            self.resize(config.window_width, config.window_height)
            self._set_theme(config.use_dark_theme)
            
            # Update tree view settings
            if hasattr(self, 'tree_panel'):
                self.tree_panel.tree_view.setAlternatingRowColors(config.tree_background_alternating)
                
            self.statusBar().showMessage(f"Configuration loaded from {config_path}")
        
    def closeEvent(self, event):
        """Handle close event"""
        # Save configuration on close
        self._save_config()
        super().closeEvent(event)
        
    @property
    def prim_model(self):
        """Get the prim model"""
        return self.prim_model


def show_usd_prim_editor():
    """Show the USD Prim Editor window"""
    global usd_prim_editor
    
    # Close existing window if it exists
    try:
        usd_prim_editor.close()
        usd_prim_editor.deleteLater()
    except:
        pass
        
    # Create new window
    usd_prim_editor = UsdPrimEditorWindow()
    usd_prim_editor.show()
    
    # Refresh the UI
    usd_prim_editor._refresh_from_maya()
    
    return usd_prim_editor

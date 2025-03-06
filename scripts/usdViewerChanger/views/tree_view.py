from typing import Optional, List
from PySide6 import QtWidgets, QtCore, QtGui

from ..models.tree_model import UsdTreeModel
from ..config import config


class UsdTreeView(QtWidgets.QTreeView):
    """Enhanced tree view for USD prims with performance optimizations"""
    
    # Signals
    primSelected = QtCore.Signal(str)  # Emitted when a prim is selected
    
    def __init__(self, parent=None):
        super(UsdTreeView, self).__init__(parent)
        
        # Set up visual appearance
        self.setAlternatingRowColors(config.tree_background_alternating)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        
        # Optimize performance for large datasets
        self.setUniformRowHeights(True)  # All rows have same height (faster)
        self.setItemsExpandable(True)
        self.setSortingEnabled(False)  # Sorting is expensive
        
        # Enable context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Connect signals
        self.expanded.connect(self._on_item_expanded)
        self.collapsed.connect(self._on_item_collapsed)
        
    def set_model(self, model: UsdTreeModel) -> None:
        """Set the tree model with proper connections"""
        # Disconnect old selection model if it exists
        if self.selectionModel():
            self.selectionModel().selectionChanged.disconnect(self._on_selection_changed)
        
        # Set new model
        super(UsdTreeView, self).setModel(model)
        
        # Connect new selection model
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)
        
        # Restore expansion state
        self._restore_expansion()
        
    def select_prim_path(self, prim_path: str) -> bool:
        """Select a prim by its path"""
        if not self.model():
            return False
            
        # Find the model index for the prim path
        found_index = self._find_index_by_path(prim_path)
        if not found_index.isValid():
            return False
            
        # Expand parent items to make the selected item visible
        parent_index = found_index.parent()
        while parent_index.isValid():
            self.expand(parent_index)
            parent_index = parent_index.parent()
            
        # Select the item
        self.selectionModel().select(
            found_index, 
            QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows
        )
        
        # Scroll to the item
        self.scrollTo(found_index)
        
        return True
        
    def _find_index_by_path(self, prim_path: str, parent_index=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        """Find a model index by prim path"""
        model = self.model()
        if not model:
            return QtCore.QModelIndex()
            
        # Search all rows at this level
        for row in range(model.rowCount(parent_index)):
            index = model.index(row, 0, parent_index)
            path = index.data(QtCore.Qt.UserRole)
            
            if path == prim_path:
                return index
                
            # Recursively search children
            if model.hasChildren(index):
                child_index = self._find_index_by_path(prim_path, index)
                if child_index.isValid():
                    return child_index
                    
        return QtCore.QModelIndex()
        
    def _on_selection_changed(self, selected, deselected) -> None:
        """Handle selection changes"""
        indexes = selected.indexes()
        if not indexes:
            return
            
        # Use the first column of the selected row
        index = indexes[0]
        prim_path = index.data(QtCore.Qt.UserRole)
        
        # Emit signal with the prim path
        self.primSelected.emit(prim_path)
        
    def _on_item_expanded(self, index: QtCore.QModelIndex) -> None:
        """Handle item expansion"""
        model = self.model()
        if isinstance(model, UsdTreeModel):
            model.track_expanded(index, True)
            
    def _on_item_collapsed(self, index: QtCore.QModelIndex) -> None:
        """Handle item collapse"""
        model = self.model()
        if isinstance(model, UsdTreeModel):
            model.track_expanded(index, False)
            
    def _restore_expansion(self) -> None:
        """Restore expansion state after model change"""
        model = self.model()
        if not isinstance(model, UsdTreeModel):
            return
            
        def expand_item(parent_index=QtCore.QModelIndex()):
            for row in range(model.rowCount(parent_index)):
                index = model.index(row, 0, parent_index)
                if model.should_expand(index):
                    self.expand(index)
                    expand_item(index)
                    
        # Start expansion from root
        expand_item()
        
    def _show_context_menu(self, position: QtCore.QPoint) -> None:
        """Show context menu for tree items"""
        index = self.indexAt(position)
        if not index.isValid():
            return
            
        # Get prim path
        prim_path = index.data(QtCore.Qt.UserRole)
        
        # Create context menu
        menu = QtWidgets.QMenu(self)
        
        # Add common actions
        expand_action = menu.addAction("Expand All Children")
        collapse_action = menu.addAction("Collapse All Children")
        menu.addSeparator()
        
        # Find in stage text action
        find_action = menu.addAction("Find in Stage Text")
        
        # Execute menu
        action = menu.exec_(self.viewport().mapToGlobal(position))
        
        # Handle action
        if action == expand_action:
            self.expandRecursively(index)
        elif action == collapse_action:
            self.collapse_recursively(index)
        elif action == find_action:
            self.parent().find_in_stage_text(prim_path)
            
    def collapse_recursively(self, index: QtCore.QModelIndex) -> None:
        """Custom method to collapse an item and all its children"""
        model = self.model()
        if not model:
            return
            
        # First collapse all children
        self._collapse_children(index)
        
        # Then collapse the item itself
        self.collapse(index)
        
        # Update tracking in model
        if isinstance(model, UsdTreeModel):
            model.track_expanded(index, False)
            
    def _collapse_children(self, parent_index: QtCore.QModelIndex) -> None:
        """Recursively collapse all children"""
        model = self.model()
        if not model:
            return
            
        for row in range(model.rowCount(parent_index)):
            child_index = model.index(row, 0, parent_index)
            if model.hasChildren(child_index):
                self._collapse_children(child_index)
                self.collapse(child_index)
                
                # Update tracking in model
                if isinstance(model, UsdTreeModel):
                    model.track_expanded(child_index, False)


class UsdTreePanel(QtWidgets.QWidget):
    """Panel containing the tree view and related controls"""
    
    def __init__(self, parent=None):
        super(UsdTreePanel, self).__init__(parent)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = QtWidgets.QHBoxLayout()
        
        # Add refresh button
        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        self.refresh_button.setToolTip("Refresh the tree from the current USD stage")
        toolbar.addWidget(self.refresh_button)
        
        # Add expand/collapse buttons
        self.expand_all_button = QtWidgets.QPushButton("Expand All")
        self.expand_all_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogListView))
        self.expand_all_button.setToolTip("Expand all items in the tree")
        toolbar.addWidget(self.expand_all_button)
        
        self.collapse_all_button = QtWidgets.QPushButton("Collapse All")
        self.collapse_all_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_FileDialogDetailedView))
        self.collapse_all_button.setToolTip("Collapse all items in the tree")
        toolbar.addWidget(self.collapse_all_button)
        
        # Add filter
        self.filter_label = QtWidgets.QLabel("Filter:")
        toolbar.addWidget(self.filter_label)
        
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.setPlaceholderText("Filter by name...")
        toolbar.addWidget(self.filter_edit)
        
        toolbar.addStretch()
        
        # Add toolbar to layout
        layout.addLayout(toolbar)
        
        # Create tree view
        self.tree_view = UsdTreeView()
        layout.addWidget(self.tree_view)
        
        # Connect signals
        self.refresh_button.clicked.connect(self.refresh_requested)
        self.expand_all_button.clicked.connect(self._expand_all)
        self.collapse_all_button.clicked.connect(self._collapse_all)
        self.filter_edit.textChanged.connect(self._apply_filter)
        
        # Set up a timer for delayed filtering
        self.filter_timer = QtCore.QTimer(self)
        self.filter_timer.setSingleShot(True)
        self.filter_timer.timeout.connect(self._apply_filter_delayed)
        
    def set_model(self, model: UsdTreeModel) -> None:
        """Set the tree model"""
        self.tree_view.set_model(model)
        
    def select_prim_path(self, prim_path: str) -> bool:
        """Select a prim by its path"""
        return self.tree_view.select_prim_path(prim_path)
        
    def get_selected_prim_path(self) -> Optional[str]:
        """Get the currently selected prim path"""
        indexes = self.tree_view.selectionModel().selectedIndexes()
        if not indexes:
            return None
            
        return indexes[0].data(QtCore.Qt.UserRole)
        
    def _expand_all(self) -> None:
        """Expand all items in the tree"""
        self.tree_view.expandAll()
        
        # Update tracking in model
        model = self.tree_view.model()
        if isinstance(model, UsdTreeModel):
            def track_all_expanded(parent_index=QtCore.QModelIndex()):
                for row in range(model.rowCount(parent_index)):
                    index = model.index(row, 0, parent_index)
                    model.track_expanded(index, True)
                    track_all_expanded(index)
                    
            track_all_expanded()
            
    def _collapse_all(self) -> None:
        """Collapse all items in the tree"""
        self.tree_view.collapseAll()
        
        # Update tracking in model
        model = self.tree_view.model()
        if isinstance(model, UsdTreeModel):
            def track_all_collapsed(parent_index=QtCore.QModelIndex()):
                for row in range(model.rowCount(parent_index)):
                    index = model.index(row, 0, parent_index)
                    model.track_expanded(index, False)
                    track_all_collapsed(index)
                    
            track_all_collapsed()
            
    def _apply_filter(self) -> None:
        """Apply filter to tree view with delay"""
        self.filter_timer.start(300)  # 300ms delay
        
    def _apply_filter_delayed(self) -> None:
        """Apply filter to tree view"""
        filter_text = self.filter_edit.text().strip().lower()
        
        if not filter_text:
            # Show all items if filter is empty
            self._show_all_items()
            return
            
        # Apply filter
        self._filter_tree(filter_text)
        
    def _show_all_items(self, parent_index=QtCore.QModelIndex()) -> None:
        """Show all items in the tree"""
        model = self.tree_view.model()
        if not model:
            return
            
        # Show the parent row
        if parent_index.isValid():
            self.tree_view.setRowHidden(parent_index.row(), parent_index.parent(), False)
            
        # Recursively show all children
        for row in range(model.rowCount(parent_index)):
            child_index = model.index(row, 0, parent_index)
            self.tree_view.setRowHidden(row, parent_index, False)
            self._show_all_items(child_index)
            
    def _filter_tree(self, filter_text: str, parent_index=QtCore.QModelIndex()) -> bool:
        """Filter the tree by name, returns True if any child matches"""
        model = self.tree_view.model()
        if not model:
            return False
            
        any_child_matches = False
        
        # Check all children
        for row in range(model.rowCount(parent_index)):
            child_index = model.index(row, 0, parent_index)
            child_matches = False
            
            # Check if this item matches
            name = child_index.data().lower()
            if filter_text in name:
                child_matches = True
                
            # Check if any descendants match
            descendants_match = self._filter_tree(filter_text, child_index)
            
            # Show or hide this row
            self.tree_view.setRowHidden(row, parent_index, not (child_matches or descendants_match))
            
            # Expand if this item or any descendant matches
            if child_matches or descendants_match:
                self.tree_view.expand(parent_index)
                any_child_matches = True
                
        return any_child_matches
        
    def find_in_stage_text(self, prim_path: str) -> None:
        """Signal to find a prim in stage text"""
        # This method will be connected to a signal in the main window
        self.parent().find_in_stage_text(prim_path)
        
    # Signal forwarding methods
    @property
    def primSelected(self) -> QtCore.Signal:
        """Forward the primSelected signal from the tree view"""
        return self.tree_view.primSelected
        
    # Create a refresh_requested signal
    refresh_requested = QtCore.Signal()

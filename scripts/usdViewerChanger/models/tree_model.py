from typing import Dict, List, Optional, Union, Set
from PySide2 import QtCore, QtGui

from pxr import Usd, UsdGeom, Sdf

from ..utils.usd_utils import get_prim_info, get_child_prims, get_child_prims_lazy, PrimInfo
from ..config import config


class UsdTreeItem:
    """Tree item for USD prims that supports lazy loading"""
    
    def __init__(self, prim: Usd.Prim, parent=None):
        self.prim = prim
        self.parent_item = parent
        self.child_items = []
        self.prim_info = None
        self._children_loaded = False
        self._has_children = None

    def child(self, row: int) -> Optional['UsdTreeItem']:
        """Get child at the specified row"""
        if row < 0 or row >= len(self.child_items):
            return None
        return self.child_items[row]

    def child_count(self) -> int:
        """Get the number of children"""
        if not self._children_loaded and config.lazy_loading:
            # If lazy loading is enabled, only load children when needed
            self._load_children()
        return len(self.child_items)

    def row(self) -> int:
        """Get the row of this item in its parent"""
        if self.parent_item:
            return self.parent_item.child_items.index(self)
        return 0

    def parent(self) -> Optional['UsdTreeItem']:
        """Get the parent item"""
        return self.parent_item

    def get_prim_info(self) -> PrimInfo:
        """Get or compute prim info"""
        if self.prim_info is None:
            self.prim_info = get_prim_info(self.prim)
        return self.prim_info

    def path(self) -> str:
        """Get the prim path as a string"""
        return str(self.prim.GetPath())

    def has_children(self) -> bool:
        """Check if this item has children without loading them"""
        if self._has_children is None:
            # Check if the prim has children - faster than loading all children
            self._has_children = bool(list(self.prim.GetFilteredChildren(predicate=Usd.PrimIsActive & ~Usd.PrimIsAbstract)))
        return self._has_children

    def _load_children(self) -> None:
        """Load children items (lazy loading)"""
        if self._children_loaded:
            return
            
        # Clear any existing children
        self.child_items.clear()
        
        # Get child prims
        child_prims = get_child_prims(self.prim)
        
        # Create child items
        for child_prim in child_prims:
            self.child_items.append(UsdTreeItem(child_prim, self))
            
        self._children_loaded = True
        self._has_children = bool(self.child_items)


class UsdTreeModel(QtCore.QAbstractItemModel):
    """Tree model for USD prims with improved performance"""
    
    COLUMNS = ["Name", "Type", "Kind", "Purpose", "Variants", "Payload"]
    
    def __init__(self, stage: Usd.Stage, parent=None):
        super(UsdTreeModel, self).__init__(parent)
        self.stage = stage
        self.root_item = UsdTreeItem(self.stage.GetPseudoRoot())
        
        # Keep track of expanded items for faster reloading
        self.expanded_paths = set()
        
    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        """Return the number of columns"""
        return len(self.COLUMNS)
    
    def data(self, index: QtCore.QModelIndex, role=QtCore.Qt.DisplayRole) -> Union[str, None, QtGui.QBrush]:
        """Get data for the specified index and role"""
        if not index.isValid():
            return None
            
        item = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            prim_info = item.get_prim_info()
            col = index.column()
            
            if col == 0:
                return prim_info.name
            elif col == 1:
                return prim_info.type_name
            elif col == 2:
                return prim_info.kind
            elif col == 3:
                return prim_info.purpose
            elif col == 4:
                # Display variant sets if available
                if prim_info.has_variants:
                    variant_sets = item.prim.GetVariantSets().GetNames()
                    return ", ".join([f"{name}" for name in variant_sets])
                return ""
            elif col == 5:
                # Display payload status
                return "Yes" if prim_info.has_payload else "No"
        
        elif role == QtCore.Qt.UserRole:
            # Store prim path for easy retrieval later
            return item.path()
            
        elif role == QtCore.Qt.BackgroundRole:
            # Highlight inactive prims
            if not item.prim.IsActive():
                return QtGui.QBrush(QtGui.QColor(200, 200, 200))
            # Highlight abstract prims
            elif item.prim.IsAbstract():
                return QtGui.QBrush(QtGui.QColor(230, 230, 250))
                
        elif role == QtCore.Qt.ForegroundRole:
            # Use different colors based on prim type
            prim_info = item.get_prim_info()
            
            # Inactive prims in gray
            if not item.prim.IsActive():
                return QtGui.QBrush(QtGui.QColor(150, 150, 150))
                
            # Custom coloring based on prim type
            if "Xform" in prim_info.type_name:
                return QtGui.QBrush(QtGui.QColor(0, 120, 215))
            elif prim_info.type_name == "Mesh":
                return QtGui.QBrush(QtGui.QColor(0, 150, 0))
            elif prim_info.type_name in ["Camera", "Light"]:
                return QtGui.QBrush(QtGui.QColor(200, 120, 0))
                
        return None
    
    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        """Return item flags"""
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    
    def headerData(self, section: int, orientation: QtCore.Qt.Orientation, role=QtCore.Qt.DisplayRole) -> str:
        """Get header data"""
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.COLUMNS[section]
        return None
    
    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        """Create an index for the specified row and column"""
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
            
        parent_item = self.root_item
        if parent.isValid():
            parent_item = parent.internalPointer()
            
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QtCore.QModelIndex()
    
    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """Get the parent index"""
        if not index.isValid():
            return QtCore.QModelIndex()
            
        child_item = index.internalPointer()
        parent_item = child_item.parent()
        
        if parent_item == self.root_item or parent_item is None:
            return QtCore.QModelIndex()
            
        return self.createIndex(parent_item.row(), 0, parent_item)
    
    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        """Get the number of rows"""
        if parent.column() > 0:
            return 0
            
        parent_item = self.root_item
        if parent.isValid():
            parent_item = parent.internalPointer()
            
        return parent_item.child_count()
    
    def hasChildren(self, parent=QtCore.QModelIndex()) -> bool:
        """Check if index has children without loading them"""
        if not parent.isValid():
            return self.root_item.has_children()
            
        return parent.internalPointer().has_children()
        
    def refresh(self) -> None:
        """Refresh the model"""
        # Save expanded paths before reset
        self.expanded_paths = set()
        self.beginResetModel()
        # Create a new root item
        self.root_item = UsdTreeItem(self.stage.GetPseudoRoot())
        self.endResetModel()
        
    def track_expanded(self, index: QtCore.QModelIndex, expanded: bool) -> None:
        """Track expanded items"""
        if not index.isValid():
            return
            
        path = index.data(QtCore.Qt.UserRole)
        if expanded:
            self.expanded_paths.add(path)
        elif path in self.expanded_paths:
            self.expanded_paths.remove(path)
            
    def should_expand(self, index: QtCore.QModelIndex) -> bool:
        """Check if the index should be expanded"""
        if not index.isValid():
            return False
            
        # Check if the path is in the expanded paths
        path = index.data(QtCore.Qt.UserRole)
        # Also check for auto-expand based on depth
        if config.auto_expand_tree:
            depth = len(path.split('/')) - 2  # Adjust for root and starting '/'
            if depth <= config.max_expanded_depth:
                return True
                
        return path in self.expanded_paths

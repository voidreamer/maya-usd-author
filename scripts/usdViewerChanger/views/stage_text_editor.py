from typing import Optional
from PySide2 import QtWidgets, QtCore, QtGui


class UsdSyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for USD files"""
    
    def __init__(self, document):
        super(UsdSyntaxHighlighter, self).__init__(document)
        
        # Keyword format
        self.keyword_format = QtGui.QTextCharFormat()
        self.keyword_format.setForeground(QtGui.QColor(120, 120, 250))
        self.keyword_format.setFontWeight(QtGui.QFont.Bold)
        
        # Prim type format
        self.prim_type_format = QtGui.QTextCharFormat()
        self.prim_type_format.setForeground(QtGui.QColor(70, 160, 70))
        self.prim_type_format.setFontWeight(QtGui.QFont.Bold)
        
        # Attribute format
        self.attribute_format = QtGui.QTextCharFormat()
        self.attribute_format.setForeground(QtGui.QColor(150, 150, 50))
        
        # Value format
        self.value_format = QtGui.QTextCharFormat()
        self.value_format.setForeground(QtGui.QColor(220, 120, 30))
        
        # Comment format
        self.comment_format = QtGui.QTextCharFormat()
        self.comment_format.setForeground(QtGui.QColor(120, 120, 120))
        self.comment_format.setFontItalic(True)
        
        # Bracket format
        self.bracket_format = QtGui.QTextCharFormat()
        self.bracket_format.setForeground(QtGui.QColor(180, 180, 180))
        self.bracket_format.setFontWeight(QtGui.QFont.Bold)
        
        # Setup rules
        self._setup_rules()
        
    def _setup_rules(self):
        """Setup highlighting rules"""
        self.rules = []
        
        # Keywords
        keywords = [
            'def', 'over', 'class', 'variantSet', 'variant', 'rel', 
            'add', 'custom', 'uniform', 'subLayers', 'references',
            'inherits', 'specializes', 'payload', 'kind', 'defaultPrim'
        ]
        
        for word in keywords:
            pattern = QtCore.QRegExp('\\b' + word + '\\b')
            self.rules.append((pattern, self.keyword_format))
        
        # Prim types
        prim_types = [
            'Xform', 'Mesh', 'Scope', 'Material', 'Shader', 'Camera',
            'Light', 'SphereLight', 'DiskLight', 'DistantLight', 'DomeLight',
            'GeomSubset', 'Points', 'SkelRoot', 'Skeleton', 'PackedUSD'
        ]
        
        for word in prim_types:
            pattern = QtCore.QRegExp('\\b' + word + '\\b')
            self.rules.append((pattern, self.prim_type_format))
        
        # Attributes (words followed by =)
        self.rules.append((QtCore.QRegExp('\\b\\w+\\s*='), self.attribute_format))
        
        # Values (quoted strings)
        self.rules.append((QtCore.QRegExp('"[^"]*"'), self.value_format))
        self.rules.append((QtCore.QRegExp("'[^']*'"), self.value_format))
        
        # Numbers
        self.rules.append((QtCore.QRegExp('\\b[0-9]+\\.[0-9]*\\b'), self.value_format))
        self.rules.append((QtCore.QRegExp('\\b[0-9]+\\b'), self.value_format))
        
        # Brackets
        self.rules.append((QtCore.QRegExp('[{}()\\[\\]]'), self.bracket_format))
        
        # Comments
        self.rules.append((QtCore.QRegExp('#[^\n]*'), self.comment_format))
        
    def highlightBlock(self, text):
        """Apply highlighting to the given block of text"""
        for pattern, format in self.rules:
            expression = QtCore.QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)


class LineNumberArea(QtWidgets.QWidget):
    """Line number area for the text editor"""
    
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.editor = editor
        
    def sizeHint(self):
        """Recommend width based on line numbers needed"""
        return QtCore.QSize(self.editor.line_number_area_width(), 0)
        
    def paintEvent(self, event):
        """Paint the line numbers"""
        self.editor.paint_line_numbers(event)


class StageTextEditor(QtWidgets.QPlainTextEdit):
    """Text editor for USD stage content with line numbers and syntax highlighting"""
    
    # Signals
    updateRequested = QtCore.Signal(str)  # Signal to update the stage
    findPrimRequested = QtCore.Signal(str)  # Signal to find a prim in the tree
    
    def __init__(self, parent=None):
        super(StageTextEditor, self).__init__(parent)
        
        # Set fixed width font
        font = QtGui.QFont("Courier New", 10)
        font.setFixedPitch(True)
        self.setFont(font)
        
        # Set tab width
        metrics = QtGui.QFontMetrics(font)
        self.setTabStopWidth(4 * metrics.width(' '))
        
        # Add line numbers
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)
        
        # Set color scheme
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2b2b2b;
                color: #a9b7c6;
            }
        """)
        
        # Apply syntax highlighting
        self.highlighter = UsdSyntaxHighlighter(self.document())
        
        # Context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def line_number_area_width(self):
        """Calculate the width of the line number area"""
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
            
        space = 3 + self.fontMetrics().width('9') * digits
        return space
        
    def update_line_number_area_width(self, _):
        """Update the width of the line number area"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
        
    def update_line_number_area(self, rect, dy):
        """Update the line number area"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
            
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)
            
    def resizeEvent(self, event):
        """Handle resize events"""
        super(StageTextEditor, self).resizeEvent(event)
        
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(), 
                                                      self.line_number_area_width(), cr.height()))
                                                      
    def paint_line_numbers(self, event):
        """Paint line numbers"""
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor(45, 45, 45))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QtGui.QColor(150, 150, 150))
                painter.drawText(0, top, self.line_number_area.width() - 3, 
                                self.fontMetrics().height(),
                                QtCore.Qt.AlignRight, number)
                                
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
            
    def find_text(self, text, case_sensitive=False):
        """Find text in the editor"""
        if not text:
            return False
            
        # Options for find
        options = QtGui.QTextDocument.FindFlags()
        if case_sensitive:
            options |= QtGui.QTextDocument.FindCaseSensitively
            
        # Start from current position
        cursor = self.textCursor()
        orig_pos = cursor.position()
        
        # Search for text
        if not self.find(text, options):
            # If not found, start from beginning
            cursor.setPosition(0)
            self.setTextCursor(cursor)
            
            if not self.find(text, options):
                # Return to original position if not found
                cursor.setPosition(orig_pos)
                self.setTextCursor(cursor)
                return False
                
        return True
        
    def find_prim(self, prim_path):
        """Find a prim in the stage text"""
        if not prim_path:
            return
            
        # Format the prim path for searching
        search_text = prim_path
        
        # Try to find the prim declaration
        patterns = [
            f'def\\s+\\w+\\s+"{search_text}"',  # def Type "path"
            f'def\\s+\\w+\\s+{search_text}',     # def Type path
            f'over\\s+\\w+\\s+"{search_text}"',  # over Type "path"
            f'over\\s+\\w+\\s+{search_text}'     # over Type path
        ]
        
        for pattern in patterns:
            cursor = self.document().find(QtCore.QRegExp(pattern))
            if not cursor.isNull():
                self.setTextCursor(cursor)
                self.centerCursor()
                return True
                
        # If not found, try to find the prim path anywhere
        return self.find_text(prim_path, False)
        
    def _show_context_menu(self, position):
        """Show custom context menu"""
        menu = self.createStandardContextMenu()
        
        # Add custom actions
        menu.addSeparator()
        
        # Find action
        find_action = menu.addAction("Find...")
        find_action.setShortcut(QtGui.QKeySequence.Find)
        
        # Goto line action
        goto_action = menu.addAction("Go to Line...")
        goto_action.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        
        # Find prim action
        cursor = self.textCursor()
        selected_text = cursor.selectedText()
        
        if selected_text:
            find_prim_action = menu.addAction(f"Find Prim in Tree: {selected_text}")
        
        # Execute menu
        action = menu.exec_(self.viewport().mapToGlobal(position))
        
        # Handle actions
        if action == find_action:
            self._show_find_dialog()
        elif action == goto_action:
            self._show_goto_dialog()
        elif selected_text and action == find_prim_action:
            self.findPrimRequested.emit(selected_text)
            
    def _show_find_dialog(self):
        """Show find dialog"""
        text, ok = QtWidgets.QInputDialog.getText(
            self, "Find", "Find what:", text=self.textCursor().selectedText()
        )
        
        if ok and text:
            self.find_text(text)
            
    def _show_goto_dialog(self):
        """Show goto line dialog"""
        line, ok = QtWidgets.QInputDialog.getInt(
            self, "Go to Line", "Line number:", 1, 1, self.document().blockCount()
        )
        
        if ok:
            cursor = QtGui.QTextCursor(self.document().findBlockByNumber(line - 1))
            self.setTextCursor(cursor)
            self.centerCursor()


class StageTextPanel(QtWidgets.QWidget):
    """Panel for editing USD stage as text"""
    
    # Signals
    updateStage = QtCore.Signal(str)  # Signal to update the stage from text
    findPrimInTree = QtCore.Signal(str)  # Signal to find a prim in the tree
    
    def __init__(self, parent=None):
        super(StageTextPanel, self).__init__(parent)
        
        # Create layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Create toolbar
        toolbar = QtWidgets.QHBoxLayout()
        
        # Add search box
        search_label = QtWidgets.QLabel("Search:")
        toolbar.addWidget(search_label)
        
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setClearButtonEnabled(True)
        self.search_box.setPlaceholderText("Search in stage text...")
        self.search_box.returnPressed.connect(self._search_text)
        toolbar.addWidget(self.search_box)
        
        # Add search button
        self.search_button = QtWidgets.QPushButton("Find")
        self.search_button.clicked.connect(self._search_text)
        toolbar.addWidget(self.search_button)
        
        # Add update button
        self.update_button = QtWidgets.QPushButton("Update Stage")
        self.update_button.clicked.connect(self._update_stage)
        toolbar.addWidget(self.update_button)
        
        toolbar.addStretch()
        
        # Add toolbar to layout
        layout.addLayout(toolbar)
        
        # Create text editor
        self.editor = StageTextEditor()
        self.editor.setReadOnly(False)  # Allow editing
        layout.addWidget(self.editor)
        
        # Connect signals
        self.editor.updateRequested.connect(self.updateStage.emit)
        self.editor.findPrimRequested.connect(self.findPrimInTree.emit)
        
    def set_text(self, text):
        """Set the text in the editor"""
        self.editor.setPlainText(text)
        
    def get_text(self):
        """Get the text from the editor"""
        return self.editor.toPlainText()
        
    def find_prim(self, prim_path):
        """Find a prim in the stage text"""
        return self.editor.find_prim(prim_path)
        
    def _search_text(self):
        """Search for text in the editor"""
        text = self.search_box.text()
        if text:
            self.editor.find_text(text)
            
    def _update_stage(self):
        """Update the stage from the editor text"""
        text = self.get_text()
        self.updateStage.emit(text)

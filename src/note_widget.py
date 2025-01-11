from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLineEdit, QLabel, QMenu, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (QAction, QColor, QPalette, QTextCharFormat, QSyntaxHighlighter, 
                        QKeySequence, QShortcut)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SearchHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, search_text=""):
        super().__init__(parent)
        self.search_text = search_text
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor("#4d4d00"))  # Dark yellow background
        self.highlight_format.setForeground(QColor("#ffffff"))  # White text

    def set_search_text(self, text):
        self.search_text = text
        self.rehighlight()

    def highlightBlock(self, text):
        if not self.search_text:
            return
            
        for match in text.lower().split(self.search_text.lower()):
            index = text.lower().find(self.search_text.lower(), 
                                    0 if match == text.lower().split(self.search_text.lower())[0] 
                                    else len(match) + len(self.search_text))
            if index >= 0:
                self.setFormat(index, len(self.search_text), self.highlight_format)

class DraggableHeader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()  # Push menu button to the right
        
        # Menu button
        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedWidth(30)
        self.menu_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.menu_button)

class NoteWidget(QWidget):
    deleted = pyqtSignal(int)  # Signal emitted when note is deleted
    updated = pyqtSignal(int, str, str, str, int)  # Signal emitted when note is updated (id, title, content, color, text_size)

    def __init__(self, note_id=None, title="", content="", color="#2d2d2d", text_size=14, parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.search_text = ""
        self.text_size = text_size
        self.color = color
        self.last_modified = None  # Will be set in initUI
        self.content_edit = None   # Will be set in initUI
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.initUI(title, content, color)
        
    def initUI(self, title, content, color):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create a container widget for the note content
        self.content_container = QWidget()
        content_layout = QVBoxLayout(self.content_container)
        content_layout.setSpacing(5)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        self.header_container = DraggableHeader()
        self.header_container.menu_button.clicked.connect(self.show_menu)
        content_layout.addWidget(self.header_container)
        
        # Content area
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Type your note here...")
        self.content_edit.setText(content)
        self.content_edit.textChanged.connect(self.note_modified)
        self.content_edit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.highlighter = SearchHighlighter(self.content_edit.document())
        
        # Set up keyboard shortcuts
        self.increase_size_shortcut = QShortcut(QKeySequence("Ctrl++"), self.content_edit)
        self.increase_size_shortcut.activated.connect(self.increase_text_size)
        
        self.decrease_size_shortcut = QShortcut(QKeySequence("Ctrl+-"), self.content_edit)
        self.decrease_size_shortcut.activated.connect(self.decrease_text_size)
        
        # Alternative shortcuts for numpad
        self.increase_size_shortcut_numpad = QShortcut(QKeySequence("Ctrl+="), self.content_edit)
        self.increase_size_shortcut_numpad.activated.connect(self.increase_text_size)
        
        # Add separator shortcut
        self.add_separator_shortcut = QShortcut(QKeySequence("Ctrl+R"), self.content_edit)
        self.add_separator_shortcut.activated.connect(self.insert_separator)
        
        content_layout.addWidget(self.content_edit)
        
        # Footer with metadata
        footer = QHBoxLayout()
        self.last_modified = QLabel("Last modified: Just now")
        footer.addWidget(self.last_modified)
        
        content_layout.addLayout(footer)
        
        # Add the container to the main layout
        layout.addWidget(self.content_container)
        
        # Set the note color and text size
        self.set_color(color)
        self.update_text_size(self.text_size)
        
        self.setMinimumSize(300, 200)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        
        logger.debug("Note widget UI initialized")
    
    def highlight_search(self, search_text):
        self.search_text = search_text
        self.highlighter.set_search_text(search_text)
    
    def update_text_size(self, size):
        self.text_size = size
        if self.content_edit:  # Check if content_edit exists
            self.content_edit.setStyleSheet(f"font-size: {size}px;")
            self.note_modified()
    
    def show_menu(self):
        menu = QMenu(self)
        
        # Color submenu
        color_menu = QMenu("Change Color", self)
        colors = {
            "Dark Gray": "#2d2d2d",
            "Blue": "#1e3242",
            "Green": "#1e3c2d",
            "Purple": "#2d1e42",
            "Red": "#421e1e",
            "Orange": "#422d1e"
        }
        
        for name, color in colors.items():
            action = QAction(name, self)
            action.triggered.connect(lambda checked, c=color: self.set_color(c))
            color_menu.addAction(action)
        
        menu.addMenu(color_menu)
        
        # Text size submenu
        text_size_menu = QMenu("Text Size", self)
        
        # Decrease text size action
        decrease_action = QAction("Decrease Size", self)
        decrease_action.triggered.connect(lambda: self.update_text_size(max(8, self.text_size - 2)))
        text_size_menu.addAction(decrease_action)
        
        # Reset text size action
        reset_action = QAction("Reset Size (14px)", self)
        reset_action.triggered.connect(lambda: self.update_text_size(14))
        text_size_menu.addAction(reset_action)
        
        # Increase text size action
        increase_action = QAction("Increase Size", self)
        increase_action.triggered.connect(lambda: self.update_text_size(min(32, self.text_size + 2)))
        text_size_menu.addAction(increase_action)
        
        menu.addMenu(text_size_menu)
        menu.addSeparator()
        
        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(self.delete_note)
        menu.addAction(delete_action)
        
        menu.exec(self.mapToGlobal(self.rect().topRight()))
    
    def set_color(self, color):
        self.color = color
        self.content_container.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 5px;
                border: 1px solid #333333;
            }}
            QTextEdit {{
                border: none;
                background: transparent;
                color: #ffffff;
                font-size: {self.text_size}px;
                selection-background-color: #264f78;
            }}
            QTextEdit::placeholder {{
                color: #888888;
            }}
            QPushButton {{
                border: none;
                background: transparent;
                color: #ffffff;
                font-size: 18px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
            }}
            QLabel {{
                color: #888888;
                font-size: 12px;
            }}
            QMenu {{
                background-color: #2d2d2d;
                border: 1px solid #333333;
                color: #ffffff;
            }}
            QMenu::item {{
                padding: 5px 20px;
            }}
            QMenu::item:selected {{
                background-color: #264f78;
            }}
        """)
        self.note_modified()
    
    def note_modified(self):
        if self.note_id is not None and hasattr(self, 'last_modified'):
            self.last_modified.setText(f"Last modified: {datetime.now().strftime('%H:%M:%S')}")
            self.updated.emit(
                self.note_id,
                "",  # Empty title since we removed it
                self.content_edit.toPlainText(),
                self.color,
                self.text_size
            )
    
    def delete_note(self):
        if self.note_id is not None:
            # First emit the signal
            note_id = self.note_id
            self.note_id = None  # Prevent recursive deletion
            self.deleted.emit(note_id)
            # The actual widget deletion will be handled by the main window
            # through the proxy item removal
    
    def enterEvent(self, event):
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        super().leaveEvent(event)
    
    def increase_text_size(self):
        self.update_text_size(min(32, self.text_size + 2))
    
    def decrease_text_size(self):
        self.update_text_size(max(8, self.text_size - 2)) 
    
    def insert_separator(self):
        """Insert a visual separator at the current cursor position."""
        separator = "\n─" * 30 + "\n"  # 30 em dashes
        cursor = self.content_edit.textCursor()
        
        # If there's selected text, replace it
        if cursor.hasSelection():
            cursor.insertText(separator)
        else:
            # If we're at the start of a line, don't add extra newline
            block_text = cursor.block().text()
            position_in_block = cursor.positionInBlock()
            
            if position_in_block == 0 and not block_text:  # Empty line
                separator = separator.lstrip()
            elif position_in_block == len(block_text):  # End of line
                separator = separator
            else:  # Middle of line
                separator = "\n" + separator
            
            cursor.insertText(separator)
        
        self.content_edit.setFocus()  # Keep focus on the text edit 
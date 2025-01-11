from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLineEdit, QLabel, QMenu, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPalette, QTextCharFormat, QSyntaxHighlighter
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
    updated = pyqtSignal(int, str, str)  # Signal emitted when note is updated

    def __init__(self, note_id=None, title="", content="", color="#2d2d2d", parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.search_text = ""
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
        content_layout.addWidget(self.content_edit)
        
        # Footer with metadata
        footer = QHBoxLayout()
        self.last_modified = QLabel("Last modified: Just now")
        footer.addWidget(self.last_modified)
        
        content_layout.addLayout(footer)
        
        # Add the container to the main layout
        layout.addWidget(self.content_container)
        
        # Set the note color
        self.set_color(color)
        
        self.setMinimumSize(300, 200)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
        
        logger.debug("Note widget UI initialized")
    
    def highlight_search(self, search_text):
        self.search_text = search_text
        self.highlighter.set_search_text(search_text)
    
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
                font-size: 14px;
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
        if self.note_id is not None:
            self.last_modified.setText(f"Last modified: {datetime.now().strftime('%H:%M:%S')}")
            self.updated.emit(
                self.note_id,
                "",  # Empty title since we removed it
                self.content_edit.toPlainText()
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
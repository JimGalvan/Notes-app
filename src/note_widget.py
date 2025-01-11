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

class NoteWidget(QWidget):
    deleted = pyqtSignal(int)  # Signal emitted when note is deleted
    updated = pyqtSignal(int, str, str)  # Signal emitted when note is updated

    def __init__(self, note_id=None, title="", content="", color="#2d2d2d", parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.search_text = ""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setMouseTracking(True)
        logger.debug(f"Created note widget with id: {note_id}")
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
        
        # Header layout
        header = QHBoxLayout()
        
        # Title input
        self.title_input = QLineEdit(title)
        self.title_input.setPlaceholderText("Title")
        self.title_input.textChanged.connect(self.note_modified)
        header.addWidget(self.title_input)
        
        # Menu button
        menu_button = QPushButton("⋮")
        menu_button.setFixedWidth(30)
        menu_button.clicked.connect(self.show_menu)
        header.addWidget(menu_button)
        
        content_layout.addLayout(header)
        
        # Content area
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Type your note here...")
        self.content_edit.setText(content)
        self.content_edit.textChanged.connect(self.note_modified)
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
    
    def highlight_search(self, search_text):
        self.search_text = search_text
        self.highlighter.set_search_text(search_text)
        
        # Highlight title matches
        if search_text:
            title_text = self.title_input.text()
            if search_text.lower() in title_text.lower():
                self.title_input.setStyleSheet("""
                    background-color: #4d4d00;
                    border-radius: 3px;
                    padding: 2px 5px;
                """)
            else:
                self.title_input.setStyleSheet("")
        else:
            self.title_input.setStyleSheet("")
    
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
            QLineEdit {{
                border: none;
                background: transparent;
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 5px;
            }}
            QLineEdit::placeholder {{
                color: #888888;
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
                self.title_input.text(),
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
    
    def mousePressEvent(self, event):
        logger.debug(f"Note: Mouse press at {event.pos()}, buttons: {event.buttons()}")
        if event.button() == Qt.MouseButton.LeftButton:
            # Only ignore left button events for dragging
            event.ignore()
            logger.debug("Note: Ignored left mouse press for dragging")
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        logger.debug(f"Note: Mouse release at {event.pos()}")
        if event.button() == Qt.MouseButton.LeftButton:
            event.ignore()
            logger.debug("Note: Ignored left mouse release for dragging")
        else:
            super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        logger.debug(f"Note: Mouse move at {event.pos()}")
        # Always ignore move events to allow dragging
        event.ignore()
        logger.debug("Note: Ignored mouse move for dragging")
    
    def enterEvent(self, event):
        logger.debug("Note widget enter event")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        logger.debug("Note widget leave event")
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event) 
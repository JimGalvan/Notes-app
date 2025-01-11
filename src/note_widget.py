from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QTextEdit, QLineEdit, QLabel, QMenu, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QPalette
from datetime import datetime

class NoteWidget(QWidget):
    deleted = pyqtSignal(int)  # Signal emitted when note is deleted
    updated = pyqtSignal(int, str, str)  # Signal emitted when note is updated

    def __init__(self, note_id=None, title="", content="", color="#2d2d2d", parent=None):
        super().__init__(parent)
        self.note_id = note_id
        self.initUI(title, content, color)
        
    def initUI(self, title, content, color):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
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
        
        layout.addLayout(header)
        
        # Content area
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("Type your note here...")
        self.content_edit.setText(content)
        self.content_edit.textChanged.connect(self.note_modified)
        layout.addWidget(self.content_edit)
        
        # Footer with metadata
        footer = QHBoxLayout()
        self.last_modified = QLabel("Last modified: Just now")
        footer.addWidget(self.last_modified)
        
        layout.addLayout(footer)
        
        # Set the note color
        self.set_color(color)
        
        # Style
        self.setStyleSheet(f"""
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
        
        self.setMinimumSize(300, 200)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum
        )
    
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
        self.setStyleSheet(self.styleSheet().replace(
            QColor(self.color).name(),
            color
        ))
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
            self.deleted.emit(self.note_id)
        self.deleteLater() 
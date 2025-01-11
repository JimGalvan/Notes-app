import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLineEdit, QScrollArea, 
                           QLabel, QSizePolicy, QMessageBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QFont
from database import Database
from note_widget import NoteWidget
from note_operations import NoteOperations
from models import Note

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.session = self.db.get_session()
        self.note_ops = NoteOperations(self.session)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Modern Notes')
        self.setMinimumSize(900, 600)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create toolbar
        toolbar = QHBoxLayout()
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Search notes...')
        self.search_bar.setMinimumHeight(40)
        self.search_bar.textChanged.connect(self.trigger_search)
        toolbar.addWidget(self.search_bar)
        
        # Add note button
        add_button = QPushButton('New Note')
        add_button.setMinimumHeight(40)
        add_button.clicked.connect(self.add_note)
        toolbar.addWidget(add_button)
        
        layout.addLayout(toolbar)
        
        # Create scrollable notes area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.notes_widget = QWidget()
        self.notes_layout = QVBoxLayout(self.notes_widget)
        self.notes_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.notes_layout.setSpacing(10)
        
        scroll.setWidget(self.notes_widget)
        layout.addWidget(scroll)
        
        # Set dark theme style
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #333333;
                border-radius: 5px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #2d2d2d;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QMessageBox {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """)
        
        self.load_notes()
    
    def load_notes(self):
        # Clear existing notes
        while self.notes_layout.count():
            child = self.notes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Load notes from database
        notes = self.note_ops.get_all_notes()
        for note in notes:
            self.add_note_widget(note)
    
    def add_note_widget(self, note: Note = None):
        if note is None:
            # Create new note in database
            note = self.note_ops.create_note("", "", "#ffffff")
        
        # Create note widget
        note_widget = NoteWidget(
            note_id=note.id,
            title=note.title,
            content=note.content,
            color=note.color
        )
        note_widget.updated.connect(self.update_note)
        note_widget.deleted.connect(self.delete_note)
        
        # Add to layout
        self.notes_layout.insertWidget(0, note_widget)
    
    def trigger_search(self):
        # Reset timer
        self.search_timer.stop()
        self.search_timer.start(300)  # Wait for 300ms before performing search
    
    def perform_search(self):
        query = self.search_bar.text().strip()
        if query:
            notes = self.note_ops.search_notes(query)
        else:
            notes = self.note_ops.get_all_notes()
        
        # Update displayed notes
        while self.notes_layout.count():
            child = self.notes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for note in notes:
            self.add_note_widget(note)
    
    def add_note(self):
        self.add_note_widget()
    
    def update_note(self, note_id: int, title: str, content: str):
        self.note_ops.update_note(note_id, title, content)
    
    def delete_note(self, note_id: int):
        if self.note_ops.delete_note(note_id):
            # Note widget will remove itself through the deleted signal
            pass
        else:
            QMessageBox.warning(self, "Error", "Failed to delete note")
    
    def closeEvent(self, event):
        self.db.close()
        super().closeEvent(event)

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 
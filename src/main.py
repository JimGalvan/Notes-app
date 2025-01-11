import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLineEdit, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QIcon, QFont
from database import Database
from note_widget import NoteWidget
from note_operations import NoteOperations
from board_widget import BoardView
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
        self.note_proxies = {}  # Store note proxies for position tracking
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
        
        # Add zoom info
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setStyleSheet("color: #888888; margin-left: 10px;")
        toolbar.addWidget(self.zoom_label)
        
        layout.addLayout(toolbar)
        
        # Create board
        self.board = BoardView()
        layout.addWidget(self.board)
        
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
            QMessageBox {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QMessageBox QPushButton {
                min-width: 80px;
            }
        """)
        
        self.load_notes()
        
        # Add help text
        help_text = QLabel(
            "Controls: Alt+Left Click or Middle Click to pan • Ctrl+Scroll to zoom • "
            "Drag notes to move them"
        )
        help_text.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(help_text)
    
    def load_notes(self):
        # Clear existing notes
        self.board.scene.clear()
        self.board.draw_grid()
        self.note_proxies.clear()
        
        # Load notes from database
        notes = self.note_ops.get_all_notes()
        for note in notes:
            self.add_note_widget(note)
    
    def add_note_widget(self, note: Note = None):
        if note is None:
            # Create new note in database
            note = self.note_ops.create_note("", "", "#2d2d2d")
        
        # Create note widget
        note_widget = NoteWidget(
            note_id=note.id,
            title=note.title,
            content=note.content,
            color=note.color
        )
        note_widget.updated.connect(self.update_note)
        note_widget.deleted.connect(self.delete_note)
        
        # Add to board
        pos = QPointF(note.position_x, note.position_y) if note.position_x is not None else None
        proxy = self.board.add_note(note_widget, pos)
        self.note_proxies[note.id] = proxy
        
        # Apply current search highlighting if exists
        if self.search_bar.text().strip():
            note_widget.highlight_search(self.search_bar.text().strip())
        
        return note_widget
    
    def trigger_search(self):
        self.search_timer.stop()
        self.search_timer.start(300)
    
    def perform_search(self):
        query = self.search_bar.text().strip()
        
        # Store positions of existing notes
        positions = {note_id: proxy.pos() for note_id, proxy in self.note_proxies.items()}
        
        # Clear and reload notes
        self.board.scene.clear()
        self.board.draw_grid()
        self.note_proxies.clear()
        
        # Get matching notes
        notes = self.note_ops.search_notes(query) if query else self.note_ops.get_all_notes()
        
        # Add notes and highlight matches
        for note in notes:
            note_widget = self.add_note_widget(note)
            if query:
                note_widget.highlight_search(query)
            
            # Restore position if it existed before
            if note.id in positions:
                self.note_proxies[note.id].setPos(positions[note.id])
    
    def add_note(self):
        self.add_note_widget()
    
    def update_note(self, note_id: int, title: str, content: str, color: str):
        # Get the note's current position
        if note_id in self.note_proxies:
            pos = self.note_proxies[note_id].pos()
            self.note_ops.update_note(note_id, title, content, color=color, position_x=pos.x(), position_y=pos.y())
        else:
            self.note_ops.update_note(note_id, title, content, color=color)
    
    def delete_note(self, note_id: int):
        if note_id in self.note_proxies:
            self.note_proxies[note_id].scene().removeItem(self.note_proxies[note_id])
            del self.note_proxies[note_id]
        
        if not self.note_ops.delete_note(note_id):
            QMessageBox.warning(self, "Error", "Failed to delete note")
    
    def closeEvent(self, event):
        # Save all note positions before closing
        for note_id, proxy in self.note_proxies.items():
            pos = proxy.pos()
            note_widget = proxy.widget()
            self.note_ops.update_note(note_id, None, None, color=note_widget.color, position_x=pos.x(), position_y=pos.y())
        
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
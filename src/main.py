import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLineEdit, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, QSizeF
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
        toolbar.setContentsMargins(10, 10, 10, 10)
        
        # Create a semi-transparent container for the toolbar
        toolbar_container = QWidget()
        toolbar_container.setObjectName("toolbarContainer")
        toolbar_container.setLayout(toolbar)
        
        # Search container
        search_container = QHBoxLayout()
        search_container.setSpacing(0)
        
        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText('Search notes...')
        self.search_bar.setMinimumHeight(40)
        self.search_bar.textChanged.connect(self.trigger_search)
        search_container.addWidget(self.search_bar)
        
        # Clear search button
        clear_search_button = QPushButton("✕")
        clear_search_button.setFixedWidth(40)
        clear_search_button.setMinimumHeight(40)
        clear_search_button.clicked.connect(lambda: self.search_bar.setText(""))
        clear_search_button.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border-top-left-radius: 0;
                border-bottom-left-radius: 0;
                color: #888888;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
        search_container.addWidget(clear_search_button)
        
        toolbar.addLayout(search_container, stretch=1)
        
        # Add note button
        add_button = QPushButton('New Note')
        add_button.setMinimumHeight(40)
        add_button.clicked.connect(self.add_note)
        toolbar.addWidget(add_button)
        
        # Add zoom controls
        zoom_container = QHBoxLayout()
        zoom_container.setSpacing(5)
        
        # Reset zoom button
        reset_zoom_button = QPushButton("Reset Zoom")
        reset_zoom_button.setMinimumHeight(40)
        reset_zoom_button.clicked.connect(self.reset_zoom)
        zoom_container.addWidget(reset_zoom_button)
        
        # Zoom label
        self.zoom_label = QLabel("Zoom: 100%")
        self.zoom_label.setStyleSheet("color: #888888; margin-left: 10px;")
        zoom_container.addWidget(self.zoom_label)
        
        toolbar.addLayout(zoom_container)
        
        # Add organize buttons
        organize_container = QHBoxLayout()
        organize_container.setSpacing(5)
        
        # Snap to Grid button
        snap_grid_button = QPushButton("Snap to Grid")
        snap_grid_button.setMinimumHeight(40)
        snap_grid_button.clicked.connect(self.snap_notes_to_grid)
        organize_container.addWidget(snap_grid_button)
        
        # Arrange Notes button
        arrange_button = QPushButton("Arrange Notes")
        arrange_button.setMinimumHeight(40)
        arrange_button.clicked.connect(self.arrange_notes)
        organize_container.addWidget(arrange_button)
        
        toolbar.addLayout(organize_container)
        
        layout.addWidget(toolbar_container)
        
        # Create board
        self.board = BoardView()
        layout.addWidget(self.board)
        
        # Set dark theme style
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            #toolbarContainer {
                background-color: #1e1e1e;
                margin: 10px;
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
            QLabel {
                color: #888888;
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
            "Drag notes to move them • Drag note edges to resize • "
            "Ctrl++ / Ctrl+- to adjust note text size • "
            "Ctrl+R to insert separator"
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
        
        # Restore viewport state
        viewport_state = self.note_ops.get_viewport_state()
        self.board.restore_viewport_state(viewport_state)
    
    def add_note_widget(self, note: Note = None):
        if note is None:
            # Create new note in database
            note = self.note_ops.create_note("", "", "#2d2d2d")
        
        # Create note widget
        note_widget = NoteWidget(
            note_id=note.id,
            title=note.title,
            content=note.content,
            color=note.color,
            text_size=note.text_size
        )
        note_widget.updated.connect(self.update_note)
        note_widget.deleted.connect(self.delete_note)
        
        # Add to board
        pos = QPointF(note.position_x, note.position_y) if note.position_x is not None else None
        proxy = self.board.add_note(note_widget, pos)
        
        # Set size if it exists in the database
        if hasattr(note, 'width') and hasattr(note, 'height'):
            proxy.setGeometry(QRectF(proxy.geometry().topLeft(), 
                                   QSizeF(note.width, note.height)))
        
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
    
    def reset_zoom(self):
        self.board.reset_zoom()
    
    def update_note(self, note_id: int, title: str, content: str, color: str, text_size: int):
        # Get the note's current position
        if note_id in self.note_proxies:
            pos = self.note_proxies[note_id].pos()
            self.note_ops.update_note(
                note_id, title, content,
                color=color,
                position_x=pos.x(),
                position_y=pos.y(),
                text_size=text_size
            )
        else:
            self.note_ops.update_note(
                note_id, title, content,
                color=color,
                text_size=text_size
            )
    
    def delete_note(self, note_id: int):
        if note_id in self.note_proxies:
            self.note_proxies[note_id].scene().removeItem(self.note_proxies[note_id])
            del self.note_proxies[note_id]
        
        if not self.note_ops.delete_note(note_id):
            QMessageBox.warning(self, "Error", "Failed to delete note")
    
    def closeEvent(self, event):
        # Save viewport state
        viewport_state = self.board.get_viewport_state()
        self.note_ops.save_viewport_state(viewport_state)
        
        # Save all note positions and sizes before closing
        for note_id, proxy in self.note_proxies.items():
            pos = proxy.pos()
            geometry = proxy.geometry()
            note_widget = proxy.widget()
            self.note_ops.update_note(
                note_id, 
                None, 
                None, 
                color=note_widget.color,
                position_x=pos.x(),
                position_y=pos.y(),
                width=int(geometry.width()),
                height=int(geometry.height())
            )
        
        self.db.close()
        super().closeEvent(event)
    
    def snap_notes_to_grid(self):
        grid_size = 100  # Same as the grid size in BoardView
        for proxy in self.note_proxies.values():
            current_pos = proxy.pos()
            # Round to nearest grid point
            new_x = round(current_pos.x() / grid_size) * grid_size
            new_y = round(current_pos.y() / grid_size) * grid_size
            proxy.setPos(new_x, new_y)
            
            # Update position in database
            note_widget = proxy.widget()
            if note_widget and note_widget.note_id:
                self.note_ops.update_note(
                    note_widget.note_id,
                    "",
                    note_widget.content_edit.toPlainText(),
                    color=note_widget.color,
                    position_x=new_x,
                    position_y=new_y,
                    text_size=note_widget.text_size
                )
    
    def arrange_notes(self):
        if not self.note_proxies:
            return
            
        # Get the viewport center
        viewport_center = self.board.mapToScene(self.board.viewport().rect().center())
        
        # Calculate grid dimensions
        note_count = len(self.note_proxies)
        grid_cols = max(2, int((note_count ** 0.5) // 1))  # Square root rounded down
        grid_rows = (note_count + grid_cols - 1) // grid_cols  # Ceiling division
        
        # Calculate starting position
        start_x = viewport_center.x() - (grid_cols * 400) / 2  # 400 = note width + spacing
        start_y = viewport_center.y() - (grid_rows * 300) / 2  # 300 = note height + spacing
        
        # Arrange notes in a grid
        col, row = 0, 0
        for proxy in self.note_proxies.values():
            new_x = start_x + col * 400
            new_y = start_y + row * 300
            
            # Animate the movement
            proxy.setPos(new_x, new_y)
            
            # Update position in database
            note_widget = proxy.widget()
            if note_widget and note_widget.note_id:
                self.note_ops.update_note(
                    note_widget.note_id,
                    "",
                    note_widget.content_edit.toPlainText(),
                    color=note_widget.color,
                    position_x=new_x,
                    position_y=new_y,
                    text_size=note_widget.text_size
                )
            
            # Move to next position
            col += 1
            if col >= grid_cols:
                col = 0
                row += 1

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 
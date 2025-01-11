from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QWidget, QGraphicsProxyWidget, QPushButton, QLineEdit, QTextEdit
from PyQt6.QtCore import Qt, QPointF, QRectF, QPoint
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen
import logging

logger = logging.getLogger(__name__)

class DraggableProxyWidget(QGraphicsProxyWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptHoverEvents(True)
        self.setFlag(self.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(self.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.dragging = False
        self.last_pos = None
    
    def mousePressEvent(self, event):
        # Get the widget under the mouse
        widget = self.widget()
        if widget:
            local_pos = widget.mapFromParent(event.pos())
            child = widget.childAt(QPoint(int(local_pos.x()), int(local_pos.y())))
            
            # If clicking on an interactive widget, let it handle the event
            if child and (isinstance(child, (QPushButton, QLineEdit, QTextEdit)) or 
                         child.cursor().shape() != Qt.CursorShape.ArrowCursor):
                return super().mousePressEvent(event)
        
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.dragging and event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.last_pos = None
            self.unsetCursor()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.dragging and self.last_pos is not None:
            delta = event.pos() - self.last_pos
            new_pos = self.pos() + delta
            self.setPos(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def hoverEnterEvent(self, event):
        # Get the widget under the mouse
        widget = self.widget()
        if widget:
            local_pos = widget.mapFromParent(event.pos())
            child = widget.childAt(QPoint(int(local_pos.x()), int(local_pos.y())))
            
            # Don't show hand cursor over interactive elements
            if not child or (not isinstance(child, (QPushButton, QLineEdit, QTextEdit)) and 
                           child.cursor().shape() == Qt.CursorShape.ArrowCursor):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().hoverEnterEvent(event)
    
    def hoverMoveEvent(self, event):
        # Update cursor based on what's under the mouse
        widget = self.widget()
        if widget:
            local_pos = widget.mapFromParent(event.pos())
            child = widget.childAt(QPoint(int(local_pos.x()), int(local_pos.y())))
            
            if not child or (not isinstance(child, (QPushButton, QLineEdit, QTextEdit)) and 
                           child.cursor().shape() == Qt.CursorShape.ArrowCursor):
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                self.unsetCursor()
        super().hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

class BoardView(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # Set up the view
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setInteractive(True)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        
        # Initialize view properties
        self.zoom_factor = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 3.0
        self.is_panning = False
        self.last_mouse_pos = None
        
        # Set up the board
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.scene.setSceneRect(-4000, -4000, 8000, 8000)  # Large canvas
        
        # Draw grid
        self.draw_grid()
    
    def draw_grid(self):
        # Draw major grid lines
        pen_major = QPen(QColor("#2d2d2d"), 1, Qt.PenStyle.SolidLine)
        pen_minor = QPen(QColor("#232323"), 1, Qt.PenStyle.SolidLine)
        
        # Draw grid lines
        grid_size = 100
        rect = self.scene.sceneRect()
        
        # Minor grid lines
        for x in range(int(rect.left()), int(rect.right()), grid_size):
            self.scene.addLine(x, rect.top(), x, rect.bottom(), pen_minor)
        for y in range(int(rect.top()), int(rect.bottom()), grid_size):
            self.scene.addLine(rect.left(), y, rect.right(), y, pen_minor)
            
        # Major grid lines
        major_grid_size = grid_size * 5
        for x in range(int(rect.left()), int(rect.right()), major_grid_size):
            self.scene.addLine(x, rect.top(), x, rect.bottom(), pen_major)
        for y in range(int(rect.top()), int(rect.bottom()), major_grid_size):
            self.scene.addLine(rect.left(), y, rect.right(), y, pen_major)
    
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        
        if event.button() == Qt.MouseButton.MiddleButton or \
           (event.button() == Qt.MouseButton.LeftButton and 
            event.modifiers() & Qt.KeyboardModifier.AltModifier):
            self.is_panning = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_panning and self.last_mouse_pos is not None:
            delta = event.pos() - self.last_mouse_pos
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            self.last_mouse_pos = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            zoom_in = event.angleDelta().y() > 0
            zoom_factor = 1.1 if zoom_in else 0.9
            
            new_zoom = self.zoom_factor * zoom_factor
            if self.min_zoom <= new_zoom <= self.max_zoom:
                self.zoom_factor = new_zoom
                self.scale(zoom_factor, zoom_factor)
                
                # Update zoom label in main window if it exists
                if hasattr(self.parent(), 'zoom_label'):
                    zoom_percentage = int(self.zoom_factor * 100)
                    self.parent().zoom_label.setText(f"Zoom: {zoom_percentage}%")
                    
            event.accept()
        else:
            # Regular scroll
            super().wheelEvent(event)
    
    def add_note(self, note_widget, pos=None):
        if pos is None:
            pos = self.mapToScene(self.viewport().rect().center())
        
        proxy = DraggableProxyWidget()
        proxy.setWidget(note_widget)
        self.scene.addItem(proxy)
        proxy.setPos(pos)
        return proxy 
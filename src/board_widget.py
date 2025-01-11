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
        self.resizing = False
        self.last_pos = None
        self.drag_offset = None
        self.resize_edge = None
        self.min_size = (300, 200)  # Minimum size (width, height)
        self.max_size = (800, 1000)  # Maximum size (width, height)
        self.resize_margin = 10  # Pixels from edge where resize is active
    
    def isInResizeArea(self, pos):
        rect = self.rect()
        x, y = pos.x(), pos.y()
        margin = self.resize_margin
        
        # Check if we're in any resize area
        left_edge = abs(rect.left() - x) <= margin
        right_edge = abs(rect.right() - x) <= margin
        top_edge = abs(rect.top() - y) <= margin
        bottom_edge = abs(rect.bottom() - y) <= margin
        
        # Check corners first
        if left_edge and top_edge:
            return 'top-left'
        if right_edge and top_edge:
            return 'top-right'
        if left_edge and bottom_edge:
            return 'bottom-left'
        if right_edge and bottom_edge:
            return 'bottom-right'
        
        # Then check edges
        if left_edge:
            return 'left'
        if right_edge:
            return 'right'
        if top_edge:
            return 'top'
        if bottom_edge:
            return 'bottom'
        
        return None
    
    def isInHeader(self, pos):
        widget = self.widget()
        if not widget:
            return False
        
        # Get the header widget
        header = widget.header_container
        if not header:
            return False
        
        # Convert to global coordinates
        scene_pos = self.mapToScene(pos)
        view = self.scene().views()[0]
        global_pos = view.mapToGlobal(view.mapFromScene(scene_pos))
        
        # Convert to header coordinates
        header_pos = header.mapFromGlobal(global_pos)
        
        # Check if we're in the header and not over a child widget
        if header.rect().contains(header_pos):
            child = header.childAt(header_pos)
            return child is None
        return False
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            resize_area = self.isInResizeArea(event.pos())
            if resize_area:
                self.resizing = True
                self.resize_edge = resize_area
                self.last_pos = event.pos()
                event.accept()
                return
            elif self.isInHeader(event.pos()):
                self.dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.drag_offset = event.pos()
                event.accept()
                return
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resizing:
                self.resizing = False
                self.resize_edge = None
                self.unsetCursor()
                event.accept()
            elif self.dragging:
                self.dragging = False
                self.drag_offset = None
                self.unsetCursor()
                event.accept()
            else:
                super().mouseReleaseEvent(event)
        else:
            super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.resizing and self.last_pos is not None:
            delta = event.pos() - self.last_pos
            current_rect = self.geometry()
            new_rect = QRectF(current_rect)
            
            # Store original values
            original_left = current_rect.left()
            original_top = current_rect.top()
            original_width = current_rect.width()
            original_height = current_rect.height()
            
            # Handle horizontal resizing
            if 'left' in self.resize_edge:
                new_width = original_width - delta.x()
                if self.min_size[0] <= new_width <= self.max_size[0]:
                    new_rect.setLeft(original_left + delta.x())
                    new_rect.setWidth(new_width)
            elif 'right' in self.resize_edge:
                new_width = original_width + delta.x()
                if self.min_size[0] <= new_width <= self.max_size[0]:
                    new_rect.setWidth(new_width)
            
            # Handle vertical resizing
            if 'top' in self.resize_edge:
                new_height = original_height - delta.y()
                if self.min_size[1] <= new_height <= self.max_size[1]:
                    new_rect.setTop(original_top + delta.y())
                    new_rect.setHeight(new_height)
            elif 'bottom' in self.resize_edge:
                new_height = original_height + delta.y()
                if self.min_size[1] <= new_height <= self.max_size[1]:
                    new_rect.setHeight(new_height)
            
            self.setGeometry(new_rect)
            self.last_pos = event.pos()
            event.accept()
        elif self.dragging and self.drag_offset is not None:
            new_pos = self.mapToScene(event.pos() - self.drag_offset)
            self.setPos(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def hoverMoveEvent(self, event):
        resize_area = self.isInResizeArea(event.pos())
        if resize_area in ['top-left', 'bottom-right']:
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif resize_area in ['top-right', 'bottom-left']:
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif resize_area in ['left', 'right']:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif resize_area in ['top', 'bottom']:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif self.isInHeader(event.pos()):
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
        self.min_zoom = 0.3  # Increased minimum zoom to ensure notes are still grabbable
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
    
    def reset_zoom(self):
        # Calculate the zoom factor needed to return to 1.0
        reset_factor = 1.0 / self.zoom_factor
        self.scale(reset_factor, reset_factor)
        self.zoom_factor = 1.0
        
        # Update zoom label in main window if it exists
        if hasattr(self.parent(), 'zoom_label'):
            self.parent().zoom_label.setText("Zoom: 100%")
    
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        
        # Only allow interaction with items when zoom is above threshold
        if self.zoom_factor >= 0.4 or not isinstance(item, DraggableProxyWidget):
            if event.button() == Qt.MouseButton.MiddleButton or \
               (event.button() == Qt.MouseButton.LeftButton and 
                event.modifiers() & Qt.KeyboardModifier.AltModifier):
                self.is_panning = True
                self.last_mouse_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
            else:
                super().mousePressEvent(event)
        else:
            # If zoom is too low, only allow panning
            if event.button() == Qt.MouseButton.MiddleButton or \
               (event.button() == Qt.MouseButton.LeftButton and 
                event.modifiers() & Qt.KeyboardModifier.AltModifier):
                self.is_panning = True
                self.last_mouse_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
    
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
    
    def get_viewport_state(self):
        """Get the current viewport state including position and zoom."""
        center = self.mapToScene(self.viewport().rect().center())
        return {
            'center_x': center.x(),
            'center_y': center.y(),
            'zoom_factor': self.zoom_factor
        }
    
    def restore_viewport_state(self, state):
        """Restore the viewport to a saved state."""
        if not state:
            return
            
        # Restore zoom
        if 'zoom_factor' in state:
            reset_factor = state['zoom_factor'] / self.zoom_factor
            self.scale(reset_factor, reset_factor)
            self.zoom_factor = state['zoom_factor']
            
            # Update zoom label
            if hasattr(self.parent(), 'zoom_label'):
                zoom_percentage = int(self.zoom_factor * 100)
                self.parent().zoom_label.setText(f"Zoom: {zoom_percentage}%")
        
        # Restore position
        if 'center_x' in state and 'center_y' in state:
            self.centerOn(state['center_x'], state['center_y']) 
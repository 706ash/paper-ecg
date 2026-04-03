"""
BaselineView.py
Created 2026

Baseline (isoelectric line) marker for voltage conversion
Supports 3 baselines for 12-lead ECG (3 rows of 4 leads each)
"""
from PyQt5 import QtGui, QtCore, QtWidgets

# Custom item type for baseline
BASELINE_ITEM_TYPE = QtWidgets.QGraphicsRectItem.UserType + 2

class BaselineItem(QtWidgets.QGraphicsRectItem):
    """
    A horizontal line marker for defining the isoelectric baseline (0 mV).
    Users drag this line to the TP segment or PR segment of the ECG to mark 0 mV.
    Supports 3 baselines for standard 12-lead ECG layout (3 rows × 4 leads).
    """

    def __init__(self, parent, baselineId=0, y_position=0, *args):
        """
        Initialize the baseline marker.
        
        Args:
            parent: QGraphicsScene that contains this item
            baselineId: ID of this baseline (0, 1, or 2 for 3-row ECG)
            y_position: Initial Y position for the baseline
        """
        super().__init__(*args)

        self.baselineId = baselineId
        self.baselineY = y_position
        self.parentScene = parent
        self.parentViews = self.parentScene.views()
        
        # Set item type
        self.type = BASELINE_ITEM_TYPE
        
        # Make the item movable
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
        
        # Set initial rect (will be updated)
        self.setRect(0, y_position, 100, 2)
        
        # Row labels for 12-lead ECG
        self.rowLabels = ["Row 1 (I, II, III)", "Row 2 (aVR, aVL, V1)", "Row 3 (V2, V3, V4)"]
        
    def paint(self, painter, option, widget=None):
        """Paint the baseline as a dashed green line."""
        sceneRect = self.parentScene.sceneRect()
        
        # Different colors for each baseline
        colors = [
            QtGui.QColor(0, 200, 100),   # Green for row 1
            QtGui.QColor(0, 150, 200),   # Blue for row 2
            QtGui.QColor(200, 150, 0),   # Orange for row 3
        ]
        color = colors[self.baselineId % len(colors)]
        
        painter.setPen(QtGui.QPen(color, 2.0, QtCore.Qt.DashLine))
        painter.setBrush(QtGui.QBrush(color, 64))
        
        # Draw the baseline across the entire image width
        lineStart = QtCore.QPointF(0, self.baselineY)
        lineEnd = QtCore.QPointF(sceneRect.width(), self.baselineY)
        painter.drawLine(lineStart, lineEnd)
        
        # Draw label with row info
        painter.setPen(QtGui.QPen(color, 255))
        painter.setFont(QtGui.QFont('Default', 10, QtGui.QFont.Bold))
        label = f"Baseline {self.baselineId+1}: {self.rowLabels[self.baselineId]} (0 mV)"
        painter.drawText(10, self.baselineY - 5, label)
        
        # Draw handle circles at ends when selected
        if self.isSelected():
            painter.setBrush(QtGui.QBrush(color))
            painter.setPen(QtGui.QPen(color, 2.0))
            # Left handle
            painter.drawEllipse(QtCore.QPointF(5, self.baselineY), 6, 6)
            # Right handle  
            painter.drawEllipse(QtCore.QPointF(sceneRect.width() - 5, self.baselineY), 6, 6)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsRectItem.ItemPositionChange:
            # Constrain movement to horizontal only (Y position stays fixed during drag via setPos)
            # But we allow Y changes through mouseMoveEvent
            currentY = self.baselineY
            newX = value.x()
            return QtCore.QPointF(newX, currentY)
            
        if change == QtWidgets.QGraphicsRectItem.ItemSelectedChange:
            self.parentViews[0].roiItemSelected.emit(f"baseline_{self.baselineId}", value)
            if value:
                self.setZValue(10)  # High z-value to stay on top
            else:
                self.setZValue(0)
                
        return QtWidgets.QGraphicsRectItem.itemChange(self, change, value)

    def mousePressEvent(self, event):
        """Handle mouse press to select the baseline."""
        super().mousePressEvent(event)
        self.update()

    def mouseMoveEvent(self, event):
        """Allow vertical dragging to adjust baseline position."""
        if self.isSelected():
            # Get the new position
            newPos = event.scenePos()
            # Update baseline Y position
            self.baselineY = newPos.y()
            self.setRect(0, self.baselineY, 100, 2)
            self.setPos(0, 0)  # Reset position, we use rect for drawing
            self.update()
            
            # Notify parent of update
            if self.parentViews:
                self.parentViews[0].updateRoiItem.emit(self)
        else:
            super().mouseMoveEvent(event)

    def getBaselineY(self):
        """Get the Y coordinate of the baseline."""
        return self.baselineY

    def setBaselineY(self, y):
        """Set the Y coordinate of the baseline."""
        self.baselineY = y
        self.setRect(0, self.baselineY, 100, 2)
        self.update()

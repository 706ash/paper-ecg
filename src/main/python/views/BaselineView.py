"""
BaselineView.py
Created 2026

Baseline (isoelectric line) marker for voltage conversion.
Supports the standard three ECG rows plus an optional rhythm row.
"""
from PyQt5 import QtGui, QtCore, QtWidgets

# Custom item type for baseline
BASELINE_ITEM_TYPE = QtWidgets.QGraphicsRectItem.UserType + 2


class BaselineItem(QtWidgets.QGraphicsRectItem):
    """
    A horizontal line marker for defining the isoelectric baseline (0 mV).
    Users drag this line to the TP segment or PR segment of the ECG to mark 0 mV.
    Supports three standard 12-lead rows plus an optional rhythm row.
    """

    ROW_LABELS = [
        "Row 1 (I, aVR, V1, V4)",
        "Row 2 (II, aVL, V2, V5)",
        "Row 3 (III, aVF, V3, V6)",
        "Row 4 (Rhythm)",
    ]

    def getScale(self):
        if hasattr(self, 'parentViews') and self.parentViews and len(self.parentViews) > 0:
            return max(self.parentViews[0].transform().m11(), 0.1)
        return 1.0

    def __init__(self, parent, baselineId=0, y_position=0, *args):
        """
        Initialize the baseline marker.

        Args:
            parent: QGraphicsScene that contains this item
            baselineId: ID of this baseline row
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

    def boundingRect(self):
        """Returns a rect that covers the entire image width to prevent artifacts."""
        sceneRect = self.parentScene.sceneRect()
        return QtCore.QRectF(0, self.baselineY - 20, sceneRect.width(), 40)

    def shape(self):
        """Returns a narrow rect for easier selection without overlapping other items."""
        sceneRect = self.parentScene.sceneRect()
        path = QtGui.QPainterPath()
        path.addRect(0, self.baselineY - 5, sceneRect.width(), 10)
        return path

    def paint(self, painter, option, widget=None):
        """Paint the baseline as a dashed colored line."""
        sceneRect = self.parentScene.sceneRect()
        scale = self.getScale()

        colors = [
            QtGui.QColor(0, 200, 100),
            QtGui.QColor(0, 150, 200),
            QtGui.QColor(200, 150, 0),
            QtGui.QColor(180, 80, 180),
        ]
        color = colors[self.baselineId % len(colors)]

        linePen = QtGui.QPen(color, 2.0, QtCore.Qt.DashLine)
        linePen.setCosmetic(False)
        painter.setPen(linePen)
        painter.drawLine(0, self.baselineY, sceneRect.width(), self.baselineY)

        painter.save()
        labelPen = QtGui.QPen(color)
        labelPen.setCosmetic(True)
        painter.setPen(labelPen)
        painter.setFont(QtGui.QFont('Default', 10, QtGui.QFont.Bold))
        rowLabel = self.ROW_LABELS[self.baselineId] if self.baselineId < len(self.ROW_LABELS) else f"Row {self.baselineId + 1}"
        label = f"Baseline {self.baselineId + 1}: {rowLabel} (0 mV)"
        painter.drawText(10, self.baselineY - (5 / scale), label)
        painter.restore()

        if self.isSelected():
            painter.setBrush(QtGui.QBrush(color))
            handlePen = QtGui.QPen(QtCore.Qt.white, 1.0)
            handlePen.setCosmetic(True)
            painter.setPen(handlePen)

            radius = 6.0 / scale
            painter.drawEllipse(QtCore.QPointF(max(5, 5 / scale), self.baselineY), radius, radius)
            painter.drawEllipse(QtCore.QPointF(sceneRect.width() - max(5, 5 / scale), self.baselineY), radius, radius)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsRectItem.ItemPositionChange:
            newY = round(value.y())
            newX = value.x()
            return QtCore.QPointF(newX, newY)

        if change == QtWidgets.QGraphicsRectItem.ItemSelectedChange:
            self.parentViews[0].roiItemSelected.emit(f"baseline_{self.baselineId}", value)
            if value:
                self.setZValue(10)
            else:
                self.setZValue(0)

        return QtWidgets.QGraphicsRectItem.itemChange(self, change, value)

    def mousePressEvent(self, event):
        """Handle mouse press to select the baseline."""
        super().mousePressEvent(event)
        self.update()

    def mouseMoveEvent(self, event):
        """Allow vertical dragging to adjust baseline position with snapping."""
        if self.isSelected():
            self.prepareGeometryChange()
            newPos = event.scenePos()
            self.baselineY = round(newPos.y())
            self.update()

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

import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets
from model.Lead import LeadId

import ImageUtilities

# According the docs, custom items should have type >= UserType (65536)
# Setting the type allows you to distinguish between items in the graphics scene
# https://doc.qt.io/archives/qt-4.8/qgraphicsitem.html#UserType-var
ROI_ITEM_TYPE = QtWidgets.QGraphicsRectItem.UserType

# From: https://github.com/drmatthews/slidecrop_pyqt/blob/master/slidecrop/gui/roi.py#L116
class ROIItem(QtWidgets.QGraphicsRectItem):

    handleTopLeft = 1
    handleTopMiddle = 2
    handleTopRight = 3
    handleMiddleLeft = 4
    handleMiddleRight = 5
    handleBottomLeft = 6
    handleBottomMiddle = 7
    handleBottomRight = 8

    baseHandleSize = +12.0
    baseHandleSpace = -6.0
    handleSize = +12.0
    handleSpace = -6.0

    def getScale(self):
        if hasattr(self, 'parentViews') and self.parentViews and len(self.parentViews) > 0:
            return max(self.parentViews[0].transform().m11(), 0.1)
        return 1.0


    handleCursors = {
        handleTopLeft: QtCore.Qt.SizeFDiagCursor,
        handleTopMiddle: QtCore.Qt.SizeVerCursor,
        handleTopRight: QtCore.Qt.SizeBDiagCursor,
        handleMiddleLeft: QtCore.Qt.SizeHorCursor,
        handleMiddleRight: QtCore.Qt.SizeHorCursor,
        handleBottomLeft: QtCore.Qt.SizeBDiagCursor,
        handleBottomMiddle: QtCore.Qt.SizeVerCursor,
        handleBottomRight: QtCore.Qt.SizeFDiagCursor,
    }

    def __init__(self, parent, leadId, *args):
        """
        Initialize the shape.
        """
        super().__init__(*args)

        self.leadId = leadId
        self.customName = None
        self.startTime = 0.0

        # Minimum width and height of box (in pixels)
        self.minHeight = 1
        self.minWidth = 1

        # QGraphicsScene that contains this ROIItem instance
        self.parentScene = parent

        # QGraphicsView that displays the parentScene
        self.parentViews = self.parentScene.views()

        self.handles = {}
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None
        self.setAcceptHoverEvents(True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsFocusable, True)
        self.updateHandlesPos()

        # Set item type to identify ROI items in scene - according to custom items should
        # have type >= UserType (65536)
        self.type = ROI_ITEM_TYPE

    @property
    def x(self):
        return self.mapToScene(self.rect()).boundingRect().toRect().x()

    @property
    def y(self):
        return self.mapToScene(self.rect()).boundingRect().toRect().y()

    @property
    def width(self):
        return self.mapToScene(self.rect()).boundingRect().toRect().width()

    @property
    def height(self):
        return self.mapToScene(self.rect()).boundingRect().toRect().height()

    def handleAt(self, point):
        """
        Returns the resize handle below the given point.
        """
        scale = self.getScale()
        # Add a 5px (on screen) hit area padding
        padding = 5.0 / scale
        for k, v, in self.handles.items():
            if v.adjusted(-padding, -padding, padding, padding).contains(point):
                return k
        return None

    def hoverMoveEvent(self, moveEvent):
        """
        Executed when the mouse moves over the shape (NOT PRESSED).
        """
        if self.isSelected():
            handle = self.handleAt(moveEvent.pos())
            cursor = QtCore.Qt.ArrowCursor if handle is None else self.handleCursors[handle]
            self.setCursor(cursor)
        super().hoverMoveEvent(moveEvent)

    def hoverLeaveEvent(self, moveEvent):
        """
        Executed when the mouse leaves the shape (NOT PRESSED).
        """
        self.setCursor(QtCore.Qt.ArrowCursor)
        super().hoverLeaveEvent(moveEvent)

    def mousePressEvent(self, mouseEvent):
        """
        Executed when the mouse is pressed on the item.
        """
        self.updateHandlesPos()
        self.mousePressPos = mouseEvent.pos()
        self.handleSelected = self.handleAt(mouseEvent.pos())
        if self.handleSelected:
            self.mousePressPos = mouseEvent.pos()
            self.mousePressRect = self.handleBounds()

        super().mousePressEvent(mouseEvent)

    def mouseMoveEvent(self, mouseEvent):
        """
        Executed when the mouse is being moved over the item while being pressed.
        """
        if self.handleSelected is not None:
            self.interactiveResize(mouseEvent.pos())
        else:
            self.updateHandlesPos()
            super().mouseMoveEvent(mouseEvent)

    def mouseReleaseEvent(self, mouseEvent):
        """
        Executed when the mouse is released from the item.
        """
        super().mouseReleaseEvent(mouseEvent)
        self.handleSelected = None
        self.mousePressPos = None
        self.mousePressRect = None

        self.parentViews[0].updateRoiItem.emit(self)
        self.update()

    def handleBounds(self):
        o = self.handleSize + self.handleSpace
        return self.rect().adjusted(-o, -o, o, o)

    def boundingRect(self):
        """
        Returns the bounding rect of the shape (including the resize handles).
        """
        # Safe generous padding ensures visual overlap like pens and texts are redrawn
        return self.rect().adjusted(-20, -20, 20, 20)

    def updateHandlesPos(self):
        """
        Update current resize handles according to the shape size and position.
        """
        scale = self.getScale()
        self.handleSize = self.baseHandleSize / scale
        self.handleSpace = self.baseHandleSpace / scale
        
        # Cap limits to prevent them from growing out of the 20-pixel safe boundingRect
        if self.handleSize > 16.0:
            self.handleSize = 16.0
            self.handleSpace = -8.0

        s = self.handleSize
        b = self.handleBounds()

        self.handles[self.handleTopLeft] = QtCore.QRectF(b.left(), b.top(), s, s)
        self.handles[self.handleTopMiddle] = QtCore.QRectF(b.center().x() - s / 2, b.top(), s, s)
        self.handles[self.handleTopRight] = QtCore.QRectF(b.right() - s, b.top(), s, s)
        self.handles[self.handleMiddleLeft] = QtCore.QRectF(b.left(), b.center().y() - s / 2, s, s)
        self.handles[self.handleMiddleRight] = QtCore.QRectF(b.right() - s, b.center().y() - s / 2, s, s)
        self.handles[self.handleBottomLeft] = QtCore.QRectF(b.left(), b.bottom() - s, s, s)
        self.handles[self.handleBottomMiddle] = QtCore.QRectF(b.center().x() - s / 2, b.bottom() - s, s, s)
        self.handles[self.handleBottomRight] = QtCore.QRectF(b.right() - s, b.bottom() - s, s, s)

    def interactiveResize(self, mousePos):
        """
        Perform shape interactive resize with snapping to image pixels.
        """
        rect = self.rect()
        # Map mouse position to scene, round it to snap to image pixels, then map back to local
        scenePos = self.mapToScene(mousePos)
        snappedScenePos = QtCore.QPointF(round(scenePos.x()), round(scenePos.y()))
        localSnappedPos = self.mapFromScene(snappedScenePos)
        
        self.prepareGeometryChange()

        if self.handleSelected == self.handleTopLeft:
            rect.setTopLeft(localSnappedPos)
        elif self.handleSelected == self.handleTopMiddle:
            rect.setTop(localSnappedPos.y())
        elif self.handleSelected == self.handleTopRight:
            rect.setTopRight(localSnappedPos)
        elif self.handleSelected == self.handleMiddleLeft:
            rect.setLeft(localSnappedPos.x())
        elif self.handleSelected == self.handleMiddleRight:
            rect.setRight(localSnappedPos.x())
        elif self.handleSelected == self.handleBottomLeft:
            rect.setBottomLeft(localSnappedPos)
        elif self.handleSelected == self.handleBottomMiddle:
            rect.setBottom(localSnappedPos.y())
        elif self.handleSelected == self.handleBottomRight:
            rect.setBottomRight(localSnappedPos)

        # Enforce minimum size after snapping
        if rect.width() < self.minWidth:
            if self.handleSelected in [self.handleTopLeft, self.handleMiddleLeft, self.handleBottomLeft]:
                rect.setLeft(rect.right() - self.minWidth)
            else:
                rect.setRight(rect.left() + self.minWidth)
        if rect.height() < self.minHeight:
            if self.handleSelected in [self.handleTopLeft, self.handleTopMiddle, self.handleTopRight]:
                rect.setTop(rect.bottom() - self.minHeight)
            else:
                rect.setBottom(rect.top() + self.minHeight)

        self.setRect(rect)
        self.updateHandlesPos()


    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsRectItem.ItemPositionChange:
            if self.parentScene is not None:
                return self.restrictMovement(value)

        if change == QtWidgets.QGraphicsRectItem.ItemSelectedChange:
            self.parentViews[0].roiItemSelected.emit(self.leadId.name, value)
            if value == True:
                self.setZValue(1)
            else:
                self.setZValue(0)

        return QtWidgets.QGraphicsRectItem.itemChange(self, change, value)


    # https://stackoverflow.com/questions/55771100/how-do-i-reimplement-the-itemchange-and-mousemoveevent-of-a-qgraphicspixmapitem
    def restrictMovement(self, value):

        boxRect = self.mapToScene(self.boundingRect()).boundingRect()
        handleOffset = self.handleSpace
        sceneRect = self.parentScene.sceneRect()

        # 'value' represents the amount the item is being moved along the x,y plane so we calculate the actual (x,y) position the item is moving to
        x = value.x()+self.handles[self.handleTopLeft].x()
        y = value.y()+self.handles[self.handleTopLeft].y()

        relativeRect = QtCore.QRectF(sceneRect.topLeft(), sceneRect.size() - boxRect.size())

        # If item is being moved out of bounds, override the appropriate x,y values to keep item within scene
        if not relativeRect.contains(x, y):
            if x < 1:
                value.setX(sceneRect.left()-self.handles[self.handleTopLeft].x()+self.handleSpace)
            elif x+boxRect.width() >= sceneRect.width():
                value.setX(sceneRect.right()-boxRect.width()-self.handles[self.handleTopLeft].x()-self.handleSpace)
            if y < 1:
                value.setY(sceneRect.top()-self.handles[self.handleTopLeft].y()+self.handleSpace)
            elif y+boxRect.height() >= sceneRect.bottom():
                value.setY(sceneRect.bottom()-boxRect.height()-self.handles[self.handleTopLeft].y()-self.handleSpace)

        # Snap to image pixels
        value.setX(round(value.x()))
        value.setY(round(value.y()))

        return QtCore.QPointF(value.x(), value.y())

    def shape(self):
        """
        Returns the shape of this item as a QPainterPath in local coordinates.
        """
        path = QtGui.QPainterPath()
        path.addRect(self.rect())
        if self.isSelected():
            for shape in self.handles.values():
                path.addEllipse(shape)
        return path

    def paint(self, painter, option, widget=None):
        """
        Paint the node in the graphic view.
        """
        self.updateHandlesPos()

        painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
        painter.setFont(QtGui.QFont('Arial', 24, QtGui.QFont.Bold))
        fontMetrics = QtGui.QFontMetrics(painter.font())

        if self.isSelected():
            # --- Cosmetic dashed border: always 1px on screen regardless of zoom ---
            dashPen = QtGui.QPen(QtGui.QColor(255, 0, 0), 1.0, QtCore.Qt.DashLine)
            dashPen.setCosmetic(True)          # fixed screen-pixel width at any zoom
            dashPen.setDashPattern([6, 4])     # 6px dash, 4px gap (screen pixels)
            painter.setPen(dashPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 15))) # More transparent
            painter.drawRect(self.rect())

            # Draw resize handles with cosmetic pen (always thin on screen)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            handlePen = QtGui.QPen(QtGui.QColor(255, 0, 0), 1.0, QtCore.Qt.SolidLine)
            handlePen.setCosmetic(True)
            painter.setPen(handlePen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0, 255)))

            for handle, rect in self.handles.items():
                painter.drawRect(rect)
        else:
            # --- Cosmetic solid thin grey border when unselected ---
            solidPen = QtGui.QPen(QtGui.QColor(128, 128, 128), 1.0, QtCore.Qt.SolidLine)
            solidPen.setCosmetic(True)
            painter.setPen(solidPen)
            painter.setBrush(QtGui.QBrush(QtGui.QColor(128, 128, 128, 40)))
            painter.drawRect(self.rect())
            
            painter.save()
            painter.setClipRect(self.rect())
            textPen = QtGui.QPen(QtGui.QColor(128, 128, 128), 1.0)
            textPen.setCosmetic(True)
            painter.setPen(textPen)
            label = self.customName if self.customName else str(self.leadId)
            painter.drawText(self.rect(), QtCore.Qt.AlignCenter, label)
            painter.restore()


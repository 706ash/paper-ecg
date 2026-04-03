"""
MainWindow.py
Created November 7, 2020

Primary window of the application
"""
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from views.EditorWidget import Editor
from model.Lead import LeadId
import QtWrapper as Qt


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()

        self.buildUI()


    def buildUI(self):
        self.buildMenuBar()
        self.buildLeadButtonDictionary()

        self.editor = Editor(self)
        self.setCentralWidget(self.editor)
        self.setContentsMargins(0,0,0,0)

        self.setWindowTitle("Paper ECG")
        # self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        if sys.platform == "darwin" or sys.platform.startswith('linux'):
            self.resize(1000, 600)
            self.show()
        else:
            self.showMaximized()


    def buildMenuBar(self):
        Qt.MenuBar(
            owner=self,
            name='bar',
            menus=[
                self.buildFileMenu(),
                self.buildLeadMenu(),
                self.buildGridMenu(),
                self.buildBaselineMenu(),
                self.buildHelpMenu()
            ]
        )

    def buildFileMenu(self):
        return Qt.Menu(
            owner=self,
            name='fileMenu',
            displayName='File',
            items=[
                Qt.MenuAction(
                    owner=self,
                    name="fileMenuOpen",
                    displayName="Open",
                    shortcut=QtGui.QKeySequence.Open,
                    statusTip="Open an image file"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="fileMenuClose",
                    displayName="Close",
                    shortcut=QtGui.QKeySequence.Close,
                    statusTip="Close image file"
                )
            ]
        )

    def buildLeadMenu(self):
        return Qt.Menu(
            owner=self,
            name='leadMenu',
            displayName='Leads',
            items=[
               Qt.MenuAction(
                    owner=self,
                    name="addLead1",
                    displayName="Add Lead I",
                    shortcut=QtGui.QKeySequence('Ctrl+1'),
                    statusTip="Add Lead I"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLead2",
                    displayName="Add Lead II",
                    shortcut=QtGui.QKeySequence('Ctrl+2'),
                    statusTip="Add Lead II"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLead3",
                    displayName="Add Lead III",
                    shortcut=QtGui.QKeySequence('Ctrl+3'),
                    statusTip="Add Lead III"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadaVR",
                    displayName="Add Lead aVR",
                    shortcut=QtGui.QKeySequence('Ctrl+4'),
                    statusTip="Add Lead aVR"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadaVL",
                    displayName="Add Lead aVL",
                    shortcut=QtGui.QKeySequence('Ctrl+5'),
                    statusTip="Add Lead aVL"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadaVF",
                    displayName="Add Lead aVF",
                    shortcut=QtGui.QKeySequence('Ctrl+6'),
                    statusTip="Add Lead aVF"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadV1",
                    displayName="Add Lead V1",
                    shortcut=QtGui.QKeySequence('Ctrl+7'),
                    statusTip="Add Lead V1"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadV2",
                    displayName="Add Lead V2",
                    shortcut=QtGui.QKeySequence('Ctrl+8'),
                    statusTip="Add Lead V2"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadV3",
                    displayName="Add Lead V3",
                    shortcut=QtGui.QKeySequence('Ctrl+9'),
                    statusTip="Add Lead V3"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadV4",
                    displayName="Add Lead V4",
                    shortcut=QtGui.QKeySequence('Ctrl+0'),
                    statusTip="Add Lead V4"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadV5",
                    displayName="Add Lead V5",
                    shortcut=QtGui.QKeySequence('Ctrl+['),
                    statusTip="Add Lead V5"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadV6",
                    displayName="Add Lead V6",
                    shortcut=QtGui.QKeySequence('Ctrl+]'),
                    statusTip="Add Lead V6"
                ),
                Qt.Separator(),
                Qt.MenuAction(
                    owner=self,
                    name="addLeadRHYTHM",
                    displayName="Add Rhythm/Long Lead",
                    shortcut=QtGui.QKeySequence('Ctrl+R'),
                    statusTip="Add an enlarged/continuous lead at the bottom"
                )
            ]
        )

    def buildGridMenu(self):
        return Qt.Menu(
            owner=self,
            name='gridMenu',
            displayName='Grid',
            items=[
               Qt.MenuAction(
                    owner=self,
                    name="addGridBox",
                    displayName="Add 5mm Grid Box",
                    shortcut=QtGui.QKeySequence('Ctrl+G'),
                    statusTip="Add a 5mm grid calibration box (place over 5mm x 5mm large square)"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="deleteAllGridBoxes",
                    displayName="Delete All Grid Boxes",
                    shortcut=None,
                    statusTip="Delete all grid calibration boxes"
                )
            ]
        )

    def buildBaselineMenu(self):
        return Qt.Menu(
            owner=self,
            name='baselineMenu',
            displayName='Baseline',
            items=[
               Qt.MenuAction(
                    owner=self,
                    name="addThreeBaselines",
                    displayName="Add 3 Baselines (for 12-lead)",
                    shortcut=QtGui.QKeySequence('Ctrl+B'),
                    statusTip="Add 3 isoelectric baselines for 12-lead ECG (one per row)"
                ),
               Qt.MenuAction(
                    owner=self,
                    name="addBaseline1",
                    displayName="Add Baseline Row 1",
                    shortcut=QtGui.QKeySequence('Ctrl+Shift+1'),
                    statusTip="Add baseline for row 1 (leads I, II, III)"
                ),
               Qt.MenuAction(
                    owner=self,
                    name="addBaseline2",
                    displayName="Add Baseline Row 2",
                    shortcut=QtGui.QKeySequence('Ctrl+Shift+2'),
                    statusTip="Add baseline for row 2 (aVR, aVL, V1)"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="addBaseline3",
                    displayName="Add Baseline Row 3",
                    shortcut=QtGui.QKeySequence('Ctrl+Shift+3'),
                    statusTip="Add baseline for row 3 (V2, V3, V4)"
                ),
               Qt.MenuAction(
                    owner=self,
                    name="addBaseline4",
                    displayName="Add Baseline Row 4 (Rhythm)",
                    shortcut=QtGui.QKeySequence('Ctrl+Shift+4'),
                    statusTip="Add baseline for the enlarged rhythm lead at the bottom"
                ),
                Qt.Separator(),
                Qt.MenuAction(
                    owner=self,
                    name="removeAllBaselines",
                    displayName="Remove All Baselines",
                    shortcut=None,
                    statusTip="Remove all baseline markers"
                )
            ]
        )

    def buildHelpMenu(self):
        return Qt.Menu(
            owner=self,
            name='helpMenu',
            displayName='Help',
            items=[
               Qt.MenuAction(
                    owner=self,
                    name="userGuideButton",
                    displayName="User Guide",
                    shortcut=None,
                    statusTip="View User Guide on GitHub"
                ),
                Qt.MenuAction(
                    owner=self,
                    name="reportIssueButton",
                    displayName="Report An Issue",
                    shortcut=None,
                    statusTip="Report and Issue on GitHub"
                )
            ]
        )

    def resizeEvent(self, event):
        QtWidgets.QMainWindow.resizeEvent(self, event)

    def buildLeadButtonDictionary(self):
        # Creates relationship between lead ID and the menu button used to add that lead
        self.leadButtons = {
            LeadId.I: self.addLead1,
            LeadId.II: self.addLead2,
            LeadId.III: self.addLead3,
            LeadId.aVR: self.addLeadaVR,
            LeadId.aVL: self.addLeadaVL,
            LeadId.aVF: self.addLeadaVF,
            LeadId.V1: self.addLeadV1,
            LeadId.V2: self.addLeadV2,
            LeadId.V3: self.addLeadV3,
            LeadId.V4: self.addLeadV4,
            LeadId.V5: self.addLeadV5,
            LeadId.V6: self.addLeadV6,
            LeadId.RHYTHM: self.addLeadRHYTHM
        }
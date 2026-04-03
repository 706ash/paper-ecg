"""
EditorWindow.py
Created November 7, 2020

-
"""
from pathlib import Path

from PyQt5 import QtCore, QtWidgets

from model.Lead import LeadId
from views.ImageView import *
from views.ROIView import *
from views.GridROIView import *
from views.BaselineView import *
from views.EditPanelLeadView import *
from views.EditPanelGlobalView import *
from QtWrapper import *
from views.MessageDialog import *

class Editor(QtWidgets.QWidget):
    processEcgData = QtCore.pyqtSignal()
    saveAnnotationsButtonClicked = QtCore.pyqtSignal()

    image = None # The openCV image

    def __init__(self, parent):
        super().__init__()
        self.mainWindow = parent

        self.initUI()
        self.connectUI()

    def initUI(self):
        self.setLayout(
            HorizontalBoxLayout(self, "main", margins=(0,0,0,0), contents=[
                HorizontalSplitter(owner=self, name="viewSplitter", contents=[
                    Custom(
                        owner=self,
                        name="imageViewer",
                        widget=ImageView()
                    ),
                    ScrollArea(
                        owner=self,
                        name="controlPanel",
                        horizontalScrollBarPolicy=QtCore.Qt.ScrollBarAlwaysOff,
                        verticalScrollBarPolicy=QtCore.Qt.ScrollBarAsNeeded,
                        widgetIsResizable=True,
                        innerWidget=
                        StackedWidget(owner=self, name="editPanel", widgets=[
                            Custom(
                                owner=self,
                                name="EditPanelGlobalView",
                                widget=EditPanelGlobalView(self)
                            ),
                            Custom(
                                owner=self,
                                name="EditPanelLeadView",
                                widget=EditPanelLeadView(self)
                            )
                        ])
                    )
                ])
            ])
        )
        self.viewSplitter.setCollapsible(0,False)
        self.viewSplitter.setCollapsible(1,False)
        self.viewSplitter.setSizes([2,1])
        self.editPanel.setCurrentIndex(0)

        # Constraint the width of the adjustable side panel on the right of the editor
        self.controlPanel.setMinimumWidth(250)
        self.controlPanel.setMaximumWidth(450)

    def connectUI(self):
        self.mainWindow.addLead1.triggered.connect(lambda: self.addLead(LeadId['I']))
        self.mainWindow.addLead2.triggered.connect(lambda: self.addLead(LeadId['II']))
        self.mainWindow.addLead3.triggered.connect(lambda: self.addLead(LeadId['III']))
        self.mainWindow.addLeadaVR.triggered.connect(lambda: self.addLead(LeadId['aVR']))
        self.mainWindow.addLeadaVL.triggered.connect(lambda: self.addLead(LeadId['aVL']))
        self.mainWindow.addLeadaVF.triggered.connect(lambda: self.addLead(LeadId['aVF']))
        self.mainWindow.addLeadV1.triggered.connect(lambda: self.addLead(LeadId['V1']))
        self.mainWindow.addLeadV2.triggered.connect(lambda: self.addLead(LeadId['V2']))
        self.mainWindow.addLeadV3.triggered.connect(lambda: self.addLead(LeadId['V3']))
        self.mainWindow.addLeadV4.triggered.connect(lambda: self.addLead(LeadId['V4']))
        self.mainWindow.addLeadV5.triggered.connect(lambda: self.addLead(LeadId['V5']))
        self.mainWindow.addLeadV6.triggered.connect(lambda: self.addLead(LeadId['V6']))

        # Grid box connections
        self.mainWindow.addGridBox.triggered.connect(lambda: self.addGridBox(expectedMm=5.0))
        self.mainWindow.deleteAllGridBoxes.triggered.connect(self.deleteAllGridBoxes)

        # Baseline connections
        self.mainWindow.addThreeBaselines.triggered.connect(self.addThreeBaselines)
        self.mainWindow.addBaseline1.triggered.connect(lambda: self.addBaseline(baselineId=0))
        self.mainWindow.addBaseline2.triggered.connect(lambda: self.addBaseline(baselineId=1))
        self.mainWindow.addBaseline3.triggered.connect(lambda: self.addBaseline(baselineId=2))
        self.mainWindow.removeAllBaselines.triggered.connect(self.removeAllBaselines)

        self.imageViewer.roiItemSelected.connect(self.setControlPanel)

        self.EditPanelLeadView.leadStartTimeChanged.connect(self.updateLeadStartTime)
        self.EditPanelLeadView.deleteLeadRoi.connect(self.deleteLeadRoi)

    def loadSavedState(self, data):
        self.EditPanelGlobalView.setRotation(data['rotation'])
        self.EditPanelGlobalView.setValues(voltScale=data['voltageScale'], timeScale=data['timeScale'])
        self.EditPanelGlobalView.setLastSavedTimeStamp(data['timeStamp'])

        leads = data['leads']
        for name in leads:
            lead = leads[name]
            cropping = lead['cropping']
            self.addLead(leadIdEnum=LeadId[name], x=cropping['x'], y=cropping['y'], width=cropping['width'], height=cropping['height'], startTime=lead['start'])

        # Load grid boxes if present in saved state
        gridBoxes = data.get('gridBoxes', [])
        for gridBoxData in gridBoxes:
            cropping = gridBoxData['cropping']
            expectedMmWidth = gridBoxData.get('expectedMmWidth', 5.0)
            expectedMmHeight = gridBoxData.get('expectedMmHeight', 5.0)
            self.addGridBox(
                expectedMm=expectedMmWidth,
                x=cropping['x'],
                y=cropping['y'],
                width=cropping['width'],
                height=cropping['height']
            )
            # Update the last added grid box's height mm if different
            gridBoxItem = self.imageViewer._scene.items()[-1]
            if hasattr(gridBoxItem, 'expectedMmHeight'):
                gridBoxItem.expectedMmHeight = expectedMmHeight

        # Load baselines if present in saved state
        baselineYs = data.get('baselineYs', {})
        for baselineId, baselineY in baselineYs.items():
            self.imageViewer.addBaseline(baselineY, baselineId=int(baselineId))


    ###########################
    # Control Panel Functions #
    ###########################

    def setControlPanel(self, leadId=None, leadSelected=False):
        if leadSelected == True and leadId is not None:
            self.showLeadDetailView(leadId)
        else:
            # self.showGlobalView(self.inputParameters.voltScale, self.inputParameters.timeScale)
            self.showGlobalView()

    def showGlobalView(self):
        # self.EditPanelGlobalView.setValues(voltScale, timeScale)
        self.editPanel.setCurrentIndex(0)

    def showLeadDetailView(self, leadId):
        # leadStartTime = self.inputParameters.leads[LeadId[leadId]].startTime
        leadStartTime = self.imageViewer.getLeadRoiStartTime(leadId)
        self.EditPanelLeadView.setValues(leadId, leadStartTime)
        self.editPanel.setCurrentIndex(1)


    ###################
    # Image Functions #
    ###################

    def resetImageEditControls(self):
        self.EditPanelGlobalView.rotationSlider.setValue(0)
        self.EditPanelGlobalView.clearTimeSpinBox()
        self.EditPanelGlobalView.clearVoltSpinBox()
        self.EditPanelGlobalView.setLastSavedTimeStamp(timeStamp=None)
        self.showGlobalView()

    def loadImageFromPath(self, path: Path):
        self.image = ImageUtilities.readImage(path)
        self.displayImage()

    def displayImage(self):
        self.imageViewer.setImage(self.image)
        self.editPanel.show()

        # Adjust zoom to fit image in view
        self.imageViewer.fitImageInView()

    def removeImage(self):
        self.image = None
        self.imageViewer.removeImage()


    ######################
    # Lead ROI functions #
    ######################

    def addLead(self, leadIdEnum, x=0, y=0, width=400, height=200, startTime=0.0):
        if self.imageViewer.hasImage():
            leadId = leadIdEnum.name

            # Disable menu action so user can't add more than one bounding box for an individual lead
            # action.setEnabled(False)
            self.mainWindow.leadButtons[leadIdEnum].setEnabled(False)

            # Create instance of Region of Interest (ROI) bounding box and add to image viewer
            roiBox = ROIItem(self.imageViewer._scene, leadId)
            roiBox.setRect(x, y, width, height)
            roiBox.startTime = startTime

            self.imageViewer._scene.addItem(roiBox)
            roiBox.show()

    def updateLeadStartTime(self, leadId, value=None):
        if value is None:
            value = self.EditPanelLeadView.leadStartTimeSpinBox.value()

        self.imageViewer.setLeadRoiStartTime(leadId, value)

    def deleteLeadRoi(self, leadId):
        self.imageViewer.removeRoiBox(leadId)   # Remove lead roi box from image view
        self.mainWindow.leadButtons[LeadId[leadId]].setEnabled(True)    # Re-enable add lead menu button
        self.setControlPanel()  # Set control panel back to global view

    def deleteAllLeadRois(self):
        self.imageViewer.removeAllRoiBoxes()  # Remove all lead roi boxes from image view

        # Re-enable all add lead menu buttons
        for _, button in self.mainWindow.leadButtons.items():
            button.setEnabled(True)

        self.setControlPanel()    # Set control panel back to global view

    ######################
    # Grid ROI functions #
    ######################

    def addGridBox(self, expectedMm=5.0, x=0, y=0, width=200, height=200):
        """Add a grid calibration box for pixel-to-mm ratio calculation."""
        if self.imageViewer.hasImage():
            # Create instance of Grid calibration box and add to image viewer
            gridBox = GridBoxItem(self.imageViewer._scene, gridId=self.imageViewer.getGridBoxCount())
            gridBox.expectedMmWidth = expectedMm
            gridBox.expectedMmHeight = expectedMm
            gridBox.setRect(x, y, width, height)
            self.imageViewer._scene.addItem(gridBox)
            gridBox.show()

    def deleteGridBox(self, gridId):
        """Remove a specific grid box from the scene."""
        self.imageViewer.removeGridBox(gridId)

    def deleteAllGridBoxes(self):
        """Remove all grid boxes from the scene."""
        self.imageViewer.removeAllGridBoxes()

    def addBaseline(self, baselineId=0):
        """Add a baseline (isoelectric line) marker for a specific row."""
        if self.imageViewer.hasImage():
            self.imageViewer.addBaseline(baselineId=baselineId)

    def addThreeBaselines(self):
        """Add all 3 baselines for 12-lead ECG."""
        if self.imageViewer.hasImage():
            self.imageViewer.addThreeBaselines()

    def removeAllBaselines(self):
        """Remove all baseline markers."""
        self.imageViewer.removeBaseline()

    def removeBaseline(self, baselineId=None):
        """Remove a specific baseline or all baselines."""
        self.imageViewer.removeBaseline(baselineId)

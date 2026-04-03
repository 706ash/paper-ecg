"""
MainController.py
Created November 9, 2020

Controls the primary window, including the menu bar and the editor.
"""
from pathlib import Path

import cv2
import json
import dataclasses
import webbrowser
from PyQt5 import QtWidgets

from ecgdigitize.image import ColorImage, openImage

from Conversion import convertECGLeads, exportSignals
from views.MainWindow import MainWindow
from views.ImageView import *
from views.EditorWidget import *
from views.ROIView import *
from views.ExportFileDialog import *
from QtWrapper import *
import Annotation
from model.Lead import Lead, LeadId, GridBox
import datetime
from model.InputParameters import InputParameters


class MainController:

    def __init__(self):
        self.window = MainWindow()
        self.connectUI()
        self.openFile = None
        self.openImage: Optional[ColorImage] = None

    def connectUI(self):
        """
        Hook UI up to handlers in the controller
        """
        self.window.fileMenuOpen.triggered.connect(self.openImageFile)
        self.window.fileMenuClose.triggered.connect(self.closeImageFile)
        self.window.editor.processEcgData.connect(self.confirmDigitization)
        self.window.editor.saveAnnotationsButtonClicked.connect(self.saveAnnotations)

        self.window.reportIssueButton.triggered.connect(lambda: webbrowser.open('https://github.com/Tereshchenkolab/paper-ecg/issues'))
        self.window.userGuideButton.triggered.connect(lambda: webbrowser.open('https://github.com/Tereshchenkolab/paper-ecg/blob/master/USER-GUIDE.md'))

    def openImageFile(self):

        # Per pathlib documentation, if no selection is made then Path('.') is returned
        #  https://docs.python.org/3/library/pathlib.html
        path = Path(self.openFileBrowser("Open File", "Images (*.png *.jpg *.jpeg *.tif *.tiff)"))

        if path != Path('.'):
            self.window.editor.loadImageFromPath(path)
            self.window.editor.resetImageEditControls()
            self.openFile = path
            self.openImage = openImage(path)
            self.attempToLoadAnnotations()
        else:
            print("[Warning] No image selected")

    def openFileBrowser(self, caption: str, fileType: str, initialPath: str ="") -> str:
        """Launches a file browser for the user to select a file to open.

        Args:
            caption (str): The caption shown to the user
            fileType (str): The acceptable file types ex: `Images (*.png *.jpg)`
            initialPath (str, optional): The path at which the file browser opens. Defaults to "".

        Returns:
            str: Path to the selected file.
        """
        absolutePath, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window, # Parent
            caption,
            initialPath, # If the initial path is `""` it defaults to the most recent path.
            fileType
        )

        return absolutePath

    def closeImageFile(self):
        """Closes out current image file and resets editor controls."""
        self.window.editor.removeImage()
        self.window.editor.deleteAllLeadRois()
        self.window.editor.resetImageEditControls()
        self.openFile = None
        self.openImage = None

    def confirmDigitization(self):
        inputParameters = self.getCurrentInputParameters()

        # <- One-off utility to save I lead as file ->
        # rotatedImage = digitize.image.rotated(self.window.editor.image, inputParameters.rotation)
        # leadData = inputParameters.leads[LeadId.I]
        # cropped = digitize.image.cropped(
        #     rotatedImage,
        #     digitize.image.Rectangle(
        #         leadData.x, leadData.y, leadData.width, leadData.height
        #     )
        # )
        # import random
        # cv2.imwrite(f"lead-pictures/{self.openFile.stem}-{random.randint(0,10**8)}.png", cropped)

        if len(inputParameters.leads) > 0:
            self.processEcgData(inputParameters)
        else:
            warningDialog = MessageDialog(
                message="Warning: No data to process\n\nPlease select at least one lead to digitize",
                title="Warning"
            )
            warningDialog.exec_()

    # we have all ECG data and export location - ready to pass off to backend to digitize
    def processEcgData(self, inputParameters):
        if self.window.editor.image is None:
            raise Exception("IMAGE NOT AVAILABLE WHEN `processEcgData` CALLED")

        extractedSignals, previewImages, rawPixelSignals = convertECGLeads(self.openImage, inputParameters)

        if extractedSignals is None:
            errorDialog = MessageDialog(
                message="Error: Signal Processing Failed\n\nPlease check your lead selection boxes",
                title="Error"
            )
            errorDialog.exec_()
        else:
            exportFileDialog = ExportFileDialog(previewImages, extractedSignals)
            if exportFileDialog.exec_():
                # Select which signals to export based on user's choice
                signalsToExport = rawPixelSignals if exportFileDialog.exportUnit == "pixels" else extractedSignals
                self.exportECGData(
                    exportFileDialog.fileExportPath,
                    exportFileDialog.delimiterDropdown.currentText(),
                    signalsToExport,
                    exportFileDialog.exportUnit,
                    inputParameters
                )

    def exportECGData(self, exportPath, delimiter, extractedSignals, exportUnit, inputParameters):
        seperatorMap = {"Comma":',', "Tab":'\t', "Space":' '}
        assert delimiter in seperatorMap, f"Unrecognized delimiter {delimiter}"

        exportSignals(extractedSignals, exportPath, separator=seperatorMap[delimiter], exportUnit=exportUnit, inputParameters=inputParameters)

    def saveAnnotations(self):

        inputParameters = self.getCurrentInputParameters()

        if self.window.editor.image is None:
            return

        assert self.openFile is not None

        def extractLeadAnnotation(lead: Lead) -> Annotation.LeadAnnotation:
            return Annotation.LeadAnnotation(
                Annotation.CropLocation(
                    lead.x,
                    lead.y,
                    lead.width,
                    lead.height,
                ),
                lead.startTime
            )

        def extractGridBoxAnnotation(gridBox: GridBox) -> Annotation.GridBoxAnnotation:
            return Annotation.GridBoxAnnotation(
                Annotation.CropLocation(
                    gridBox.x,
                    gridBox.y,
                    gridBox.width,
                    gridBox.height,
                ),
                gridBox.expectedMmWidth,
                gridBox.expectedMmHeight
            )

        metadataDirectory = self.openFile.parent / '.paperecg'
        if not metadataDirectory.exists():
            metadataDirectory.mkdir()

        filePath = metadataDirectory / (self.openFile.stem + '-' + self.openFile.suffix[1:] + '.json')

        print("leads\n", inputParameters.leads.items())

        leads = {
            name: extractLeadAnnotation(lead) for name, lead in inputParameters.leads.items()
        }

        gridBoxes = [
            extractGridBoxAnnotation(gridBox) for gridBox in inputParameters.gridBoxes
        ]

        currentDateTime = (datetime.datetime.now()).strftime("%m/%d/%Y, %H:%M:%S")

        Annotation.Annotation(
            timeStamp = currentDateTime,
            image=Annotation.ImageMetadata(self.openFile.name, directory=str(self.openFile.parent.absolute())),
            rotation=inputParameters.rotation,
            timeScale=inputParameters.timeScale,
            voltageScale=inputParameters.voltScale,
            leads=leads,
            gridBoxes=gridBoxes,
            baselineYs=inputParameters.baselineYs
        ).save(filePath)

        print("Metadata successfully saved to:", str(filePath))
        self.window.editor.EditPanelGlobalView.setLastSavedTimeStamp(currentDateTime)

    def attempToLoadAnnotations(self):
        if self.window.editor.image is None:
            return

        assert self.openFile is not None

        metadataDirectory = self.openFile.parent / '.paperecg'
        if not metadataDirectory.exists():
            return

        filePath = metadataDirectory / (self.openFile.stem + '-' + self.openFile.suffix[1:] + '.json')
        if not filePath.exists():
            return

        print("Loading saved state from:", filePath, '...')

        # Load the saved state
        with open(filePath) as file:
            data = json.load(file)

        self.window.editor.loadSavedState(data)

    def getCurrentInputParameters(self):
        return InputParameters(
            rotation=self.window.editor.EditPanelGlobalView.getRotation(),
            timeScale=self.window.editor.EditPanelGlobalView.timeScaleSpinBox.value(),
            voltScale=self.window.editor.EditPanelGlobalView.voltScaleSpinBox.value(),
            leads=self.window.editor.imageViewer.getAllLeadRoisAsDict(),
            gridBoxes=self.window.editor.imageViewer.getAllGridBoxesAsList(),
            baselineYs=self.window.editor.imageViewer.getAllBaselineYs()  # Dict of {id: y}
        )



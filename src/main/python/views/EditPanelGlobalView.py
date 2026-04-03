from datetime import datetime
from PyQt5 import QtCore, QtWidgets

from QtWrapper import *
import model.EcgModel as EcgModel
import ecgdigitize
from ecgdigitize.image import ColorImage
from views.MessageDialog import *

DEFAULT_TIME_SCALE = 25
DEFAULT_VOLTAGE_SCALE = 10

class EditPanelGlobalView(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()

        self.editorWidget = parent

        self.sizePolicy().setHorizontalPolicy(QtWidgets.QSizePolicy.Expanding)
        self.sizePolicy().setVerticalPolicy(QtWidgets.QSizePolicy.Fixed)
        self.setMinimumWidth(380)

        self.initUI()
        self.connectUI()

    def initUI(self):

        VerticalBoxLayout(owner=self, name="mainLayout", margins=(5, 5, 5, 5), contents=[
            GroupBox(owner=self, name="adjustmentsGroup", title="Image Adjustments", layout=
                VerticalBoxLayout(owner=self, name="adjustmentsGroupLayout", contents=[
                    Label("Rotation"),
                    HorizontalSlider(self, "rotationSlider"),
                    HorizontalBoxLayout(owner=self, name="buttonLayout", margins=(0, 0, 0, 0), contents=[
                        PushButton(self, "autoRotateButton", text="Auto Rotate"),
                        PushButton(self, "resetRotationButton", text="Reset")
                    ])
                ])
            ),
            GroupBox(owner=self, name="gridCalibrationGroup", title="Grid Calibration", layout=
                VerticalBoxLayout(owner=self, name="gridCalibrationLayout", contents=[
                    Label(
                        owner=self,
                        name="gridCalibrationLabel",
                        text="Place grid boxes over known grid regions"
                    ),
                    HorizontalBoxLayout(owner=self, name="pixelPerMmLayout", contents=[
                        Label(
                            owner=self,
                            name="pixelPerMmLabel",
                            text="Pixels/mm: "
                        ),
                        Label(
                            owner=self,
                            name="pixelPerMmValue",
                            text="Not calibrated"
                        )
                    ]),
                    PushButton(
                        owner=self,
                        name="autoCalculateScaleButton",
                        text="Auto-Calculate Scales from Grid"
                    )
                ])
            ),
            GroupBox(owner=self, name="baselineGroup", title="Baseline (Isoelectric Line)", layout=
                VerticalBoxLayout(owner=self, name="baselineLayout", contents=[
                    Label(
                        owner=self,
                        name="baselineLabel",
                        text="Mark baseline (0 mV) for each row of 12-lead ECG"
                    ),
                    HorizontalBoxLayout(owner=self, name="baseline1Layout", contents=[
                        Label(
                            owner=self,
                            name="baseline1Label",
                            text="Row 1 (I, aVR, V1, V4): "
                        ),
                        Label(
                            owner=self,
                            name="baseline1YValue",
                            text="Not set"
                        )
                    ]),
                    HorizontalBoxLayout(owner=self, name="baseline2Layout", contents=[
                        Label(
                            owner=self,
                            name="baseline2Label",
                            text="Row 2 (II, aVL, V2, V5): "
                        ),
                        Label(
                            owner=self,
                            name="baseline2YValue",
                            text="Not set"
                        )
                    ]),
                    HorizontalBoxLayout(owner=self, name="baseline3Layout", contents=[
                        Label(
                            owner=self,
                            name="baseline3Label",
                            text="Row 3 (III, aVF, V3, V6): "
                        ),
                        Label(
                            owner=self,
                            name="baseline3YValue",
                            text="Not set"
                        )
                    ]),
                    Label(
                        owner=self,
                        name="baselineHelpLabel",
                        text="Use Baseline > Add 3 Baselines, then drag each to TP/PR segment"
                    )
                ])
            ),
            GroupBox(owner=self, name="gridScaleGroup", title="Manual Grid Scale", layout=
                FormLayout(owner=self, name="controlsLayout", contents=[
                    (
                        Label(
                            owner=self,
                            name="timeScaleLabel",
                            text="Time Scale: "
                        ),
                        HorizontalBoxLayout(
                            owner=self,
                            name="timeScaleBoxLayout",
                            contents=[
                                SpinBox(
                                    owner=self,
                                    name="timeScaleSpinBox",
                                    minVal=1,
                                    maxVal=1000,
                                    suffix=" mm/s",
                                    defaultValue=DEFAULT_TIME_SCALE
                                )
                            ]
                        )
                    ),
                    (
                        Label(
                            owner=self,
                            name="voltScaleLabel",
                            text="Voltage Scale: "
                        ),
                        HorizontalBoxLayout(
                            owner=self,
                            name="voltageScaleBoxLayout",
                            contents=[
                                SpinBox(
                                    owner=self,
                                    name="voltScaleSpinBox",
                                    minVal=1,
                                    maxVal=1000,
                                    suffix=" mm/mV",
                                    defaultValue=DEFAULT_VOLTAGE_SCALE
                                )
                            ]
                        )

                    )
                ])
            ),
            PushButton(
                owner=self,
                name="processDataButton",
                text="Process Lead Data"
            ),
            PushButton(
                owner=self,
                name="saveAnnotationsButton",
                text="Save Metadata"
            ),
            Label(
                owner=self,
                name="lastSavedTimeStamp",
                text=""
            )
        ])

        self.mainLayout.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignHCenter)
        self.setLayout(self.mainLayout)

        # Align the field labels in the grid scale form to the left
        self.controlsLayout.setFormAlignment(QtCore.Qt.AlignLeft)
        self.controlsLayout.setLabelAlignment(QtCore.Qt.AlignLeft)
        # Force the rows to grow horizontally
        self.controlsLayout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        # Align the inputs in the grid scale form to the right
        self.timeScaleBoxLayout.setAlignment(QtCore.Qt.AlignRight)
        self.voltageScaleBoxLayout.setAlignment(QtCore.Qt.AlignRight)

        self.lastSavedTimeStamp.setAlignment(QtCore.Qt.AlignCenter)

        self.clearTimeSpinBox()
        self.clearVoltSpinBox()
        self.pixelPerMmValue.setAlignment(QtCore.Qt.AlignRight)


    def connectUI(self):
        self.rotationSlider.sliderPressed.connect(self.rotationSliderChanged)
        self.rotationSlider.sliderMoved.connect(self.rotationSliderChanged)
        self.rotationSlider.setRange(-15 * 10, 15 * 10)

        self.autoRotateButton.clicked.connect(self.autoRotate)
        self.resetRotationButton.clicked.connect(self.resetRotation)

        self.processDataButton.clicked.connect(lambda: self.editorWidget.processEcgData.emit())
        self.saveAnnotationsButton.clicked.connect(lambda: self.editorWidget.saveAnnotationsButtonClicked.emit())
        self.autoCalculateScaleButton.clicked.connect(self.autoCalculateScalesFromGrid)

        # Connect to ROI updates to refresh pixel/mm and baseline display
        self.editorWidget.imageViewer.updateRoiItem.connect(self.updateGridCalibrationDisplay)
        self.editorWidget.imageViewer.updateRoiItem.connect(self.updateBaselineDisplay)

    def clearVoltSpinBox(self):
        self.voltScaleSpinBox.setValue(DEFAULT_VOLTAGE_SCALE)

    def clearTimeSpinBox(self):
        self.timeScaleSpinBox.setValue(DEFAULT_TIME_SCALE)

    def rotationSliderChanged(self, _ = None):
        value = self.getRotation()
        self.editorWidget.imageViewer.rotateImage(value)

    def getRotation(self) -> float:
        return self.rotationSlider.value() / -10

    def setRotation(self, angle: float):
        self.rotationSlider.setValue(angle * -10)
        self.rotationSliderChanged()

    def autoRotate(self):
        if self.editorWidget.image is None: return

        colorImage = ColorImage(self.editorWidget.image)
        angle = ecgdigitize.estimateRotationAngle(colorImage)

        if angle is None:
            errorModal = QtWidgets.QMessageBox()
            errorModal.setWindowTitle("Error")
            errorModal.setText("Unable to detect the angle automatically!")
            errorModal.setInformativeText("Use the slider to adjust the rotation manually")
            errorModal.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            errorModal.exec_()
        else:
            self.setRotation(angle)

    def resetRotation(self):
        self.setRotation(0)

    def setValues(self, voltScale, timeScale):
        self.voltScaleSpinBox.setValue(voltScale)
        self.timeScaleSpinBox.setValue(timeScale)

    def setLastSavedTimeStamp(self, timeStamp=None):
        if timeStamp is not None:
            self.lastSavedTimeStamp.setText("Last saved: " + timeStamp)
        else:
            self.lastSavedTimeStamp.setText(None)

    def updateGridCalibrationDisplay(self, _=None):
        """Update the pixel/mm display based on grid boxes."""
        pxPerMmX, pxPerMmY = self.editorWidget.imageViewer.getAveragePixelPerMmFromGridBoxes()
        
        if pxPerMmX is not None and pxPerMmY is not None:
            avgPxPerMm = (pxPerMmX + pxPerMmY) / 2.0
            self.pixelPerMmValue.setText(f"{avgPxPerMm:.2f} (X: {pxPerMmX:.2f}, Y: {pxPerMmY:.2f})")
            self.pixelPerMmValue.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.pixelPerMmValue.setText("Not calibrated")
            self.pixelPerMmValue.setStyleSheet("")

    def autoCalculateScalesFromGrid(self):
        """Auto-calculate time and voltage scales from grid boxes."""
        pxPerMmX, pxPerMmY = self.editorWidget.imageViewer.getAveragePixelPerMmFromGridBoxes()
        
        if pxPerMmX is None or pxPerMmY is None:
            errorModal = QtWidgets.QMessageBox()
            errorModal.setWindowTitle("No Grid Calibration")
            errorModal.setText("No grid boxes found!")
            errorModal.setInformativeText("Please add at least one grid box by going to Grid > Add 5mm Grid Box and placing it over a known grid region (e.g., 5mm x 5mm square).")
            errorModal.setStandardButtons(QtWidgets.QMessageBox.Ok)
            errorModal.exec_()
            return
        
        # Standard ECG paper: 25 mm/s time scale, 10 mm/mV voltage scale
        # Grid boxes give us pixels/mm, which we can use to verify/adjust scales
        avgPxPerMm = (pxPerMmX + pxPerMmY) / 2.0
        
        infoModal = QtWidgets.QMessageBox()
        infoModal.setWindowTitle("Grid Calibration Complete")
        infoModal.setText(f"Calibrated pixel-to-mm ratio: {avgPxPerMm:.2f} pixels/mm")
        infoModal.setInformativeText(
            f"X-axis: {pxPerMmX:.2f} pixels/mm\n"
            f"Y-axis: {pxPerMmY:.2f} pixels/mm\n\n"
            "The system will use this calibration to convert pixel measurements to mm.\n"
            "Ensure your time scale (mm/s) and voltage scale (mm/mV) are correct for your ECG paper."
        )
        infoModal.setStandardButtons(QtWidgets.QMessageBox.Ok)
        infoModal.exec_()

    def updateBaselineDisplay(self, _=None):
        """Update the baseline Y displays for all 3 baselines."""
        baselines = self.editorWidget.imageViewer.getAllBaselineYs()
        
        # Update each baseline display
        for i in range(3):
            label = getattr(self, f"baseline{i+1}YValue", None)
            if label:
                baselineY = baselines.get(i, None)
                if baselineY is not None:
                    label.setText(f"{baselineY:.1f}")
                    label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    label.setText("Not set")
                    label.setStyleSheet("")


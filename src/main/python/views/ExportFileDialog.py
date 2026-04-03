from PyQt5 import QtWidgets, QtCore
from QtWrapper import *
from views.ImagePreviewDialog import ImagePreviewDialog
import matplotlib.pyplot as plt

fileTypesDictionary = {
    "Text File (*.txt)": "txt",
    "CSV (*.csv)": "csv"
}


class ExportFileDialog(QtWidgets.QDialog):

    def __init__(self, previewImages, rawPixelSignals=None):
        super().__init__()
        self.leadPreviewImages = previewImages
        self.rawPixelSignals = rawPixelSignals or {}
        self.fileExportPath = None
        self.fileType = None
        self.exportUnit = "pixels"  # Default to pixels
        self.setWindowTitle("Export ECG Data")
        self.resize(700, 400)  #arbitrary size - just set to this for development purposes
        self.buildUI()

    def buildUI(self):

        self.leadPreviewLayout = QtWidgets.QFormLayout()

        # Create label and preview button for each lead that was processed
        for leadId, image in sorted(self.leadPreviewImages.items(), key=lambda img: img[0].value):
            
            buttonBox = QtWidgets.QWidget()
            buttonBoxLayout = QtWidgets.QHBoxLayout(buttonBox)
            buttonBoxLayout.setContentsMargins(0, 0, 0, 0)
            
            previewBtn = QtWidgets.QPushButton("Image Preview")
            previewBtn.clicked.connect(lambda checked, img=image.data, title=leadId.name: self.displayPreview(img, title))
            buttonBoxLayout.addWidget(previewBtn)
            
            signal = self.rawPixelSignals.get(leadId)
            if signal is not None:
                plotBtn = QtWidgets.QPushButton("Plot Signal")
                plotBtn.clicked.connect(lambda checked, sig=signal, title=leadId.name: self.displaySignalPlot(sig, title))
                buttonBoxLayout.addWidget(plotBtn)
                
            self.leadPreviewLayout.addRow(
                Label(owner=self, text="Lead " + str(leadId.name)),
                buttonBox
            )

        VerticalBoxLayout(owner=self, name="mainLayout", contents=[
            HorizontalBoxLayout(owner=self, name="chooseFileLayout", contents=[
                Label(
                    owner=self,
                    name="chooseFileLabel",
                    text="Export to:"
                ),
                LineEdit(
                    owner=self,
                    name="chooseFileTextBox",
                    contents="Choose file path",
                    readOnly=True
                ),
                PushButton(
                    owner=self,
                    name="chooseFileButton",
                    text="..."
                )
            ]),
            HorizontalBoxLayout(owner=self, name="exportTypeLayout", contents=[
                    Label(
                        owner=self,
                        name="exportTypeLabel",
                        text="Export Type: "
                    ),
                    ComboBox(
                        owner=self,
                        name="exportTypeDropdown",
                        items=[
                            "Pixel Coordinates",
                            "Voltage (mV)"
                        ]
                    )

            ]),
            HorizontalBoxLayout(owner=self, name="delimiterChoiceLayout", contents=[
                    Label(
                        owner=self,
                        name="delimiterLabel",
                        text="Data Delimiter: "
                    ),
                    ComboBox(
                        owner=self,
                        name="delimiterDropdown",
                        items=[
                            "Comma",
                            "Tab",
                            "Space"
                        ]
                    )

            ]),
            VerticalBoxLayout(owner=self, name="leadPreviewLayout_v", contents=[
                Label(
                    owner=self,
                    name="leadPreviewLabel",
                    text="Preview Selected Leads:"
                ),
                ScrollArea(
                    owner=self,
                    name="leadPreivewScrollArea",
                    innerWidget=
                        Widget(
                            owner=self,
                            name="leadPreviewWidget",
                            layout=self.leadPreviewLayout
                        )
                )
            ]),
            HorizontalBoxLayout(owner=self, name="confirmCancelButtonLayout", contents=[
                Label(
                    owner=self,
                    name="errorMessageLabel",
                    text=""
                ),
                PushButton(
                    owner=self,
                    name="confirmButton",
                    text="Export"
                ),
                PushButton(
                    owner=self,
                    name="cancelButton",
                    text="Cancel"
                )
            ])
        ])

        self.delimiterChoiceLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.exportTypeLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.confirmCancelButtonLayout.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)

        self.setLayout(self.mainLayout)

        self.connectUI()

    def connectUI(self):
        self.chooseFileButton.clicked.connect(lambda: self.openSaveFileDialog())
        self.confirmButton.clicked.connect(lambda: self.confirmExportPath())
        self.cancelButton.clicked.connect(lambda: self.close())
        self.exportTypeDropdown.currentTextChanged.connect(self.updateExportType)

    def updateExportType(self, text):
        """Update the export unit based on dropdown selection."""
        if text == "Voltage (mV)":
            self.exportUnit = "mV"
        else:
            self.exportUnit = "pixels"

    def openSaveFileDialog(self):
        path, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Export to File",
            filter="Text File (*.txt);;CSV (*.csv)"
        )
        if path is not "":
            self.errorMessageLabel.setText("")
            self.chooseFileTextBox.setText(path)
            self.fileExportPath = path
            tmpType = fileTypesDictionary.get(selectedFilter)
            if tmpType is not None:
                self.fileType = tmpType

    def confirmExportPath(self):
        if self.fileExportPath is not None and self.fileType is not None:
            self.accept()
        else:
            print("no export path selected")
            self.errorMessageLabel.setText("Please select a valid export path")

    def displayPreview(self, image, title):
        previewDialog = ImagePreviewDialog(image, title)
from PyQt5 import QtWidgets, QtCore
from QtWrapper import *
from views.ImagePreviewDialog import ImagePreviewDialog
import matplotlib.pyplot as plt

fileTypesDictionary = {
    "Text File (*.txt)": "txt",
    "CSV (*.csv)": "csv"
}


class ExportFileDialog(QtWidgets.QDialog):

    def __init__(self, previewImages, rawPixelSignals=None):
        super().__init__()
        self.leadPreviewImages = previewImages
        self.rawPixelSignals = rawPixelSignals or {}
        self.fileExportPath = None
        self.fileType = None
        self.exportUnit = "pixels"  # Default to pixels
        self.setWindowTitle("Export ECG Data")
        self.resize(700, 400)  #arbitrary size - just set to this for development purposes
        self.buildUI()

    def buildUI(self):

        self.leadPreviewLayout = QtWidgets.QFormLayout()

        # Create label and preview button for each lead that was processed
        for leadId, image in sorted(self.leadPreviewImages.items(), key=lambda img: img[0].value):
            
            buttonBox = QtWidgets.QWidget()
            buttonBoxLayout = QtWidgets.QHBoxLayout(buttonBox)
            buttonBoxLayout.setContentsMargins(0, 0, 0, 0)
            
            previewBtn = QtWidgets.QPushButton("Image Preview")
            previewBtn.clicked.connect(lambda checked, img=image.data, title=leadId.name: self.displayPreview(img, title))
            buttonBoxLayout.addWidget(previewBtn)
            
            signal = self.rawPixelSignals.get(leadId)
            if signal is not None:
                plotBtn = QtWidgets.QPushButton("Plot Signal")
                plotBtn.clicked.connect(lambda checked, sig=signal, title=leadId.name: self.displaySignalPlot(sig, title))
                buttonBoxLayout.addWidget(plotBtn)
                
            self.leadPreviewLayout.addRow(
                Label(owner=self, text="Lead " + str(leadId.name)),
                buttonBox
            )

        VerticalBoxLayout(owner=self, name="mainLayout", contents=[
            HorizontalBoxLayout(owner=self, name="chooseFileLayout", contents=[
                Label(
                    owner=self,
                    name="chooseFileLabel",
                    text="Export to:"
                ),
                LineEdit(
                    owner=self,
                    name="chooseFileTextBox",
                    contents="Choose file path",
                    readOnly=True
                ),
                PushButton(
                    owner=self,
                    name="chooseFileButton",
                    text="..."
                )
            ]),
            HorizontalBoxLayout(owner=self, name="exportTypeLayout", contents=[
                    Label(
                        owner=self,
                        name="exportTypeLabel",
                        text="Export Type: "
                    ),
                    ComboBox(
                        owner=self,
                        name="exportTypeDropdown",
                        items=[
                            "Pixel Coordinates",
                            "Voltage (mV)"
                        ]
                    )

            ]),
            HorizontalBoxLayout(owner=self, name="delimiterChoiceLayout", contents=[
                    Label(
                        owner=self,
                        name="delimiterLabel",
                        text="Data Delimiter: "
                    ),
                    ComboBox(
                        owner=self,
                        name="delimiterDropdown",
                        items=[
                            "Comma",
                            "Tab",
                            "Space"
                        ]
                    )

            ]),
            VerticalBoxLayout(owner=self, name="leadPreviewLayout_v", contents=[
                Label(
                    owner=self,
                    name="leadPreviewLabel",
                    text="Preview Selected Leads:"
                ),
                ScrollArea(
                    owner=self,
                    name="leadPreivewScrollArea",
                    innerWidget=
                        Widget(
                            owner=self,
                            name="leadPreviewWidget",
                            layout=self.leadPreviewLayout
                        )
                )
            ]),
            HorizontalBoxLayout(owner=self, name="confirmCancelButtonLayout", contents=[
                Label(
                    owner=self,
                    name="errorMessageLabel",
                    text=""
                ),
                PushButton(
                    owner=self,
                    name="confirmButton",
                    text="Export"
                ),
                PushButton(
                    owner=self,
                    name="cancelButton",
                    text="Cancel"
                )
            ])
        ])

        self.delimiterChoiceLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.exportTypeLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.confirmCancelButtonLayout.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignRight)

        self.setLayout(self.mainLayout)

        self.connectUI()

    def connectUI(self):
        self.chooseFileButton.clicked.connect(lambda: self.openSaveFileDialog())
        self.confirmButton.clicked.connect(lambda: self.confirmExportPath())
        self.cancelButton.clicked.connect(lambda: self.close())
        self.exportTypeDropdown.currentTextChanged.connect(self.updateExportType)

    def updateExportType(self, text):
        """Update the export unit based on dropdown selection."""
        if text == "Voltage (mV)":
            self.exportUnit = "mV"
        else:
            self.exportUnit = "pixels"

    def openSaveFileDialog(self):
        path, selectedFilter = QtWidgets.QFileDialog.getSaveFileName(
            parent=self,
            caption="Export to File",
            filter="Text File (*.txt);;CSV (*.csv)"
        )
        if path is not "":
            self.errorMessageLabel.setText("")
            self.chooseFileTextBox.setText(path)
            self.fileExportPath = path
            tmpType = fileTypesDictionary.get(selectedFilter)
            if tmpType is not None:
                self.fileType = tmpType

    def confirmExportPath(self):
        if self.fileExportPath is not None and self.fileType is not None:
            self.accept()
        else:
            print("no export path selected")
            self.errorMessageLabel.setText("Please select a valid export path")

    def displayPreview(self, image, title):
        previewDialog = ImagePreviewDialog(image, title)
        previewDialog.exec_()
        
    def displaySignalPlot(self, signal, title):
        # We can just pop up a matplotlib figure directly. Matplotlib's default 
        # Qt5Agg backend integrates well enough to just show it in a new window.
        fig, ax = plt.subplots(figsize=(10, 4))
        # Y values increase downwards in image pixels. Let's invert Y axis for intuition.
        ax.plot(signal, linewidth=2)
        ax.invert_yaxis()
        
        ax.set_title(f"Extracted 1D Signal - Lead {title}")
        ax.set_xlabel("Time (500 Hz samples)")
        ax.set_ylabel("Amplitude")
        plt.tight_layout()
        plt.show(block=False)

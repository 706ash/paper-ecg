"""
metadata.py

Contains classes and functions for handling metadata associated with leads used as inputs to
the extraction process. "Metadata" generally refers to non-image, human-provided data.
"""
from os import path
import dataclasses
import json
import pathlib
import datetime
from typing import Any, Dict, List, Optional, Union

from model import Lead


VERSION = 0


def noneValuesRemoved(dictionary: Dict[Any, Any]) -> Dict[Any, Any]:
    return {key: value for key, value in dictionary.items() if value is not None}


@dataclasses.dataclass(frozen=True)
class CropLocation():
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        assert isinstance(self.x, int)
        assert isinstance(self.y, int)
        assert isinstance(self.width, int)
        assert isinstance(self.height, int)


@dataclasses.dataclass(frozen=True)
class ImageMetadata():
    name: str
    directory: Optional[str] = None
    hashValue: Optional[Any] = None


@dataclasses.dataclass(frozen=True)
class LeadAnnotation:
    cropping: CropLocation
    start: Union[float, int]


@dataclasses.dataclass(frozen=True)
class GridBoxAnnotation:
    """Annotation for a grid calibration box.
    
    Attributes:
        cropping: Location and dimensions of the grid box in pixels
        expectedMmWidth: Expected physical width in mm (default 5.0 for one large square)
        expectedMmHeight: Expected physical height in mm (default 5.0 for one large square)
    """
    cropping: CropLocation
    expectedMmWidth: float = 5.0
    expectedMmHeight: float = 5.0


@dataclasses.dataclass(frozen=True)
class Schema:
    name: str
    version: int

    def __post_init__(self):
        assert isinstance(self.name, str)
        assert '.' not in self.name
        assert isinstance(self.version, int)

    def __repr__(self) -> str:
        return f"{self.name}.{self.version}"


@dataclasses.dataclass(frozen=True)
class Annotation:
    """Stores annotations made by the user to save their work for later.

    Example:
    ```
    Annotation(
        ImageMetadata("fullscan.png"), # Optionally, directory and hashValue
        0.0,  # Rotation
        25.0,  # Time scale
        10.0,  # Voltage Scale
        {
            Lead.LeadName.I: LeadAnnotation(
                CropLocation(0, 0, 20, 40),
                0.0
            ),
            Lead.LeadName.III: LeadAnnotation(
                CropLocation(0, 0, 20, 40),
                0.0
            )
        },
        [
            GridBoxAnnotation(
                CropLocation(100, 100, 50, 50),
                5.0, 5.0
            )
        ]
    )
    ```
    """
    schema: Schema = dataclasses.field(
        default=Schema("paper-ecg-user-annotation", VERSION), init=False
    )

    timeStamp: str
    image: ImageMetadata
    rotation: Union[int, float]
    timeScale: Union[int, float]
    voltageScale: Union[int, float]
    leads: Dict[Lead.LeadId, LeadAnnotation]
    gridBoxes: List[GridBoxAnnotation] = dataclasses.field(default_factory=list)
    baselineYs: Dict[int, float] = dataclasses.field(default_factory=dict)  # {baselineId: y_position}

    def toDict(self):
        dictionary = dataclasses.asdict(self)  # <3 dataclasses

        # Need to customize the leads to convert enum to string
        dictionary["leads"] = {
            lead.name: dataclasses.asdict(annotation) for lead, annotation in self.leads.items()
        }
        # Remove None entries from the image since it has optional fields
        dictionary["image"] = noneValuesRemoved(dataclasses.asdict(self.image))
        # Keep gridBoxes as list of dicts
        dictionary["gridBoxes"] = [dataclasses.asdict(annotation) for annotation in self.gridBoxes]

        return dictionary

    def save(self, filePath: pathlib.Path):
        dictionary = self.toDict()
        jsonSerial = json.dumps(dictionary)

        with filePath.open('w') as file:
            file.write(jsonSerial)

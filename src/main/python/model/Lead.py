"""
lead.py

Type representing an ECG lead.
"""

from enum import Enum
import dataclasses


class LeadId(Enum):
    """Enumerates the different names for leads

    `Enum` provides lots of awesome functionality:

      - Check if a string is a valid member of this enum:
        ```
        someString in Lead.__members__
        ```

      - Convert a string to enum:
        ```
        myLead = Lead[someString]
        ```
    """

    I   = 0
    II  = 1
    III = 2
    aVR = 3
    aVL = 4
    aVF = 5
    V1  = 6
    V2  = 7
    V3  = 8
    V4  = 9
    V5  = 10
    V6  = 11
    RHYTHM = 12

    def __str__(self) -> str:
        names = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'Rhythm']
        return names[self.value]

    def __repr__(self) -> str:
        return self.__str__()


@dataclasses.dataclass(frozen=True)
class Lead:
    x: int
    y: int
    width: int
    height: int
    startTime: int
    name: str = ""


@dataclasses.dataclass(frozen=True)
class GridBox:
    """Data class representing a grid calibration box.
    
    Users place this box over a known grid region (e.g., 5mm x 5mm large square)
    to calculate the pixel-to-mm ratio for accurate voltage and time scaling.
    
    Attributes:
        x: X coordinate of top-left corner (pixels)
        y: Y coordinate of top-left corner (pixels)
        width: Width of the box (pixels)
        height: Height of the box (pixels)
        expectedMmWidth: Expected physical width in mm (default 5.0 for one large square)
        expectedMmHeight: Expected physical height in mm (default 5.0 for one large square)
    """
    x: int
    y: int
    width: int
    height: int
    expectedMmWidth: float = 5.0
    expectedMmHeight: float = 5.0

    def getPixelPerMm(self):
        """Calculate the pixel-to-mm ratio.
        
        Returns:
            tuple: (pixelsPerMmX, pixelsPerMmY)
        """
        if self.expectedMmWidth > 0 and self.expectedMmHeight > 0:
            pixelsPerMmX = self.width / self.expectedMmWidth
            pixelsPerMmY = self.height / self.expectedMmHeight
            return pixelsPerMmX, pixelsPerMmY
        return None, None

    def getAveragePixelPerMm(self):
        """Calculate the average pixel-to-mm ratio.
        
        Returns:
            float: Average pixels per mm
        """
        px, py = self.getPixelPerMm()
        if px is not None and py is not None:
            return (px + py) / 2.0
        return None


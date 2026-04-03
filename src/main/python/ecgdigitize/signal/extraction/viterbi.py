"""
viterbi.py
Created June 1, 2021

...
"""
from collections import defaultdict
from functools import partial

from dataclasses import dataclass
from ecgdigitize import signal
from math import isnan, sqrt, asin, pi
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

import numpy as np

from ... import common
from ...common import Numeric
from ...image import BinaryImage


@dataclass(frozen=True)
class Point:
    x: Numeric
    y: Numeric

    @property
    def index(self) -> int:
        if isinstance(self.x, int):
            return self.x
        else:
            return round(self.x)

    @property
    def values(self) -> Tuple[Numeric, Numeric]:
        return (self.x, self.y)


def findContiguousRegions(oneDimImage: np.ndarray) -> Iterable[Tuple[int, int]]:
    """
    ex: |---###--#-----#####|  (where # is on, - is off)
        |0123456789...      |
    returns [(3,5), (8,8), (14,18)]
    """
    locations = []
    start = None
    for index, pixel in enumerate(oneDimImage):
        if pixel > 0 and start is None:
            start = index
        elif pixel == 0 and start is not None:
            locations.append((start, index))
            start = None

    return locations


def findContiguousRegionCenters(oneDimImage: np.ndarray) -> Iterable[int]:
    """
    ex: |---###--#-----#####|  (where # is on, - is off)
        |0123456789...      |
    returns [4, 8, 16]

    Rounds down to the nearest int
    """
    return [int(np.mean(list(locationPair))) for locationPair in findContiguousRegions(oneDimImage)]


def euclideanDistance(x: Numeric, y: Numeric) -> float:
    return sqrt((x**2) + (y**2))


def distanceBetweenPoints(firstPoint: Point, secondPoint: Point) -> float:
    return euclideanDistance(firstPoint.x - secondPoint.x, firstPoint.y - secondPoint.y)


def angleFromOffsets(x: Numeric, y: Numeric) -> float:
    return asin(y/euclideanDistance(x,y)) / pi * 180


def angleBetweenPoints(firstPoint: Point, secondPoint: Point) -> float:
    deltaX = secondPoint.x - firstPoint.x
    deltaY = secondPoint.y - firstPoint.y
    return angleFromOffsets(deltaX, deltaY)


def angleSimilarity(firstAngle: float, secondAngle: float) -> float:
    return (180 - abs(secondAngle - firstAngle)) / 180


def searchArea(initialRow: int, radius: int) -> Iterable[Tuple[int, int]]:
    area = []
    for column in range(1, radius+1):
        verticalOffset = 0
        while euclideanDistance(column, verticalOffset + 1) <= float(radius):
            verticalOffset += 1
        area.append((initialRow - verticalOffset, initialRow + verticalOffset))

    return area


def getPointLocations(image: np.ndarray) -> List[List[Point]]:
    columns = np.swapaxes(image, 0, 1)

    raw_regions = []
    # Scan horizontally across the image
    for column, pixels in enumerate(columns):
        regions = list(findContiguousRegions(pixels))
        raw_regions.append(regions)

    def get_c_at(c_idx, relative_to):
        if 0 <= c_idx < len(raw_regions) and raw_regions[c_idx]:
            return min([(s+e)/2.0 for s, e in raw_regions[c_idx]], key=lambda c: abs(c - relative_to))
        return relative_to

    pointLocations = []
    for col in range(len(columns)):
        regions = raw_regions[col]
        col_points = []
        
        for start, end in regions:
            center = (start + end) / 2.0
            height = end - start
            
            y_point = center
            
            if height >= 5:
                # Look slightly further out in case of noise or 2-pixel wide apex
                c_prev = get_c_at(col - 1, center)
                if c_prev == center: c_prev = get_c_at(col - 2, center)
                
                c_next = get_c_at(col + 1, center)
                if c_next == center: c_next = get_c_at(col + 2, center)
                
                # Upward peak: neighbors are significantly lower (higher Y index)
                if (c_prev - center) >= 2 and (c_next - center) >= 2:
                    y_point = start
                # Downward peak: neighbors are significantly higher (lower Y index)
                elif (center - c_prev) >= 2 and (center - c_next) >= 2:
                    y_point = end
                    
            col_points.append(Point(col, y_point))
            
        pointLocations.append(col_points)

    return pointLocations


# TODO: Make score multiply, or normalize the score by the length of the path
def score(currentPoint: Point, candidatePoint: Point, candidateAngle: float) -> float:
    # Distance weight and Angle weight
    DISTANCE_WEIGHT = 0.6
    
    dx = currentPoint.x - candidatePoint.x
    dy = currentPoint.y - candidatePoint.y
    
    # Dampen the vertical distance penalty. 
    # ECG peaks (especially R-peaks) involve large Y deviations.
    # Standard Euclidean distance makes these peaks "expensive", causing undershooting.
    # By dividing dy by 5.0, we make climb-intensive paths much more competitive.
    dampenedDistance = sqrt(dx**2 + (dy/5.0)**2)
    
    currentAngle = angleBetweenPoints(candidatePoint, currentPoint)
    angleValue = 1 - angleSimilarity(currentAngle, candidateAngle)

    return (dampenedDistance * DISTANCE_WEIGHT) + (angleValue * (1 - DISTANCE_WEIGHT))


def getAdjacent(pointsByColumn, bestPathToPoint, startingColumn: int, minimumLookBack: int):
    rightColumnIndex = startingColumn
    leftColumnIndex = int(common.lowerClamp(startingColumn-minimumLookBack, 0))

    result = list(common.flatten(pointsByColumn[leftColumnIndex:rightColumnIndex]))

    while len(result) == 0 and leftColumnIndex >= 0:
        leftColumnIndex -= 1
        result = list(common.flatten(pointsByColumn[leftColumnIndex:rightColumnIndex])) # TODO: Make this more efficient?

    for point in result:
        assert point in bestPathToPoint, "Found point that hasn't yet been frozen"
        pointScore, _, pointAngle = bestPathToPoint[point]
        yield pointScore, point, pointAngle


def interpolate(fromPoint: Point, toPoint: Point) -> Iterator[Point]:
    slope = (toPoint.y - fromPoint.y) / (toPoint.x - fromPoint.x)
    f = lambda x: slope * (x - toPoint.x) + toPoint.y

    for x in range(fromPoint.index + 1, toPoint.index):
        yield Point(x, f(x))


def convertPointsToSignal(points: List[Point], width: Optional[int] = None) -> np.ndarray:
    assert len(points) > 0

    firstPoint = points[0]  # farthest from y-axis (recall we `back`-tracked earlier so paths are reversed)
    lastPoint = points[-1]  # closest to y-axis

    arraySize = width or (firstPoint.x + 1)
    signal = np.full(arraySize, np.nan, dtype=float)

    signal[firstPoint.index] = firstPoint.y
    priorPoint = firstPoint

    for point in points[1:]:
        if point.index + 1 < arraySize:
            if isnan(signal[point.index + 1]):
                for interpolatedPoint in interpolate(point, priorPoint):
                    if 0 <= interpolatedPoint.index < arraySize:
                        signal[interpolatedPoint.index] = interpolatedPoint.y

        if 0 <= point.index < arraySize:
            signal[point.index] = point.y
        priorPoint = point

    # Final padding: if the signal ends a few pixels early, carry the last value to the end
    endIdx = firstPoint.index
    if endIdx < arraySize - 1:
        signal[endIdx:arraySize] = firstPoint.y

    return signal


def extractSignal(binary: BinaryImage) -> Optional[np.ndarray]:
    pointsByColumn = getPointLocations(binary.data)
    points = list(common.flatten(pointsByColumn))

    if len(points) == 0:
        return None

    bestPathToPoint: Dict[Point, Tuple[float, Optional[Point], float]] = {}

    # Initialize the DP table with base cases (far left side)
    # We allow the signal to start in any of the first 10 columns
    for column in pointsByColumn[:10]:
        for point in column:
            bestPathToPoint[point] = (0, None, 0)

    # Build the table
    for column in pointsByColumn[1:]:
        for point in column:
            # Use look-back of 1 so it prefers nearest columns first (important for peaks)
            # The getAdjacent function will automatically look deeper if a column is empty.
            adjacent = list(getAdjacent(pointsByColumn, bestPathToPoint, point.index, minimumLookBack=1))

            if len(adjacent) == 0:
                bestPathToPoint[point] = (1000, None, 0) # High cost for disconnected points
            else:
                bestScore: float
                bestPoint: Point
                bestScore, bestPoint = min(
                    [(score(point, candidatePoint, candidateAngle) + cadidateScore, candidatePoint)
                    for cadidateScore, candidatePoint, candidateAngle in adjacent],
                    key=lambda triplet: triplet[0]
                )
                bestPathToPoint[point] = (bestScore, bestPoint, angleBetweenPoints(bestPoint, point))

    # Search for the best ending point in the last columns
    # We want the FAR RIGHT point, don't just minimize score globally
    OPTIMAL_ENDING_WIDTH = 50
    candidates = list(getAdjacent(pointsByColumn, bestPathToPoint, startingColumn=binary.width, minimumLookBack=OPTIMAL_ENDING_WIDTH))
    
    if not candidates:
        return None
        
    # Group candidates by column and pick from the rightmost non-empty column
    max_x = max(p.x for _, p, _ in candidates)
    rightmost_candidates = [c for c in candidates if c[1].x == max_x]
    
    # Within the rightmost column, pick the best score
    _, current = min(
        [(totalScore, point) for totalScore, point, _ in rightmost_candidates],
        key=lambda pair: pair[0]
    )
    
    bestPath = []
    while current is not None:
        bestPath.append(current)
        _, current, _ = bestPathToPoint[current]

    signal = convertPointsToSignal(bestPath, width=binary.width)

    # scores = [bestPathToPoint[point][0] ** .5 for point in points]
    # plt.imshow(binary.toColor().data, cmap='Greys')
    # plt.scatter([point.x for point in points], [point.y for point in points], c=scores)
    # # plt.plot(signal, c='purple')
    # plt.show()

    return signal

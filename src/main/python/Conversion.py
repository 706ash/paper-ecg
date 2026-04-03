from pathlib import Path

import numpy as np
from numpy.lib.arraysetops import isin

import ecgdigitize
import ecgdigitize.signal
import ecgdigitize.image
from ecgdigitize import common, visualization
from ecgdigitize.image import ColorImage, Rectangle

from model.InputParameters import InputParameters


def convertECGLeads(inputImage: ColorImage, parameters: InputParameters):
    # Apply rotation
    rotatedImage = ecgdigitize.image.rotated(inputImage, parameters.rotation)

    # Crop each lead
    leadImages = {
        leadId: ecgdigitize.image.cropped(rotatedImage, Rectangle(lead.x, lead.y, lead.width, lead.height))
        for leadId, lead in parameters.leads.items()
    }

    extractSignal = ecgdigitize.digitizeSignal
    extractGrid   = ecgdigitize.digitizeGrid

    # Map all lead images to signal data
    signals = {
        leadId: extractSignal(leadImage)
        for leadId, leadImage in leadImages.items()
    }

    # If all signals failed -> Failure
    if all([isinstance(signal, common.Failure) for _, signal in signals.items()]):
        return None, None

    previews = {
        leadId: visualization.overlaySignalOnImage(signal, image)
        for (leadId, image), (_, signal) in zip(leadImages.items(), signals.items())
    }

    # Map leads to grid size estimates
    gridSpacings = {
        leadId: extractGrid(leadImage)
        for leadId, leadImage in leadImages.items()
    }
    # Just got successful spacings
    spacings = [spacing for spacing in gridSpacings.values() if not isinstance(spacing, common.Failure)]

    if len(spacings) == 0:
        return None, None

    samplingPeriodInPixels = gridHeightInPixels = common.mean(spacings)

    # Store raw signals (in pixels, zero-referenced but not scaled to mV)
    rawSignals = {
        leadId: ecgdigitize.signal.zeroECGSignal(signal)
        for leadId, signal in signals.items()
    }

    # Scale signals to mV
    scaledSignals = {
        leadId: ecgdigitize.signal.verticallyScaleECGSignal(
            rawSignal,
            gridHeightInPixels,
            parameters.voltScale, gridSizeInMillimeters=1.0
        )
        for leadId, rawSignal in rawSignals.items()
    }

    # TODO: Pass in the grid size in mm
    samplingPeriod = ecgdigitize.signal.ecgSignalSamplingPeriod(samplingPeriodInPixels, parameters.timeScale, gridSizeInMillimeters=1.0)

    # Zero pad all signals on the left based on their start times and the samplingPeriod
    paddedRawSignals = {
        leadId: common.padLeft(signal, int(parameters.leads[leadId].startTime / samplingPeriod))
        for leadId, signal in rawSignals.items()
    }
    
    paddedScaledSignals = {
        leadId: common.padLeft(signal, int(parameters.leads[leadId].startTime / samplingPeriod))
        for leadId, signal in scaledSignals.items()
    }

    # Pad all signals on the right to same length
    maxLength = max([len(s) for _, s in paddedRawSignals.items()])
    fullRawSignals = {
        leadId: common.padRight(signal, maxLength - len(signal))
        for leadId, signal in paddedRawSignals.items()
    }
    
    maxLength = max([len(s) for _, s in paddedScaledSignals.items()])
    fullScaledSignals = {
        leadId: common.padRight(signal, maxLength - len(signal))
        for leadId, signal in paddedScaledSignals.items()
    }

    # Resample everything to exactly 500 Hz (0.002s intervals)
    TARGET_SAMPLING_RATE = 500.0
    target_dt = 1.0 / TARGET_SAMPLING_RATE
    
    old_times = np.arange(maxLength) * samplingPeriod
    if len(old_times) > 0:
        new_length = int(np.ceil(old_times[-1] / target_dt))
        new_times = np.arange(new_length) * target_dt
        
        fullRawSignals_500Hz = {
            leadId: np.interp(new_times, old_times, signal)
            for leadId, signal in fullRawSignals.items()
        }
        fullScaledSignals_500Hz = {
            leadId: np.interp(new_times, old_times, signal)
            for leadId, signal in fullScaledSignals.items()
        }
    else:
        fullRawSignals_500Hz = fullRawSignals
        fullScaledSignals_500Hz = fullScaledSignals

    # Return both raw (pixels) and scaled (mV) signals
    return fullScaledSignals_500Hz, previews, fullRawSignals_500Hz


def exportSignals(leadSignals, filePath, separator='\t', exportUnit='pixels', inputParameters=None):
    """Exports a dict of lead signals to file

    Args:
        leadSignals: Dict mapping lead id's to np array of signal data
        filePath: Path to export file
        separator: Field separator character
        exportUnit: 'pixels' or 'mV' - for labeling purposes
        inputParameters: InputParameters object (not used directly since signals are pre-converted)
    """
    leads = common.zipDict(leadSignals)
    leads.sort(key=lambda pair: pair[0].value)

    assert len(leads) >= 1
    lengthOfFirst = len(leads[0][1])

    assert all([len(signal) == lengthOfFirst for key, signal in leads])

    collated = np.array([signal for _, signal in leads])
    output = np.swapaxes(collated, 0, 1)

    if not issubclass(type(filePath), Path):
        filePath = Path(filePath)

    if filePath.exists():
        print("Warning: Output file will be overwritten!")

    outputLines = [
        separator.join(
            [str(val) for val in row]
        ) + "\n"
        for row in output
    ]

    with open(filePath, 'w') as outputFile:
        outputFile.writelines(outputLines)


# Removed convertSignalsToMV - signals are now pre-converted in convertECGLeads

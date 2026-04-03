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

    # Track how far each padded signal extends before further padding
    signalLengths = {
        leadId: len(signal)
        for leadId, signal in paddedRawSignals.items()
    }
    
    # Use trimmed signals (without extra right-padding) for interpolation
    trimmedRawSignals = {
        leadId: signal[:signalLengths[leadId]]
        for leadId, signal in paddedRawSignals.items()
    }
    trimmedScaledSignals = {
        leadId: signal[:signalLengths[leadId]]
        for leadId, signal in paddedScaledSignals.items()
    }

    # Resample everything to exactly 500 Hz (0.002s intervals)
    TARGET_SAMPLING_RATE = 500.0
    target_dt = 1.0 / TARGET_SAMPLING_RATE
    
    fullRawSignals_500Hz = {}
    fullScaledSignals_500Hz = {}
    for leadId, rawSignal in trimmedRawSignals.items():
        trimmedLength = len(rawSignal)
        if trimmedLength == 0:
            fullRawSignals_500Hz[leadId] = np.array([])
            fullScaledSignals_500Hz[leadId] = np.array([])
            continue

        old_times = np.arange(trimmedLength) * samplingPeriod
        duration = old_times[-1]
        if duration <= 0:
            new_times = np.array([0.0])
        else:
            new_length = int(np.floor(duration / target_dt)) + 1
            new_times = np.arange(new_length) * target_dt

        fullRawSignals_500Hz[leadId] = np.interp(new_times, old_times, rawSignal)
        scaledSignal = trimmedScaledSignals[leadId]
        fullScaledSignals_500Hz[leadId] = np.interp(new_times, old_times, scaledSignal)

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
    maxLength = max(len(signal) for _, signal in leads)

    if not issubclass(type(filePath), Path):
        filePath = Path(filePath)

    if filePath.suffix == '.npz':
        # Save as named numpy arrays for easy access
        export_dict = {}
        for lead_id, signal in leads:
            # Use custom name if provided in inputParameters, otherwise use Enum name
            name = lead_id.name
            if inputParameters and lead_id in inputParameters.leads:
                custom_name = inputParameters.leads[lead_id].name
                if custom_name:
                    name = custom_name
            export_dict[name] = signal
            
        export_dict['sampling_rate'] = 500.0  # Common metadata
        np.savez(filePath, **export_dict)
        return

    if filePath.exists():
        print("Warning: Output file will be overwritten!")

    outputLines = []
    for row_index in range(maxLength):
        row_values = []
        for _, signal in leads:
            if row_index < len(signal):
                row_values.append(str(signal[row_index]))
            else:
                row_values.append('')
        outputLines.append(separator.join(row_values) + "\n")

    with open(filePath, 'w') as outputFile:
        outputFile.writelines(outputLines)


# Removed convertSignalsToMV - signals are now pre-converted in convertECGLeads

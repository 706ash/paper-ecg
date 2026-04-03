# Grid Calibration and Baseline Guide

## Overview

The Paper ECG application includes enhanced features for accurate ECG digitization:

1. **Grid Calibration** - Define pixel-to-mm ratio using 5mm grid boxes (resizable)
2. **3 Baseline Markers** - Mark isoelectric lines for each of the 3 rows in 12-lead ECG
3. **Dual Export Options** - Export as pixel coordinates or voltage (mV) values

## Features

### 1. Grid Calibration (5mm Boxes) - FIXED

**Purpose:** Convert pixel measurements to physical units (mm)

**How to Use:**
1. Go to `Grid > Add 5mm Grid Box` (or press `Ctrl+G`)
2. A blue calibration box will appear
3. **Drag the box** by clicking inside it
4. **Resize the box** by clicking and dragging the **8 blue handles** around the border:
   - Corner handles: Resize both width and height
   - Edge handles: Resize one dimension only
5. Place over a **5mm × 5mm large square** on the ECG grid
6. The "Pixels/mm" display shows the calculated calibration ratio

**Tips:**
- Place grid boxes over clear grid regions without signal overlap
- Use 2-3 grid boxes for averaging
- The system displays X and Y axis calibration separately
- **Box is now fully resizable like lead boxes!**

### 2. Three Baseline Markers (for 12-lead ECG)

**Purpose:** Define the 0 mV reference for each row of the 12-lead ECG

Standard 12-lead ECGs are arranged in 3 rows:
- **Row 1:** Leads I, II, III
- **Row 2:** Leads aVR, aVL, V1 (sometimes V2)
- **Row 3:** Leads V2-V6 (varies by layout)

Each row may have a different baseline position due to:
- Paper positioning during scanning
- Grid line variations
- Signal placement on the original printout

**How to Use:**
1. Go to `Baseline > Add 3 Baselines (for 12-lead)` (or press `Ctrl+B`)
2. Three colored dashed lines will appear:
   - **Green:** Baseline 1 for Row 1 (I, II, III)
   - **Blue:** Baseline 2 for Row 2 (aVR, aVL, V1)
   - **Orange:** Baseline 3 for Row 3 (V2, V3, V4)
3. **Drag each baseline vertically** to align with the **TP segment** or **PR segment** of leads in that row
4. The baseline Y positions are displayed in the control panel

**Individual Baseline Options:**
- `Baseline > Add Baseline Row 1` (Ctrl+Shift+1) - Add only row 1 baseline
- `Baseline > Add Baseline Row 2` (Ctrl+Shift+2) - Add only row 2 baseline
- `Baseline > Add Baseline Row 3` (Ctrl+Shift+3) - Add only row 3 baseline
- `Baseline > Remove All Baselines` - Remove all baselines

**Why It Matters:**
- Pixels above baseline → Positive voltage (mV)
- Pixels below baseline → Negative voltage (mV)
- Essential for accurate ST-segment analysis and QT measurement
- Different rows may need different baselines

### 3. Export Options

When exporting digitized ECG data, you have two options:

#### Option A: Pixel Coordinates
- **What:** Raw extracted signal in pixel units (zero-referenced)
- **Use Case:** Further custom processing, algorithm development
- **Export Selection:** Choose "Pixel Coordinates" in the export dialog

#### Option B: Voltage (mV)
- **What:** Signal converted to millivolts using grid calibration
- **Use Case:** Clinical analysis, research, machine learning
- **Export Selection:** Choose "Voltage (mV)" in the export dialog
- **Requirements:** 
  - Grid boxes must be placed for calibration
  - Baselines should be set for accurate 0 mV reference

## Complete Workflow

### Step-by-Step Guide

1. **Open ECG Image**
   - `File > Open` → Select your ECG scan

2. **Correct Rotation** (if needed)
   - Use the rotation slider
   - Or click "Auto Rotate"

3. **Add Grid Calibration**
   - `Grid > Add 5mm Grid Box`
   - **Drag and resize** to fit exactly over a 5mm × 5mm large square
   - Use the 8 handles around the border for precise sizing
   - Add 2-3 boxes in different regions
   - Verify "Pixels/mm" shows reasonable values (typically 4-6 for 300 DPI scans)

4. **Set Baselines**
   - `Baseline > Add 3 Baselines (for 12-lead)`
   - **Drag each colored line** to the TP/PR segment of its corresponding row
   - Green line → Row 1 (I, II, III)
   - Blue line → Row 2 (aVR, aVL, V1)
   - Orange line → Row 3 (V2, V3, V4)
   - Verify baseline Y positions are displayed

5. **Add Lead Boxes**
   - `Lead > Add Lead I, II, III, V1-V6`
   - Place boxes around each lead waveform
   - Set lead start times

6. **Set Grid Scales**
   - Time Scale: 25 mm/s (standard)
   - Voltage Scale: 10 mm/mV (standard)

7. **Process and Export**
   - Click "Process Lead Data"
   - Preview signals
   - Select export type:
     - **Pixel Coordinates** → Raw pixel values
     - **Voltage (mV)** → Clinical units
   - Choose delimiter (Comma for CSV)
   - Click "Export"

## Technical Details

### Grid Calibration Math

When you place a 5mm grid box:
```
pixelsPerMmX = boxWidthPixels / 5.0
pixelsPerMmY = boxHeightPixels / 5.0
averagePixelsPerMm = (pixelsPerMmX + pixelsPerMmY) / 2.0
```

### Voltage Conversion Math

For mV export, the conversion uses the baseline and grid calibration:
```
voltage_mV = ((baselineY - signalY) / pixelsPerMmY) / voltageScale_mmPerMV

Where:
- baselineY: Y position of the isoelectric line (0 mV reference)
- signalY: Y position of the signal at each point
- pixelsPerMmY: From grid calibration (Y-axis)
- voltageScale_mmPerMV: Typically 10 mm/mV
```

### Baseline Convention

- Image Y coordinates increase downward (top of image = 0)
- ECG voltage increases upward (positive = up)
- Therefore: `voltage ∝ (baselineY - signalY)`

## File Formats

### Export File Format (CSV with mV)
```
Lead_I,Lead_II,Lead_III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6
0.05,0.08,0.03,-0.02,0.04,0.06,0.12,0.15,0.10,0.08,0.06,0.04
0.06,0.09,0.04,-0.01,0.05,0.07,0.14,0.18,0.12,0.09,0.07,0.05
...
```

### Export File Format (CSV with Pixels)
```
Lead_I,Lead_II,Lead_III,aVR,aVL,aVF,V1,V2,V3,V4,V5,V6
5,8,3,-2,4,6,12,15,10,8,6,4
6,9,4,-1,5,7,14,18,12,9,7,5
...
```

### Saved Metadata (JSON)
```json
{
  "schema": "paper-ecg-user-annotation.0",
  "timeStamp": "04/02/2026, 10:30:00",
  "image": {
    "name": "patient_ecg.jpg",
    "directory": "C:/ECG/Images"
  },
  "rotation": 0.5,
  "timeScale": 25,
  "voltageScale": 10,
  "leads": { ... },
  "gridBoxes": [
    {
      "cropping": { "x": 100, "y": 150, "width": 225, "height": 228 },
      "expectedMmWidth": 5.0,
      "expectedMmHeight": 5.0
    }
  ],
  "baselineYs": {
    "0": 180.5,
    "1": 450.2,
    "2": 720.8
  }
}
```

## Troubleshooting

### Grid box won't resize
- Make sure you're clicking on the **handles** (small blue squares at corners and edges)
- The box must be **selected** (highlighted) to show handles
- Click once on the box to select it, then drag a handle

### "Not calibrated" for Pixels/mm
- Add at least one 5mm grid box
- Ensure the box is properly sized (not too small)
- Resize the box to cover a full 5mm × 5mm square

### Baseline not showing
- Check `Baseline > Add 3 Baselines` was clicked
- Zoom out if the line is hard to see (colored dashed lines)
- Each baseline has a different color for identification

### Export shows all zeros
- Check that lead boxes contain actual signal
- Verify signal extraction preview shows the waveform

### mV values seem incorrect
- Verify grid boxes are placed over actual 5mm squares
- Check baselines are on isoelectric segments (TP or PR)
- Confirm voltage scale is set correctly (usually 10 mm/mV)
- Ensure baseline is above the signal for positive voltages

## Best Practices

1. **Always calibrate first** - Place grid boxes before lead selection
2. **Use multiple grid boxes** - 2-3 boxes improves accuracy
3. **Set all 3 baselines** - One for each row of the 12-lead ECG
4. **Place baselines carefully** - TP segment is most reliable for 0 mV
5. **Save metadata** - Preserves all annotations for later
6. **Export as mV for clinical use** - Pixel coordinates only for custom processing
7. **Verify with preview** - Always check signal preview before export
8. **Resize grid boxes precisely** - Use the handles for accurate sizing

## Menu Summary

| Menu | Item | Shortcut | Description |
|------|------|----------|-------------|
| Grid | Add 5mm Grid Box | Ctrl+G | Add grid calibration box (resizable) |
| Grid | Delete All Grid Boxes | - | Remove all grid boxes |
| Baseline | Add 3 Baselines (for 12-lead) | Ctrl+B | Add 3 baselines for 12-lead ECG |
| Baseline | Add Baseline Row 1 | Ctrl+Shift+1 | Add baseline for row 1 |
| Baseline | Add Baseline Row 2 | Ctrl+Shift+2 | Add baseline for row 2 |
| Baseline | Add Baseline Row 3 | Ctrl+Shift+3 | Add baseline for row 3 |
| Baseline | Remove All Baselines | - | Remove all baselines |
| File | Export | - | Export with pixel/mV option |

## Updates in This Version

### Fixed
- ✅ **Grid box resizing** - Now works correctly with 8 handles like lead boxes
- ✅ **Grid box font** - Smaller font no longer interferes with resizing

### Added
- ✅ **3 Baseline markers** - One for each row of 12-lead ECG
- ✅ **Individual baseline colors** - Green (row 1), Blue (row 2), Orange (row 3)
- ✅ **Baseline display panel** - Shows Y position for all 3 baselines
- ✅ **Export type selection** - Pixel coordinates or voltage (mV)

### Changed
- ❌ Removed: 1mm grid box option (simplified to 5mm only)
- ❌ Removed: Single baseline option (now 3 baselines for 12-lead)

## Research Applications

Accurate calibration and baseline marking enables:
- **QT/QTc interval measurement** - Requires precise time scaling
- **ST-segment analysis** - Requires accurate baseline and voltage
- **QRS amplitude criteria** - Voltage-based diagnostic criteria
- **Machine learning** - Standardized mV inputs for models
- **Multi-center studies** - Consistent units across different scanners

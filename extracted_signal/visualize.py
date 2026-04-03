import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --- Configuration ---
# Replace this with the actual path to your exported file
FILE_PATH = "leads.csv"

# The separator used during export ("Comma", "Tab", or "Space")
# Change this to "\t" if you exported using Tabs, or " " for Spaces.
SEPARATOR = "," 

# The data is sampled uniformly at 500 Hz
SAMPLING_RATE = 500.0 

# Set this to a specific lead index (e.g. 1) to only plot that lead.
# Set it to None to plot all leads.
TARGET_LEAD = 3

def plot_ecg_csv():
    # 1. Load the CSV data.
    # The export tool currently does not write a header row, so we specify header=None
    try:
        data = pd.read_csv(FILE_PATH, sep=SEPARATOR, header=None)
    except FileNotFoundError:
        print(f"Error: File '{FILE_PATH}' not found. Please double-check the path.")
        return
        
    num_samples = len(data)
    num_leads = data.shape[1]
    
    print(f"Loaded {num_samples} samples across {num_leads} lead(s).")

    # 2. Generate the timeline (X-axis)
    # 500 Hz means each sample takes 1/500 = 0.002 seconds
    time_array = np.arange(num_samples) / SAMPLING_RATE

    # 3. Set up the display plot
    fig, ax = plt.subplots(figsize=(15, 6))

    all_plotted_data = []

    # Depending on how many leads were captured, loop through and plot each column
    for col_index in range(num_leads):
        if TARGET_LEAD is not None and col_index + 1 != TARGET_LEAD:
            continue  # Skip leads that don't match the target
            
        signal = data[col_index].values
        ax.plot(time_array, signal, linewidth=1.5, label=f"Lead {col_index + 1}")
        
        # Only consider finite non-zero values for axis scaling
        finite_vals = signal[np.isfinite(signal) & (signal != 0)]
        if len(finite_vals) > 0:
            all_plotted_data.extend(finite_vals)

    # 4. Decorate the axes specifically for ECG tracing conventions
    ax.set_title("Exported Paper ECG Signals")
    ax.set_xlabel("Time (Seconds)")
    ax.set_ylabel("Amplitude (mV)")
    
    # Calculate better Y-axis limits if we have data
    if all_plotted_data:
        try:
            y_min = np.nanmin(all_plotted_data)
            y_max = np.nanmax(all_plotted_data)
            if np.isfinite(y_min) and np.isfinite(y_max):
                margin = (y_max - y_min) * 0.2 if y_max != y_min else 1.0
                ax.set_ylim(y_min - margin, y_max + margin)
        except Exception:
            pass

    if num_leads > 1:
        ax.legend(loc="upper right")
        
    # Standard ECGs usually have grids to make visual inference easier 
    ax.grid(True, linestyle='--', alpha=0.6)
    
    # 5. Render Plot
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_ecg_csv()

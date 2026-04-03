import numpy as np
import matplotlib.pyplot as plt

# --- Configuration ---
# Replace this with the actual path to your exported .npz file
FILE_PATH = "leads.npz"

# Set this to a specific lead name (e.g. "I", "II", "aVR", "V1") to only plot that lead.
# Set it to None to plot all leads contained in the file.
TARGET_LEAD = "II"

def plot_ecg_npz():
    # 1. Load the NPZ data.
    try:
        data = np.load(FILE_PATH)
    except FileNotFoundError:
        print(f"Error: File '{FILE_PATH}' not found. Please double-check the path.")
        return
    
    # Metadata
    sampling_rate = data.get('sampling_rate', 500.0)
    lead_names = [k for k in data.keys() if k != 'sampling_rate']
    
    print(f"Loaded {len(lead_names)} leads from NPZ: {', '.join(lead_names)}")

    # 2. Set up the display plot
    fig, ax = plt.subplots(figsize=(15, 6))

    all_plotted_data = []

    # Map the leads from the file
    for lead in lead_names:
        if TARGET_LEAD is not None and lead != TARGET_LEAD:
            continue
            
        signal = data[lead]
        num_samples = len(signal)
        time_array = np.arange(num_samples) / sampling_rate
        
        ax.plot(time_array, signal, linewidth=1.5, label=f"Lead {lead}")
        
        # Collect non-zero and finite values for axis scaling
        finite_vals = signal[np.isfinite(signal) & (signal != 0)]
        if len(finite_vals) > 0:
            all_plotted_data.extend(finite_vals)

    # 3. Decorate axes
    ax.set_title(f"Exported Paper ECG Signals (NPZ) - {FILE_PATH}")
    ax.set_xlabel("Time (Seconds)")
    ax.set_ylabel("Amplitude (mV)")
    
    if all_plotted_data:
        try:
            y_min = np.nanmin(all_plotted_data)
            y_max = np.nanmax(all_plotted_data)
            if np.isfinite(y_min) and np.isfinite(y_max):
                margin = (y_max - y_min) * 0.2 if y_max != y_min else 1.0
                ax.set_ylim(y_min - margin, y_max + margin)
        except Exception:
            pass

    ax.legend(loc="upper right")
    ax.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    plot_ecg_npz()

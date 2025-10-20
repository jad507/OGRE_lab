import pandas as pd
from accel_io import read_many_csvs, estimate_sample_rate_hz
import matplotlib.pyplot as plt
from pathlib import Path
from accel_fft import run_fft_overlay

source_folder = Path(r"D:\Users\jad507\OneDrive - The Pennsylvania State University\Documents\AstroStats\accel\Session_2025-10-14_160804")

# Typical: Welch PSD, 4 s segments, 50% overlap, log‑x, up to Nyquist
figs = run_fft_overlay(
    source_folder,
    method="welch",          # fallback to "rfft" if SciPy not installed
    nperseg_seconds=4.0,
    noverlap_ratio=0.5,
    max_f_hz=None,           # e.g., 400 if you want to cap at 400 Hz
    out_dir="fft_output",    # saves PNG + CSV there (optional)
    log_x=True,
    log_y=False,
)

# If running in a script, show figures:

plt.show()

# # Option A: Explicit file list (your two samples)
# files = [
#     Path("AccelData_2025-10-14_160804_File0001.csv"),
#     Path("AccelData_2025-10-14_160804_File0002.csv"),
# ]
# df = read_many_csvs(directory=source_folder)  # sorted by AbsoluteTime by default
#
# print(df.head())            # first few rows
# print(df.columns.tolist())  # includes: AbsoluteTime, t_rel_s, t_abs_s, Mirror_*, Desk_Y_g, source_file, file_index, session_start
#
# # Sample rate estimate using absolute time (recommended when stitching files)
# fs_hz = estimate_sample_rate_hz(df["t_abs_s"])
# print(f"Estimated sample rate: {fs_hz:.2f} Hz")
#
# # If you prefer the original per-file RelativeTime_s for diagnostics:
# fs_file_hz = df.groupby("source_file", sort=False)["t_rel_s"].apply(estimate_sample_rate_hz)
# print(fs_file_hz)
#
#
# plt.figure(figsize=(10, 4))
# plt.plot(df["t_abs_s"], df["Mirror_X_g"], label="Mirror_X_g", linewidth=0.8)
# plt.plot(df["t_abs_s"], df["Mirror_Y_g"], label="Mirror_Y_g", linewidth=0.8)
# plt.plot(df["t_abs_s"], df["Mirror_Z_g"], label="Mirror_Z_g", linewidth=0.8)
# plt.xlabel("Time (s)")
# plt.ylabel("Acceleration (g)")
# plt.legend()
# plt.tight_layout()
# plt.show()




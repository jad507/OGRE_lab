import pandas as pd
from accel_io import read_many_csvs, estimate_sample_rate_hz
import matplotlib.pyplot as plt
from pathlib import Path
from accel_fft import run_fft_overlay

# This script will take a look at all the Accelerometer Sessions in all the folders in accel, smash together all the
# data from all the individual CSVs, and output the collective FFTs on a per-session basis. Uses accel_fft to hold the
# various functions.
# Your starting point
source_folder = Path(r"D:\Users\jad507\OneDrive - The Pennsylvania State University\Documents\AstroStats\accel\Session_2025-10-14_160804")

parent_dir = source_folder.parent
print(f"Scanning parent: {parent_dir}")

# Collect all Session* folders
session_dirs = sorted([p for p in parent_dir.iterdir() if p.is_dir() and p.name.startswith("Session")])

print(f"Found {len(session_dirs)} session folders")
for session_dir in session_dirs:
    print(f"\n=== Processing: {session_dir.name} ===")

    # Find CSVs in this session
    files = sorted(session_dir.glob("AccelData_*.csv"))
    if not files:
        print("  (No AccelData_*.csv files found; skipping)")
        continue

    # Each session gets its own output subfolder
    out_dir = Path("../fft_output") / session_dir.name

    try:
        # Run with your preferred settings
        figs = run_fft_overlay(
            files=files,              # safest; works even if run_fft_overlay doesn't accept directories
            method="welch",
            nperseg_seconds=60.0,
            noverlap_ratio=0.5,
            max_f_hz=None,
            out_dir=out_dir,          # saves PNGs + CSVs here
            log_x=True,
            log_y=False,
        )
        print(f"  Saved outputs to: {out_dir.resolve()}")

        # If you are processing many sessions, you may not want to display now:
        # for fig in figs.values():
        #     plt.close(fig)

    except Exception as e:
        print(f"  ERROR in {session_dir.name}: {e}")


# If running in a script, show figures:

# plt.show()

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




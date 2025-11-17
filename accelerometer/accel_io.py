from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


# ---- Configuration -----------------------------------------------------------

EXPECTED_COLUMNS = [
    "AbsoluteTime",
    "RelativeTime_s",
    "Mirror_Y_g",
    "Mirror_X_g",
    "Mirror_Z_g",
    "Desk_Y_g",
]

# Regex to parse names like:
#   AccelData_2025-10-14_160804_File0001.csv
FILENAME_RE = re.compile(
    r"^AccelData_(?P<date>\d{4}-\d{2}-\d{2})_(?P<hms>\d{6})_File(?P<index>\d+)\.csv$"
)


# ---- Helpers ----------------------------------------------------------------

def parse_filename_info(path: Path) -> Tuple[pd.Timestamp, int]:
    """
    Extract session start (as naive local timestamp) and file index from filename.
    """
    m = FILENAME_RE.match(path.name)
    if not m:
        raise ValueError(f"Filename does not match expected pattern: {path.name}")

    date_str = m.group("date")        # e.g., "2025-10-14"
    hms_str = m.group("hms")          # e.g., "160804" -> 16:08:04
    file_index = int(m.group("index"))

    # Build "YYYY-MM-DD HH:MM:SS"
    session_start = pd.to_datetime(
        f"{date_str} {hms_str[0:2]}:{hms_str[2:4]}:{hms_str[4:6]}",
        format="%Y-%m-%d %H:%M:%S",
        errors="raise",
    )
    return session_start, file_index


def _validate_columns(df: pd.DataFrame, strict: bool = True) -> None:
    # Strip any whitespace and normalize column names (common CSV quirk)
    df.columns = [c.strip() for c in df.columns]
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing and strict:
        raise ValueError(f"Missing expected columns: {missing}")


def read_single_csv(
    path: Path,
    strict_columns: bool = True,
    dtype_floats: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Read one accelerometer CSV into a DataFrame with parsed timestamps.
    Adds columns: source_file, file_index, session_start, t_abs_s (computed later).
    """
    if dtype_floats is None:
        dtype_floats = {
            "RelativeTime_s": "float64",
            "Mirror_Y_g": "float64",
            "Mirror_X_g": "float64",
            "Mirror_Z_g": "float64",
            "Desk_Y_g": "float64",
        }

    session_start, file_index = parse_filename_info(Path(path))

    df = pd.read_csv(
        path,
        # If you ever see odd headers or leading spaces, engine="python" can help:
        # engine="python",
        dtype=dtype_floats,
    )

    _validate_columns(df, strict=strict_columns)

    # Parse AbsoluteTime; the data looks like "YYYY-MM-DD HH:MM:SS.sss"
    # We'll coerce errors to NaT and then drop if any appear.
    df["AbsoluteTime"] = pd.to_datetime(
        df["AbsoluteTime"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"
    )
    bad = df["AbsoluteTime"].isna().sum()
    if bad:
        raise ValueError(f"{bad} rows have unparsable AbsoluteTime in {path}")

    df["source_file"] = Path(path).name
    df["file_index"] = file_index
    df["session_start"] = session_start

    # Keep original RelativeTime_s as provided
    df.rename(columns={"RelativeTime_s": "t_rel_s"}, inplace=True)

    # We'll compute `t_abs_s` after concatenating multiple files
    return df


def read_many_csvs(
    file_paths: Iterable[Path | str] | Path | str = (),
    directory: Optional[Path | str] = None,
    glob_pattern: str = "AccelData_*.csv",
    sort_by: str = "AbsoluteTime",
    strict_columns: bool = True,
) -> pd.DataFrame:
    """
    Read & concatenate many CSVs. You can pass an iterable of paths OR a directory.
    The result is time-sorted and contains a continuous time column `t_abs_s`
    starting at 0 from the earliest AbsoluteTime across all files.

    Args:
        file_paths: iterable of file paths to read (takes precedence if provided)
        directory: folder to scan (used when file_paths is empty)
        glob_pattern: filename pattern (default matches your naming convention)
        sort_by: "AbsoluteTime" (default) or "file_index" to force file order
        strict_columns: if True, raise when expected columns are missing

    Returns:
        pandas.DataFrame with all rows and added metadata columns.
    """
    paths: List[Path] = []
    if file_paths:
        if isinstance(file_paths, (str, Path)):
            paths = [Path(file_paths)]
        else:
            paths = [Path(p) for p in file_paths]

    elif directory:
        paths = sorted(Path(directory).glob(glob_pattern))
    else:
        raise ValueError("Provide either file_paths or a directory to scan.")

    if not paths:
        raise FileNotFoundError("No CSV files found.")

    # Read all
    frames = [read_single_csv(p, strict_columns=strict_columns) for p in paths]

    # Sort: by AbsoluteTime (default) or by file index if you prefer strict file order
    if sort_by == "file_index":
        frames.sort(key=lambda f: (int(f["file_index"].iloc[0]), f["AbsoluteTime"].min()))
    else:  # "AbsoluteTime"
        frames.sort(key=lambda f: f["AbsoluteTime"].min())

    df = pd.concat(frames, ignore_index=True)

    # Compute continuous absolute time in seconds starting at 0 from the earliest stamp
    t0 = df["AbsoluteTime"].min()
    df["t_abs_s"] = (df["AbsoluteTime"] - t0).dt.total_seconds().astype("float64")

    return df


def estimate_sample_rate_hz(
    t_seconds: pd.Series, robust: bool = True
) -> float:
    """
    Estimate sample rate using time differences in seconds.
    If robust=True, use the median dt to reduce the effect of outliers.
    """
    if t_seconds.size < 2:
        return float("nan")
    dt = np.diff(t_seconds.to_numpy(dtype=np.float64))
    dt = dt[~np.isnan(dt)]
    if dt.size == 0:
        return float("nan")
    if robust:
        dt_est = np.median(dt)
    else:
        dt_est = dt.mean()
    return float(1.0 / dt_est) if dt_est > 0 else float("inf")
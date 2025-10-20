from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from scipy import signal as _scipy_signal  # type: ignore
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False

from accel_io import read_many_csvs, estimate_sample_rate_hz


AXES = ["Mirror_X_g", "Mirror_Y_g", "Mirror_Z_g", "Desk_Y_g"]


@dataclass
class FFTOptions:
    method: str = "welch"           # "welch" (preferred) or "rfft"
    nperseg_seconds: float = 4.0    # Welch segment length in seconds
    noverlap_ratio: float = 0.5     # 50% overlap
    window: str = "hann"
    detrend: str = "constant"
    scaling: str = "density"        # for Welch: "density" [g^2/Hz] or "spectrum" [g^2]
    max_f_hz: Optional[float] = None  # limit x-axis to this max frequency
    log_x: bool = True
    log_y: bool = False
    tight_layout: bool = True
    alpha: float = 0.7
    lw: float = 1.2
    out_dir: Optional[Path] = None  # if set, save figures/CSVs here


def _welch_psd(
    x: np.ndarray,
    fs: float,
    opts: FFTOptions,
) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Welch PSD using SciPy when available. Returns (f, Pxx, y_label).
    Pxx units: g^2/Hz when scaling="density"; g^2 when "spectrum".
    """
    if not _HAVE_SCIPY:
        raise RuntimeError("SciPy not available for Welch PSD")

    nperseg = max(8, int(round(opts.nperseg_seconds * fs)))
    # ensure nperseg is not longer than the data
    nperseg = min(nperseg, x.size)
    # choose even power-of-two-ish length for efficiency
    # (not required, but often faster)
    # snap nperseg to nearest power of two without exceeding
    pw2 = 1 << (nperseg.bit_length() - 1)
    nperseg = max(8, min(nperseg, pw2))
    noverlap = int(round(opts.noverlap_ratio * nperseg))

    f, Pxx = _scipy_signal.welch(
        x,
        fs=fs,
        window=opts.window,
        nperseg=nperseg,
        noverlap=noverlap,
        detrend=opts.detrend,
        scaling=opts.scaling,
        return_onesided=True,
        average="mean",
    )
    y_label = "PSD [g²/Hz]" if opts.scaling == "density" else "Power [g²]"
    return f, Pxx, y_label
def _rfft_mag(
    x: np.ndarray,
    fs: float,
) -> Tuple[np.ndarray, np.ndarray, str]:
    """
    Fallback single-segment magnitude spectrum using numpy.rfft.
    Amplitude scaling is single-sided; units are 'g'.
    """
    N = x.size
    if N < 2:
        return np.array([0.0]), np.array([np.nan]), "Amplitude [g]"

    # Remove DC to reduce leakage
    x = x - np.mean(x)
    # Hann window to reduce leakage; compensate amplitude
    w = np.hanning(N)
    xw = x * w

    # Single-sided frequency axis
    freqs = np.fft.rfftfreq(N, d=1.0 / fs)
    X = np.fft.rfft(xw)

    # RMS window amplitude correction (coherent gain for Hann is 0.5)
    coherent_gain = w.sum() / N
    # single-sided amplitude spectrum (scale by 2 for positive freqs except DC/Nyquist)
    mag = (np.abs(X) / (N * coherent_gain))
    if N % 2 == 0:
        mag[1:-1] *= 2.0
    else:
        mag[1:] *= 2.0

    return freqs, mag.astype(np.float64), "Amplitude [g]"


def compute_spectrum_for_file(
    df_file: pd.DataFrame,
    opts: FFTOptions,
    file_label: Optional[str] = None,
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """
    Compute spectrum per axis for one file (returns {axis: (f, S)}).
    """
    # Estimate per-file sample rate from relative time
    fs = estimate_sample_rate_hz(df_file["t_rel_s"])
    if not np.isfinite(fs) or fs <= 0:
        raise ValueError(f"Cannot estimate sampling rate for {file_label or ''}")

    # Prepare output dict
    spectra: Dict[str, Tuple[np.ndarray, np.ndarray]] = {}

    use_welch = (opts.method.lower() == "welch") and _HAVE_SCIPY
    for axis in AXES:
        if axis not in df_file.columns:
            continue
        x = df_file[axis].to_numpy(dtype=np.float64)

        if use_welch:
            f, S, _ = _welch_psd(x, fs, opts)
        else:
            f, S, _ = _rfft_mag(x, fs)

        if opts.max_f_hz is not None:
            m = f <= opts.max_f_hz
            f = f[m]
            S = S[m]

        spectra[axis] = (f, S)

    return spectra


def plot_overlaid_spectra_by_axis(
    per_file_spectra: Dict[str, Dict[str, Tuple[np.ndarray, np.ndarray]]],
    opts: FFTOptions,
    y_label_hint: Optional[str] = None,
) -> Dict[str, plt.Figure]:
    """
    per_file_spectra: {file_label: {axis: (f, S)}}
    Returns {axis: Figure}
    """
    figs: Dict[str, plt.Figure] = {}
    y_label = y_label_hint or ("PSD [g²/Hz]" if _HAVE_SCIPY and opts.method == "welch" else "Amplitude [g]")

    for axis in AXES:
        # Create a figure per axis
        fig, ax = plt.subplots(figsize=(9, 5))
        for file_label, spectra in per_file_spectra.items():
            if axis not in spectra:
                continue
            f, S = spectra[axis]
            ax.plot(f, S, label=file_label, alpha=opts.alpha, lw=opts.lw)

        ax.set_title(f"{axis} — {opts.method.upper()}")
        ax.set_xlabel("Frequency [Hz]")
        ax.set_ylabel(y_label)
        ax.grid(True, which="both", alpha=0.3)
        if opts.log_x:
            ax.set_xscale("log")
            # Nicely spaced decades if log-x
            ax.set_xlim(left=max(1e-3, ax.get_xlim()[0]))
        if opts.log_y:
            ax.set_yscale("log")
        ax.legend(loc="best", ncols=1, fontsize=9)

        if opts.tight_layout:
            fig.tight_layout()
        figs[axis] = fig

        # Save figure if requested
        if opts.out_dir:
            opts.out_dir.mkdir(parents=True, exist_ok=True)
            fig_path = opts.out_dir / f"{axis}_{opts.method}.png"
            fig.savefig(fig_path, dpi=150)

    return figs


def export_psd_csvs(
    per_file_spectra: Dict[str, Dict[str, Tuple[np.ndarray, np.ndarray]]],
    out_dir: Path,
):
    """
    Writes one CSV per file with columns: freq_hz, <axis1>, <axis2>, ...
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    for file_label, spectra in per_file_spectra.items():
        # Build common frequency grid if needed: pick the densest one as reference
        # (Assumes all same fs & parameters; otherwise we interpolate)
        ref_axis = next(iter(spectra.keys()))
        f_ref, _ = spectra[ref_axis]
        data = {"freq_hz": f_ref}
        for axis, (f, S) in spectra.items():
            if len(f) != len(f_ref) or not np.allclose(f, f_ref):
                # interpolate to reference grid
                S_interp = np.interp(f_ref, f, S, left=np.nan, right=np.nan)
                data[axis] = S_interp
            else:
                data[axis] = S
        df_out = pd.DataFrame(data)
        csv_path = out_dir / f"{file_label}_spectrum.csv"
        df_out.to_csv(csv_path, index=False)


from pathlib import Path
from typing import Iterable, Optional

def run_fft_overlay(
    files: Iterable[Path | str] | Path | str,
    method: str = "welch",
    nperseg_seconds: float = 4.0,
    noverlap_ratio: float = 0.5,
    max_f_hz: Optional[float] = None,
    out_dir: Optional[Path | str] = None,
    log_x: bool = True,
    log_y: bool = False,
):
    # Normalize 'files' to a list of Paths
    file_list: list[Path]
    if isinstance(files, (str, Path)):
        p = Path(files)
        if p.is_dir():
            file_list = sorted(p.glob("AccelData_*.csv"))
        else:
            file_list = [p]
    else:
        file_list = [Path(f) for f in files]

    if not file_list:
        raise FileNotFoundError("No CSV files matched in the given input.")

    opts = FFTOptions(
        method=method,
        nperseg_seconds=nperseg_seconds,
        noverlap_ratio=noverlap_ratio,
        max_f_hz=max_f_hz,
        out_dir=(Path(out_dir) if out_dir else None),
        log_x=log_x,
        log_y=log_y,
    )

    # Read & process
    # Read all rows but keep file identity for per-file FFT
    # Use loader's concatenation then split per file
    df_all = read_many_csvs(file_paths=file_list, sort_by="AbsoluteTime")
    per_file_spectra: Dict[str, Dict[str, Tuple[np.ndarray, np.ndarray]]] = {}

    for file_name, df_file in df_all.groupby("source_file", sort=False):
        # Build a readable label: "File0001 (16:09:46)" or just filename stem
        try:
            t0 = pd.to_datetime(df_file["AbsoluteTime"].iloc[0])
            label = f'{Path(file_name).stem} ({t0.strftime("%H:%M:%S")})'
        except Exception:
            label = Path(file_name).stem

        spectra = compute_spectrum_for_file(df_file, opts, file_label=label)
        per_file_spectra[label] = spectra

    figs = plot_overlaid_spectra_by_axis(per_file_spectra, opts)

    # Optional CSV export (one CSV per file)
    if opts.out_dir:
        export_psd_csvs(per_file_spectra, opts.out_dir)

    return figs
import json
from pathlib import Path

import gdown
import numpy as np
from scipy.io import loadmat

from task_and_baseline import baseline, build_task_helpers


# ============================================================
# Configuration
# ============================================================

DATA_FILE = Path("challenge.mat")

# Safe switch for the experimental spatial rank-1 stage.
# If the score becomes INVALID or worse than baseline, set this to False.
ENABLE_RANK1_STAGE = True

# Conservative value for the first experiment.
# Try: 0.25, 0.50, 0.75, 1.00
# If INVALID appears, return to 0.25 or disable the stage.
RANK1_ALPHA = 0.25


# ============================================================
# Dataset loading
# ============================================================

def download_dataset_if_needed():
    """
    Download challenge.mat only if it is not already present.

    The original script used gdown.download(..., fuzzy=True).
    Some recent gdown versions do not support the fuzzy argument,
    therefore a direct Google Drive file id URL is used here.
    """
    if DATA_FILE.exists():
        print(f"Dataset already exists: {DATA_FILE}")
        return

    file_id = "1BBHVSI4KB-B8OX46eN1Nm4ARCeq6Rui4"
    url = f"https://drive.google.com/uc?id={file_id}"

    print("Downloading challenge.mat ...")
    output = gdown.download(url, str(DATA_FILE), quiet=False)

    if output is None and not DATA_FILE.exists():
        raise RuntimeError(
            "Dataset download failed. Please check internet connection "
            "or download challenge.mat manually."
        )


download_dataset_if_needed()

data = loadmat(str(DATA_FILE), simplify_cells=True)

tx = data["tx"].astype(np.complex128)
rx = data["rx"].astype(np.complex128)
Fs = float(data["Fs"])

N, _ = tx.shape

tx_n = tx / (
    np.sqrt(np.mean(np.abs(tx) ** 2, axis=0, keepdims=True)) + 1e-30
)

helpers = build_task_helpers(tx_n, Fs, N)


# ============================================================
# Signal processing helpers
# ============================================================

def rank1_from_band_matrix_local(band_matrix):
    """
    Estimate the dominant spatially coherent rank-1 component
    across RX channels in the scoring band.

    Parameters
    ----------
    band_matrix : ndarray, shape (N, n_rx)
        Band-limited complex residual matrix.

    Returns
    -------
    rank1_matrix : ndarray, shape (N, n_rx)
        Dominant rank-1 spatial component reconstructed in the RX channels.
    """
    cov = band_matrix.conj().T @ band_matrix / band_matrix.shape[0]
    _, vecs = np.linalg.eigh(cov)

    dominant_vec = vecs[:, -1]
    shared_waveform = band_matrix @ dominant_vec

    denom = np.vdot(shared_waveform, shared_waveform) + 1e-30

    coeffs = np.array(
        [
            np.vdot(shared_waveform, band_matrix[:, ch]) / denom
            for ch in range(band_matrix.shape[1])
        ],
        dtype=np.complex128,
    )

    return shared_waveform[:, None] * coeffs[None, :]


# ============================================================
# Applicant solution
# ============================================================

def your_canceller(tx_n, rx):
    """
    Interference cancellation for complex multichannel signals.

    Stage 1:
    TX-driven nonlinear cancellation using the provided physically motivated
    baseline model. The model predicts the structured nonlinear interference
    component from TX-derived features and subtracts it from RX.

    Stage 2:
    Optional conservative rank-1 subtraction of the dominant spatially coherent
    residual component in the scoring band.

    If the rank-1 stage gives INVALID score or degrades the metric, set
    ENABLE_RANK1_STAGE = False and keep the stable baseline-based solution.
    """
    del tx_n

    # Stage 1: physically motivated TX-driven nonlinear cancellation.
    tx_pred = helpers["fit_tx_prediction"](rx)
    rx_after_tx = rx - tx_pred

    if not ENABLE_RANK1_STAGE:
        return rx_after_tx

    # Stage 2: estimate the spatially coherent residual component
    # in the same frequency band used by the official metric.
    residual_band = np.column_stack(
        [
            helpers["score_filter"](rx_after_tx[:, ch])
            for ch in range(rx_after_tx.shape[1])
        ]
    )

    rank1_pred = rank1_from_band_matrix_local(residual_band)

    # Conservative subtraction. Too large alpha may fail validity.
    rx_hat = rx_after_tx - RANK1_ALPHA * rank1_pred

    return rx_hat


# ============================================================
# Evaluation and output
# ============================================================

print("\n=== Baseline ===")
baseline_output = baseline(tx_n, rx, helpers["fit_tx_prediction"])
baseline_reds, baseline_avg = helpers["score"](
    rx,
    baseline_output,
    label="baseline",
)

print("=== Your Solution ===")
your_output = your_canceller(tx_n, rx)
yours_reds, yours_avg = helpers["score"](
    rx,
    your_output,
    label="yours",
)

results = {
    "baseline": {
        "per_channel_db": [float(x) for x in baseline_reds],
        "average_db": float(baseline_avg),
    },
    "yours": {
        "per_channel_db": [float(x) for x in yours_reds],
        "average_db": float(yours_avg),
    }
}

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("Saved results.json")
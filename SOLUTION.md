# SMILES-2026-Signal Solution

## 1. Reproducibility

The solution was tested locally on Windows with Python 3.

Run from a clean checkout:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python applicant_solution.py
```

The script downloads `challenge.mat` if needed, runs the baseline and my method, and writes `results.json`.

The repository contains:

```text
applicant_solution.py
task_and_baseline.py
results.json
requirements.txt
SOLUTION.md
```

I did not modify `task_and_baseline.py` or the dataset.

## 2. Task understanding

This task is interference cancellation in complex multichannel signals.

The project README states: “This is a real-world problem. The data comes from actual hardware measurements.”

The received signal is modeled as:

```text
rx = s + I + eta
```

where `s` is the desired signal, `I` is structured interference, and `eta` is background noise.

The important physical point is that the interference is not arbitrary. According to the task statement, it has two components:

```text
I = F_c(TX) + E
```

Here `F_c(TX)` is a nonlinear TX-driven component, while `E` is an external spatially coherent component observed across the four RX channels.

This interpretation was the main reason for choosing a conservative signal-processing solution rather than direct spectral suppression. The README also notes that a valid removed component must be explainable as “a TX-driven nonlinear component” plus “a spatially coherent rank-1 component”.

## 3. Baseline

The provided baseline is physically meaningful. It constructs nonlinear TX-derived features, including cubic intermodulation-like terms:

```text
x_i^2 * conj(x_j)
```

These terms are consistent with a nonlinear leakage model: products between different transmit channels can generate structured components in the receive band. The baseline then fits a regularized linear model with time lags and subtracts the predicted TX-driven interference from each RX channel.

My local baseline result was:

```text
ch0: 3.98 dB
ch1: 4.86 dB
ch2: 3.49 dB
ch3: 3.74 dB
average: 4.02 dB
```

## 4. Final approach

The final solution has two stages.

First, I use the provided TX-driven nonlinear cancellation model. This removes the component of interference that is explainable by nonlinear functions of the transmitted signals.

Second, I add a conservative spatial rank-1 residual cancellation stage. After baseline subtraction, I apply the scoring-band filter to the residual, estimate the dominant spatial component across the four RX channels using eigenvalue decomposition of the RX-channel covariance matrix, and subtract only a scaled part of this component.

The final model is:

```text
rx_hat = rx - tx_pred - alpha * rank1_pred
```

where:

```text
tx_pred      = TX-driven nonlinear interference estimate
rank1_pred   = dominant spatially coherent residual component
alpha        = conservative subtraction coefficient
```

For the submitted result I used:

```text
alpha = 0.25
```

This value was selected because it improved all four channels while keeping the rank-1 subtraction weak enough to remain physically interpretable.

## 5. Implementation details

The implementation is in:

```text
applicant_solution.py
```

The main entry point remains:

```text
python applicant_solution.py
```

The main function is:

```text
your_canceller(tx_n, rx)
```

I also changed dataset loading to avoid repeated downloads and to avoid relying on the deprecated `fuzzy=True` argument in recent versions of `gdown`.

## 6. Experiments

Due to the short time before submission, I focused on a small number of physically motivated experiments rather than a broad hyperparameter search.

The baseline gave:

```text
average: 4.02 dB
```

Adding the conservative rank-1 stage with `alpha = 0.25` gave:

```text
ch0: 5.28 dB
ch1: 5.66 dB
ch2: 5.02 dB
ch3: 4.56 dB
average: 5.13 dB
```

The improvement over baseline was:

```text
+1.11 dB average
```

The improvement was positive for all four RX channels.

## 7. Failed or postponed attempts

I considered testing stronger rank-1 subtraction values such as:

```text
alpha = 0.50, 0.75, 1.00
```

I did not include them in the final submission because the task contains an explainability validity check. Aggressive residual subtraction could improve the numerical metric locally but become less defensible physically or fail validation.

Under the submission time constraint, I chose the conservative version that already improves the baseline and directly follows the physical structure described in the task.

## 8. Final result

The final metric stored in `results.json` is:

```text
ch0: 5.28 dB
ch1: 5.66 dB
ch2: 5.02 dB
ch3: 4.56 dB
average_db = 5.13 dB
```

## 9. Limitations

This is a compact and conservative solution. It does not perform systematic parameter tuning or add new nonlinear TX features beyond the provided baseline. The next improvement would be a controlled sweep of the rank-1 coefficient and a deeper residual analysis, while preserving the physical explainability of the removed component.

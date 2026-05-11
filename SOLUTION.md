# SMILES-2026-Signal Solution

## 1. Reproducibility

The solution was tested locally with Python 3 on Windows.


```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python applicant_solution.py
```


## 2. Task understanding

The task is interference cancellation in complex multichannel signals. The dataset contains 6 complex transmit channels and 4 complex receive channels. The received signal is affected by structured interference caused by the transmitter chain and by an additional spatially coherent external component.

The target output has the same shape as the input RX signal. The method should subtract the estimated interference while preserving the remaining received signal structure.

The quality metric is computed in a limited frequency band where the interference is concentrated. Therefore, a simple band-zeroing approach is not appropriate: the removed component should be physically interpretable as a TX-driven nonlinear interference component and/or a spatially coherent residual component.

## 3. Baseline

The provided baseline uses a physically motivated model of TX-driven nonlinear interference. It builds nonlinear features from the TX channels, including cubic intermodulation-like terms of the form:

```text
x_i^2 * conj(x_j)
```

Several time lags are used for these nonlinear features. A regularized linear model is then fitted to predict the interference component in each RX channel. The predicted TX-driven interference is subtracted from the received signal.

In my local run, the provided baseline produced the following result:

```text
  ch0: 3.98 dB
  ch1: 4.86 dB
  ch2: 3.49 dB
  ch3: 3.74 dB
  Metric [baseline]: 4.02 dB
```

## 4. Final approach

The final method uses two stages.

The first stage is the provided physically motivated TX-driven nonlinear cancellation model. It predicts the part of the interference that can be explained by nonlinear functions of the TX channels and subtracts it from RX.

The second stage is a conservative spatial rank-1 residual cancellation. After the TX-driven cancellation, the residual is filtered with the same scoring-band filter. Then the dominant spatially coherent component across the four RX channels is estimated using an eigenvalue decomposition of the RX-channel covariance matrix in the scoring band. A scaled version of this rank-1 component is subtracted from the residual.

The final output is:

```text
rx_hat = rx - tx_pred - alpha * rank1_pred
```

where `tx_pred` is the TX-driven nonlinear interference prediction, `rank1_pred` is the estimated dominant spatially coherent residual component, and `alpha` is a conservative subtraction coefficient.

For the submitted run I used:

```text
alpha = 0.25
```

This value was chosen as a conservative setting: it improved the metric while avoiding an overly aggressive residual subtraction.

## 5. Implementation details

```text
applicant_solution.py
```

The main function is:

```text
your_canceller(tx_n, rx)
```

## 6. Experiments

I first verified that the original baseline runs correctly and produces `results.json`.

Then I added a spatial rank-1 residual cancellation stage after the baseline. The first tested conservative setting was:

```text
alpha = 0.25
```

This setting improved the average metric from 4.02 dB to 5.13 dB.

The resulting per-channel metrics were:

```text
ch0: 5.28 dB
ch1: 5.66 dB
ch2: 5.02 dB
ch3: 4.56 dB
average: 5.13 dB
```

The improvement was consistent across all four RX channels.

## 7. Failed or postponed attempts

I considered trying stronger rank-1 subtraction coefficients such as `alpha = 0.50`, `0.75`, and `1.00`. However, rank-1 subtraction must be used carefully: if the removed component becomes too aggressive or insufficiently explainable, the solution may fail the validity check.

Because of the submission time constraint, I selected the conservative `alpha = 0.25` configuration that already improved all four channels while keeping the method simple and interpretable.

Further work could include a more systematic sweep of `alpha`, validation of the rank-1 residual energy, and comparison of full-band versus scoring-band rank-1 estimation.

## 8. Final result

The final result is stored in:

```text
results.json
```

Final submitted metric:

```text
ch0: 5.28 dB
ch1: 5.66 dB
ch2: 5.02 dB
ch3: 4.56 dB
average_db = 5.13 dB
```

## 9. Limitations

The solution is intentionally conservative. It improves the baseline by adding a physically interpretable spatial rank-1 residual cancellation stage, but it does not perform a large hyperparameter search or introduce more complex nonlinear models.

A possible next improvement would be to tune the rank-1 subtraction strength more systematically and to test additional TX-derived nonlinear features while keeping the removed component compatible with the task validity constraints.

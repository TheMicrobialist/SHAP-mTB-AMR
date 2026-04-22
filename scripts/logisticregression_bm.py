#!/usr/bin/env python3
"""
Logistic Regression Benchmark — v4
Mirrors the structure of benchmark.py but focuses solely on Logistic Regression.

Variants tested:
  - LR L2 (Ridge)    : standard ridge-penalised, good general baseline
  - LR L1 (Lasso)    : lasso-penalised, performs implicit feature selection
  - LR ElasticNet    : mix of L1 + L2 (l1_ratio=0.5), best of both

All variants:
  - class_weight="balanced"  to handle class imbalance
  - StandardScaler (sparse-safe, with_mean=False) inside a Pipeline
  - 5-fold stratified cross-validation (Accuracy + AUC-ROC)
  - Hold-out test set evaluation
  - Verbose timing at every major step

Outputs:
  - results/benchmark_LR_<DRUG>_v4.csv
  - results/model_objects_LR_<DRUG>.pkl   (for visualize.py)
"""

import argparse
import os
import pickle
import time
import warnings
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ────────────────────────────────────────────────────────────────────
TEST_SIZE    = 0.2
RANDOM_STATE = 42
CV_FOLDS     = 5
MAX_ITER     = 2000   # saga needs more iterations on large sparse data
# ─────────────────────────────────────────────────────────────────────────────


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(seconds: float) -> str:
    """Format elapsed seconds as HH:MM:SS."""
    return str(timedelta(seconds=round(seconds)))


def section(title: str) -> None:
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")


def subsection(title: str) -> None:
    print(f"\n  {'─'*55}")
    print(f"    {title}")
    print(f"  {'─'*55}")


def tick(label: str) -> float:
    """Print a timestamped start message and return the start time."""
    t = time.perf_counter()
    print(f"  [START]  {label} ...", flush=True)
    return t


def tock(t0: float, label: str = "") -> float:
    """Print elapsed time since t0 and return elapsed seconds."""
    elapsed = time.perf_counter() - t0
    suffix  = f" [{label}]" if label else ""
    print(f"  [DONE ]  {fmt(elapsed)}{suffix}", flush=True)
    return elapsed
# ─────────────────────────────────────────────────────────────────────────────


parser = argparse.ArgumentParser(description="Logistic Regression benchmark v4")
parser.add_argument(
    "--drug", default="RIFAMPICIN",
    choices=["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"],
)
args = parser.parse_args()
DRUG = args.drug

os.makedirs("results", exist_ok=True)

script_start = time.perf_counter()
section(f"Logistic Regression Benchmark v4 — Drug: {DRUG}")

# ── Load data ─────────────────────────────────────────────────────────────────
subsection("Loading data")

t0 = tick("Reading ml_matrix.csv.gz")
df = pd.read_csv("../resistance_dataset/ml_matrix.csv.gz", index_col="SAMPLE")
tock(t0, "file loaded")

print(f"\n    Matrix shape  : {df.shape}")

t0 = tick("Filtering features and labels")
feature_cols  = [c for c in df.columns if c.startswith("pos_")]
y_raw         = df[DRUG]
mask          = y_raw.isin([0, 1])
X             = df[feature_cols][mask]
y             = y_raw[mask].astype(int)
tock(t0, "features ready")

n_resistant   = int(y.sum())
n_susceptible = int((y == 0).sum())

print(f"\n    Drug          : {DRUG}")
print(f"    Samples       : {len(y)}")
print(f"    Resistant (1) : {n_resistant}  ({100 * y.mean():.1f}%)")
print(f"    Susceptible(0): {n_susceptible} ({100 * (1 - y.mean()):.1f}%)")
print(f"    Features      : {X.shape[1]}")
print(f"    Class ratio   : 1:{n_susceptible / n_resistant:.2f} (R:S)")

t0 = tick("Performing stratified train/test split (80/20)")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)
tock(t0, "split done")

print(f"\n    Train samples : {len(y_train)}")
print(f"    Test  samples : {len(y_test)}")

# ── Model definitions ─────────────────────────────────────────────────────────
#
# All three variants share:
#   - saga solver     (supports L1, L2, ElasticNet; efficient on sparse data)
#   - class_weight="balanced"
#   - StandardScaler(with_mean=False) — sparse-safe; prevents data leakage via Pipeline
#   - C=0.1           (moderate regularisation; tune with grid search if needed)

def make_lr_pipeline(penalty: str, l1_ratio: float = None) -> Pipeline:
    """Build a StandardScaler -> LogisticRegression pipeline."""
    lr_kwargs = dict(
        penalty=penalty,
        C=0.1,
        class_weight="balanced",
        solver="saga",
        max_iter=MAX_ITER,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    if penalty == "elasticnet":
        lr_kwargs["l1_ratio"] = l1_ratio

    return Pipeline([
        ("scaler", StandardScaler(with_mean=False)),
        ("clf",    LogisticRegression(**lr_kwargs)),
    ])


models = {
    "LR L2 (Ridge)":  make_lr_pipeline("l2"),
    "LR L1 (Lasso)":  make_lr_pipeline("l1"),
    "LR ElasticNet":  make_lr_pipeline("elasticnet", l1_ratio=0.5),
}

# ── Training & evaluation loop ────────────────────────────────────────────────
cv      = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
results = []
trained = {}

for name, model in models.items():
    subsection(f"Model: {name}")
    model_start = time.perf_counter()

    # ── Fit ──────────────────────────────────────────────────────────────────
    t0 = tick(f"Fitting on {len(y_train)} training samples  (max_iter={MAX_ITER})")
    model.fit(X_train, y_train)
    fit_time = tock(t0, "fit complete")
    trained[name] = model

    # Check convergence
    n_iter = model.named_steps["clf"].n_iter_[0]
    converged = n_iter < MAX_ITER
    print(f"    Solver iterations : {n_iter} / {MAX_ITER}"
          f"  ({'CONVERGED' if converged else 'WARNING: did not converge — increase MAX_ITER'})")

    # ── Hold-out evaluation ───────────────────────────────────────────────────
    t0     = tick("Predicting on hold-out test set")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    tock(t0, "predict complete")

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print(f"\n    Hold-out Accuracy : {acc:.4f}")
    print(f"    Hold-out AUC-ROC  : {auc:.4f}")
    print()
    # Indent classification report for readability
    report = classification_report(
        y_test, y_pred,
        target_names=["Susceptible", "Resistant"],
        digits=4,
    )
    for line in report.splitlines():
        print(f"    {line}")

    # Report non-zero coefficients (L1 / ElasticNet perform feature selection)
    coef      = model.named_steps["clf"].coef_[0]
    n_nonzero = int(np.sum(coef != 0))
    print(f"\n    Non-zero coefficients : {n_nonzero} / {len(coef)}"
          f"  ({100 * n_nonzero / len(coef):.1f}% of features retained)")

    # ── 5-fold cross-validation ───────────────────────────────────────────────
    print()
    t0 = tick(f"Running {CV_FOLDS}-fold stratified CV — accuracy  "
              f"({CV_FOLDS} fits × {len(y_train)} samples each)")
    cv_acc = cross_val_score(model, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    tock(t0, "CV accuracy done")

    t0 = tick(f"Running {CV_FOLDS}-fold stratified CV — AUC-ROC")
    cv_auc = cross_val_score(model, X, y, cv=cv, scoring="roc_auc", n_jobs=-1)
    tock(t0, "CV AUC-ROC done")

    print(f"\n    CV Accuracy  (per fold) : {' | '.join(f'{v:.4f}' for v in cv_acc)}")
    print(f"    CV AUC-ROC  (per fold) : {' | '.join(f'{v:.4f}' for v in cv_auc)}")
    print(f"\n    CV Accuracy  : {cv_acc.mean():.4f} ± {cv_acc.std():.4f}")
    print(f"    CV AUC-ROC   : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

    model_elapsed = time.perf_counter() - model_start
    print(f"\n    Total time for {name} : {fmt(model_elapsed)}")

    results.append({
        "Model":              name,
        "Test Accuracy":      round(acc, 4),
        "Test AUC-ROC":       round(auc, 4),
        "CV Accuracy Mean":   round(cv_acc.mean(), 4),
        "CV Accuracy Std":    round(cv_acc.std(),  4),
        "CV AUC-ROC Mean":    round(cv_auc.mean(), 4),
        "CV AUC-ROC Std":     round(cv_auc.std(),  4),
        "Non-zero Coefs":     n_nonzero,
        "Converged":          converged,
        "Solver Iterations":  n_iter,
        "Fit Time (s)":       round(fit_time, 2),
    })

# ── Summary table ─────────────────────────────────────────────────────────────
results_df = (
    pd.DataFrame(results)
    .sort_values("CV AUC-ROC Mean", ascending=False)
    .reset_index(drop=True)
)

section(f"LOGISTIC REGRESSION SUMMARY — {DRUG}")
print(results_df.to_string(index=False))

csv_path = f"results/benchmark_LR_{DRUG}_v4.csv"
results_df.to_csv(csv_path, index=False)
print(f"\n  Metrics saved : {csv_path}")

# ── Serialise for visualize.py ────────────────────────────────────────────────
pkl_path = f"results/model_objects_LR_{DRUG}.pkl"
with open(pkl_path, "wb") as f:
    pickle.dump({
        "drug":         DRUG,
        "feature_cols": feature_cols,
        "X_train":      X_train,
        "X_test":       X_test,
        "y_train":      y_train,
        "y_test":       y_test,
        "trained":      trained,
    }, f)
print(f"  Model objects : {pkl_path}")

total_elapsed = time.perf_counter() - script_start
print(f"\n  Total script runtime : {fmt(total_elapsed)}")
print(f"\n{'='*65}")
print(f"  DONE — {DRUG}")
print(f"  Run visualize.py --drug {DRUG} to generate plots")
print(f"{'='*65}\n")
#!/usr/bin/env python3
"""
Multi-Label Benchmarking — Issue #8
Trains and evaluates models predicting resistance to all four
RIPE drugs simultaneously using MultiOutputClassifier.

Compares per-drug AUC-ROC against single-drug models (benchmark_v4.csv).

Models:
  - Random Forest
  - LightGBM
  - XGBoost
  - Linear SVM (SGD)

Output:
  - results/benchmark_multi_v1.csv   — per-drug + macro AUC-ROC
  - results/model_objects_multi.pkl  — models + data for visualize.py

Usage:
  python3 scripts/benchmark_multi.py
"""

import os
import pickle
import warnings

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import (
    accuracy_score,
    hamming_loss,
    roc_auc_score,
)
from sklearn.model_selection import KFold, train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import lightgbm as lgb
import xgboost as xgb

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ─────────────────────────────────────────────────────────────────────
DRUGS        = ["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"]
N_ESTIMATORS = 300
TEST_SIZE    = 0.2
RANDOM_STATE = 42
CV_FOLDS     = 5
# ──────────────────────────────────────────────────────────────────────────────

os.makedirs("results", exist_ok=True)

print(f"\n{'='*65}")
print(f" Multi-Label Benchmark v1 — All 4 RIPE drugs simultaneously")
print(f"{'='*65}")

# ── Load data ──────────────────────────────────────────────────────────────────
print("\nLoading matrix...")
df = pd.read_csv("resistance_dataset/ml_matrix.csv.gz", index_col="SAMPLE")
print(f"  Full matrix shape: {df.shape}")

feature_cols = [c for c in df.columns if c.startswith("pos_")]

# Keep only samples with labels for ALL 4 drugs
mask = df[DRUGS].notna().all(axis=1)
X    = df[feature_cols][mask]
Y    = df[DRUGS][mask].astype(int)

print(f"\n  Samples with all 4 labels: {len(Y)}")
print(f"  Features: {X.shape[1]}")
print(f"\n  Resistance rates in multi-label subset:")
for drug in DRUGS:
    n_r = int(Y[drug].sum())
    pct = 100 * Y[drug].mean()
    print(f"    {drug:<15}: {n_r:>4} resistant ({pct:.1f}%)")

# Resistance profile distribution
profiles = Y.apply(lambda row: "".join(row.astype(str)), axis=1)
print(f"\n  Top 10 resistance profiles (RIF-INH-ETH-PZA):")
print(f"  {'Profile':<12} {'Count':>6} {'%':>6}")
for profile, count in profiles.value_counts().head(10).items():
    print(f"  {profile:<12} {count:>6} {100*count/len(Y):>5.1f}%")
print(f"\n  Total unique profiles: {profiles.nunique()}")

# ── Train/test split ───────────────────────────────────────────────────────────
# Note: StratifiedKFold not supported for multi-label — use KFold
X_train, X_test, Y_train, Y_test = train_test_split(
    X, Y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE
)

print(f"\n  Train samples: {len(X_train)}")
print(f"  Test samples:  {len(X_test)}")

# ── Helper: compute per-drug + macro AUC-ROC ───────────────────────────────────
def compute_auc(Y_true, Y_prob_list):
    """
    Y_prob_list: list of arrays from predict_proba()
                 one array per drug, shape (n_samples, 2)
    Returns: dict of per-drug AUC + macro average
    """
    aucs = {}
    for i, drug in enumerate(DRUGS):
        prob_resistant = Y_prob_list[i][:, 1]
        aucs[drug] = round(roc_auc_score(Y_true[drug], prob_resistant), 4)
    aucs["Macro"] = round(np.mean(list(aucs.values())), 4)
    return aucs


def compute_cv_auc(model, X, Y, cv):
    """
    Manual CV loop for multi-label AUC-ROC.
    sklearn cross_val_score doesn't support multi-output AUC directly.
    """
    per_drug_aucs = {drug: [] for drug in DRUGS}

    for train_idx, val_idx in cv.split(X):
        X_tr, X_val = X.iloc[train_idx], X.iloc[val_idx]
        Y_tr, Y_val = Y.iloc[train_idx], Y.iloc[val_idx]

        model.fit(X_tr, Y_tr)
        Y_prob = model.predict_proba(X_val)

        for i, drug in enumerate(DRUGS):
            prob = Y_prob[i][:, 1]
            auc  = roc_auc_score(Y_val[drug], prob)
            per_drug_aucs[drug].append(auc)

    # Return mean ± std per drug
    cv_results = {}
    for drug in DRUGS:
        vals = per_drug_aucs[drug]
        cv_results[drug] = {
            "mean": round(np.mean(vals), 4),
            "std":  round(np.std(vals),  4)
        }
    macro_means = [cv_results[d]["mean"] for d in DRUGS]
    cv_results["Macro"] = {
        "mean": round(np.mean(macro_means), 4),
        "std":  round(np.std(macro_means),  4)
    }
    return cv_results


# ── Model definitions (same base models as benchmark.py) ──────────────────────
# Note: scale_pos_weight for XGBoost not directly supported in MultiOutput
# Using class_weight="balanced" equivalent via sample_weight in fit is complex
# → XGBoost uses equal weighting in multi-output mode

n_resistant   = int(Y_train["RIFAMPICIN"].sum())
n_susceptible = int((Y_train["RIFAMPICIN"] == 0).sum())
scale_pos_w   = n_susceptible / n_resistant

base_models = {

    "Random Forest": RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),

    "LightGBM": lgb.LGBMClassifier(
        n_estimators=N_ESTIMATORS,
        class_weight="balanced",
        learning_rate=0.05,
        num_leaves=63,
        min_child_samples=10,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,
    ),

    "XGBoost": xgb.XGBClassifier(
        n_estimators=N_ESTIMATORS,
        scale_pos_weight=scale_pos_w,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="logloss",
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=0,
    ),

    "Linear SVM (SGD)": Pipeline([
        ("scaler", StandardScaler(with_mean=False)),
        ("clf", SGDClassifier(
            loss="modified_huber",
            class_weight="balanced",
            alpha=1e-4,
            max_iter=200,
            tol=1e-3,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ]),
}

# Wrap each base model in MultiOutputClassifier
models = {
    name: MultiOutputClassifier(base, n_jobs=-1)
    for name, base in base_models.items()
}

# ── Training & evaluation loop ─────────────────────────────────────────────────
cv      = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
results = []
trained = {}

for name, model in models.items():
    print(f"\n{'─'*65}")
    print(f"  Model: {name}")
    print(f"{'─'*65}")

    # Fit on full training set
    model.fit(X_train, Y_train)
    trained[name] = model

    # Hold-out evaluation
    Y_pred     = model.predict(X_test)
    Y_prob     = model.predict_proba(X_test)
    Y_pred_df  = pd.DataFrame(Y_pred, columns=DRUGS, index=Y_test.index)

    # Per-drug AUC-ROC
    test_aucs = compute_auc(Y_test, Y_prob)

    # Hamming loss (fraction of labels incorrectly predicted)
    h_loss = round(hamming_loss(Y_test, Y_pred_df), 4)

    # Subset accuracy (exact match across all 4 drugs)
    subset_acc = round(accuracy_score(Y_test, Y_pred_df), 4)

    print(f"\n  Hold-out metrics:")
    print(f"  {'Drug':<15} {'AUC-ROC':>8}")
    print(f"  {'─'*25}")
    for drug in DRUGS:
        print(f"  {drug:<15} {test_aucs[drug]:>8.4f}")
    print(f"  {'─'*25}")
    print(f"  {'Macro AUC-ROC':<15} {test_aucs['Macro']:>8.4f}")
    print(f"  {'Hamming Loss':<15} {h_loss:>8.4f}")
    print(f"  {'Subset Acc':<15} {subset_acc:>8.4f}")

    # Cross-validation AUC-ROC
    print(f"\n  Running {CV_FOLDS}-fold CV (this may take a few minutes)...")
    cv_aucs = compute_cv_auc(model, X, Y, cv)

    print(f"\n  CV AUC-ROC:")
    print(f"  {'Drug':<15} {'Mean':>8} {'Std':>8}")
    print(f"  {'─'*35}")
    for drug in DRUGS:
        print(f"  {drug:<15} {cv_aucs[drug]['mean']:>8.4f} "
              f"± {cv_aucs[drug]['std']:>6.4f}")
    print(f"  {'─'*35}")
    print(f"  {'Macro':<15} {cv_aucs['Macro']['mean']:>8.4f} "
          f"± {cv_aucs['Macro']['std']:>6.4f}")

    # Store results
    row = {
        "Model":              name,
        "Hamming Loss":       h_loss,
        "Subset Accuracy":    subset_acc,
        "Macro AUC-ROC":      test_aucs["Macro"],
        "CV Macro AUC Mean":  cv_aucs["Macro"]["mean"],
        "CV Macro AUC Std":   cv_aucs["Macro"]["std"],
    }
    for drug in DRUGS:
        row[f"Test AUC {drug}"]    = test_aucs[drug]
        row[f"CV AUC {drug} Mean"] = cv_aucs[drug]["mean"]
        row[f"CV AUC {drug} Std"]  = cv_aucs[drug]["std"]

    results.append(row)

# ── Summary ────────────────────────────────────────────────────────────────────
results_df = (
    pd.DataFrame(results)
    .sort_values("CV Macro AUC Mean", ascending=False)
    .reset_index(drop=True)
)

print(f"\n\n{'='*65}")
print(f" MULTI-LABEL BENCHMARK SUMMARY")
print(f"{'='*65}")

# Print concise summary table
summary_cols = ["Model", "Macro AUC-ROC", "CV Macro AUC Mean",
                "CV Macro AUC Std", "Hamming Loss", "Subset Accuracy"]
print(results_df[summary_cols].to_string(index=False))

print(f"\n  Per-drug CV AUC-ROC:")
print(f"  {'Model':<22}", end="")
for drug in DRUGS:
    print(f" {drug[:3]:>10}", end="")
print()
print(f"  {'─'*65}")
for _, row in results_df.iterrows():
    print(f"  {row['Model']:<22}", end="")
    for drug in DRUGS:
        print(f" {row[f'CV AUC {drug} Mean']:>10.4f}", end="")
    print()

# ── Compare against single-drug models ────────────────────────────────────────
print(f"\n  Comparison vs single-drug RF (from benchmark_DRUG_v4.csv):")
print(f"  {'Drug':<15} {'Single-drug RF':>16} {'Multi-label RF':>16} {'Delta':>8}")
print(f"  {'─'*60}")

single_drug_aucs = {
    "RIFAMPICIN":   0.9690,
    "ISONIAZID":    0.9464,
    "ETHAMBUTOL":   0.8997,
    "PYRAZINAMIDE": 0.8831,
}

rf_row = results_df[results_df["Model"] == "Random Forest"].iloc[0]
for drug in DRUGS:
    single = single_drug_aucs[drug]
    multi  = rf_row[f"CV AUC {drug} Mean"]
    delta  = multi - single
    sign   = "+" if delta >= 0 else ""
    print(f"  {drug:<15} {single:>16.4f} {multi:>16.4f} {sign}{delta:>7.4f}")

# ── Save outputs ───────────────────────────────────────────────────────────────
csv_path = "results/benchmark_multi_v1.csv"
results_df.to_csv(csv_path, index=False)
print(f"\n  Metrics saved: {csv_path}")

pkl_path = "results/model_objects_multi.pkl"
with open(pkl_path, "wb") as f:
    pickle.dump({
        "drugs":        DRUGS,
        "feature_cols": feature_cols,
        "X_train":      X_train,
        "X_test":       X_test,
        "Y_train":      Y_train,
        "Y_test":       Y_test,
        "trained":      trained,
        "profiles":     profiles,
    }, f)
print(f"  Model objects: {pkl_path}")

print(f"\n{'='*65}")
print(f" DONE")
print(f"  Next: run visualize.py --mode multi to generate plots")
print(f"{'='*65}\n")
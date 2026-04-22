#!/usr/bin/env python3
"""
Multi-Model Benchmarking — v4
Trains and evaluates all models, saves results to CSV.
Run visualize.py afterwards to generate charts and SHAP plots.

Models:
  - Random Forest
  - LightGBM
  - XGBoost
  - Linear SVM (SGD)

All models:
  - Handle class imbalance via class_weight / scale_pos_weight
  - 5-fold stratified cross-validation (Accuracy + AUC-ROC)
  - Hold-out test set evaluation

Output:
  - results/benchmark_<DRUG>_v4.csv   — metrics table
  - results/model_objects_<DRUG>.pkl  — serialised models + data for SHAP
"""

import argparse
import os
import pickle
import warnings

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import lightgbm as lgb
import xgboost as xgb

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ────────────────────────────────────────────────────────────────────
N_ESTIMATORS = 300
TEST_SIZE    = 0.2
RANDOM_STATE = 42
CV_FOLDS     = 5
# ─────────────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Multi-model benchmark v4")
parser.add_argument(
    "--drug", default="RIFAMPICIN",
    choices=["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"],
)
args = parser.parse_args()
DRUG = args.drug

os.makedirs("results", exist_ok=True)

print(f"\n{'='*65}")
print(f" Multi-Model Benchmark v4 — Drug: {DRUG}")
print(f"{'='*65}")

# ── Load data ─────────────────────────────────────────────────────────────────
print("\nLoading matrix...")
df = pd.read_csv("../resistance_dataset/ml_matrix.csv.gz", index_col="SAMPLE")
print(f"Matrix shape: {df.shape}")

feature_cols  = [c for c in df.columns if c.startswith("pos_")]
y_raw         = df[DRUG]
mask          = y_raw.isin([0, 1])
X             = df[feature_cols][mask]
y             = y_raw[mask].astype(int)

n_resistant   = int(y.sum())
n_susceptible = int((y == 0).sum())
scale_pos_w   = n_susceptible / n_resistant  # for XGBoost

print(f"\n  Drug          : {DRUG}")
print(f"  Samples       : {len(y)}")
print(f"  Resistant (1) : {n_resistant}  ({100*y.mean():.1f}%)")
print(f"  Susceptible(0): {n_susceptible} ({100*(1-y.mean()):.1f}%)")
print(f"  Features      : {X.shape[1]}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)

# ── Model definitions ─────────────────────────────────────────────────────────
models = {

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
        use_label_encoder=False,
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

# ── Training & evaluation loop ────────────────────────────────────────────────
cv      = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
results = []
trained = {}  # model name → fitted model object (for visualize.py)

for name, model in models.items():
    print(f"\n{'─'*55}")
    print(f"  Model: {name}")
    print(f"{'─'*55}")

    model.fit(X_train, y_train)
    trained[name] = model

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    acc    = accuracy_score(y_test, y_pred)
    auc    = roc_auc_score(y_test, y_prob)

    print(f"  Hold-out Accuracy : {acc:.4f}")
    print(f"  Hold-out AUC-ROC  : {auc:.4f}")
    print()
    print(classification_report(
        y_test, y_pred,
        target_names=["Susceptible", "Resistant"],
        digits=4,
    ))

    print(f"  Running {CV_FOLDS}-fold CV...")
    cv_acc = cross_val_score(model, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    cv_auc = cross_val_score(model, X, y, cv=cv, scoring="roc_auc",  n_jobs=-1)

    print(f"  CV Accuracy : {cv_acc.mean():.4f} ± {cv_acc.std():.4f}")
    print(f"  CV AUC-ROC  : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

    results.append({
        "Model":            name,
        "Test Accuracy":    round(acc, 4),
        "Test AUC-ROC":     round(auc, 4),
        "CV Accuracy Mean": round(cv_acc.mean(), 4),
        "CV Accuracy Std":  round(cv_acc.std(),  4),
        "CV AUC-ROC Mean":  round(cv_auc.mean(), 4),
        "CV AUC-ROC Std":   round(cv_auc.std(),  4),
    })

# ── Save metrics CSV ──────────────────────────────────────────────────────────
results_df = (
    pd.DataFrame(results)
    .sort_values("CV AUC-ROC Mean", ascending=False)
    .reset_index(drop=True)
)

print(f"\n\n{'='*65}")
print(f" BENCHMARK SUMMARY — {DRUG}")
print(f"{'='*65}")
print(results_df.to_string(index=False))

csv_path = f"results/benchmark_{DRUG}_v4.csv"
results_df.to_csv(csv_path, index=False)
print(f"\n  Metrics saved : {csv_path}")

# ── Serialise models + split data for visualize.py ───────────────────────────
pkl_path = f"results/model_objects_{DRUG}.pkl"
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

print(f"\n{'='*65}")
print(f" DONE — run visualize.py --drug {DRUG} to generate plots")
print(f"{'='*65}\n")

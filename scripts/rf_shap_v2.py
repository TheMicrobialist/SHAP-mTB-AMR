#!/usr/bin/env python3
"""
Random Forest + SHAP on ML matrix — v2
Improvements over v1:
  - class_weight="balanced" to handle class imbalance
  - AUC-ROC metric in addition to accuracy
  - 5-fold cross-validation for more reliable estimates
  - Results saved with _v2 suffix for comparison with v1
"""

import os
import argparse
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


N_ESTIMATORS   = 300     # v1 used 100; more trees = more stable
TEST_SIZE      = 0.2
RANDOM_STATE   = 42
TOP_N_FEATURES = 50      # for SHAP (subset like Noah did)
CV_FOLDS       = 5       # cross-validation folds
# ============================================================

parser = argparse.ArgumentParser(description="RF + SHAP v2 — balanced, AUC-ROC, CV")
parser.add_argument("--drug", default="RIFAMPICIN",
                    choices=["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"])
args = parser.parse_args()
DRUG = args.drug

print(f"\n{'='*60}")
print(f"RF + SHAP v2 — Drug: {DRUG}")
print(f"{'='*60}")

# Load matrix
print("Loading matrix...")
df = pd.read_csv(
    "resistance_dataset/ml_matrix.csv.gz",
    index_col="SAMPLE"
)
print(f"Matrix shape: {df.shape}")

# Split features and labels
feature_cols = [c for c in df.columns if c.startswith("pos_")]

# Filter to samples with labels for this drug
y_raw = df[DRUG]
mask  = y_raw.isin([0, 1])
X     = df[feature_cols][mask]
y     = y_raw[mask].astype(int)

print(f"\nDrug          : {DRUG}")
print(f"Samples       : {len(y)}")
print(f"Resistant (1) : {y.sum()} ({100*y.mean():.1f}%)")
print(f"Susceptible(0): {(y==0).sum()} ({100*(1-y.mean()):.1f}%)")
print(f"Features      : {X.shape[1]}")
print(f"Class ratio   : 1:{(y==0).sum()/y.sum():.2f} (S:R)")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE,
    stratify=y
)

# ── Random Forest with balanced class weights ──────────────
print(f"\nTraining Random Forest v2 (n={N_ESTIMATORS}, balanced)...")
rf = RandomForestClassifier(
    n_estimators=N_ESTIMATORS,
    class_weight="balanced",   # Fix 1: handle class imbalance
    random_state=RANDOM_STATE,
    n_jobs=-1
)
rf.fit(X_train, y_train)

import joblib
os.makedirs("models", exist_ok=True)
joblib.dump(rf, f"models/rf_{DRUG}_v2.joblib")
print(f"Saved: models/rf_{DRUG}_v2.joblib")

# Fix 2: AUC-ROC in addition to accuracy
y_pred     = rf.predict(X_test)
y_prob     = rf.predict_proba(X_test)[:, 1]
acc        = accuracy_score(y_test, y_pred)
auc        = roc_auc_score(y_test, y_prob)

print(f"\n  Accuracy : {acc:.4f}")
print(f"  AUC-ROC  : {auc:.4f}")
print(f"\n{classification_report(y_test, y_pred, target_names=['Susceptible','Resistant'])}")

# Fix 3: 5-fold cross-validation
print(f"Running {CV_FOLDS}-fold cross-validation...")
cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

cv_acc = cross_val_score(rf, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
cv_auc = cross_val_score(rf, X, y, cv=cv, scoring="roc_auc",  n_jobs=-1)

print(f"  CV Accuracy : {cv_acc.mean():.4f} ± {cv_acc.std():.4f}")
print(f"  CV AUC-ROC  : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

# Save metrics to text file
metrics_path = f"results/metrics_{DRUG}_v2.txt"
with open(metrics_path, "w") as f:
    f.write(f"Drug: {DRUG}\n")
    f.write(f"Samples: {len(y)}\n")
    f.write(f"Resistant: {y.sum()} ({100*y.mean():.1f}%)\n")
    f.write(f"Susceptible: {(y==0).sum()} ({100*(1-y.mean()):.1f}%)\n\n")
    f.write(f"Accuracy : {acc:.4f}\n")
    f.write(f"AUC-ROC  : {auc:.4f}\n\n")
    f.write(f"CV Accuracy : {cv_acc.mean():.4f} +/- {cv_acc.std():.4f}\n")
    f.write(f"CV AUC-ROC  : {cv_auc.mean():.4f} +/- {cv_auc.std():.4f}\n\n")
    f.write(classification_report(y_test, y_pred,
            target_names=["Susceptible", "Resistant"]))
print(f"  Metrics saved: {metrics_path}")

# ── SHAP on top N features ─────────────────────────────────
importances  = pd.Series(rf.feature_importances_, index=feature_cols)
top_features = importances.nlargest(TOP_N_FEATURES).index.tolist()

print(f"\nTop {TOP_N_FEATURES} features for SHAP:")
for i, f in enumerate(top_features[:10], 1):
    print(f"  {i:2d}. {f}  (importance: {importances[f]:.4f})")

# Smaller RF on top features
rf_small = RandomForestClassifier(
    n_estimators=N_ESTIMATORS,
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1
)
rf_small.fit(X_train[top_features], y_train)

acc_small = accuracy_score(y_test, rf_small.predict(X_test[top_features]))
auc_small = roc_auc_score(y_test, rf_small.predict_proba(X_test[top_features])[:, 1])
print(f"\n  Top {TOP_N_FEATURES} model accuracy : {acc_small:.4f}")
print(f"  Top {TOP_N_FEATURES} model AUC-ROC  : {auc_small:.4f}")

# SHAP with background dataset (fixes FutureWarning)
print(f"\nRunning SHAP TreeExplainer...")
background = shap.sample(X_train[top_features], 100, random_state=RANDOM_STATE)
explainer  = shap.TreeExplainer(
    rf_small,
    data=background,
    feature_perturbation="interventional",
    feature_names=top_features
)
shap_values = explainer(X_test[top_features], check_additivity=False)

# SHAP summary plot — saved with _v2 suffix
plot_path = f"results/shap_summary_{DRUG}_v2.png"
shap.summary_plot(
    shap_values[:, :, 1],
    X_test[top_features],
    feature_names=top_features,
    show=False
)
plt.tight_layout()
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  SHAP plot saved: {plot_path}")

print(f"\n{'='*60}")
print(f"DONE — {DRUG}")
print(f"  Accuracy (test)  : {acc:.4f}")
print(f"  AUC-ROC (test)   : {auc:.4f}")
print(f"  CV AUC-ROC       : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")
print(f"{'='*60}\n")

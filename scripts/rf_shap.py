#!/usr/bin/env python3
"""
Random Forest + SHAP on ML matrix
Start with RIFAMPICIN, replicate Noah's workflow
"""
import argparse
import gzip
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import shap

# DRUG          = "RIFAMPICIN"   # "ISONIAZID", "RIFAMPICIN", "ETHAMBUTOL", "PYRAZINAMIDE"
parser = argparse.ArgumentParser()
parser.add_argument("--drug", default="RIFAMPICIN")
args = parser.parse_args()
DRUG = args.drug

N_ESTIMATORS  = 100            # Noah used 50
TEST_SIZE     = 0.2
RANDOM_STATE  = 42
TOP_N_FEATURES = 50            # for SHAP 
# ============================================================

print(f"Loading matrix...")
df = pd.read_csv(
    "resistance_dataset/ml_matrix.csv.gz",
    index_col="SAMPLE"
)

print(f"Matrix shape: {df.shape}")

# Split features and labels
feature_cols = [c for c in df.columns if c.startswith("pos_")]
drug_cols    = ["ISONIAZID", "RIFAMPICIN", "ETHAMBUTOL", "PYRAZINAMIDE"]

X = df[feature_cols]

# Filter to samples with labels for this drug
y_raw = df[DRUG]
mask  = y_raw.isin([0, 1])   # drop NaN/unknown
X     = X[mask]
y     = y_raw[mask].astype(int)

print(f"\nDrug: {DRUG}")
print(f"  Samples with labels : {len(y)}")
print(f"  Resistant (1)       : {y.sum()}")
print(f"  Susceptible (0)     : {(y==0).sum()}")
print(f"  Features            : {X.shape[1]}")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)

# Random Forest
print(f"\nTraining Random Forest (n_estimators={N_ESTIMATORS})...")
rf = RandomForestClassifier(
    n_estimators=N_ESTIMATORS,
    random_state=RANDOM_STATE,
    n_jobs=-1
)
rf.fit(X_train, y_train)

acc = accuracy_score(y_test, rf.predict(X_test))
print(f"  Accuracy: {acc:.4f}")
print(classification_report(y_test, rf.predict(X_test),
      target_names=["Susceptible", "Resistant"]))

# Top N features by importance (for SHAP efficiency)
importances  = pd.Series(rf.feature_importances_, index=feature_cols)
top_features = importances.nlargest(TOP_N_FEATURES).index.tolist()
print(f"\nTop {TOP_N_FEATURES} features selected for SHAP")

# Smaller RF on top features (like Noah did)
rf_small = RandomForestClassifier(
    n_estimators=N_ESTIMATORS,
    random_state=RANDOM_STATE,
    n_jobs=-1
)
rf_small.fit(X_train[top_features], y_train)

acc_small = accuracy_score(y_test, rf_small.predict(X_test[top_features]))
print(f"  Accuracy (top {TOP_N_FEATURES} features): {acc_small:.4f}")

# SHAP
print(f"\nRunning SHAP TreeExplainer...")
background = shap.sample(X_train[top_features], 100, random_state=42)
explainer = shap.TreeExplainer(
    rf_small,
    data=background,
    feature_perturbation="interventional",
    feature_names=top_features
)
shap_values = explainer(
    X_test[top_features],
    check_additivity=False
)

# Summary plot
print("Saving SHAP summary plot...")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

shap.summary_plot(
    shap_values[:, :, 1],   # class 1 = Resistant
    X_test[top_features],
    feature_names=top_features,
    show=False
)
plt.tight_layout()
plt.savefig(f"results/shap_summary_{DRUG}.png", dpi=150, bbox_inches="tight")
plt.close()
print(f"  Saved: results/shap_summary_{DRUG}.png")

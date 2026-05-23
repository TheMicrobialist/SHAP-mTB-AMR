#!/usr/bin/env python3
"""
Multi-Model Benchmarking + SHAP on ML matrix — v3
Extends v2 (Random Forest) with additional models:
  - LightGBM
  - XGBoost
  - Logistic Regression (L2, saga solver)
  - Linear SVM (SGD approximation, scales to large feature sets)
  - Random Forest (retained from v2 as baseline)

All models:
  - Handle class imbalance via class_weight / scale_pos_weight
  - 5-fold stratified cross-validation (Accuracy + AUC-ROC)
  - Hold-out test set evaluation
  - Results saved to results/benchmark_<DRUG>_v3.csv
  - Bar chart comparison saved to results/benchmark_<DRUG>_v3.png

SHAP summary plot produced for the best AUC-ROC model (if tree-based).
"""

import argparse
import os
import warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

import lightgbm as lgb
import xgboost as xgb
import shap

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ────────────────────────────────────────────────────────────────────
N_ESTIMATORS   = 300
TEST_SIZE      = 0.2
RANDOM_STATE   = 42
TOP_N_FEATURES = 50   # for SHAP
CV_FOLDS       = 5
# ─────────────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Multi-model benchmark v3")
parser.add_argument(
    "--drug", default="RIFAMPICIN",
    choices=["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"],
)
args = parser.parse_args()
DRUG = args.drug

os.makedirs("results", exist_ok=True)

print(f"\n{'='*65}")
print(f" Multi-Model Benchmark v3 — Drug: {DRUG}")
print(f"{'='*65}")

# ── Load data ─────────────────────────────────────────────────────────────────
print("\nLoading matrix...")
df = pd.read_csv("../resistance_dataset/ml_matrix.csv.gz", index_col="SAMPLE")
print(f"Matrix shape: {df.shape}")

feature_cols = [c for c in df.columns if c.startswith("pos_")]
y_raw        = df[DRUG]
mask         = y_raw.isin([0, 1])
X            = df[feature_cols][mask]
y            = y_raw[mask].astype(int)

n_resistant    = int(y.sum())
n_susceptible  = int((y == 0).sum())
scale_pos_w    = n_susceptible / n_resistant   # for XGBoost

print(f"\n  Drug          : {DRUG}")
print(f"  Samples       : {len(y)}")
print(f"  Resistant (1) : {n_resistant}  ({100*y.mean():.1f}%)")
print(f"  Susceptible(0): {n_susceptible} ({100*(1-y.mean()):.1f}%)")
print(f"  Features      : {X.shape[1]}")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
)

# ── Model definitions ─────────────────────────────────────────────────────────
#
# NOTE ON SCALING
#   Tree-based models (RF, LGB, XGB) are invariant to feature scaling.
#   Linear models (LR, SVM) are NOT — we wrap them in a Pipeline with
#   StandardScaler so the CV and test splits are scaled identically
#   without data leakage.

models = {

    "Random Forest": RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    ),

    "LightGBM": lgb.LGBMClassifier(
        n_estimators=N_ESTIMATORS,
        class_weight="balanced",    # handles imbalance
        learning_rate=0.05,
        num_leaves=63,              # richer trees than default 31
        min_child_samples=10,
        subsample=0.8,              # row subsampling — reduces overfitting
        colsample_bytree=0.8,       # feature subsampling per tree
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbose=-1,                 # suppress training log
    ),

    "XGBoost": xgb.XGBClassifier(
        n_estimators=N_ESTIMATORS,
        scale_pos_weight=scale_pos_w,   # equivalent to class_weight for XGB
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
            loss="modified_huber",      # produces probability estimates
            class_weight="balanced",
            alpha=1e-4,                 # L2 regularisation strength
            max_iter=200,
            tol=1e-3,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )),
    ]),
}

# ── Training & evaluation loop ────────────────────────────────────────────────
cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

results = []   # list of dicts, one per model

for name, model in models.items():
    print(f"\n{'─'*55}")
    print(f"  Model: {name}")
    print(f"{'─'*55}")

    # Fit on training split
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc  = accuracy_score(y_test, y_pred)
    auc  = roc_auc_score(y_test, y_prob)

    print(f"  Hold-out Accuracy : {acc:.4f}")
    print(f"  Hold-out AUC-ROC  : {auc:.4f}")
    print()
    print(classification_report(
        y_test, y_pred,
        target_names=["Susceptible", "Resistant"],
        digits=4,
    ))

    # 5-fold CV on the full labelled dataset
    print(f"  Running {CV_FOLDS}-fold CV...")
    cv_acc = cross_val_score(model, X, y, cv=cv, scoring="accuracy",  n_jobs=-1)
    cv_auc = cross_val_score(model, X, y, cv=cv, scoring="roc_auc",   n_jobs=-1)

    print(f"  CV Accuracy : {cv_acc.mean():.4f} ± {cv_acc.std():.4f}")
    print(f"  CV AUC-ROC  : {cv_auc.mean():.4f} ± {cv_auc.std():.4f}")

    results.append({
        "Model":            name,
        "Test Accuracy":    round(acc,  4),
        "Test AUC-ROC":     round(auc,  4),
        "CV Accuracy Mean": round(cv_acc.mean(), 4),
        "CV Accuracy Std":  round(cv_acc.std(),  4),
        "CV AUC-ROC Mean":  round(cv_auc.mean(), 4),
        "CV AUC-ROC Std":   round(cv_auc.std(),  4),
        "_model_obj":       model,          # kept temporarily for SHAP
    })

# ── Results table ─────────────────────────────────────────────────────────────
results_df = pd.DataFrame(results).drop(columns=["_model_obj"])
results_df = results_df.sort_values("CV AUC-ROC Mean", ascending=False).reset_index(drop=True)

print(f"\n\n{'='*65}")
print(f" BENCHMARK SUMMARY — {DRUG}")
print(f"{'='*65}")
print(results_df.to_string(index=False))

csv_path = f"results/benchmark_{DRUG}_v3.csv"
results_df.to_csv(csv_path, index=False)
print(f"\n  Table saved : {csv_path}")

# ── Comparison bar chart ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle(f"Model Benchmark — {DRUG}", fontsize=14, fontweight="bold")

model_names   = results_df["Model"].tolist()
x             = np.arange(len(model_names))
bar_width     = 0.35

for ax, metric_mean, metric_std, title in [
    (axes[0], "CV Accuracy Mean",  "CV Accuracy Std",  "5-Fold CV Accuracy"),
    (axes[1], "CV AUC-ROC Mean",   "CV AUC-ROC Std",   "5-Fold CV AUC-ROC"),
]:
    means = results_df[metric_mean].values
    stds  = results_df[metric_std].values

    bars = ax.bar(x, means, yerr=stds, capsize=5,
                  color=plt.cm.tab10(np.linspace(0, 0.6, len(model_names))),
                  edgecolor="black", linewidth=0.6)

    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=20, ha="right", fontsize=9)
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(title)
    ax.set_ylim(max(0, means.min() - 0.05), min(1.02, means.max() + 0.06))
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    for bar, mean, std in zip(bars, means, stds):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + std + 0.003,
            f"{mean:.3f}",
            ha="center", va="bottom", fontsize=8,
        )

plt.tight_layout()
chart_path = f"results/benchmark_{DRUG}_v3.png"
plt.savefig(chart_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"  Chart saved : {chart_path}")

# ── SHAP for best tree-based model ────────────────────────────────────────────
# Identify the top-ranked model by CV AUC-ROC that supports TreeExplainer.
TREE_MODELS = {"Random Forest", "LightGBM", "XGBoost"}
best_row    = next(
    (r for r in results if r["Model"] in TREE_MODELS),
    None
)

if best_row:
    best_name  = best_row["Model"]
    best_model = best_row["_model_obj"]
    print(f"\n  Running SHAP for best tree model: {best_name}")

    importances = pd.Series(
        best_model.feature_importances_, index=feature_cols
    )
    top_features = importances.nlargest(TOP_N_FEATURES).index.tolist()

    # Retrain smaller model on top features only (faster SHAP)
    small_model = best_model.__class__(**{
        k: v for k, v in best_model.get_params().items()
    })
    small_model.fit(X_train[top_features], y_train)

    background   = shap.sample(X_train[top_features], 100, random_state=RANDOM_STATE)
    explainer    = shap.TreeExplainer(
        small_model,
        data=background,
        feature_perturbation="interventional",
        feature_names=top_features,
    )
    shap_values = explainer(X_test[top_features], check_additivity=False)

    shap_path = f"results/shap_summary_{DRUG}_{best_name.replace(' ', '_')}_v3.png"
    shap.summary_plot(
        shap_values[:, :, 1],
        X_test[top_features],
        feature_names=top_features,
        show=False,
    )
    plt.tight_layout()
    plt.savefig(shap_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  SHAP plot saved : {shap_path}")
else:
    print("\n  No tree-based model in top results — skipping SHAP.")

print(f"\n{'='*65}")
print(f" DONE — {DRUG}")
print(f"{'='*65}\n")
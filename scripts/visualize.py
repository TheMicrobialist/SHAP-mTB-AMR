#!/usr/bin/env python3
"""
Visualization — v4
Reads outputs from benchmark.py and produces:
  1. Bar chart  — results/benchmark_<DRUG>_v4.png   (CV Accuracy + AUC-ROC)
  2. SHAP plot  — results/shap_summary_<DRUG>_<MODEL>_v4.png

Must be run after benchmark.py for the same --drug.
"""

import argparse
import os
import pickle
import warnings

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ────────────────────────────────────────────────────────────────────
TOP_N_FEATURES = 50
RANDOM_STATE   = 42
TREE_MODELS    = {"Random Forest", "LightGBM", "XGBoost"}
# ─────────────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="Visualize benchmark results v4")
parser.add_argument(
    "--drug", default="RIFAMPICIN",
    choices=["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"],
)
args = parser.parse_args()
DRUG = args.drug

os.makedirs("results", exist_ok=True)

# ── Load benchmark CSV ────────────────────────────────────────────────────────
csv_path = f"results/benchmark_{DRUG}_v4.csv"
if not os.path.exists(csv_path):
    raise FileNotFoundError(
        f"{csv_path} not found — run benchmark.py --drug {DRUG} first."
    )
results_df = pd.read_csv(csv_path)
print(f"\nLoaded metrics: {csv_path}")
print(results_df.to_string(index=False))

# ── Load serialised models ────────────────────────────────────────────────────
pkl_path = f"results/model_objects_{DRUG}.pkl"
if not os.path.exists(pkl_path):
    raise FileNotFoundError(
        f"{pkl_path} not found — run benchmark.py --drug {DRUG} first."
    )
with open(pkl_path, "rb") as f:
    store = pickle.load(f)

feature_cols = store["feature_cols"]
X_train      = store["X_train"]
X_test       = store["X_test"]
y_train      = store["y_train"]
trained      = store["trained"]
print(f"Loaded model objects: {pkl_path}\n")

# ── 1. Bar chart ──────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle(f"Model Benchmark — {DRUG}", fontsize=14, fontweight="bold")

model_names = results_df["Model"].tolist()
x           = np.arange(len(model_names))
colors      = plt.cm.tab10(np.linspace(0, 0.6, len(model_names)))

for ax, mean_col, std_col, title in [
    (axes[0], "CV Accuracy Mean", "CV Accuracy Std", "5-Fold CV Accuracy"),
    (axes[1], "CV AUC-ROC Mean",  "CV AUC-ROC Std",  "5-Fold CV AUC-ROC"),
]:
    means = results_df[mean_col].values
    stds  = results_df[std_col].values

    bars = ax.bar(
        x, means, yerr=stds, capsize=5,
        color=colors, edgecolor="black", linewidth=0.6,
    )
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
chart_path = f"results/benchmark_{DRUG}_v4.png"
plt.savefig(chart_path, dpi=150, bbox_inches="tight")
plt.close()
print(f"Bar chart saved : {chart_path}")

# ── 2. SHAP — best tree-based model by CV AUC-ROC ────────────────────────────
# Results are already sorted by CV AUC-ROC Mean descending.
best_name = next(
    (name for name in results_df["Model"] if name in TREE_MODELS),
    None,
)

if best_name is None:
    print("No tree-based model found in results — skipping SHAP.")
else:
    best_model = trained[best_name]
    print(f"\nRunning SHAP for best tree model: {best_name}")

    # Select top-N features by importance
    importances  = pd.Series(best_model.feature_importances_, index=feature_cols)
    top_features = importances.nlargest(TOP_N_FEATURES).index.tolist()

    print(f"  Top {TOP_N_FEATURES} features (first 10):")
    for i, feat in enumerate(top_features[:10], 1):
        print(f"    {i:2d}. {feat}  (importance: {importances[feat]:.4f})")

    # Retrain a smaller model on top features only (faster SHAP)
    small_model = best_model.__class__(**best_model.get_params())
    small_model.fit(X_train[top_features], y_train)

    # SHAP TreeExplainer with interventional perturbation
    background  = shap.sample(X_train[top_features], 100, random_state=RANDOM_STATE)
    explainer   = shap.TreeExplainer(
        small_model,
        data=background,
        feature_perturbation="interventional",
        feature_names=top_features,
    )
    shap_values = explainer(X_test[top_features], check_additivity=False)

    shap_path = f"results/shap_summary_{DRUG}_{best_name.replace(' ', '_')}_v4.png"
    shap.summary_plot(
        shap_values[:, :, 1],
        X_test[top_features],
        feature_names=top_features,
        show=False,
    )
    plt.tight_layout()
    plt.savefig(shap_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"SHAP plot saved : {shap_path}")

print(f"\nDone — all outputs written to results/")

#!/usr/bin/env python3
"""
Cross-Drug SHAP Attribution Analysis — Issue #8 Part 2 & 3
===========================================================
Partitions samples by resistance profile and computes mean
absolute SHAP values per group to identify positions whose
attribution changes with co-resistance context.

Implements:
  - Sample partitioning into resistance profile groups
  - Per-group mean absolute SHAP values per drug model
  - SHAP delta metric (co-resistance vs single-drug)
  - Results saved for visualize.py plotting

Usage:
  python3 scripts/shap_cross_drug.py
  python3 scripts/shap_cross_drug.py --drug-pair RIF INH
  python3 scripts/shap_cross_drug.py --all-pairs

Output:
  results/shap_cross_drug_{A}_{B}.csv   — delta scores per position
  results/shap_cross_drug_results.pkl   — full results for visualize.py
"""

import argparse
import os
import pickle
import warnings

import numpy as np
import pandas as pd
import shap

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# ── Config ─────────────────────────────────────────────────────────────────────
DRUGS      = ["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"]
DRUG_SHORT = {"RIFAMPICIN": "RIF", "ISONIAZID": "INH",
              "ETHAMBUTOL": "ETH", "PYRAZINAMIDE": "PZA"}

# All 6 drug pairs
DRUG_PAIRS = [
    ("RIFAMPICIN",  "ISONIAZID"),
    ("RIFAMPICIN",  "ETHAMBUTOL"),
    ("RIFAMPICIN",  "PYRAZINAMIDE"),
    ("ISONIAZID",   "ETHAMBUTOL"),
    ("ISONIAZID",   "PYRAZINAMIDE"),
    ("ETHAMBUTOL",  "PYRAZINAMIDE"),
]

TOP_N       = 50    # top features for SHAP (stability)
RANDOM_STATE = 42
# ──────────────────────────────────────────────────────────────────────────────

os.makedirs("results", exist_ok=True)

# ── Args ───────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Cross-drug SHAP attribution analysis"
)
parser.add_argument(
    "--drug-pair", nargs=2,
    metavar=("DRUG_A", "DRUG_B"),
    choices=DRUGS,
    help="Analyse one drug pair (e.g. --drug-pair RIFAMPICIN ISONIAZID)"
)
parser.add_argument(
    "--all-pairs", action="store_true",
    help="Run all 6 drug pairs (default if no --drug-pair given)"
)
args = parser.parse_args()

if args.drug_pair:
    pairs_to_run = [tuple(args.drug_pair)]
else:
    pairs_to_run = DRUG_PAIRS

# ── Load model objects ─────────────────────────────────────────────────────────
pkl_path = "results/model_objects_multi.pkl"
print(f"\nLoading: {pkl_path}")
with open(pkl_path, "rb") as f:
    obj = pickle.load(f)

feature_cols = obj["feature_cols"]
X_train      = obj["X_train"]
X_test       = obj["X_test"]
Y_train      = obj["Y_train"]
Y_test       = obj["Y_test"]
profiles     = obj["profiles"]   # Series: sample → "1111" etc.

# Use RF model (best performer from benchmark_multi)
rf_multi = obj["trained"]["Random Forest"]

# Reconstruct full dataset (train + test)
X_all = pd.concat([X_train, X_test])
Y_all = pd.concat([Y_train, Y_test])
profiles_all = profiles  # already covers all 5,180 samples

print(f"  Full dataset: {len(X_all)} samples × {len(feature_cols)} features")
print(f"  Unique profiles: {profiles_all.nunique()}")

# ── Compute SHAP values for ALL samples ────────────────────────────────────────
# Use top 50 features per drug for stability (same approach as rf_shap_v2.py)
print(f"\nComputing SHAP values for all {len(X_all)} samples...")
print(f"  Using top {TOP_N} features per drug for stability")

# Get feature importances from each estimator in MultiOutputClassifier
# rf_multi.estimators_[i] = RF for drug i
drug_shap_values = {}

for i, drug in enumerate(DRUGS):
    print(f"\n  Drug: {drug}")
    rf_drug = rf_multi.estimators_[i]
    # Reduce tree count for SHAP stability — use 100 trees instead of 300
    from sklearn.ensemble import RandomForestClassifier
    rf_small = RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )
    # Get feature subset
    importances  = pd.Series(rf_drug.feature_importances_, index=feature_cols)
    top_features = importances.nlargest(TOP_N).index.tolist()
    # Retrain small RF on top features only
    rf_small.fit(X_train[top_features], Y_train.iloc[:, i])
    rf_drug = rf_small  # use smaller model for SHAP

    # Top 50 features by importance for this drug
    importances  = pd.Series(rf_drug.feature_importances_,
                             index=feature_cols)
    top_features = importances.nlargest(TOP_N).index.tolist()

    # Background: 100 samples from training data
    background = X_train[top_features].sample(
        100, random_state=RANDOM_STATE
    )

    explainer = shap.TreeExplainer(
        rf_drug,
        data=background,
        feature_perturbation="interventional"
    )

    # Compute SHAP for all samples
    X_top = X_all[top_features]
    # Process in batches to avoid memory corruption on Mac ARM
    BATCH_SIZE = 500
    n_samples  = len(X_top)
    shap_list  = []

    for start in range(0, n_samples, BATCH_SIZE):
        end   = min(start + BATCH_SIZE, n_samples)
        batch = X_top.iloc[start:end]
        sv    = explainer.shap_values(batch, check_additivity=False)
        if isinstance(sv, list):
            shap_list.append(sv[1])
        else:
            shap_list.append(sv[:, :, 1] if sv.ndim == 3 else sv)
        print(f"    Batch {start}-{end} done")

    shap_arr = np.vstack(shap_list)

    # Handle output format
    if isinstance(shap_vals, list):
        shap_arr = shap_vals[1]   # class 1 = Resistant
    else:
        shap_arr = shap_vals[:, :, 1] if shap_vals.ndim == 3 else shap_vals

    # Store as DataFrame: samples × top_features
    shap_df = pd.DataFrame(
        shap_arr,
        index=X_all.index,
        columns=top_features
    )

    drug_shap_values[drug] = {
        "shap_df":      shap_df,
        "top_features": top_features,
    }

    print(f"    SHAP shape: {shap_df.shape}")
    print(f"    Top feature: {top_features[0]}")

# ── Partition samples + compute cross-drug SHAP ────────────────────────────────

print(f"\n{'='*65}")
print(f" Cross-Drug SHAP Attribution Analysis")
print(f"{'='*65}")

all_pair_results = {}

for drug_a, drug_b in pairs_to_run:
    a_idx = DRUGS.index(drug_a)
    b_idx = DRUGS.index(drug_b)
    a_s   = DRUG_SHORT[drug_a]
    b_s   = DRUG_SHORT[drug_b]

    print(f"\n{'─'*65}")
    print(f"  Pair: {drug_a} ({a_s}) × {drug_b} ({b_s})")
    print(f"{'─'*65}")

    # ── Partition samples ──────────────────────────────────────────────────────
    # Profile string format: RIF-INH-ETH-PZA
    # drug_a position = a_idx, drug_b position = b_idx

    def get_profile_mask(profiles, drug_idx, value):
        """Samples where drug at drug_idx has given value (0 or 1)."""
        return profiles.apply(lambda p: int(p[drug_idx]) == value)

    # Group definitions (Noah's issue: ALL combinations, not just co-resistance)
    groups = {
        f"{a_s}_only":    (get_profile_mask(profiles_all, a_idx, 1) &
                           get_profile_mask(profiles_all, b_idx, 0)),
        f"{b_s}_only":    (get_profile_mask(profiles_all, a_idx, 0) &
                           get_profile_mask(profiles_all, b_idx, 1)),
        f"{a_s}+{b_s}":   (get_profile_mask(profiles_all, a_idx, 1) &
                           get_profile_mask(profiles_all, b_idx, 1)),
        "neither":        (get_profile_mask(profiles_all, a_idx, 0) &
                           get_profile_mask(profiles_all, b_idx, 0)),
    }

    print(f"\n  Sample counts per group:")
    for group_name, mask in groups.items():
        print(f"    {group_name:<15}: {mask.sum():>5} samples")

    # ── Compute mean absolute SHAP per group ───────────────────────────────────
    # Use shared features (intersection of top features for drug_a and drug_b)
    shared_features = list(
        set(drug_shap_values[drug_a]["top_features"]) &
        set(drug_shap_values[drug_b]["top_features"])
    )
    print(f"\n  Shared top features: {len(shared_features)}")

    group_shap = {}   # group_name → {drug → mean_abs_shap Series}

    for group_name, mask in groups.items():
        group_idx   = profiles_all[mask].index
        group_shap[group_name] = {}

        for drug in [drug_a, drug_b]:
            shap_df = drug_shap_values[drug]["shap_df"]
            # Samples in this group that have SHAP values
            common_idx = shap_df.index.intersection(group_idx)

            if len(common_idx) == 0:
                group_shap[group_name][drug] = pd.Series(
                    0.0, index=shared_features
                )
                continue

            # Mean absolute SHAP for shared features
            mean_abs = (shap_df.loc[common_idx, shared_features]
                        .abs().mean())
            group_shap[group_name][drug] = mean_abs

    # ── SHAP delta metric ──────────────────────────────────────────────────────
    # Delta = mean_abs_SHAP(co-resistant group) - mean_abs_SHAP(single-drug group)
    # For drug_a: compare {a_s}+{b_s} group vs {a_s}_only group
    # For drug_b: compare {a_s}+{b_s} group vs {b_s}_only group

    co_key     = f"{a_s}+{b_s}"
    a_only_key = f"{a_s}_only"
    b_only_key = f"{b_s}_only"

    delta_a = (group_shap[co_key][drug_a] -
               group_shap[a_only_key][drug_a])
    delta_b = (group_shap[co_key][drug_b] -
               group_shap[b_only_key][drug_b])

    # ── Build results DataFrame ────────────────────────────────────────────────
    pair_df = pd.DataFrame({
        "position":               shared_features,
        f"shap_{a_s}_only":       group_shap[a_only_key][drug_a].values,
        f"shap_{b_s}_only":       group_shap[b_only_key][drug_b].values,
        f"shap_{a_s}_in_coresist": group_shap[co_key][drug_a].values,
        f"shap_{b_s}_in_coresist": group_shap[co_key][drug_b].values,
        f"shap_{a_s}_neither":    group_shap["neither"][drug_a].values,
        f"shap_{b_s}_neither":    group_shap["neither"][drug_b].values,
        f"delta_{a_s}":           delta_a.values,
        f"delta_{b_s}":           delta_b.values,
    })

    # Sort by absolute delta (most interesting positions first)
    pair_df["max_abs_delta"] = pair_df[[f"delta_{a_s}",
                                         f"delta_{b_s}"]].abs().max(axis=1)
    pair_df = pair_df.sort_values("max_abs_delta", ascending=False)

    # ── Print top findings ─────────────────────────────────────────────────────
    print(f"\n  Top 10 positions by SHAP delta:")
    print(f"  {'Position':<15} {'Gene':<8} "
          f"{a_s+' delta':>12} {b_s+' delta':>12} {'Interpretation'}")
    print(f"  {'─'*70}")

    # Add gene annotation
    from scripts.vcf_to_prediction import get_gene_for_position
    pair_df["gene"] = pair_df["position"].apply(get_gene_for_position)

    for _, row in pair_df.head(10).iterrows():
        d_a = row[f"delta_{a_s}"]
        d_b = row[f"delta_{b_s}"]

        # Interpret delta
        if d_a > 0.001 and d_b > 0.001:
            interpretation = "amplified in co-resistance"
        elif d_a > 0.001:
            interpretation = f"{a_s} amplified"
        elif d_b > 0.001:
            interpretation = f"{b_s} amplified"
        elif d_a < -0.001 and d_b < -0.001:
            interpretation = "suppressed in co-resistance"
        else:
            interpretation = "independent"

        print(f"  {row['position']:<15} {row['gene']:<8} "
              f"{d_a:>+12.4f} {d_b:>+12.4f}  {interpretation}")

    # Save pair CSV
    csv_path = f"results/shap_cross_drug_{a_s}_{b_s}.csv"
    pair_df.to_csv(csv_path, index=False)
    print(f"\n  Saved: {csv_path}")

    all_pair_results[f"{a_s}_{b_s}"] = {
        "pair":        (drug_a, drug_b),
        "groups":      groups,
        "group_shap":  group_shap,
        "delta_df":    pair_df,
        "n_samples":   {g: m.sum() for g, m in groups.items()},
    }

# ── Save full results for visualize.py ────────────────────────────────────────
results_pkl = "results/shap_cross_drug_results.pkl"
with open(results_pkl, "wb") as f:
    pickle.dump({
        "pairs":             all_pair_results,
        "drug_shap_values":  drug_shap_values,
        "profiles_all":      profiles_all,
        "Y_all":             Y_all,
        "feature_cols":      feature_cols,
    }, f)
print(f"\nFull results saved: {results_pkl}")

# ── Summary ────────────────────────────────────────────────────────────────────
print(f"\n{'='*65}")
print(f" SUMMARY")
print(f"{'='*65}")
print(f"  Pairs analysed: {len(pairs_to_run)}")
for pair_key, res in all_pair_results.items():
    drug_a, drug_b = res["pair"]
    a_s = DRUG_SHORT[drug_a]
    b_s = DRUG_SHORT[drug_b]
    n_co = res["n_samples"][f"{a_s}+{b_s}"]
    delta_df = res["delta_df"]
    top_pos  = delta_df.iloc[0]["position"]
    top_gene = delta_df.iloc[0]["gene"]
    print(f"\n  {a_s} × {b_s}:")
    print(f"    Co-resistant samples: {n_co}")
    print(f"    Top delta position:   {top_pos} ({top_gene})")

print(f"\n  Next: run visualize.py --mode multi --drug-pair RIF INH")
print(f"{'='*65}\n")
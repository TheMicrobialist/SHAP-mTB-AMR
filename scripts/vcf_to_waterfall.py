#!/usr/bin/env python3
"""
vcf_to_waterfall.py
===================
VCF → resistance prediction + SHAP values + waterfall plot.

Same prediction path as vcf_to_prediction.py, plus a per-isolate waterfall
PNG for the resistant class. A beeswarm is not produced — that plot needs
a cohort of isolates, not a single VCF.

Usage:
    python3 scripts/vcf_to_waterfall.py \\
        --vcf test_data/ERR040120.filtered.vcf.gz \\
        --drug RIFAMPICIN

    python3 scripts/vcf_to_waterfall.py \\
        --vcf test_data/ERR040120.filtered.vcf.gz \\
        --all-drugs

Output:
    results/predictions/{sample}_predictions.json
    results/predictions/{sample}_{drug}_shap_values.csv
    results/predictions/{sample}_{drug}_waterfall.png
"""

import os
import sys
import json
import argparse
from pathlib import Path

import pandas as pd
import joblib
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vcf_to_prediction import (
    DRUGS,
    parse_vcf,
    encode_sample,
    get_gene_for_position,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MATRIX = REPO_ROOT / "resistance_dataset" / "ml_matrix.csv.gz"


def sample_id_from_vcf(vcf_path):
    name = os.path.basename(vcf_path)
    for suffix in (".filtered.vcf.gz", ".vcf.gz", ".filtered.vcf", ".vcf"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return Path(name).stem


def feature_label(feat):
    gene = get_gene_for_position(feat)
    return f"{feat} ({gene})" if gene else feat


def resistant_explanation(explanation):
    """Slice a TreeExplainer Explanation down to one isolate, class 1."""
    values = explanation.values
    if getattr(values, "ndim", 0) == 3:
        return explanation[0, :, 1]
    if getattr(values, "ndim", 0) == 2:
        return explanation[0]
    return explanation


def predict_and_explain(sample_id, feature_vector, drug, model_dir, matrix_path):
    """
    Load trained RF model, predict resistance, compute SHAP Explanation.

    Returns (result dict, shap Series, single-sample Explanation for class 1).
    """
    model_path = os.path.join(model_dir, f"rf_{drug}_v2.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    print(f"  Loading model: {model_path}")
    rf = joblib.load(model_path)
    X = pd.DataFrame([feature_vector], columns=feature_vector.index)

    prob = rf.predict_proba(X)[0][1]
    label = "Resistant" if prob >= 0.5 else "Susceptible"
    print(f"  Prediction: {label} (probability: {prob:.4f})")

    print("  Computing SHAP values...")
    df_bg = pd.read_csv(
        matrix_path,
        index_col="SAMPLE",
        usecols=["SAMPLE"] + list(feature_vector.index),
    ).dropna().sample(100, random_state=42)

    explainer = shap.TreeExplainer(
        rf,
        data=df_bg,
        feature_perturbation="interventional",
        feature_names=list(feature_vector.index),
    )
    explanation = explainer(X, check_additivity=False)
    sample_exp = resistant_explanation(explanation)
    sample_exp.feature_names = [feature_label(f) for f in feature_vector.index]

    shap_series = pd.Series(sample_exp.values, index=feature_vector.index)
    shap_series = shap_series[shap_series != 0]
    top_shap_details = []
    for feat in shap_series.abs().nlargest(20).index:
        top_shap_details.append({
            "position": feat,
            "gene": get_gene_for_position(feat),
            "encoded_value": int(feature_vector[feat]),
            "shap_value": round(float(shap_series[feat]), 6),
        })

    result = {
        "sample": sample_id,
        "drug": drug,
        "prediction": label,
        "probability_resistant": round(float(prob), 4),
        "top_shap_features": top_shap_details,
    }
    return result, shap_series, sample_exp


def save_waterfall(sample_exp, path, sample_id, drug, result, max_display):
    shap.plots.waterfall(sample_exp, max_display=max_display, show=False)
    plt.suptitle(
        f"{sample_id} — {drug}  {result['prediction']}  "
        f"(P(resistant)={result['probability_resistant']:.4f})",
        fontsize=11,
        y=1.02,
    )
    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


def save_shap_csv(shap_series, feature_vector, path):
    encoded = feature_vector.reindex(shap_series.index)
    shap_df = pd.DataFrame({
        "position": shap_series.index,
        "gene": [get_gene_for_position(p) for p in shap_series.index],
        "encoded_value": encoded.values,
        "shap_value": shap_series.values,
    }).sort_values("shap_value", key=abs, ascending=False)
    shap_df.to_csv(path, index=False)


def main():
    parser = argparse.ArgumentParser(
        description="VCF → resistance prediction + SHAP waterfall plot"
    )
    parser.add_argument("--vcf", required=True, help="Path to VCF or VCF.gz file")
    parser.add_argument(
        "--drug", default="RIFAMPICIN", choices=DRUGS,
        help="Drug to predict resistance for",
    )
    parser.add_argument(
        "--model-dir", default="models/",
        help="Directory containing trained .joblib models",
    )
    parser.add_argument(
        "--output-dir", default="results/predictions/",
        help="Directory to save output files",
    )
    parser.add_argument(
        "--matrix", default=str(DEFAULT_MATRIX),
        help="Path to ml_matrix.csv.gz (feature columns + SHAP background)",
    )
    parser.add_argument("--all-drugs", action="store_true",
                        help="Run prediction for all 4 drugs")
    parser.add_argument(
        "--max-display", type=int, default=15,
        help="Number of features to show on the waterfall (default: 15)",
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    sample_id = sample_id_from_vcf(args.vcf)

    print(f"\n{'='*60}")
    print(f"Sample: {sample_id}")
    print(f"VCF:    {args.vcf}")
    print(f"{'='*60}")

    print("\nLoading feature columns from ml_matrix...")
    df_cols = pd.read_csv(args.matrix, nrows=0, index_col="SAMPLE")
    feature_cols = [c for c in df_cols.columns if c.startswith("pos_")]
    print(f"  {len(feature_cols)} AMR gene positions loaded")

    print(f"\nParsing VCF: {args.vcf}")
    variants = parse_vcf(args.vcf)

    print("\nEncoding sample...")
    feature_vector = encode_sample(variants, feature_cols)

    drugs_to_run = DRUGS if args.all_drugs else [args.drug]
    all_results = {}
    for drug in drugs_to_run:
        print(f"\n--- {drug} ---")
        try:
            result, shap_series, sample_exp = predict_and_explain(
                sample_id, feature_vector, drug, args.model_dir, args.matrix
            )
            all_results[drug] = result

            csv_path = os.path.join(
                args.output_dir, f"{sample_id}_{drug}_shap_values.csv"
            )
            save_shap_csv(shap_series, feature_vector, csv_path)
            print(f"  SHAP values saved: {csv_path}")

            plot_path = os.path.join(
                args.output_dir, f"{sample_id}_{drug}_waterfall.png"
            )
            save_waterfall(
                sample_exp, plot_path, sample_id, drug, result, args.max_display
            )
            print(f"  Waterfall plot saved: {plot_path}")

        except FileNotFoundError as e:
            print(f"  SKIPPED: {e}")

    json_path = os.path.join(args.output_dir, f"{sample_id}_predictions.json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nPredictions saved: {json_path}")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for drug, res in all_results.items():
        mark = "R" if res["prediction"] == "Resistant" else "S"
        print(
            f"  [{mark}] {drug:<15}: {res['prediction']:<12} "
            f"(prob: {res['probability_resistant']:.4f})"
        )
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

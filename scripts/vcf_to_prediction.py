#!/usr/bin/env python3
"""
vcf_to_prediction.py
====================
End-to-end workflow: VCF file → resistance prediction + SHAP values

Usage:
    python3 scripts/vcf_to_prediction.py \
        --vcf test_data/ERR040120.filtered.vcf.gz \
        --drug RIFAMPICIN \
        --model-dir models/ \
        --output-dir results/predictions/
   
     # All 4 drugs at once
    python3 scripts/vcf_to_prediction.py \
        --vcf test_data/ERR040120.filtered.vcf.gz \
        --all-drugs
Output:
    results/predictions/ERR040120_RIFAMPICIN_prediction.json
    results/predictions/ERR040120_RIFAMPICIN_shap_values.csv
"""

import os
import gzip
import json
import argparse
import numpy as np
import pandas as pd
import joblib
import shap

# ============================================================
# SETTINGS
# ============================================================
DRUGS = ["RIFAMPICIN", "ISONIAZID", "ETHAMBUTOL", "PYRAZINAMIDE"]

# Nucleotide encoding (same as ml_matrix.csv.gz)
NUC_ENCODE = {"A": 1, "T": 2, "C": 3, "G": 4}

# AMR gene coordinates on H37Rv (NC_000962.3)
AMR_GENES = {
    "rpoB":  (759807,  763325),
    "katG":  (2153889, 2156111),
    "inhA":  (1674202, 1675011),
    "fabG1": (1673440, 1674183),
    "embB":  (4246514, 4249810),
    "embA":  (4243233, 4246517),
    "embC":  (4239863, 4243147),
    "pncA":  (2288681, 2289241),
    "rpsA":  (1833542, 1834987),
}
# ============================================================


def parse_vcf(vcf_path):
    """
    Parse a VCF or VCF.gz file.
    Returns a dict: {position (int): alt_allele (str)}
    Only SNPs retained (len REF == 1 and len ALT == 1).
    """
    variants = {}
    opener = gzip.open if vcf_path.endswith(".gz") else open

    with opener(vcf_path, "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 5:
                continue
            chrom, pos, _, ref, alt = parts[0], int(parts[1]), parts[2], parts[3], parts[4]

            # SNPs only
            if len(ref) != 1 or len(alt) != 1:
                continue

            variants[pos] = alt.upper()

    print(f"  Parsed {len(variants)} SNPs from VCF")
    return variants


def encode_sample(variants, feature_columns):
    """
    Encode a sample's variants as a feature vector
    matching the ml_matrix.csv.gz format.
    Missing positions → 0 (assume REF).
    """
    # Start with all zeros (REF)
    feature_vector = pd.Series(0, index=feature_columns, dtype=int)

    matched = 0
    for pos, alt in variants.items():
        col = f"pos_{pos}"
        if col in feature_vector.index:
            feature_vector[col] = NUC_ENCODE.get(alt, 0)
            matched += 1

    print(f"  {matched} variants matched to AMR gene positions")
    return feature_vector


def get_gene_for_position(pos):
    """Return gene name for a genomic position, or None."""
    pos = int(pos.replace("pos_", ""))
    for gene, (start, end) in AMR_GENES.items():
        if start <= pos <= end:
            return gene
    return "unknown"


def predict_and_explain(sample_id, feature_vector, drug, model_dir):
    """
    Load trained RF model, predict resistance,
    compute SHAP values, return structured results.
    """
    model_path = os.path.join(model_dir, f"rf_{drug}_v2.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    print(f"  Loading model: {model_path}")
    rf = joblib.load(model_path)

    # Reshape to 2D array (1 sample)
    X = pd.DataFrame([feature_vector], columns=feature_vector.index)

    # Prediction
    prob = rf.predict_proba(X)[0][1]   # probability of Resistant
    label = "Resistant" if prob >= 0.5 else "Susceptible"

    print(f"  Prediction: {label} (probability: {prob:.4f})")

    # SHAP values — interventional mode with background for numerical stability
    print("  Computing SHAP values...")
    df_bg = pd.read_csv(
        "resistance_dataset/ml_matrix.csv.gz",
        index_col="SAMPLE",
        usecols=["SAMPLE"] + list(feature_vector.index)
    ).dropna().sample(100, random_state=42)

    explainer = shap.TreeExplainer(
        rf,
        data=df_bg,
        feature_perturbation="interventional"
    )
    shap_vals = explainer.shap_values(X, check_additivity=False)

    # Handle both old (list) and new (3-D array) SHAP output formats
    if isinstance(shap_vals, list):
        shap_array = shap_vals[1][0]
    else:
        shap_array = shap_vals[0, :, 1] if shap_vals.ndim == 3 else shap_vals[0]

    shap_series = pd.Series(shap_array, index=feature_vector.index)
    # Top 20 features by absolute SHAP value
    top_shap = shap_series.abs().nlargest(20)
    top_shap_details = []
    for feat in top_shap.index:
        top_shap_details.append({
            "position":       feat,
            "gene":           get_gene_for_position(feat),
            "encoded_value":  int(feature_vector[feat]),
            "shap_value":     round(float(shap_series[feat]), 6)
        })

    result = {
        "sample":     sample_id,
        "drug":       drug,
        "prediction": label,
        "probability_resistant": round(float(prob), 4),
        "top_shap_features": top_shap_details
    }

    return result, shap_series


def main():
    parser = argparse.ArgumentParser(
        description="VCF → resistance prediction + SHAP values"
    )
    parser.add_argument("--vcf",        required=True,
                        help="Path to VCF or VCF.gz file")
    parser.add_argument("--drug",       default="RIFAMPICIN",
                        choices=DRUGS,
                        help="Drug to predict resistance for")
    parser.add_argument("--model-dir",  default="models/",
                        help="Directory containing trained .joblib models")
    parser.add_argument("--output-dir", default="results/predictions/",
                        help="Directory to save output files")
    parser.add_argument("--all-drugs",  action="store_true",
                        help="Run prediction for all 4 drugs")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Get sample ID from filename
    sample_id = os.path.basename(args.vcf).replace(
        ".filtered.vcf.gz", "").replace(".vcf.gz", "")
    print(f"\n{'='*60}")
    print(f"Sample: {sample_id}")
    print(f"VCF:    {args.vcf}")
    print(f"{'='*60}")

    # Load feature columns from ml_matrix
    print("\nLoading feature columns from ml_matrix...")
    matrix_path = "resistance_dataset/ml_matrix.csv.gz"
    df_cols = pd.read_csv(matrix_path, nrows=0, index_col="SAMPLE")
    feature_cols = [c for c in df_cols.columns if c.startswith("pos_")]
    print(f"  {len(feature_cols)} AMR gene positions loaded")

    # Parse VCF
    print(f"\nParsing VCF: {args.vcf}")
    variants = parse_vcf(args.vcf)

    # Encode sample
    print("\nEncoding sample...")
    feature_vector = encode_sample(variants, feature_cols)

    # Predict for one or all drugs
    drugs_to_run = DRUGS if args.all_drugs else [args.drug]

    all_results = {}
    for drug in drugs_to_run:
        print(f"\n--- {drug} ---")
        try:
            result, shap_series = predict_and_explain(
                sample_id, feature_vector, drug, args.model_dir
            )
            all_results[drug] = result

            # Save SHAP values CSV
            shap_path = os.path.join(
                args.output_dir,
                f"{sample_id}_{drug}_shap_values.csv"
            )
            shap_df = pd.DataFrame({
                "position":      shap_series.index,
                "gene":          [get_gene_for_position(p)
                                  for p in shap_series.index],
                "encoded_value": feature_vector.values,
                "shap_value":    shap_series.values
            })
            shap_df = shap_df.sort_values(
                "shap_value", key=abs, ascending=False
            )
            shap_df.to_csv(shap_path, index=False)
            print(f"  SHAP values saved: {shap_path}")

        except FileNotFoundError as e:
            print(f"  SKIPPED: {e}")

    # Save prediction JSON
    json_path = os.path.join(
        args.output_dir,
        f"{sample_id}_predictions.json"
    )
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nPredictions saved: {json_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for drug, res in all_results.items():
        emoji = "🔴" if res["prediction"] == "Resistant" else "🟢"
        print(f"  {emoji} {drug:<15}: {res['prediction']:<12} "
              f"(prob: {res['probability_resistant']:.4f})")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
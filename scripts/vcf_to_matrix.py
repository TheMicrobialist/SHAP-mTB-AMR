#!/usr/bin/env python3
"""
VCF to ML-Ready Feature Matrix Conversion
- Removes outlier samples
- Keeps SNPs only
- Filters to AMR gene regions using H37Rv GFF
- Applies prevalence filter
- Encodes nucleotides as: 0=REF, 1=A, 2=T, 3=C, 4=G
- Joins resistance labels
- Outputs ML-ready matrix as CSV
"""

import gzip
import csv
import argparse
from pathlib import Path
from collections import defaultdict

# ============================================================
# SETTINGS — adjust here as needed
# ============================================================

# Outlier samples to remove (from QC report)
OUTLIER_SAMPLES = {
    "ERR1034652",   # 228,929 variants
    "ERR1035353",   # 12,634 variants
    "ERR1213920",   # 11,797 variants
}

# Remove samples with fewer than this many variants (likely failed alignments)
MIN_VARIANTS = 100

# Remove samples with more than this many variants (outliers)
MAX_VARIANTS = 10000

# Minimum fraction of samples a position must appear in
MIN_PREV_FRAC = 0.0

# AMR genes to keep, by drug
AMR_GENES = {
    "RIFAMPICIN":    ["rpoB"],
    "ISONIAZID":     ["katG", "inhA", "fabG1"],
    "ETHAMBUTOL":    ["embB", "embA", "embC"],
    "PYRAZINAMIDE":  ["pncA", "rpsA"],
}

# Drug labels to include in output
DRUGS = ["ISONIAZID", "RIFAMPICIN", "ETHAMBUTOL", "PYRAZINAMIDE"]

# Nucleotide encoding
NUC_ENCODE = {"A": 1, "T": 2, "C": 3, "G": 4}

# ============================================================


def parse_gff(gff_path, target_genes):
    """
    Parse H37Rv GFF file and extract coordinates for target AMR genes.
    Returns dict: gene_name -> list of (start, end) tuples (1-based, inclusive)
    """
    gene_coords = defaultdict(list)
    all_target = set(g for genes in target_genes.values() for g in genes)

    with open(gff_path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) < 9:
                continue
            feature_type = parts[2]
            if feature_type not in ("gene", "CDS"):
                continue

            start = int(parts[3])
            end   = int(parts[4])
            attrs = parts[8]

            # Extract gene name from attributes
            gene_name = None
            for attr in attrs.split(";"):
                if attr.startswith("Name=") or attr.startswith("gene="):
                    gene_name = attr.split("=")[1].strip()
                    break

            if gene_name and gene_name in all_target:
                gene_coords[gene_name].append((start, end))

    print(f"[GFF] Found coordinates for: {list(gene_coords.keys())}")
    missing = all_target - set(gene_coords.keys())
    if missing:
        print(f"[GFF] WARNING - genes not found in GFF: {missing}")

    return gene_coords


def pos_in_amr_genes(pos, gene_coords):
    """Check if a genomic position falls within any AMR gene region."""
    pos = int(pos)
    for gene, intervals in gene_coords.items():
        for start, end in intervals:
            if start <= pos <= end:
                return gene
    return None


def load_biosample_map(biosample_path):
    """Load run accession -> biosample mapping."""
    run_to_biosample = {}
    with open(biosample_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            run = row.get("run_accession", "").strip()
            bio = row.get("biosample", "").strip()
            if run and bio:
                run_to_biosample[run] = bio
    print(f"[MAP] Loaded {len(run_to_biosample)} run->biosample mappings")
    return run_to_biosample


def load_labels(labels_path):
    """Load biosample -> resistance labels."""
    biosample_labels = {}
    with open(labels_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            biosample = row.get("accessions", "").strip()
            if biosample:
                biosample_labels[biosample] = {
                    d: row.get(d, "").strip() for d in DRUGS
                }
    print(f"[LABELS] Loaded labels for {len(biosample_labels)} biosamples")
    return biosample_labels


def encode_nucleotide(ref, alt):
    """
    Encode ALT nucleotide as integer.
    0=REF (no variant), 1=A, 2=T, 3=C, 4=G
    """
    return NUC_ENCODE.get(alt.upper(), 0)


def encode_label(val):
    """Encode R/S label as 1/0/NaN."""
    if val == "R":
        return 1
    elif val == "S":
        return 0
    return ""  # NaN in CSV


def main():
    parser = argparse.ArgumentParser(description="Build ML-ready matrix from VCF variants")
    parser.add_argument("--variants",      default="resistance_dataset/all_variants.csv.gz")
    parser.add_argument("--gff",           default="reference/GCF_000195955.2_ASM19595v2_genomic.gff")
    parser.add_argument("--biosample-map", default="resistance_dataset/biosample_to_run.tsv")
    parser.add_argument("--labels",        default="resistance_dataset/master_table_resistance.csv")
    parser.add_argument("--output",        default="resistance_dataset/ml_matrix.csv.gz")
    args = parser.parse_args()

    variants_path  = Path(args.variants)
    gff_path       = Path(args.gff)
    biosample_path = Path(args.biosample_map)
    labels_path    = Path(args.labels)
    output_path    = Path(args.output)

    # ----------------------------------------------------------
    # Step 1 — Parse GFF for AMR gene coordinates
    # ----------------------------------------------------------
    print("\n[Step 1] Parsing GFF for AMR gene coordinates...")
    gene_coords = parse_gff(gff_path, AMR_GENES)

    # ----------------------------------------------------------
    # Step 2 — Load biosample map and labels
    # ----------------------------------------------------------
    print("\n[Step 2] Loading biosample map and resistance labels...")
    run_to_biosample = load_biosample_map(biosample_path)
    biosample_labels = load_labels(labels_path)

    # ----------------------------------------------------------
    # Step 3 — First pass: count variants per sample + positions
    # ----------------------------------------------------------
    print("\n[Step 3] First pass: counting variants per sample and position...")
    sample_counts   = defaultdict(int)
    position_counts = defaultdict(int)

    with gzip.open(variants_path, "rt") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row["SAMPLE"]
            pos    = row["POS"]
            ref    = row["REF"]
            alt    = row["ALT"]

            # SNPs only
            if len(ref) != 1 or len(alt) != 1:
                continue
            # Skip outliers
            if sample in OUTLIER_SAMPLES:
                continue

            sample_counts[sample]   += 1
            position_counts[pos]    += 1

    # Determine valid samples
    valid_samples = {
        s for s, c in sample_counts.items()
        if MIN_VARIANTS <= c <= MAX_VARIANTS
    }
    print(f"    Valid samples after outlier + min/max filter: {len(valid_samples)}")

    # Determine prevalent positions (≥1% of valid samples)
    min_count = int(MIN_PREV_FRAC * len(valid_samples))
    prevalent_positions = {
        p for p, c in position_counts.items()
        if c >= min_count
    }
    print(f"    Prevalent positions (>={MIN_PREV_FRAC*100:.0f}%): {len(prevalent_positions)}")

    # ----------------------------------------------------------
    # Step 4 — Filter positions to AMR genes only
    # ----------------------------------------------------------
    print("\n[Step 4] Filtering positions to AMR gene regions...")
    amr_positions = {}   # pos -> gene_name
    for pos in prevalent_positions:
        gene = pos_in_amr_genes(pos, gene_coords)
        if gene:
            amr_positions[pos] = gene

    print(f"    Positions in AMR genes: {len(amr_positions)}")

    # Sort positions numerically for consistent column order
    sorted_positions = sorted(amr_positions.keys(), key=lambda x: int(x))
    print(f"    Final feature count: {len(sorted_positions)}")

    # ----------------------------------------------------------
    # Step 5 — Second pass: build sample x position matrix
    # ----------------------------------------------------------
    print("\n[Step 5] Second pass: building variant matrix...")
    # Initialize matrix: sample -> {pos -> encoded_value}
    matrix = {s: {} for s in valid_samples}

    with gzip.open(variants_path, "rt") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row["SAMPLE"]
            pos    = row["POS"]
            ref    = row["REF"]
            alt    = row["ALT"]

            if sample not in valid_samples:
                continue
            if pos not in amr_positions:
                continue
            if len(ref) != 1 or len(alt) != 1:
                continue

            matrix[sample][pos] = encode_nucleotide(ref, alt)

    # ----------------------------------------------------------
    # Step 6 — Join resistance labels and write output
    # ----------------------------------------------------------
    print("\n[Step 6] Joining labels and writing output...")

    col_names = [f"pos_{p}" for p in sorted_positions]
    fieldnames = ["SAMPLE"] + col_names + DRUGS

    total_written = 0
    no_label      = 0

    with gzip.open(output_path, "wt", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()

        for sample in sorted(valid_samples):
            biosample = run_to_biosample.get(sample)
            labels    = biosample_labels.get(biosample, {}) if biosample else {}

            row = {"SAMPLE": sample}

            # Encode positions: 0=REF if no variant called
            for pos in sorted_positions:
                row[f"pos_{pos}"] = matrix[sample].get(pos, 0)

            # Add drug labels
            for drug in DRUGS:
                row[drug] = encode_label(labels.get(drug, ""))

            writer.writerow(row)
            total_written += 1

            if not labels:
                no_label += 1

    print(f"\n{'='*60}")
    print(f"DONE")
    print(f"  Samples written     : {total_written}")
    print(f"  Samples no label    : {no_label}")
    print(f"  Features (columns)  : {len(sorted_positions)}")
    print(f"  Output              : {output_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

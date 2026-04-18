#!/usr/bin/env python3
"""
QC report for all_variants.csv.gz before ML matrix conversion.
Checks variant distribution, outliers, missingness, and label joinability.
"""

import gzip
import csv
import sys
import argparse
from pathlib import Path
from collections import Counter

# ============================================================
# CUTOFF SETTINGS — adjust here as needed
# ============================================================
MIN_VARIANTS     = 100      # Flag samples with fewer variants than this
MAX_VARIANTS     = 10000    # Flag samples with more variants than this (outliers)
MIN_PREV_FRAC    = 0.01     # Min fraction of samples a position must appear in (1%)
DRUGS            = ["ISONIAZID", "RIFAMPICIN", "ETHAMBUTOL", "PYRAZINAMIDE"]
# ============================================================


def main():
    parser = argparse.ArgumentParser(description="QC report for all_variants.csv.gz")
    parser.add_argument("--variants",      default="resistance_dataset/all_variants.csv.gz")
    parser.add_argument("--biosample-map", default="resistance_dataset/biosample_to_run.tsv")
    parser.add_argument("--labels",        default="resistance_dataset/master_table_resistance.csv")
    parser.add_argument("--output",        default="resistance_dataset/qc_report.txt")
    args = parser.parse_args()

    variants_path  = Path(args.variants)
    biosample_path = Path(args.biosample_map)
    labels_path    = Path(args.labels)
    output_path    = Path(args.output)

    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 60)
    log("QC REPORT — all_variants.csv.gz")
    log("=" * 60)

    # 1. Load biosample → run mapping
    log("\n[1] Loading biosample -> run mapping...")
    run_to_biosample = {}
    with open(biosample_path) as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            run = row.get("run_accession", "").strip()
            bio = row.get("biosample", "").strip()
            if run and bio:
                run_to_biosample[run] = bio
    log(f"    Run accessions mapped: {len(run_to_biosample)}")

    # 2. Load resistance labels
    log("\n[2] Loading resistance labels...")
    biosample_labels = {}
    with open(labels_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            biosample = row.get("accessions", "").strip()
            if biosample:
                biosample_labels[biosample] = {d: row.get(d, "").strip() for d in DRUGS}
    log(f"    Samples with labels: {len(biosample_labels)}")

    # 3. Parse all_variants.csv.gz
    log("\n[3] Parsing all_variants.csv.gz...")
    sample_counts   = Counter()
    position_counts = Counter()
    chroms          = set()
    alt_types       = Counter()

    with gzip.open(variants_path, "rt") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample = row["SAMPLE"]
            pos    = row["POS"]
            chrom  = row["CHROM"]
            ref    = row["REF"]
            alt    = row["ALT"]

            sample_counts[sample]   += 1
            position_counts[pos]    += 1
            chroms.add(chrom)

            # Variant type
            if len(ref) == 1 and len(alt) == 1:
                alt_types["SNP"] += 1
            elif len(ref) > len(alt):
                alt_types["DEL"] += 1
            elif len(ref) < len(alt):
                alt_types["INS"] += 1
            else:
                alt_types["OTHER"] += 1

    total_variants = sum(sample_counts.values())
    total_samples  = len(sample_counts)
    counts         = sorted(sample_counts.values())

    log(f"    Total variants     : {total_variants:,}")
    log(f"    Total samples      : {total_samples:,}")
    log(f"    Unique positions   : {len(position_counts):,}")
    log(f"    Chromosomes found  : {chroms}")

    # 4. Variant type breakdown
    log("\n[4] Variant type breakdown:")
    for vtype, count in sorted(alt_types.items(), key=lambda x: -x[1]):
        pct = 100 * count / total_variants
        log(f"    {vtype:<8}: {count:>10,}  ({pct:.1f}%)")

    # 5. Per-sample variant count distribution
    log("\n[5] Per-sample variant count distribution:")
    log(f"    Min    : {counts[0]:,}")
    log(f"    Median : {counts[len(counts)//2]:,}")
    log(f"    Mean   : {total_variants//total_samples:,}")
    log(f"    Max    : {counts[-1]:,}")

    # 6. Outlier detection
    low_samples  = [s for s, c in sample_counts.items() if c < MIN_VARIANTS]
    high_samples = [s for s, c in sample_counts.items() if c > MAX_VARIANTS]

    log(f"\n[6] Outlier detection (min={MIN_VARIANTS}, max={MAX_VARIANTS}):")
    log(f"    Samples below min : {len(low_samples)}")
    log(f"    Samples above max : {len(high_samples)}")
    if high_samples:
        log("    Top outliers:")
        for s in sorted(high_samples, key=lambda x: -sample_counts[x])[:10]:
            log(f"      {s}: {sample_counts[s]:,} variants")

    # 7. Position prevalence filter
    min_count      = int(MIN_PREV_FRAC * total_samples)
    common_pos     = {p for p, c in position_counts.items() if c >= min_count}

    log(f"\n[7] Position prevalence filter (>={MIN_PREV_FRAC*100:.0f}% samples = >={min_count}):")
    log(f"    Before filter : {len(position_counts):,}")
    log(f"    After filter  : {len(common_pos):,}")
    log(f"    Removed       : {len(position_counts) - len(common_pos):,}")

    # 8. Label join check
    log("\n[8] Label join check:")
    matched   = 0
    unmatched = []
    for run in sample_counts:
        biosample = run_to_biosample.get(run)
        if biosample and biosample in biosample_labels:
            matched += 1
        else:
            unmatched.append(run)
    log(f"    Samples with labels    : {matched:,}")
    log(f"    Samples without labels : {len(unmatched):,}")
    if unmatched[:5]:
        log(f"    Example unmatched      : {unmatched[:5]}")

    # 9. Drug label coverage
    log("\n[9] Drug label coverage (among matched samples):")
    drug_counts = Counter()
    for run in sample_counts:
        biosample = run_to_biosample.get(run)
        if biosample and biosample in biosample_labels:
            for drug in DRUGS:
                val = biosample_labels[biosample].get(drug, "")
                if val in ("R", "S"):
                    drug_counts[drug] += 1
    for drug in DRUGS:
        log(f"    {drug:<20}: {drug_counts[drug]:,} labelled samples")

    # Summary
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"  Ready for ML matrix : {'YES' if matched > 1000 else 'NO - check label join'}")
    log(f"  Samples to use      : {matched:,}")
    log(f"  Features (filtered) : {len(common_pos):,}")
    log(f"  Outliers to remove  : {len(high_samples):,}")
    log("=" * 60)

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()

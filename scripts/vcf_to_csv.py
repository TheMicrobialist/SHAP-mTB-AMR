#!/usr/bin/env python3
"""
Merge all filtered VCFs into a single long-format CSV.
Output columns: SAMPLE, CHROM, POS, REF, ALT
"""

import gzip
import csv
import sys
import argparse
from pathlib import Path


def parse_vcf(vcf_path):
    sample = vcf_path.name.replace(".filtered.vcf.gz", "")
    try:
        with gzip.open(vcf_path, "rt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                fields = line.strip().split("\t")
                if len(fields) < 5:
                    continue
                chrom, pos, ref, alt = fields[0], fields[1], fields[3], fields[4]
                yield {"SAMPLE": sample, "CHROM": chrom, "POS": pos, "REF": ref, "ALT": alt}
    except Exception as e:
        print(f"[WARNING] Failed to parse {vcf_path.name}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Merge filtered VCFs into a single long-format CSV."
    )
    parser.add_argument(
        "--vcf-root",
        default="/global/project/hpcg1553/Aspen_Nanzhen_Qiao/Noah_Git/SHAP-mTB-AMR/vcf",
        help="Root directory containing batch_* subdirectories"
    )
    parser.add_argument(
        "--output",
        default="/global/project/hpcg1553/Aspen_Nanzhen_Qiao/Noah_Git/SHAP-mTB-AMR/resistance_dataset/all_variants.csv",
        help="Output CSV path"
    )
    args = parser.parse_args()

    vcf_root = Path(args.vcf_root)
    output_csv = Path(args.output)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    if not vcf_root.exists():
        print(f"[ERROR] VCF root not found: {vcf_root}", file=sys.stderr)
        sys.exit(1)

    batches = sorted(vcf_root.glob("batch_*/"))
    if not batches:
        print(f"[ERROR] No batch_* directories found under {vcf_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(batches)} batches under {vcf_root}")
    print(f"Output: {output_csv}\n")

    total_variants = 0
    total_samples = 0
    failed_samples = []

    with open(output_csv, "w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["SAMPLE", "CHROM", "POS", "REF", "ALT"])
        writer.writeheader()

        for batch in batches:
            vcfs = sorted(batch.glob("*.filtered.vcf.gz"))
            print(f"[{batch.name}] {len(vcfs)} filtered VCFs found")

            for vcf in vcfs:
                count = 0
                try:
                    for row in parse_vcf(vcf):
                        writer.writerow(row)
                        count += 1
                    total_variants += count
                    total_samples += 1
                    print(f"  [{vcf.stem}] {count} variants written")
                except Exception as e:
                    print(f"  [WARNING] Skipping {vcf.name}: {e}", file=sys.stderr)
                    failed_samples.append(str(vcf))

    print(f"\n{'='*50}")
    print(f"Done.")
    print(f"  Samples processed : {total_samples}")
    print(f"  Total variants    : {total_variants}")
    print(f"  Failed samples    : {len(failed_samples)}")
    if failed_samples:
        failed_log = output_csv.parent / "failed_vcf_samples.txt"
        with open(failed_log, "w") as f:
            f.write("\n".join(failed_samples))
        print(f"  Failed list saved : {failed_log}")
    print(f"  Output CSV        : {output_csv}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

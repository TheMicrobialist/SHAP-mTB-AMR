

#!/bin/bash

# call_variants.sh
# Purpose: Call SNP variants from aligned BAM files for Mycobacterium tuberculosis
# Usage: call_variants.sh <bam_dir> <reference_fasta> <output_dir> [threads]

set -euo pipefail

BAM_DIR=$1
REFERENCE=$2
OUTDIR=$3
THREADS=${4:-4}

if [ -z "$BAM_DIR" ] || [ -z "$REFERENCE" ] || [ -z "$OUTDIR" ]; then
    echo "Usage: $0 <bam_dir> <reference_fasta> <output_dir> [threads]"
    exit 1
fi

mkdir -p "$OUTDIR"

module load StdEnv/2023
module load samtools
module load bcftools

echo "Starting variant calling..."
echo "BAM directory: $BAM_DIR"
echo "Reference genome: $REFERENCE"
echo "Output directory: $OUTDIR"

for bam in "${BAM_DIR}"/*.bam; do
    base=$(basename "$bam" .bam)

    echo "Processing sample: $base"

    # Use bcftools mpileup (samtools mpileup no longer supports VCF/BCF generation)
    bcftools mpileup -Ou -f "$REFERENCE" "$bam" \
        | bcftools call -mv -Oz -o "${OUTDIR}/${base}.vcf.gz"

    bcftools index "${OUTDIR}/${base}.vcf.gz"

    echo "Finished: $base"
done

echo "Variant calling complete."
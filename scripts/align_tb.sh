#!/bin/bash

# align_tb.sh
# Purpose: Align paired-end FASTQ reads from Mycobacterium tuberculosis samples
# Usage: align_tb.sh <fastq_dir> <reference_fasta> <output_dir> [threads]

set -euo pipefail

FASTQ_DIR=$1
REFERENCE=$2
OUTDIR=$3
THREADS=${4:-8}

if [ -z "$FASTQ_DIR" ] || [ -z "$REFERENCE" ] || [ -z "$OUTDIR" ]; then
    echo "Usage: $0 <fastq_dir> <reference_fasta> <output_dir> [threads]"
    exit 1
fi

mkdir -p "$OUTDIR"

module load StdEnv/2023
module load bwa
module load samtools

echo "Starting alignment..."
echo "FASTQ directory: $FASTQ_DIR"
echo "Reference genome: $REFERENCE"
echo "Output directory: $OUTDIR"
echo "Threads: $THREADS"

for r1 in "${FASTQ_DIR}"/*_1.trim.fastq; do
    r2="${r1/_1.trim.fastq/_2.trim.fastq}"
    base=$(basename "$r1" _1.trim.fastq)

    echo "Processing sample: $base"

    bwa mem -t "$THREADS" "$REFERENCE" "$r1" "$r2" \
        | samtools sort -@ "$THREADS" -o "${OUTDIR}/${base}.bam"

    samtools index "${OUTDIR}/${base}.bam"

    echo "Finished: $base"
done

echo "Alignment complete."

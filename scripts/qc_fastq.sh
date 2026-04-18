#!/bin/bash

set -euo pipefail

FASTQ_DIR=$1
OUTDIR=$2
THREADS=${3:-8}

mkdir -p "$OUTDIR"

module load StdEnv/2023
module load fastp

for r1 in "${FASTQ_DIR}"/*_1.fastq; do
    r2="${r1/_1.fastq/_2.fastq}"
    base=$(basename "$r1" _1.fastq)

    fastp \
        -i "$r1" \
        -I "$r2" \
        -o "${OUTDIR}/${base}_1.trim.fastq" \
        -O "${OUTDIR}/${base}_2.trim.fastq" \
        -h "${OUTDIR}/${base}.html" \
        -j "${OUTDIR}/${base}.json" \
        -w "$THREADS"
done
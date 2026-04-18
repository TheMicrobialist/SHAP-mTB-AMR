#!/bin/bash

# Usage: download_fastq.sh run_accessions.txt output_directory
# Downloads FASTQ files for each SRA/ENA run accession

set -euo pipefail

ACCESSION_LIST=$1
OUTDIR=$2
THREADS=${3:-8}

if [ -z "$ACCESSION_LIST" ] || [ -z "$OUTDIR" ]; then
    echo "Usage: $0 <run_accessions.txt> <output_dir> [threads]"
    exit 1
fi

mkdir -p "$OUTDIR"

module load sra-toolkit

echo "Starting FASTQ download..."
echo "Input list: $ACCESSION_LIST"
echo "Output directory: $OUTDIR"
echo "Threads: $THREADS"

while read -r run; do
    if [ -z "$run" ]; then
        continue
    fi

    echo "Downloading $run"

    fasterq-dump "$run" \
        --split-files \
        --threads "$THREADS" \
        -O "$OUTDIR"

done < "$ACCESSION_LIST"

echo "All downloads finished."
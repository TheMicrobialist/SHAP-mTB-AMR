#!/bin/bash

# Usage: download_fastq.sh run_accessions.txt output_directory [threads]
# Robust FASTQ downloader for HPC (retry + scratch-aware + skip completed)

set -euo pipefail

ACCESSION_LIST=$1
OUTDIR=$2
THREADS=${3:-4}

if [ -z "$ACCESSION_LIST" ] || [ -z "$OUTDIR" ]; then
    echo "Usage: $0 <run_accessions.txt> <output_dir> [threads]"
    exit 1
fi

mkdir -p "$OUTDIR"

module load StdEnv/2023

# Use node-local temp if available (faster and more stable)
TMP_BASE=${SLURM_TMPDIR:-/tmp}
mkdir -p "$TMP_BASE"

echo "Starting FASTQ download..."
echo "Input list: $ACCESSION_LIST"
echo "Output directory: $OUTDIR"
echo "Threads: $THREADS"
echo "Temp directory: $TMP_BASE"

total=0
success=0
failed=0

while read -r run; do
    if [ -z "$run" ]; then
        continue
    fi

    total=$((total + 1))

    # Skip if already downloaded
    if [ -f "$OUTDIR/${run}_1.fastq" ] && [ -f "$OUTDIR/${run}_2.fastq" ]; then
        echo "[$run] Already exists. Skipping."
        continue
    fi

    echo "[$run] Downloading..."

    success_flag=0

    for attempt in {1..3}; do
        echo "[$run] Attempt $attempt"

        WORKDIR="$TMP_BASE/$run"
        mkdir -p "$WORKDIR"

        # Download from ENA (avoid SRA-toolkit issues)
        prefix=${run:0:6}
        subdir=${run:0:10}

        url_1="https://ftp.sra.ebi.ac.uk/vol1/fastq/${prefix}/${subdir}/${run}_1.fastq.gz"
        url_2="https://ftp.sra.ebi.ac.uk/vol1/fastq/${prefix}/${subdir}/${run}_2.fastq.gz"

        wget -q -c --tries=3 --timeout=30 \
            -O "$WORKDIR/${run}_1.fastq.gz" "$url_1" &
        pid1=$!

        wget -q -c --tries=3 --timeout=30 \
            -O "$WORKDIR/${run}_2.fastq.gz" "$url_2" &
        pid2=$!

        wait $pid1
        status1=$?
        wait $pid2
        status2=$?

        if [ $status1 -eq 0 ] && [ $status2 -eq 0 ]; then
            mv "$WORKDIR/${run}_1.fastq.gz" "$OUTDIR/" 2>/dev/null || true
            mv "$WORKDIR/${run}_2.fastq.gz" "$OUTDIR/" 2>/dev/null || true

            rm -rf "$WORKDIR"

            echo "[$run] Download successful (ENA)"
            success=$((success + 1))
            success_flag=1
            break
        else
            echo "[$run] Attempt $attempt failed (ENA)"
            sleep 5
        fi
    done

    if [ "$success_flag" -eq 0 ]; then
        echo "[$run] FAILED after 3 attempts"
        failed=$((failed + 1))
    fi

done < "$ACCESSION_LIST"

echo "=============================="
echo "Download summary"
echo "Total:   $total"
echo "Success: $success"
echo "Failed:  $failed"
echo "=============================="
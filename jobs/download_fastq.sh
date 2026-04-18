#!/bin/bash
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=1-06:00:00
#SBATCH --output=%x_%A.out
#SBATCH --error=%x_%A.err

# Usage: sbatch download_fastq.sh run_accessions.txt output_directory
set -uo pipefail   # removed -e so one failed download doesn't kill everything

ACCESSION_LIST=$1
OUTDIR=$2
THREADS=${SLURM_CPUS_PER_TASK:-4}

# Resolve to absolute path to avoid SLURM working directory issues
ACCESSION_LIST=$(readlink -f "$ACCESSION_LIST")

# Auto-generate unique failed log file (avoid overwriting input)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FAILED_LOG="$OUTDIR/failed_accessions_${TIMESTAMP}.txt"
echo "[INFO] Failed accessions will be written to: $FAILED_LOG"

# Initialize file
: > "$FAILED_LOG"

# Prevent accidental overwrite if input file equals output file
if [ "$(readlink -f "$ACCESSION_LIST")" = "$(readlink -f "$FAILED_LOG")" ]; then
    echo "[ERROR] Input and output file are the same. Exiting to prevent data loss."
    exit 1
fi

if [ ! -s "$ACCESSION_LIST" ]; then
    echo "[INFO] No accessions to process. Exiting."
    exit 0
fi

mkdir -p "$OUTDIR"
module load StdEnv/2023
# Load GNU parallel if available, otherwise fallback
if module avail parallel &>/dev/null; then
    module load parallel
else
    echo "[WARNING] GNU parallel module not found, using xargs fallback"
fi

TMP_BASE=${SLURM_TMPDIR:-/tmp}
mkdir -p "$TMP_BASE"

# Build correct ENA URL based on accession length
get_ena_url() {
    local run=$1
    local read=$2  # 1 or 2
    local prefix="${run:0:6}"
    local len=${#run}

    if [ "$len" -eq 9 ]; then
        echo "https://ftp.sra.ebi.ac.uk/vol1/fastq/${prefix}/${run}/${run}_${read}.fastq.gz"
    elif [ "$len" -eq 10 ]; then
        local suffix="00${run: -1}"
        echo "https://ftp.sra.ebi.ac.uk/vol1/fastq/${prefix}/${suffix}/${run}/${run}_${read}.fastq.gz"
    elif [ "$len" -eq 11 ]; then
        local suffix="0${run: -2}"
        echo "https://ftp.sra.ebi.ac.uk/vol1/fastq/${prefix}/${suffix}/${run}/${run}_${read}.fastq.gz"
    fi
}

download_run() {
    local run=$1
    local outdir=$2

    # Check if R1 exists and is valid (gzip integrity check)
    if [ -f "$outdir/${run}_1.fastq.gz" ]; then
        if gunzip -t "$outdir/${run}_1.fastq.gz" 2>/dev/null; then
            echo "[$run] Valid R1 exists. Skipping."
            return 0
        else
            echo "[$run] Corrupted R1 detected. Removing and re-downloading."
            rm -f "$outdir/${run}_1.fastq.gz"
        fi
    fi

    # Also validate R2 if present (optional paired-end)
    if [ -f "$outdir/${run}_2.fastq.gz" ]; then
        if ! gunzip -t "$outdir/${run}_2.fastq.gz" 2>/dev/null; then
            echo "[$run] Corrupted R2 detected. Removing."
            rm -f "$outdir/${run}_2.fastq.gz"
        fi
    fi

    local workdir="$TMP_BASE/$run"
    mkdir -p "$workdir"

    for attempt in 1 2 3; do
        echo "[$run] Attempt $attempt"

        local url1 url2
        url1=$(get_ena_url "$run" 1)
        url2=$(get_ena_url "$run" 2)

        # Download R1 (required)
        wget -q -c --tries=3 --timeout=60 -O "$workdir/${run}_1.fastq.gz" "$url1"
        local status1=$?

        # Download R2 (optional — single-end runs won't have it)
        wget -q -c --tries=3 --timeout=60 -O "$workdir/${run}_2.fastq.gz" "$url2" || true
        # Check R2 is non-empty; if not, remove it (single-end)
        if [ ! -s "$workdir/${run}_2.fastq.gz" ]; then
            rm -f "$workdir/${run}_2.fastq.gz"
        fi

        if [ $status1 -eq 0 ] && [ -s "$workdir/${run}_1.fastq.gz" ]; then
            mv "$workdir/"*.fastq.gz "$outdir/" 2>/dev/null || true
            rm -rf "$workdir"
            echo "[$run] SUCCESS"
            return 0
        else
            echo "[$run] Attempt $attempt failed, retrying in 10s..."
            sleep 10
        fi
    done

    echo "[$run] FAILED after 3 attempts" >&2
    echo "$run" >> "$FAILED_LOG"
    rm -rf "$workdir"
    return 1
}

export -f download_run get_ena_url
export TMP_BASE OUTDIR FAILED_LOG

# Run N downloads in parallel (one per CPU)
total=0; success=0; failed=0

# Use GNU parallel across accessions — this is the key fix for CPU efficiency
if command -v parallel &>/dev/null; then
    parallel --jobs "$THREADS" --line-buffer \
        --env download_run --env get_ena_url \
        "download_run {} $OUTDIR" :::: "$ACCESSION_LIST"
else
    echo "[INFO] Using xargs fallback"
    cat "$ACCESSION_LIST" | xargs -I {} -P "$THREADS" bash -c 'download_run "$@"' _ {} "$OUTDIR"
fi

# Tally results
total=$(wc -l < "$ACCESSION_LIST")
failed=$(wc -l < "$FAILED_LOG")
success=$((total - failed))

echo "=============================="
echo "Download Summary"
echo "Total:   $total"
echo "Success: $success"
echo "Failed:  $failed"
echo "Failed list: $FAILED_LOG"
echo "=============================="
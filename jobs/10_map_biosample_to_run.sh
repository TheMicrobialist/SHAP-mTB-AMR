#!/bin/bash
#SBATCH --job-name=map_biosample
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=12:00:00
#SBATCH -o logs/map_biosample_%A.out
#SBATCH -e logs/map_biosample_%A.err

set -euo pipefail

module load StdEnv/2023

PROJECT_DIR="/global/project/hpcg1553/Aspen_Nanzhen_Qiao/Noah_Git/SHAP-mTB-AMR"
SRA_ACC="$PROJECT_DIR/resistance_dataset/sra_accessions.txt"
OUTPUT="$PROJECT_DIR/resistance_dataset/biosample_to_run.tsv"

echo "Mapping biosample accessions to SRA run accessions..."
echo "Input:  $SRA_ACC"
echo "Output: $OUTPUT"
echo "Start:  $(date)"

# Write header
echo -e "biosample\trun_accession" > "$OUTPUT"

query_biosample() {
    local biosample=$1
    local output=$2

    # Try sample_accession first, then secondary_sample_accession
    local runs
    runs=$(curl -s --retry 3 --retry-delay 5 --max-time 30 \
        "https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=sample_accession=${biosample}&fields=run_accession&format=tsv" \
        | tail -n +2)

    if [ -z "$runs" ]; then
        runs=$(curl -s --retry 3 --retry-delay 5 --max-time 30 \
            "https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=secondary_sample_accession=${biosample}&fields=run_accession&format=tsv" \
            | tail -n +2)
    fi

    if [ -n "$runs" ]; then
        while read -r run; do
            [ -n "$run" ] && flock "$output" bash -c "echo -e '${biosample}\t${run}' >> '$output'"
        done <<< "$runs"
        echo "[OK] $biosample -> $runs"
    else
        echo "[WARN] $biosample: no run accessions found"
        flock "$output" bash -c "echo -e '${biosample}\t' >> '$output'"
    fi
}

export -f query_biosample
export OUTPUT

# Run in parallel
cat "$SRA_ACC" | xargs -n 1 -P "${SLURM_CPUS_PER_TASK:-8}" \
    -I {} bash -c 'query_biosample "$@"' _ {} "$OUTPUT"

echo "Done. $(wc -l < "$OUTPUT") lines written."
echo "End: $(date)"
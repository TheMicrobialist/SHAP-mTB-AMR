#!/bin/bash
#SBATCH --job-name=qc_variants
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH -o logs/qc_variants_%A.out
#SBATCH -e logs/qc_variants_%A.err

set -euo pipefail

module load StdEnv/2020
module load python/3.8.10

PROJECT_DIR="/global/project/hpcg1553/Aspen_Nanzhen_Qiao/Noah_Git/SHAP-mTB-AMR"

echo "Start: $(date)"

python3 "$PROJECT_DIR/scripts/qc_variants.py" \
    --variants      "$PROJECT_DIR/resistance_dataset/all_variants.csv.gz" \
    --biosample-map "$PROJECT_DIR/resistance_dataset/biosample_to_run.tsv" \
    --labels        "$PROJECT_DIR/resistance_dataset/master_table_resistance.csv" \
    --output        "$PROJECT_DIR/resistance_dataset/qc_report.txt"

echo "End: $(date)"

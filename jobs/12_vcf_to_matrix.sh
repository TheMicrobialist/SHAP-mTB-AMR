#!/bin/bash
#SBATCH --job-name=vcf_to_matrix
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH -o logs/vcf_to_matrix_%A.out
#SBATCH -e logs/vcf_to_matrix_%A.err

set -euo pipefail

module load StdEnv/2020
module load python/3.8.10

PROJECT_DIR="/global/project/hpcg1553/Aspen_Nanzhen_Qiao/Noah_Git/SHAP-mTB-AMR"

echo "Start: $(date)"

python3 "$PROJECT_DIR/scripts/vcf_to_matrix.py" \
    --variants      "$PROJECT_DIR/resistance_dataset/all_variants.csv.gz" \
    --gff           "$PROJECT_DIR/reference/GCF_000195955.2_ASM19595v2_genomic.gff" \
    --biosample-map "$PROJECT_DIR/resistance_dataset/biosample_to_run.tsv" \
    --labels        "$PROJECT_DIR/resistance_dataset/master_table_resistance.csv" \
    --output        "$PROJECT_DIR/resistance_dataset/ml_matrix.csv.gz"

echo "End: $(date)"

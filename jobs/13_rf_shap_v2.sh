#!/bin/bash
#SBATCH --job-name=rf_shap_v2
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=6:00:00
#SBATCH -o logs/rf_shap_v2_%A.out
#SBATCH -e logs/rf_shap_v2_%A.err

module load StdEnv/2023
module load scipy-stack/2026a
source ~/envs/rfshap/bin/activate

PROJECT_DIR="/global/project/hpcg1553/Aspen_Nanzhen_Qiao/Noah_Git/SHAP-mTB-AMR"
mkdir -p "$PROJECT_DIR/results"

echo "Start: $(date)"

for DRUG in RIFAMPICIN ISONIAZID ETHAMBUTOL PYRAZINAMIDE; do
    echo "Processing: $DRUG"
    python3 "$PROJECT_DIR/scripts/rf_shap_v2.py" --drug "$DRUG"
done

echo "End: $(date)"

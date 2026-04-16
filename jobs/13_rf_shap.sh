#!/bin/bash
#SBATCH --job-name=rf_shap
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH -o logs/rf_shap_%A.out
#SBATCH -e logs/rf_shap_%A.err

# Environment setup
# First time: run bash scripts/setup_env.sh
# Then: sbatch jobs/rf_shap.sh

module load StdEnv/2023
module load scipy-stack/2026a
source ~/envs/rfshap/bin/activate

PROJECT_DIR="/global/project/hpcg1553/Aspen_Nanzhen_Qiao/Noah_Git/SHAP-mTB-AMR"
mkdir -p "$PROJECT_DIR/results"

echo "Start: $(date)"

# Run for all 4 drugs
for DRUG in RIFAMPICIN ISONIAZID ETHAMBUTOL PYRAZINAMIDE; do
    echo "Processing: $DRUG"
    python3 "$PROJECT_DIR/scripts/rf_shap.py" --drug "$DRUG"
done

echo "End: $(date)"

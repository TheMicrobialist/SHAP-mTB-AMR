#!/bin/bash
# setup_env.sh — Run once to create the Python environment for RF + SHAP analysis
# Usage: bash scripts/setup_env.sh

module load StdEnv/2023
module load scipy-stack/2026a

# Create virtual environment
mkdir -p ~/envs
python3 -m venv ~/envs/rfshap

# Activate and install
source ~/envs/rfshap/bin/activate
pip install --upgrade pip
pip install scikit-learn shap matplotlib pandas

echo "Environment ready."
echo "To activate: module load StdEnv/2023 scipy-stack/2026a && source ~/envs/rfshap/bin/activate"

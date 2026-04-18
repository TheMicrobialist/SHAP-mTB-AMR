#!/bin/bash
#SBATCH --job-name=download_fastq
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=qp24@queensu.ca
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err

module load StdEnv/2023

# Move to the directory where the sbatch command was submitted
cd "$SLURM_SUBMIT_DIR"

# Make the download script executable
chmod +x scripts/download_fastq.sh

# Run download on the small test set first
scripts/download_fastq.sh \
    resistance_dataset/test_runs.txt \
    fastq_test \
    8

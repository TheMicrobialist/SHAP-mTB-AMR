#!/bin/bash
#SBATCH --job-name=qc_fastq
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=qp24@queensu.ca
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err

module load StdEnv/2023
module load fastp

# Move to the directory where the sbatch command was submitted
cd "$SLURM_SUBMIT_DIR"

# Ensure QC script is executable
chmod +x scripts/qc_fastq.sh

# Run QC on downloaded FASTQ test data
scripts/qc_fastq.sh \
    fastq_test \
    fastq_qc \
    8

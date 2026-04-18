#!/bin/bash
#SBATCH --job-name=tb_pipeline
#SBATCH --cpus-per-task=8
#SBATCH --mem=20G
#SBATCH --time=4:00:00
#SBATCH --array=1-20%10
#SBATCH -o logs/%x.%A_%a.out
#SBATCH -e logs/%x.%A_%a.err

set -euo pipefail

# Clean module environment and load compatible toolchain
module --force purge
module load StdEnv/2023
module load sra-toolkit
module load fastp
module load bwa
module load samtools
module load bcftools

# Print module list for debugging in SLURM logs
module list

PROJECT_DIR="$(cd "$SLURM_SUBMIT_DIR" && pwd)"
cd "$PROJECT_DIR"

# Ensure logs directory exists (must exist before job submission for SLURM to write logs)
mkdir -p "$PROJECT_DIR/logs"

# Match pipeline threads to SLURM allocation
export THREADS=$SLURM_CPUS_PER_TASK

# Ensure pipeline output directories exist
mkdir -p "$PROJECT_DIR/fastq"
mkdir -p "$PROJECT_DIR/qc_fastq"
mkdir -p "$PROJECT_DIR/aligned_bam"
mkdir -p "$PROJECT_DIR/vcf"

RUN_LIST="$PROJECT_DIR/resistance_dataset/test20.txt"
TASK_ID=${SLURM_ARRAY_TASK_ID:-1}
RUN_ID=$(sed -n "${TASK_ID}p" "$RUN_LIST")

if [ -z "$RUN_ID" ]; then
    echo "No RUN_ID found for task ${TASK_ID}. Exiting."
    exit 1
fi

chmod +x "$PROJECT_DIR/scripts/process_tb_sample.sh"

"$PROJECT_DIR/scripts/process_tb_sample.sh" \
    "$RUN_ID" \
    "$PROJECT_DIR/fastq" \
    "$PROJECT_DIR/qc_fastq" \
    "$PROJECT_DIR/aligned_bam" \
    "$PROJECT_DIR/vcf" \
    "$PROJECT_DIR/reference/H37Rv.fasta"
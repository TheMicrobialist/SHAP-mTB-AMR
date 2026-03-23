#!/bin/bash
#SBATCH --job-name=tb_batch
#SBATCH --cpus-per-task=8
#SBATCH --mem=20G
#SBATCH --time=24:00:00
#SBATCH --array=1-1000%20
#SBATCH -o logs/%x_${BATCH}_%A_%a.out
#SBATCH -e logs/%x_${BATCH}_%A_%a.err

# !!! pre-downloaded FASTQ files

set -euo pipefail

# Clean module environment and load compatible toolchain
# module --force purge
module load StdEnv/2023
module load fastp/1.0.1
module load bwa/0.7.18
module load samtools/1.22.1
module load bcftools/1.22

# Print module list for debugging in SLURM logs
module list

BATCH=${BATCH:-aa}

echo "Running batch: $BATCH"

PROJECT_DIR="$(cd "$SLURM_SUBMIT_DIR" && pwd)"
cd "$PROJECT_DIR"

# Ensure logs directory exists (must exist before job submission for SLURM to write logs)
mkdir -p "$PROJECT_DIR/logs"

# Match pipeline threads to SLURM allocation
export THREADS=$SLURM_CPUS_PER_TASK

SCRATCH_BASE="/global/scratch/hpc6144/tb_pipeline"

# FASTQ now stored on scratch (pre-downloaded)
FASTQ_DIR="/global/scratch/hpc6144/tb_fastq/batch_${BATCH}"

# Ensure pipeline output directories exist
mkdir -p "$SCRATCH_BASE/qc_fastq/batch_${BATCH}"
mkdir -p "$SCRATCH_BASE/aligned_bam/batch_${BATCH}"
mkdir -p "$PROJECT_DIR/vcf/batch_${BATCH}"

RUN_LIST="$PROJECT_DIR/resistance_dataset/batch_${BATCH}"
TASK_ID=${SLURM_ARRAY_TASK_ID:-1}
RUN_ID=$(sed -n "${TASK_ID}p" "$RUN_LIST")

if [ -z "$RUN_ID" ]; then
    echo "No RUN_ID found for task ${TASK_ID}. Exiting."
    exit 1
fi

chmod +x "$PROJECT_DIR/scripts/process_tb_sample.sh"

"$PROJECT_DIR/scripts/process_tb_sample.sh" \
    "$RUN_ID" \
    "$FASTQ_DIR" \
    "$SCRATCH_BASE/qc_fastq/batch_${BATCH}" \
    "$SCRATCH_BASE/aligned_bam/batch_${BATCH}" \
    "$PROJECT_DIR/vcf/batch_${BATCH}" \
    "$PROJECT_DIR/reference/H37Rv.fasta"
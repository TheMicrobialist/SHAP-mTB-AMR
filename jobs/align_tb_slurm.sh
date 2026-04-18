#!/bin/bash
#SBATCH --job-name=align_tb
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=qp24@queensu.ca
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err

module load StdEnv/2023

cd "$SLURM_SUBMIT_DIR"

chmod +x scripts/align_tb.sh

# Run alignment on trimmed FASTQ files
scripts/align_tb.sh \
    fastq_qc \
    reference/H37Rv.fasta \
    aligned_bam \
    8

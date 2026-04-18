#!/bin/bash
#SBATCH --job-name=call_variants
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=qp24@queensu.ca
#SBATCH -o %x.%j.out
#SBATCH -e %x.%j.err

module load StdEnv/2023
module load samtools
module load bcftools

cd "$SLURM_SUBMIT_DIR"

chmod +x scripts/call_variants.sh

# Run SNP calling on aligned BAM files
scripts/call_variants.sh \
    aligned_bam \
    reference/H37Rv.fasta \
    vcf \
    4
